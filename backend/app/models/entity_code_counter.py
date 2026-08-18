"""Contador transaccional de códigos de entidad — Fase 005.1.

Una fila por tipo de entidad (`organization`, `branch`, `warehouse`). El siguiente
número se reserva bloqueando esa fila con ``SELECT … FOR UPDATE`` dentro de la misma
transacción que crea la entidad, que es el mecanismo que el proyecto ya usa para
numerar documentos (``documents/series/series_repository.py``).

Lo que **no** se hace, porque falla bajo concurrencia: ``COUNT(*) + 1`` y
``MAX(code) + 1`` sin bloqueo. Dos peticiones simultáneas leerían el mismo valor.

Se aceptan huecos: si la creación falla tras reservar el número, ese número se
pierde. Perseguir una secuencia sin huecos obligaría a serializar los rollbacks y no
aporta nada — el código identifica, no cuenta.
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, utc_now


class EntityCodeCounter(Base):
    __tablename__ = "entity_code_counters"

    #: `organization`, `branch` o `warehouse`. Es la clave primaria: hay exactamente
    #: un contador por tipo, y la unicidad la garantiza la propia PK.
    entity_type: Mapped[str] = mapped_column(String(30), primary_key=True)
    next_value: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
