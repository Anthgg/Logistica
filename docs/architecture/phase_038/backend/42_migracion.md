# 42. Migración

`ab380110038dc` depende del head real `aa370110037dc`, crea 21 tablas en orden FK y revierte en orden inverso. El manifiesto de tablas es explícito y las definiciones se toman del metadata ORM de la entrega para evitar divergencia.

No se ejecuta contra producción durante la implementación. Antes de desplegar: backup, `alembic upgrade head`, smoke test, revisión de índices y plan de rollback.

