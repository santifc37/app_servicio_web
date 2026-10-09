"""Endpoints GET sobre la entidad sensor (catálogo solo lectura)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import sensor as crud_sensor
from app.database.connection import get_db
from app.models.sensor import Sensor
from app.schemas.sensor import SensorOut

router = APIRouter()


def sensor_o_404(db: Session, sensor_id: int) -> Sensor:
    """Busca un sensor por id o responde 404 si no existe."""
    sensor = crud_sensor.get_sensor_por_id(db, sensor_id)
    if sensor is None:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")
    return sensor


@router.get("/sensores", response_model=list[SensorOut])
def listar_sensores(db: Session = Depends(get_db)):
    """Devuelve todos los sensores del catálogo."""
    return crud_sensor.get_sensores(db)


@router.get("/sensores/por-codigo/{codigo}", response_model=SensorOut)
def obtener_sensor_por_codigo(codigo: str, db: Session = Depends(get_db)):
    """Devuelve un sensor por su código (ej. AQ-001) o 404 si no existe."""
    sensor = crud_sensor.get_sensor_por_codigo(db, codigo)
    if sensor is None:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")
    return sensor


@router.get("/sensores/{sensor_id}", response_model=SensorOut)
def obtener_sensor(sensor_id: int, db: Session = Depends(get_db)):
    """Devuelve un sensor por su id o 404 si no existe."""
    return sensor_o_404(db, sensor_id)
