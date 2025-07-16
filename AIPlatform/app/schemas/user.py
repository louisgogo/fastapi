"""
User Pydantic schemas.

@author malou
@since 2024-12-19
Note: 用户相关的Pydantic模式定义
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    """
    User base schema.
    
    Note: 用户基础模式，包含用户公共字段
    """
    
    name: str = Field(..., min_length=1, max_length=100, description="用户姓名")
    email: EmailStr = Field(..., description="用户邮箱")
    department: Optional[str] = Field(None, max_length=50, description="用户部门")


class UserCreate(UserBase):
    """
    User creation schema.
    
    Note: 用户创建模式
    """
    
    status: Optional[str] = Field(default="active", description="用户状态")


class UserUpdate(BaseModel):
    """
    User update schema.
    
    Note: 用户更新模式
    """
    
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="用户姓名")
    email: Optional[EmailStr] = Field(None, description="用户邮箱")
    department: Optional[str] = Field(None, max_length=50, description="用户部门")
    status: Optional[str] = Field(None, description="用户状态")


class UserResponse(UserBase):
    """
    User response schema.
    
    Note: 用户响应模式
    """
    
    id: uuid.UUID = Field(..., description="用户ID")
    status: str = Field(..., description="用户状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """
    User list response schema.
    
    Note: 用户列表响应模式
    """
    
    users: list[UserResponse] = Field(..., description="用户列表")
    total: int = Field(..., description="总用户数")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")


class UserStatsResponse(BaseModel):
    """
    User statistics response schema.
    
    Note: 用户统计响应模式
    """
    
    total_users: int = Field(..., description="总用户数")
    active_users: int = Field(..., description="活跃用户数")
    inactive_users: int = Field(..., description="非活跃用户数")
    suspended_users: int = Field(..., description="暂停用户数")
    departments: dict[str, int] = Field(..., description="各部门用户数") 