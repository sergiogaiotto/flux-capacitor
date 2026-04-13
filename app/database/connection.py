"""Conexão SQLite (async) + session factory."""
import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import create_engine
from app.config import settings
from app.database.models import Base


os.makedirs("data", exist_ok=True)

# Engine async (operações da app)
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

# Engine sync (apenas para init_db)
sync_engine = create_engine(settings.DATABASE_SYNC_URL, echo=False, future=True)


async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


def init_db() -> None:
    """Cria tabelas caso não existam + seed da API key default + migrações leves."""
    Base.metadata.create_all(bind=sync_engine)
    from sqlalchemy.orm import Session
    from sqlalchemy import text
    from app.database.models import ApiKey

    # migrações idempotentes para bancos criados antes de novas colunas
    _MIGRATIONS = [
        "ALTER TABLE slides ADD COLUMN visual_type VARCHAR(32) DEFAULT 'prose'",
    ]
    with sync_engine.begin() as conn:
        for stmt in _MIGRATIONS:
            try:
                conn.execute(text(stmt))
            except Exception:
                # coluna já existe ou tabela ainda não criada — seguir adiante
                pass

    with Session(sync_engine) as s:
        exists = s.query(ApiKey).filter_by(key=settings.API_DEFAULT_KEY).first()
        if not exists:
            s.add(ApiKey(key=settings.API_DEFAULT_KEY, label="default"))
            s.commit()

    # seed dos system prompts (idempotente)
    from app.core.prompts import seed_defaults
    seed_defaults()
