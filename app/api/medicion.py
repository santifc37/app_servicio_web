"""Endpoints GET sobre la entidad medicion (histórico de mediciones IoT)."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.sensor import sensor_o_404
from app.crud import medicion as crud_medicion
from app.database.connection import get_db
from app.models.medicion import Medicion
from app.schemas.medicion import MedicionOut, convertir_a_hora_colombiana

router = APIRouter()


def _a_utc_aware(valor: datetime) -> datetime:
    """Interpreta un datetime naive como UTC y lo devuelve con tzinfo."""
    if valor.tzinfo is None or valor.tzinfo.utcoffset(valor) is None:
        return valor.replace(tzinfo=timezone.utc)
    return valor.astimezone(timezone.utc)


def _medicion_out(medicion: Medicion) -> MedicionOut:
    """Construye el MedicionOut con timestamp_utc de la fila y local colombiano."""
    return MedicionOut(
        id=medicion.id,
        sensor_magnitud_id=medicion.sensor_magnitud_id,
        valor=medicion.valor,
        timestamp_utc=medicion.timestamp_utc,
        timestamp_local=convertir_a_hora_colombiana(medicion.timestamp_utc),
    )


@router.get("/mediciones/{medicion_id}", response_model=MedicionOut)
def obtener_medicion(medicion_id: int, db: Session = Depends(get_db)):
    """Devuelve una medición por id; 404 si no existe."""
    medicion = crud_medicion.get_medicion_por_id(db, medicion_id)
    if medicion is None:
        raise HTTPException(status_code=404, detail="Medición no encontrada")
    return _medicion_out(medicion)


@router.get("/sensores/{sensor_id}/mediciones", response_model=list[MedicionOut])
def listar_mediciones(
    sensor_id: int,
    magnitud: str | None = None,
    desde: datetime | None = None,
    hasta: datetime | None = None,
    limit: int | None = Query(None, ge=1),
    db: Session = Depends(get_db),
):
    """Histórico de mediciones de un sensor, de más reciente a más antigua.

    Filtros combinables: magnitud, rango desde/hasta (inclusivo) y limit
    (las N más recientes). 404 si el sensor no existe; 400 si desde > hasta.
    """
    sensor_o_404(db, sensor_id)

    # Normaliza a UTC aware antes de comparar: Postgres no debe ver naive.
    if desde is not None and hasta is not None:
        if _a_utc_aware(desde) > _a_utc_aware(hasta):
            raise HTTPException(
                status_code=400,
                detail="El parámetro desde no puede ser mayor que hasta",
            )

    mediciones = crud_medicion.get_mediciones(
        db,
        sensor_id=sensor_id,
        magnitud=magnitud,
        desde=desde,
        hasta=hasta,
        limit=limit,
    )
    return [_medicion_out(m) for m in mediciones]


@router.get("/sensores/{sensor_id}/ultima-medicion", response_model=MedicionOut)
def obtener_ultima_medicion(sensor_id: int, db: Session = Depends(get_db)):
    """Devuelve la medición más reciente del sensor.

    404 si el sensor no existe o si aún no tiene mediciones registradas.
    """
    sensor_o_404(db, sensor_id)
    medicion = crud_medicion.get_ultima_medicion(db, sensor_id)
    if medicion is None:
        raise HTTPException(
            status_code=404,
            detail="El sensor no tiene mediciones registradas",
        )
    return _medicion_out(medicion)
