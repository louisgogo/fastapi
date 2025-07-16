"""
Pytest configuration and fixtures.

@author malou
@since 2024-12-19
Note: 测试配置和通用固件，支持异步测试
"""

import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.database.connection import get_db, get_async_db
from app.models.base import Base
from app.services.user_service import UserService
from app.schemas.user import UserCreate

# 测试数据库配置 - 强制使用SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
ASYNC_SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# 同步数据库引擎
sync_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

# 异步数据库引擎
async_engine = create_async_engine(
    ASYNC_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

# 会话工厂
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
AsyncTestingSessionLocal = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    """
    Setup test database tables.
    
    Note: 设置测试数据库表，会话级别自动执行
    """
    # 创建所有表
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # 清理所有表
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def async_session():
    """
    Create async database session for testing with transaction rollback.
    
    @return AsyncSession 异步数据库会话
    Note: 创建测试用的异步数据库会话，使用事务回滚保证数据隔离
    """
    # 创建连接
    connection = await async_engine.connect()
    # 开始事务
    transaction = await connection.begin()
    
    # 创建会话，绑定到事务
    session = AsyncSession(bind=connection, expire_on_commit=False)
    
    try:
        yield session
    finally:
        # 关闭会话
        await session.close()
        # 回滚事务，确保测试数据不会保留
        await transaction.rollback()
        # 关闭连接
        await connection.close()


@pytest_asyncio.fixture
async def user_service(async_session: AsyncSession):
    """
    Create UserService instance for testing.
    
    @param async_session AsyncSession 异步数据库会话
    @return UserService 用户服务实例
    Note: 创建测试用的用户服务实例
    """
    return UserService(async_session)


@pytest.fixture
def sync_session():
    """
    Create sync database session for testing with transaction rollback.
    
    @return Session 同步数据库会话
    Note: 创建测试用的同步数据库会话，使用事务回滚保证数据隔离
    """
    # 创建连接
    connection = sync_engine.connect()
    # 开始事务
    transaction = connection.begin()
    
    # 创建会话，绑定到事务
    session = sessionmaker(bind=connection)()
    
    try:
        yield session
    finally:
        # 关闭会话
        session.close()
        # 回滚事务，确保测试数据不会保留
        transaction.rollback()
        # 关闭连接
        connection.close()


def get_test_db():
    """
    Override database dependency for testing.
    
    @return Session 测试数据库会话
    Note: 测试时覆盖数据库依赖
    """
    # 创建连接
    connection = sync_engine.connect()
    # 开始事务
    transaction = connection.begin()
    
    # 创建会话，绑定到事务
    session = sessionmaker(bind=connection)()
    
    try:
        yield session
    finally:
        # 关闭会话
        session.close()
        # 回滚事务，确保测试数据不会保留
        transaction.rollback()
        # 关闭连接
        connection.close()


async def get_test_async_db():
    """
    Override async database dependency for testing.
    
    @return AsyncSession 测试异步数据库会话
    Note: 测试时覆盖异步数据库依赖
    """
    # 创建连接
    connection = await async_engine.connect()
    # 开始事务
    transaction = await connection.begin()
    
    # 创建会话，绑定到事务
    session = AsyncSession(bind=connection, expire_on_commit=False)
    
    try:
        yield session
    finally:
        # 关闭会话
        await session.close()
        # 回滚事务，确保测试数据不会保留
        await transaction.rollback()
        # 关闭连接
        await connection.close()


# 覆盖数据库依赖 - 确保API测试也使用测试数据库
app.dependency_overrides[get_db] = get_test_db
app.dependency_overrides[get_async_db] = get_test_async_db


@pytest.fixture
def client():
    """
    Create test client.
    
    @return TestClient 测试客户端
    Note: 创建FastAPI测试客户端
    """
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client():
    """
    Create async test client.
    
    @return AsyncClient 异步测试客户端
    Note: 创建异步HTTP测试客户端
    """
    async with AsyncClient(base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_user_create_data():
    """
    Sample user creation data with unique email.
    
    @return UserCreate 示例用户创建数据
    Note: 测试用的示例用户数据，使用唯一邮箱避免冲突
    """
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    return UserCreate(
        name=f"Test User {unique_id}",
        email=f"test-{unique_id}@example.com",
        department="Finance",
        status="active"
    )


@pytest.fixture
def test_headers():
    """
    Test request headers.
    
    @return dict 测试请求头
    Note: 测试用的HTTP请求头
    """
    return {
        "X-API-Key": "test-api-key-123",
        "Content-Type": "application/json"
    } 