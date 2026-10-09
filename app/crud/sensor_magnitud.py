"""Operaciones de consulta sobre la tabla sensor_magnitudes (catálogo solo lectura)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sensor_magnitud import SensorMagnitud


def get_magnitudes_por_sensor(db: Session, sensor_id: int) -> list[SensorMagnitud]:
    """Devuelve las magnitudes configuradas de un sensor, ordenadas por id."""
    return list(
        db.scalars(
            select(SensorMagnitud)
            .where(SensorMagnitud.sensor_id == sensor_id)
            .order_by(SensorMagnitud.id)
        )
    )


def get_sensor_magnitud_por_id(db: Session, id: int) -> SensorMagnitud | None:
    """Devuelve una configuración de magnitud por su id, o None si no existe."""
    return db.get(SensorMagnitud, id)


def get_magnitud_config(
    db: Session, sensor_id: int, magnitud: str
) -> SensorMagnitud | None:
    """Devuelve la configuración (sensor_id, magnitud) o None si no existe."""
    return db.scalars(
        select(SensorMagnitud).where(
            SensorMagnitud.sensor_id == sensor_id,
            SensorMagnitud.magnitud == magnitud,
        )
    ).one_or_none()
