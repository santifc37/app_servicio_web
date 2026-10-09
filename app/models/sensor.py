"""Modelo ORM de la tabla sensores (catálogo de solo lectura)."""

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class Sensor(Base):
    __tablename__ = "sensores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    categoria: Mapped[str] = mapped_column(String(30), nullable=False)
    ubicacion: Mapped[str] = mapped_column(String(100), nullable=False)
    activo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "categoria IN ('AIRE', 'GAS', 'AGUA', 'AMBIENTE')",
            name="ck_sensores_categoria",
        ),
    )
