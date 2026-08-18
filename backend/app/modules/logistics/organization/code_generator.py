"""Generación de códigos de entidad — Fase 005.1.

El usuario dejó de inventar códigos: los genera el backend. El frontend nunca
calcula secuencias, porque no puede garantizar unicidad entre pestañas ni entre
usuarios.

Formato: ``<PREFIJO><6 dígitos>`` — ``ORG000001``, ``SED000001``, ``ALM000001``.

Sin guion, a propósito y contra el ejemplo del pedido: ``warehouses.code`` prefija
los códigos de ubicación de F022, cuyo validador exige ``^[A-Z0-9]{2,20}$``. Un
``ALM-000001`` sería rechazado allí. Aplicar la misma regla a las tres entidades
evita una excepción por entidad que alguien acabaría incumpliendo.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entity_code_counter import EntityCodeCounter

#: Prefijo por tipo de entidad. La longitud total (3 + 6 = 9) cabe de sobra en los
#: `varchar(30)` de las tres tablas y bajo el límite de 20 de F022.
ENTITY_PREFIXES: dict[str, str] = {
    "organization": "ORG",
    "branch": "SED",
    "warehouse": "ALM",
}

SEQUENCE_WIDTH = 6


class EntityCodeGenerator:
    """Reserva el siguiente código de forma segura ante concurrencia."""

    def next_code(self, db: Session, entity_type: str) -> str:
        prefix = ENTITY_PREFIXES.get(entity_type)
        if prefix is None:
            raise ValueError(f"Tipo de entidad sin prefijo definido: {entity_type}")

        counter = self._lock_counter(db, entity_type)
        value = counter.next_value
        counter.next_value = value + 1
        db.flush()
        return f"{prefix}{value:0{SEQUENCE_WIDTH}d}"

    def _lock_counter(self, db: Session, entity_type: str) -> EntityCodeCounter:
        """Fila del contador, bloqueada hasta el final de la transacción.

        `with_for_update` serializa a las peticiones concurrentes en este punto: la
        segunda espera a que la primera confirme, así que nunca leen el mismo valor.
        """
        counter = db.scalars(
            select(EntityCodeCounter)
            .where(EntityCodeCounter.entity_type == entity_type)
            .with_for_update()
        ).first()
        if counter is not None:
            return counter

        # Primera vez para este tipo. Si dos peticiones llegan a la vez, una de las
        # dos perderá la carrera del INSERT; se relee con bloqueo en lugar de
        # propagar el error, porque la fila ya existe y es lo que se necesitaba.
        counter = EntityCodeCounter(entity_type=entity_type, next_value=1)
        db.add(counter)
        try:
            db.flush()
        except Exception:
            db.rollback()
            counter = db.scalars(
                select(EntityCodeCounter)
                .where(EntityCodeCounter.entity_type == entity_type)
                .with_for_update()
            ).first()
            if counter is None:
                raise
        return counter


entity_code_generator = EntityCodeGenerator()
