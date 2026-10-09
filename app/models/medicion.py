"""Modelo ORM de la tabla mediciones (histórico de mediciones IoT).

El id es BIGSERIAL en la base de datos: las inserciones no lo setean a mano,
sino que confían en el default de la secuencia.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class Medicion(Base):
    __tablename__ = "mediciones"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sensor_magnitud_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "sensor_magnitudes.id", onupdate="CASCADE", ondelete="RESTRICT",
            name="fk_mediciones_sensor_magnitud_id",
        ),
        nullable=False,
    )
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    timestamp_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    fecha_recepcion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("idx_mediciones_sensor_magnitud", "sensor_magnitud_id"),
        Index("idx_mediciones_timestamp_utc", "timestamp_utc"),
        Index(
            "idx_mediciones_magnitud_timestamp",
            "sensor_magnitud_id",
            "timestamp_utc",
        ),
    )
