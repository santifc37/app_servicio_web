"""Endpoints GET sobre la entidad sensor_magnitud (configuración de sensores)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.sensor import sensor_o_404
from app.crud import sensor_magnitud as crud_sensor_magnitud
from app.database.connection import get_db
from app.schemas.sensor_magnitud import SensorMagnitudOut

router = APIRouter()


@router.get("/sensores/{sensor_id}/magnitudes", response_model=list[SensorMagnitudOut])
def listar_magnitudes_del_sensor(sensor_id: int, db: Session = Depends(get_db)):
    """Devuelve las magnitudes configuradas de un sensor; 404 si el sensor no existe."""
    sensor_o_404(db, sensor_id)
    return crud_sensor_magnitud.get_magnitudes_por_sensor(db, sensor_id)


@router.get("/sensor-magnitudes/{id}", response_model=SensorMagnitudOut)
def obtener_sensor_magnitud(id: int, db: Session = Depends(get_db)):
    """Devuelve una configuración de magnitud por id; 404 si no existe."""
    config = crud_sensor_magnitud.get_sensor_magnitud_por_id(db, id)
    if config is None:
        raise HTTPException(status_code=404, detail="Sensor magnitud no encontrado")
    return config
