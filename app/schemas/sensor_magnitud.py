"""Esquema Pydantic de salida para la entidad sensor_magnitud."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class SensorMagnitudOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sensor_id: int
    magnitud: str
    unidad: str
    valor_minimo: Decimal
    valor_maximo: Decimal
