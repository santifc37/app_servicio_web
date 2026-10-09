"""Conexion a PostgreSQL para el taller.

Construye la URL de conexion a partir de las variables DB_* del archivo .env,
crea el engine y la fabrica de sesiones de SQLAlchemy, y expone la dependencia
get_db para FastAPI. El esquema remoto ya existe: aqui no se genera DDL.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

_VARIABLES_REQUERIDAS = ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")

_faltantes = [nombre for nombre in _VARIABLES_REQUERIDAS if not os.getenv(nombre)]
if _faltantes:
    raise RuntimeError(
        "Faltan variables de entorno requeridas para la conexion a la base de "
        f"datos: {', '.join(_faltantes)}. Configúralas en el archivo .env."
    )

DATABASE_URL = (
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Clase base declarativa para todos los modelos ORM."""


def get_db():
    """Dependencia de FastAPI: cede una sesión y la cierra al terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
