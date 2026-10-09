"""Esquemas Pydantic de la entidad medicion.

Incluye el payload entrante desde MQTT y el esquema de salida para la API,
con la conversión de UTC a hora local de Colombia (UTC−5, sin horario de
verano) reutilizable por la capa de endpoints.
"""

from datetime import datetime, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, StrictFloat, StrictInt, field_validator

ZONA_HORARIA_COLOMBIA = ZoneInfo("America/Bogota")


def convertir_a_hora_colombiana(momento_utc: datetime) -> str:
    """Convierte un datetime UTC al formato local 'YYYY-MM-DD HH:MM:SS'."""
    if momento_utc.tzinfo is None:
        momento_utc = momento_utc.replace(tzinfo=timezone.utc)
    local = momento_utc.astimezone(ZONA_HORARIA_COLOMBIA)
    return local.strftime("%Y-%m-%d %H:%M:%S")


class MedicionItem(BaseModel):
    """Cada medición individual dentro de un payload MQTT."""

    # Estricto: "24.6" (texto) o true/false se rechazan; ints y floats se aceptan.
    value: StrictFloat | StrictInt
    unit: str = Field(min_length=1)

    @field_validator("value")
    @classmethod
    def valor_finito(cls, valor):
        if isinstance(valor, float) and (valor != valor or valor in (float("inf"), float("-inf"))):
            raise ValueError("El valor debe ser un número finito.")
        return valor


class MedicionPayload(BaseModel):
    """Mensaje MQTT entrante; sensor_id corresponde a sensores.codigo."""

    sensor_id: str = Field(min_length=1)
    timestamp: datetime
    measurements: dict[str, MedicionItem] = Field(min_length=1)

    @field_validator("timestamp", mode="before")
    @classmethod
    def timestamp_debe_ser_texto(cls, valor):
        # Evita que un número (epoch) o booleano sea interpretado como fecha.
        if not isinstance(valor, str):
            raise ValueError("El timestamp debe ser una cadena ISO 8601.")
        return valor

    @field_validator("timestamp")
    @classmethod
    def timestamp_debe_ser_con_zona_horaria(cls, valor: datetime) -> datetime:
        if valor.tzinfo is None or valor.tzinfo.utcoffset(valor) is None:
            raise ValueError("El timestamp debe incluir la zona horaria (offset o Z).")
        return valor


class MedicionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sensor_magnitud_id: int
    valor: Decimal
    timestamp_utc: datetime
    timestamp_local: str
