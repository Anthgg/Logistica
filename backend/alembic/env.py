from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.database.base import Base
import app.models.registry  # noqa: F401

from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler
from sqlalchemy.dialects.postgresql import JSONB

if not hasattr(SQLiteTypeCompiler, "visit_JSONB"):
    def visit_JSONB(self, type_, **kw):
        return self.visit_JSON(type_, **kw)
    SQLiteTypeCompiler.visit_JSONB = visit_JSONB

import datetime
import uuid
from sqlalchemy import event, Engine

@event.listens_for(Engine, "connect")
def _register_sqlite_funcs(dbapi_connection, connection_record):
    if hasattr(dbapi_connection, "create_function"):
        try:
            dbapi_connection.create_function("gen_random_uuid", 0, lambda: str(uuid.uuid4()))
            dbapi_connection.create_function("now", 0, lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
        except Exception:
            pass

from alembic.operations import Operations
from alembic.ddl.sqlite import SQLiteImpl

SQLiteImpl.add_constraint = lambda self, constraint: None

_orig_create_check = Operations.create_check_constraint
_orig_drop_constraint = Operations.drop_constraint
_orig_create_fk = Operations.create_foreign_key


def _safe_create_check(self, *args, **kwargs):
    if self.migration_context.dialect.name == "sqlite":
        return None
    return _orig_create_check(self, *args, **kwargs)


def _safe_drop_constraint(self, *args, **kwargs):
    if self.migration_context.dialect.name == "sqlite":
        return None
    return _orig_drop_constraint(self, *args, **kwargs)


def _safe_create_fk(self, *args, **kwargs):
    if self.migration_context.dialect.name == "sqlite":
        return None
    return _orig_create_fk(self, *args, **kwargs)


Operations.create_check_constraint = _safe_create_check
Operations.drop_constraint = _safe_drop_constraint
Operations.create_foreign_key = _safe_create_fk

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
