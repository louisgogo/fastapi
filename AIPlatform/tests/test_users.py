"""
Tests for user management functionality.

@author malou
@since 2025-01-08
Note: 用户管理功能测试，使用异步数据库连接
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.user import User
from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserUpdate
from app.core.exceptions import ValidationException


class TestUserService:
    """Test user service functionality."""
    
    # 为UserService测试添加异步标记
    pytestmark = pytest.mark.asyncio

    async def test_create_user_success(
        self, 
        user_service: UserService
    ):
        """
        Test successful user creation.
        
        @param user_service UserService 用户服务实例
        Note: 测试成功创建用户
        """
        # Arrange - 创建唯一的用户数据
        unique_id = str(uuid.uuid4())[:8]
        sample_user_create_data = UserCreate(
            name=f"Test User {unique_id}",
            email=f"test-{unique_id}@example.com",
            department="Finance",
            status="active"
        )
        
        # Act
        user = await user_service.create_user(sample_user_create_data)
        
        # Assert
        assert user is not None
        assert user.name == sample_user_create_data.name
        assert user.email == sample_user_create_data.email
        assert user.department == sample_user_create_data.department
        assert user.status == "active"
        assert user.id is not None

    async def test_create_user_duplicate_email_fails(
        self, 
        user_service: UserService
    ):
        """
        Test user creation fails with duplicate email.
        
        @param user_service UserService 用户服务实例
        Note: 测试重复邮箱创建用户失败
        """
        # Arrange - 创建唯一的用户数据
        unique_id = str(uuid.uuid4())[:8]
        sample_user_create_data = UserCreate(
            name=f"Test User {unique_id}",
            email=f"test-{unique_id}@example.com",
            department="Finance",
            status="active"
        )
        
        # Arrange - Create first user
        await user_service.create_user(sample_user_create_data)
        
        # Act & Assert
        with pytest.raises(ValidationException, match="already exists"):
            await user_service.create_user(sample_user_create_data)

    async def test_get_user_by_id_success(
        self, 
        user_service: UserService
    ):
        """
        Test successful user retrieval by ID.
        
        @param user_service UserService 用户服务实例
        Note: 测试通过ID成功获取用户
        """
        # Arrange - 创建唯一的用户数据
        unique_id = str(uuid.uuid4())[:8]
        sample_user_create_data = UserCreate(
            name=f"Test User {unique_id}",
            email=f"test-{unique_id}@example.com",
            department="Finance",
            status="active"
        )
        
        created_user = await user_service.create_user(sample_user_create_data)
        
        # Act
        user = await user_service.get_user_by_id(created_user.id)
        
        # Assert
        assert user is not None
        assert user.id == created_user.id
        assert user.email == sample_user_create_data.email

    async def test_get_user_by_id_not_found(self, user_service: UserService):
        """
        Test user retrieval by ID returns None for non-existent user.
        
        @param user_service UserService 用户服务实例
        Note: 测试获取不存在的用户返回None
        """
        # Act - Use a random UUID that doesn't exist
        random_uuid = uuid.uuid4()
        user = await user_service.get_user_by_id(random_uuid)
        
        # Assert
        assert user is None

    async def test_get_user_by_email_success(
        self, 
        user_service: UserService
    ):
        """
        Test successful user retrieval by email.
        
        @param user_service UserService 用户服务实例
        Note: 测试通过邮箱成功获取用户
        """
        # Arrange - 创建唯一的用户数据
        unique_id = str(uuid.uuid4())[:8]
        sample_user_create_data = UserCreate(
            name=f"Test User {unique_id}",
            email=f"test-{unique_id}@example.com",
            department="Finance",
            status="active"
        )
        
        await user_service.create_user(sample_user_create_data)
        
        # Act
        user = await user_service.get_user_by_email(sample_user_create_data.email)
        
        # Assert
        assert user is not None
        assert user.email == sample_user_create_data.email

    async def test_update_user_success(
        self, 
        user_service: UserService
    ):
        """
        Test successful user update.
        
        @param user_service UserService 用户服务实例
        Note: 测试成功更新用户
        """
        # Arrange - 创建唯一的用户数据
        unique_id = str(uuid.uuid4())[:8]
        sample_user_create_data = UserCreate(
            name=f"Test User {unique_id}",
            email=f"test-{unique_id}@example.com",
            department="Finance",
            status="active"
        )
        
        created_user = await user_service.create_user(sample_user_create_data)
        update_data = UserUpdate(name="Updated Name", department="IT", email=sample_user_create_data.email, status="active")
        
        # Act
        updated_user = await user_service.update_user(created_user.id, update_data)
        
        # Assert
        assert updated_user is not None
        assert updated_user.name == "Updated Name"
        assert updated_user.department == "IT"
        assert updated_user.email == sample_user_create_data.email  # Email unchanged

    async def test_delete_user_success(
        self, 
        user_service: UserService
    ):
        """
        Test successful user deletion.
        
        @param user_service UserService 用户服务实例
        Note: 测试成功删除用户
        """
        # Arrange - 创建唯一的用户数据
        unique_id = str(uuid.uuid4())[:8]
        sample_user_create_data = UserCreate(
            name=f"Test User {unique_id}",
            email=f"test-{unique_id}@example.com",
            department="Finance",
            status="active"
        )
        
        created_user = await user_service.create_user(sample_user_create_data)
        
        # Act
        result = await user_service.delete_user(created_user.id)
        
        # Assert
        assert result is True
        
        # Verify user is deleted
        user = await user_service.get_user_by_id(created_user.id)
        assert user is None

    async def test_get_users_with_pagination(
        self, 
        user_service: UserService
    ):
        """
        Test user list retrieval with pagination.
        
        @param user_service UserService 用户服务实例
        Note: 测试分页获取用户列表
        """
        # Arrange - Create multiple users with unique emails
        base_id = str(uuid.uuid4())[:8]
        for i in range(5):
            user_data = UserCreate(
                name=f"User {base_id}-{i}",
                email=f"user-{base_id}-{i}@example.com",
                department="Finance",
                status="active"
            )
            await user_service.create_user(user_data)
        
        # Act
        users, total = await user_service.get_users(skip=0, limit=3)
        
        # Assert
        assert len(users) == 3
        assert total >= 5  # 可能有其他测试的数据，但至少有5个

    async def test_get_user_stats(
        self, 
        user_service: UserService
    ):
        """
        Test user statistics retrieval.
        
        @param user_service UserService 用户服务实例
        Note: 测试获取用户统计信息
        """
        # Arrange - 创建唯一的用户数据
        unique_id = str(uuid.uuid4())[:8]
        sample_user_create_data = UserCreate(
            name=f"Test User {unique_id}",
            email=f"test-{unique_id}@example.com",
            department="Finance",
            status="active"
        )
        
        await user_service.create_user(sample_user_create_data)
        
        # Act
        stats = await user_service.get_user_stats()
        
        # Assert
        assert stats is not None
        assert hasattr(stats, 'total_users')
        assert stats.total_users >= 1


class TestUserAPI:
    """Test user API endpoints."""

    def test_create_user_endpoint(self, client: TestClient):
        """
        Test user creation endpoint.
        
        @param client TestClient 测试客户端
        Note: 测试用户创建API端点
        """
        # Arrange - 创建唯一的用户数据
        unique_id = str(uuid.uuid4())[:8]
        user_data = {
            "name": f"API Test User {unique_id}",
            "email": f"api-test-{unique_id}@example.com",
            "department": "IT",
            "status": "active"
        }
        
        # Act
        response = client.post("/api/v1/users/", json=user_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == user_data["name"]
        assert data["email"] == user_data["email"]

    def test_get_users_endpoint(self, client: TestClient):
        """
        Test get users endpoint.
        
        @param client TestClient 测试客户端
        Note: 测试获取用户列表API端点
        """
        # Act
        response = client.get("/api/v1/users/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data

    def test_get_user_stats_endpoint(self, client: TestClient):
        """
        Test get user stats endpoint.
        
        @param client TestClient 测试客户端
        Note: 测试获取用户统计信息API端点
        """
        # Act
        response = client.get("/api/v1/users/stats")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data 