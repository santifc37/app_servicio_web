"""Operaciones sobre la tabla mediciones: consultas históricas e inserción.

Las consultas históricas resuelven primero los ids de sensor_magnitudes del
sensor (opcionalmente acotados a una magnitud) y luego filtran mediciones por
esos ids. Los filtros de rango se normalizan a UTC con zona horaria antes de
comparar en SQL para que Postgres nunca reciba un datetime naive.
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.medicion import Medicion
from app.models.sensor_magnitud import SensorMagnitud


def _a_utc_aware(valor: datetime) -> datetime:
    """Interpreta un datetime naive como UTC y lo devuelve con tzinfo."""
    if valor.tzinfo is None or valor.tzinfo.utcoffset(valor) is None:
        return valor.replace(tzinfo=timezone.utc)
    return valor.astimezone(timezone.utc)


def _ids_magnitudes_del_sensor(
    db: Session, sensor_id: int, magnitud: str | None = None
) -> list[int]:
    """Ids de sensor_magnitudes del sensor, acotados a una magnitud si se indica."""
    stmt = select(SensorMagnitud.id).where(SensorMagnitud.sensor_id == sensor_id)
    if magnitud is not None:
        stmt = stmt.where(SensorMagnitud.magnitud == magnitud)
    return list(db.scalars(stmt))


def get_medicion_por_id(db: Session, id: int) -> Medicion | None:
    """Devuelve una medición por su id, o None si no existe."""
    return db.get(Medicion, id)


def get_mediciones(
    db: Session,
    sensor_id: int,
    magnitud: str | None = None,
    desde: datetime | None = None,
    hasta: datetime | None = None,
    limit: int | None = None,
) -> list[Medicion]:
    """Histórico de mediciones de un sensor, de más reciente a más antigua.

    - magnitud: acota la consulta a una sola magnitud del sensor.
    - desde/hasta: rango inclusivo sobre timestamp_utc (normalizado a UTC aware).
    - limit: devuelve las N más recientes (ORDER BY timestamp_utc DESC + LIMIT).
    """
    ids_magnitudes = _ids_magnitudes_del_sensor(db, sensor_id, magnitud)
    if not ids_magnitudes:
        return []

    stmt = select(Medicion).where(Medicion.sensor_magnitud_id.in_(ids_magnitudes))
    if desde is not None:
        stmt = stmt.where(Medicion.timestamp_utc >= _a_utc_aware(desde))
    if hasta is not None:
        stmt = stmt.where(Medicion.timestamp_utc <= _a_utc_aware(hasta))
    stmt = stmt.order_by(Medicion.timestamp_utc.desc())
    if limit is not None:
        stmt = stmt.limit(limit)
    return list(db.scalars(stmt))


def get_ultima_medicion(db: Session, sensor_id: int) -> Medicion | None:
    """Devuelve la medición más reciente del sensor, o None si no tiene."""
    stmt = (
        select(Medicion)
        .join(SensorMagnitud, Medicion.sensor_magnitud_id == SensorMagnitud.id)
        .where(SensorMagnitud.sensor_id == sensor_id)
        .order_by(Medicion.timestamp_utc.desc())
        .limit(1)
    )
    return db.scalars(stmt).first()


def insertar_mediciones(db: Session, registros: list[Medicion]) -> None:
    """Inserta una lista de mediciones en una sola transacción.

    Los ids no se setean a mano: confía en el default de la secuencia
    (BIGSERIAL). Hace commit una sola vez; ante un error hace rollback y
    re-lanza la excepción.
    """
    try:
        db.add_all(registros)
        db.commit()
    except Exception:
        db.rollback()
        raise
