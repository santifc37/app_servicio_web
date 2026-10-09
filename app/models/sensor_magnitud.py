"""Modelo ORM de la tabla sensor_magnitudes (catálogo de solo lectura)."""

from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class SensorMagnitud(Base):
    __tablename__ = "sensor_magnitudes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sensor_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "sensores.id", onupdate="CASCADE", ondelete="RESTRICT",
            name="fk_sensor_magnitudes_sensor_id",
        ),
        nullable=False,
    )
    magnitud: Mapped[str] = mapped_column(String(50), nullable=False)
    unidad: Mapped[str] = mapped_column(String(20), nullable=False)
    valor_minimo: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    valor_maximo: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "sensor_id", "magnitud", name="uq_sensor_magnitudes_sensor_magnitud"
        ),
        CheckConstraint(
            "valor_minimo < valor_maximo", name="ck_sensor_magnitudes_rango"
        ),
    )
