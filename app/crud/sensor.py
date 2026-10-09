"""Operaciones de consulta sobre la tabla sensores (catálogo solo lectura)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sensor import Sensor


def get_sensores(db: Session) -> list[Sensor]:
    """Devuelve todos los sensores ordenados por id."""
    return list(db.scalars(select(Sensor).order_by(Sensor.id)))


def get_sensor_por_id(db: Session, sensor_id: int) -> Sensor | None:
    """Devuelve un sensor por su id primario, o None si no existe."""
    return db.get(Sensor, sensor_id)


def get_sensor_por_codigo(db: Session, codigo: str) -> Sensor | None:
    """Devuelve un sensor por su código (columna codigo), o None si no existe."""
    return db.scalars(select(Sensor).where(Sensor.codigo == codigo)).one_or_none()
