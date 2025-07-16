"""
Database package.

异步优先的数据库连接，推荐使用 get_async_db() 函数
"""

from .connection import (
    SessionLocal, engine, get_db, get_session, create_tables, drop_tables,
    AsyncSessionLocal, async_engine, get_async_db, create_tables_sync, drop_tables_sync
)

__all__ = [
    "SessionLocal",  # 同步会话工厂（兼容性）
    "engine",        # 同步引擎（兼容性）
    "get_db",        # 同步依赖（兼容性）
    "get_session",   # 兼容性别名
    "create_tables", # 同步创建表（兼容性）
    "drop_tables",   # 同步删除表（兼容性）
    
    # 异步版本（推荐使用）
    "AsyncSessionLocal",  # 异步会话工厂
    "async_engine",       # 异步引擎
    "get_async_db",       # 异步依赖（推荐）
    "create_tables_sync", # 同步创建表
    "drop_tables_sync",   # 同步删除表
] 