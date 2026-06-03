from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from passlib.hash import bcrypt

from database import Base, engine, get_db
from models import User, Question, Match, Result
from websocket import manager


BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

app = FastAPI(title="Trivia Multiplayer API")


# ==========================
# CORS
# ==========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================
# ARCHIVOS ESTÁTICOS
# ==========================

app.mount(
    "/static",
    StaticFiles(directory=str(FRONTEND_DIR)),
    name="static"
)


# ==========================
# CREAR TABLAS
# ==========================

Base.metadata.create_all(bind=engine)


# ==========================
# PÁGINAS HTML
# ==========================

@app.get("/")
def root():
    return FileResponse(FRONTEND_DIR / "login.html")


@app.get("/game")
def game():
    return FileResponse(FRONTEND_DIR / "game.html")


@app.get("/ranking-page")
def ranking_page():
    return FileResponse(FRONTEND_DIR / "ranking.html")


@app.get("/health")
def health():
    return {"status": "ok"}


# ==========================
# REGISTRO
# ==========================

@app.post("/register")
def register(
    username: str,
    password: str,
    db: Session = Depends(get_db)
):

    existing_user = (
        db.query(User)
        .filter(User.username == username)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="El usuario ya existe"
        )

    new_user = User(
        username=username,
        password=bcrypt.hash(password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "Usuario registrado correctamente",
        "user_id": new_user.id
    }


# ==========================
# LOGIN
# ==========================

@app.post("/login")
def login(
    username: str,
    password: str,
    db: Session = Depends(get_db)
):

    user = (
        db.query(User)
        .filter(User.username == username)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Usuario no encontrado"
        )

    if not bcrypt.verify(password, user.password):
        raise HTTPException(
            status_code=401,
            detail="Contraseña incorrecta"
        )

    return {
        "message": "Login exitoso",
        "id": user.id,
        "username": user.username,
        "points": user.points
    }


# ==========================
# PREGUNTAS INICIALES
# ==========================

@app.post("/seed-questions")
def seed_questions(db: Session = Depends(get_db)):

    existing = db.query(Question).count()

    if existing > 0:
        return {"message": "Las preguntas ya existen"}

    questions = [
        {
            "question": "Capital de Colombia",
            "a": "Medellin",
            "b": "Bogota",
            "c": "Cali",
            "d": "Cartagena",
            "correct": "B"
        },
        {
            "question": "2 + 2",
            "a": "3",
            "b": "4",
            "c": "5",
            "d": "6",
            "correct": "B"
        },
        {
            "question": "Color del cielo",
            "a": "Azul",
            "b": "Rojo",
            "c": "Verde",
            "d": "Negro",
            "correct": "A"
        }
    ]

    for q in questions:

        db.add(
            Question(
                question=q["question"],
                option_a=q["a"],
                option_b=q["b"],
                option_c=q["c"],
                option_d=q["d"],
                correct_answer=q["correct"]
            )
        )

    db.commit()

    return {"message": "Preguntas agregadas correctamente"}


# ==========================
# LISTAR PREGUNTAS
# ==========================

@app.get("/questions")
def get_questions(
    db: Session = Depends(get_db)
):
    return db.query(Question).all()


# ==========================
# CREAR PARTIDA
# ==========================

@app.post("/create-match")
def create_match(
    db: Session = Depends(get_db)
):

    match = Match(status="waiting")

    db.add(match)
    db.commit()
    db.refresh(match)

    return {
        "match_id": match.id,
        "status": match.status
    }


# ==========================
# UNIRSE A PARTIDA
# ==========================

@app.post("/join-match")
def join_match(
    user_id: int,
    match_id: int,
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )

    match = db.query(Match).filter(
        Match.id == match_id
    ).first()

    if not match:
        raise HTTPException(
            status_code=404,
            detail="Partida no encontrada"
        )

    db.add(
        Result(
            user_id=user_id,
            match_id=match_id,
            score=0
        )
    )

    db.commit()

    return {
        "message": "Jugador unido a la partida"
    }


# ==========================
# RESPONDER
# ==========================

@app.post("/answer")
def answer_question(
    user_id: int,
    question_id: int,
    answer: str,
    db: Session = Depends(get_db)
):

    question = db.query(Question).filter(
        Question.id == question_id
    ).first()

    if not question:
        raise HTTPException(
            status_code=404,
            detail="Pregunta no encontrada"
        )

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )

    if answer.upper() == question.correct_answer:

        user.points += 100
        db.commit()

        return {
            "correct": True,
            "new_points": user.points
        }

    return {
        "correct": False,
        "new_points": user.points
    }


# ==========================
# RANKING
# ==========================

@app.get("/ranking")
def ranking(
    db: Session = Depends(get_db)
):

    users = (
        db.query(User)
        .order_by(User.points.desc())
        .all()
    )

    return [
        {
            "id": user.id,
            "username": user.username,
            "points": user.points
        }
        for user in users
    ]


# ==========================
# PODIO
# ==========================

@app.get("/podium")
def podium(
    db: Session = Depends(get_db)
):

    users = (
        db.query(User)
        .order_by(User.points.desc())
        .limit(3)
        .all()
    )

    return [
        {
            "username": user.username,
            "points": user.points
        }
        for user in users
    ]


# ==========================
# WEBSOCKET CHAT
# ==========================

@app.websocket("/ws/{username}")
async def websocket_endpoint(
    websocket: WebSocket,
    username: str
):

    await manager.connect(websocket)

    await manager.broadcast(
        f"{username} se conectó"
    )

    try:

        while True:

            message = await websocket.receive_text()

            await manager.broadcast(
                f"{username}: {message}"
            )

    except WebSocketDisconnect:

        manager.disconnect(websocket)

        await manager.broadcast(
            f"{username} salió"
        )