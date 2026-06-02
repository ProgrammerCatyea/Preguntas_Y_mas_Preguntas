from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import ForeignKey
from sqlalchemy import DateTime

from sqlalchemy.orm import relationship

from datetime import datetime

from database import Base


# ==========================
# USUARIOS
# ==========================

class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    username = Column(
        String(50),
        unique=True,
        nullable=False
    )

    password = Column(
        String(255),
        nullable=False
    )

    points = Column(
        Integer,
        default=0
    )


# ==========================
# PREGUNTAS
# ==========================

class Question(Base):
    __tablename__ = "questions"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    question = Column(
        String,
        nullable=False
    )

    option_a = Column(
        String,
        nullable=False
    )

    option_b = Column(
        String,
        nullable=False
    )

    option_c = Column(
        String,
        nullable=False
    )

    option_d = Column(
        String,
        nullable=False
    )

    correct_answer = Column(
        String(1),
        nullable=False
    )


# ==========================
# PARTIDAS
# ==========================

class Match(Base):
    __tablename__ = "matches"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    status = Column(
        String(20),
        default="waiting"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    results = relationship(
        "Result",
        back_populates="match"
    )


# ==========================
# RESULTADOS
# ==========================

class Result(Base):
    __tablename__ = "results"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    match_id = Column(
        Integer,
        ForeignKey("matches.id"),
        nullable=False
    )

    score = Column(
        Integer,
        default=0
    )

    user = relationship(
        "User"
    )

    match = relationship(
        "Match",
        back_populates="results"
    )