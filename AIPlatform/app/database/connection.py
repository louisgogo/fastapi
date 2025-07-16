"""
Database connection management.

@author malou
@since 2024-12-19
Note: 异步数据库连接和会话管理，提供异步数据库连接池和会话工厂
      统一使用异步数据库连接，推荐使用 get_async_db() 函数
"""

from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import get_settings, get_database_url, get_async_database_url
from app.models.base import Base

# 获取配置
settings = get_settings()

# 创建同步数据库引擎（仅用于初始化表结构）
sync_engine = create_engine(
    get_database_url(),
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    pool_pre_ping=settings.DATABASE_POOL_PRE_PING,
    echo=settings.DATABASE_ECHO,  # 开发环境下打印SQL
)

# 创建异步数据库引擎
async_engine = create_async_engine(
    get_async_database_url(),
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    pool_pre_ping=settings.DATABASE_POOL_PRE_PING,
    echo=settings.DATABASE_ECHO,  # 开发环境下打印SQL
)

# 创建同步会话工厂（仅用于兼容）
SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine
)

# 创建异步会话工厂（主要使用）
AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取异步数据库会话（推荐使用）
    
    @return AsyncGenerator[AsyncSession, None] 异步数据库会话生成器
    Note: 获取异步数据库会话，用于异步依赖注入
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_db() -> Session:
    """
    获取同步数据库会话（仅兼容性使用，不推荐）
    
    @return Session 同步数据库会话
    Note: 同步数据库会话，仅用于向后兼容，新代码应使用get_async_db()
    """
    db = SyncSessionLocal()
    try:
        return db
    finally:
        db.close()


async def create_tables() -> None:
    """
    异步创建数据库表
    
    Note: 异步创建数据库表
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables() -> None:
    """
    异步删除数据库表（谨慎使用）
    
    Note: 异步删除数据库表（谨慎使用）
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def create_tables_sync() -> None:
    """
    同步创建数据库表（仅用于初始化脚本）
    
    Note: 同步创建数据库表，仅用于应用启动时的初始化
    """
    Base.metadata.create_all(bind=sync_engine)


def drop_tables_sync() -> None:
    """
    同步删除数据库表（谨慎使用，仅用于开发环境重置）
    
    Note: 同步删除数据库表（谨慎使用）
    """
    Base.metadata.drop_all(bind=sync_engine)


async def close_async_engine() -> None:
    """
    关闭异步数据库引擎
    
    Note: 关闭异步数据库引擎，用于应用关闭时清理资源
    """
    await async_engine.dispose()


def close_sync_engine() -> None:
    """
    关闭同步数据库引擎
    
    Note: 关闭同步数据库引擎，用于应用关闭时清理资源
    """
    sync_engine.dispose()


# 兼容性别名 - 建议使用新的异步函数
get_session = get_async_db  # 推荐异步
create_all_tables = create_tables_sync  # 兼容

# 兼容性别名 - 为了向后兼容
engine = sync_engine  # 同步引擎别名
SessionLocal = SyncSessionLocal  # 同步会话工厂别名 