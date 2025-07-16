"""
User management API routes.

@author malou
@since 2025-01-08
Note: 用户管理API路由，使用异步数据库连接
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_async_db
from app.schemas.common import SuccessResponse, ErrorResponse
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    UserStatsResponse
)
from app.services.user_service import UserService
from app.utils.logger import LoggerAdapter

logger = LoggerAdapter(__name__)
router = APIRouter(tags=["users"])

async def get_user_service(session: AsyncSession = Depends(get_async_db)) -> UserService:
    """
    @param session AsyncSession 异步数据库会话
    @return UserService 用户服务实例
    Note: 获取用户服务实例
    """
    return UserService(session)


@router.post("/", response_model=SuccessResponse[UserResponse])
async def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    """
    @param user_data UserCreate 用户创建数据
    @param user_service UserService 用户服务实例
    @return SuccessResponse[UserResponse] 创建的用户信息
    @throws HTTPException 如果创建失败
    Note: 创建新用户
    """
    try:
        logger.info(f"Creating user with email: {user_data.email}")
        user = await user_service.create_user(user_data)
        
        logger.info(f"User created successfully: {user.id}")
        return SuccessResponse(
            data=UserResponse.model_validate(user),
            message="User created successfully"
        )
    except ValueError as e:
        logger.error(f"Failed to create user: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=SuccessResponse[UserListResponse])
async def list_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of records to return"),
    department: Optional[str] = Query(None, description="Filter by department"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    user_service: UserService = Depends(get_user_service)
):
    """
    @param skip int 跳过的记录数
    @param limit int 返回的记录数
    @param department Optional[str] 部门过滤
    @param is_active Optional[bool] 活跃状态过滤
    @param user_service UserService 用户服务实例
    @return SuccessResponse[UserListResponse] 用户列表
    Note: 获取用户列表，支持分页和过滤
    """
    try:
        logger.info(f"Getting users list: skip={skip}, limit={limit}")
        users, total = await user_service.get_users(
            skip=skip,
            limit=limit,
            department=department,
            is_active=is_active
        )
        
        user_responses = [UserResponse.model_validate(user) for user in users]
        
        return SuccessResponse(
            data=UserListResponse(
                users=user_responses,
                total=total,
                skip=skip,
                limit=limit
            ),
            message="Users retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Failed to get users list: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{user_id}", response_model=SuccessResponse[UserResponse])
async def get_user(
    user_id: str,
    user_service: UserService = Depends(get_user_service)
):
    """
    @param user_id str 用户ID（UUID字符串）
    @param user_service UserService 用户服务实例
    @return SuccessResponse[UserResponse] 用户信息
    @throws HTTPException 如果用户不存在
    Note: 根据ID获取用户
    """
    try:
        logger.info(f"Getting user: {user_id}")
        import uuid
        user_uuid = uuid.UUID(user_id)
        user = await user_service.get_user_by_id(user_uuid)
        
        if not user:
            logger.warning(f"User not found: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        return SuccessResponse(
            data=UserResponse.model_validate(user),
            message="User retrieved successfully"
        )
    except ValueError:
        logger.error(f"Invalid UUID format: {user_id}")
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{user_id}", response_model=SuccessResponse[UserResponse])
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    user_service: UserService = Depends(get_user_service)
):
    """
    @param user_id str 用户ID（UUID字符串）
    @param user_data UserUpdate 用户更新数据
    @param user_service UserService 用户服务实例
    @return SuccessResponse[UserResponse] 更新后的用户信息
    @throws HTTPException 如果用户不存在或更新失败
    Note: 更新用户信息
    """
    try:
        logger.info(f"Updating user: {user_id}")
        import uuid
        user_uuid = uuid.UUID(user_id)
        user = await user_service.update_user(user_uuid, user_data)
        
        if not user:
            logger.warning(f"User not found for update: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        logger.info(f"User updated successfully: {user_id}")
        return SuccessResponse(
            data=UserResponse.model_validate(user),
            message="User updated successfully"
        )
    except ValueError as e:
        if "invalid literal for int()" in str(e) or "badly formed hexadecimal UUID string" in str(e):
            logger.error(f"Invalid UUID format: {user_id}")
            raise HTTPException(status_code=400, detail="Invalid user ID format")
        logger.error(f"Failed to update user: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating user: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{user_id}", response_model=SuccessResponse[dict])
async def delete_user(
    user_id: str,
    user_service: UserService = Depends(get_user_service)
):
    """
    @param user_id str 用户ID（UUID字符串）
    @param user_service UserService 用户服务实例
    @return SuccessResponse[dict] 成功消息
    @throws HTTPException 如果用户不存在
    Note: 删除用户（软删除）
    """
    try:
        logger.info(f"Deleting user: {user_id}")
        import uuid
        user_uuid = uuid.UUID(user_id)
        success = await user_service.delete_user(user_uuid)
        
        if not success:
            logger.warning(f"User not found for deletion: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        logger.info(f"User deleted successfully: {user_id}")
        return SuccessResponse(
            data={"user_id": user_id},
            message="User deleted successfully"
        )
    except ValueError:
        logger.error(f"Invalid UUID format: {user_id}")
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete user: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats/overview", response_model=SuccessResponse[UserStatsResponse])
async def get_user_stats(
    user_service: UserService = Depends(get_user_service)
):
    """
    @param user_service UserService 用户服务实例
    @return SuccessResponse[UserStatsResponse] 用户统计信息
    Note: 获取用户统计概览
    """
    try:
        logger.info("Getting user statistics")
        stats = await user_service.get_user_stats()
        
        return SuccessResponse(
            data=stats,
            message="User statistics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Failed to get user statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/email/{email}", response_model=SuccessResponse[UserResponse])
async def get_user_by_email(
    email: str,
    user_service: UserService = Depends(get_user_service)
):
    """
    @param email str 用户邮箱地址
    @param user_service UserService 用户服务实例
    @return SuccessResponse[UserResponse] 用户信息
    @throws HTTPException 如果用户不存在
    Note: 根据邮箱地址获取用户
    """
    try:
        logger.info(f"Getting user by email: {email}")
        user = await user_service.get_user_by_email(email)
        
        if not user:
            logger.warning(f"User not found with email: {email}")
            raise HTTPException(status_code=404, detail="User not found")
        
        return SuccessResponse(
            data=UserResponse.model_validate(user),
            message="User retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user by email: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error") 