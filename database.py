"""
Database configuration for Supabase PostgreSQL
Usando psycopg3 para compatibilidade com pgbouncer
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

load_dotenv(Path(__file__).parent / '.env')

DATABASE_URL = os.environ.get('DATABASE_URL')

# Usar psycopg (psycopg3) que tem melhor suporte para pgbouncer
# Se psycopg não disponível, usar asyncpg com configurações especiais
try:
    import psycopg
    ASYNC_DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://')
    
    engine = create_async_engine(
        ASYNC_DATABASE_URL,
        poolclass=NullPool,
        echo=False,
    )
except ImportError:
    # Fallback para asyncpg
    ASYNC_DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')
    
    engine = create_async_engine(
        ASYNC_DATABASE_URL,
        poolclass=NullPool,
        echo=False,
        connect_args={
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
        }
    )

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
