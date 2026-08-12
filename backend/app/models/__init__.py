"""Modelos SQLAlchemy.

Las clases se importan de sus módulos concretos para evitar ciclos durante la
inicialización. ``app.database.base`` registra todos los modelos en metadata.
"""

__all__: list[str] = []
