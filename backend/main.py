from pathlib import Path
import os

from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from passlib.hash import bcrypt

from database import Base, engine, get_db
from models import User, Question, Match, Result
from websocket import manager


# Clave secreta para el panel admin (configurable desde variable de entorno en Render)
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "admin1234")


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
# SCHEMA PARA NUEVA PREGUNTA
# ==========================

class QuestionCreate(BaseModel):
    question: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: str  # "A", "B", "C" o "D"


# ==========================
# PREGUNTAS INICIALES
# ==========================

@app.post("/seed-questions")
def seed_questions(db: Session = Depends(get_db)):

    existing = db.query(Question).count()

    if existing > 0:
        return {"message": "Las preguntas ya existen"}

    questions = [
        # Geografía
        {
            "question": "¿Cuál es la capital de Colombia?",
            "a": "Medellín", "b": "Bogotá", "c": "Cali", "d": "Cartagena",
            "correct": "B"
        },
        {
            "question": "¿Cuál es el río más largo del mundo?",
            "a": "Nilo", "b": "Amazonas", "c": "Yangtsé", "d": "Misisipi",
            "correct": "A"
        },
        {
            "question": "¿En qué continente está Egipto?",
            "a": "Asia", "b": "Europa", "c": "África", "d": "América",
            "correct": "C"
        },
        {
            "question": "¿Cuál es el país más grande del mundo?",
            "a": "China", "b": "Estados Unidos", "c": "Canadá", "d": "Rusia",
            "correct": "D"
        },
        # Ciencias
        {
            "question": "¿Cuántos planetas hay en el sistema solar?",
            "a": "7", "b": "8", "c": "9", "d": "10",
            "correct": "B"
        },
        {
            "question": "¿Cuál es la fórmula química del agua?",
            "a": "CO2", "b": "NaCl", "c": "H2O", "d": "O2",
            "correct": "C"
        },
        {
            "question": "¿A qué velocidad viaja la luz aproximadamente?",
            "a": "100.000 km/s", "b": "200.000 km/s", "c": "300.000 km/s", "d": "400.000 km/s",
            "correct": "C"
        },
        {
            "question": "¿Cuál es el hueso más largo del cuerpo humano?",
            "a": "Húmero", "b": "Tibia", "c": "Radio", "d": "Fémur",
            "correct": "D"
        },
        # Historia
        {
            "question": "¿En qué año llegó Colón a América?",
            "a": "1490", "b": "1492", "c": "1500", "d": "1510",
            "correct": "B"
        },
        {
            "question": "¿Quién fue el primer presidente de Colombia?",
            "a": "Simón Bolívar", "b": "Francisco de Paula Santander", "c": "Antonio Nariño", "d": "Manuel Murillo Toro",
            "correct": "A"
        },
        # Matemáticas
        {
            "question": "¿Cuánto es 2 + 2?",
            "a": "3", "b": "4", "c": "5", "d": "6",
            "correct": "B"
        },
        {
            "question": "¿Cuál es la raíz cuadrada de 144?",
            "a": "10", "b": "11", "c": "12", "d": "14",
            "correct": "C"
        },
        {
            "question": "¿Cuántos grados tiene un triángulo?",
            "a": "90°", "b": "180°", "c": "270°", "d": "360°",
            "correct": "B"
        },
        # Cultura general
        {
            "question": "¿De qué color es el cielo despejado?",
            "a": "Verde", "b": "Rojo", "c": "Azul", "d": "Amarillo",
            "correct": "C"
        },
        {
            "question": "¿Cuántos colores tiene el arcoíris?",
            "a": "5", "b": "6", "c": "7", "d": "8",
            "correct": "C"
        },
        {
            "question": "¿Cuál es el deporte más popular del mundo?",
            "a": "Baloncesto", "b": "Béisbol", "c": "Fútbol", "d": "Tenis",
            "correct": "C"
        },
        {
            "question": "¿Cuántas horas tiene un día?",
            "a": "12", "b": "20", "c": "24", "d": "48",
            "correct": "C"
        },
        {
            "question": "¿Cuántos días tiene un año bisiesto?",
            "a": "364", "b": "365", "c": "366", "d": "367",
            "correct": "C"
        },
        {
            "question": "¿Cuál es el animal más rápido del mundo?",
            "a": "León", "b": "Guepardo", "c": "Halcón peregrino", "d": "Águila",
            "correct": "C"
        },
        {
            "question": "¿En qué país se inventó el papel?",
            "a": "India", "b": "Egipto", "c": "Japón", "d": "China",
            "correct": "D"
        },
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

    return {"message": f"{len(questions)} preguntas agregadas correctamente"}


# ==========================
# ADMIN — AGREGAR PREGUNTA
# ==========================

@app.post("/admin/questions")
def add_question(
    data: QuestionCreate,
    x_admin_secret: str = Header(default=None),
    db: Session = Depends(get_db)
):
    """
    Agrega una nueva pregunta. Requiere el header X-Admin-Secret.
    Configura ADMIN_SECRET como variable de entorno en Render.
    """
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado: clave admin incorrecta"
        )

    if data.correct_answer.upper() not in ("A", "B", "C", "D"):
        raise HTTPException(
            status_code=400,
            detail="correct_answer debe ser A, B, C o D"
        )

    new_q = Question(
        question=data.question,
        option_a=data.option_a,
        option_b=data.option_b,
        option_c=data.option_c,
        option_d=data.option_d,
        correct_answer=data.correct_answer.upper()
    )

    db.add(new_q)
    db.commit()
    db.refresh(new_q)

    return {
        "message": "Pregunta creada correctamente",
        "id": new_q.id
    }


# ==========================
# ADMIN — ELIMINAR PREGUNTA
# ==========================

@app.delete("/admin/questions/{question_id}")
def delete_question(
    question_id: int,
    x_admin_secret: str = Header(default=None),
    db: Session = Depends(get_db)
):
    """
    Elimina una pregunta por ID. Requiere el header X-Admin-Secret.
    """
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado: clave admin incorrecta"
        )

    question = db.query(Question).filter(Question.id == question_id).first()

    if not question:
        raise HTTPException(
            status_code=404,
            detail="Pregunta no encontrada"
        )

    db.delete(question)
    db.commit()

    return {"message": f"Pregunta {question_id} eliminada correctamente"}


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