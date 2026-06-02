from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# URL de PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "No se encontró la variable DATABASE_URL en el archivo .env"
    )

# Crear motor de conexión
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

# Crear sesiones
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base para modelos
Base = declarative_base()


# Dependencia para FastAPI
def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()