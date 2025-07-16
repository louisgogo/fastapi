"""
API Key Pydantic schemas.

@author malou
@since 2024-12-19
Note: API密钥相关的Pydantic模式定义
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class APIKeyBase(BaseModel):
    """
    API Key base schema.
    
    Note: API密钥基础模式，包含API密钥公共字段
    """
    
    name: Optional[str] = Field(None, max_length=100, description="密钥名称")
    permissions: Optional[dict] = Field(default_factory=dict, description="权限配置")
    expires_days: Optional[int] = Field(None, ge=1, le=3650, description="有效期天数")


class APIKeyCreate(APIKeyBase):
    """
    API Key creation schema.
    
    Note: API密钥创建模式
    """
    
    user_id: uuid.UUID = Field(..., description="关联用户ID")


class APIKeyUpdate(BaseModel):
    """
    API Key update schema.
    
    Note: API密钥更新模式
    """
    
    name: Optional[str] = Field(None, max_length=100, description="密钥名称")
    permissions: Optional[dict] = Field(None, description="权限配置")
    is_active: Optional[bool] = Field(None, description="是否激活")
    expires_at: Optional[datetime] = Field(None, description="过期时间")


class APIKeyResponse(APIKeyBase):
    """
    API Key response schema.
    
    Note: API密钥响应模式
    """
    
    id: uuid.UUID = Field(..., description="密钥ID")
    key_value: str = Field(..., description="密钥值")
    user_id: uuid.UUID = Field(..., description="关联用户ID")
    is_active: bool = Field(..., description="是否激活")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    last_used_at: Optional[datetime] = Field(None, description="最后使用时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)


class APIKeyListResponse(BaseModel):
    """
    API Key list response schema.
    
    Note: API密钥列表响应模式
    """
    
    api_keys: list[APIKeyResponse] = Field(..., description="API密钥列表")
    total: int = Field(..., description="总记录数")
    skip: int = Field(..., description="跳过的记录数")
    limit: int = Field(..., description="每页记录数")


class APIKeyStatsResponse(BaseModel):
    """
    API Key statistics response schema.
    
    Note: API密钥统计响应模式
    """
    
    total_keys: int = Field(..., description="总密钥数")
    active_keys: int = Field(..., description="激活密钥数")
    expired_keys: int = Field(..., description="过期密钥数")
    inactive_keys: int = Field(..., description="非激活密钥数")


class APIKeyValidationResponse(BaseModel):
    """
    API Key validation response schema.
    
    Note: API密钥验证响应模式
    """
    
    is_valid: bool = Field(..., description="是否有效")
    user_id: Optional[uuid.UUID] = Field(None, description="关联用户ID")
    permissions: Optional[dict] = Field(None, description="权限配置")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    reason: Optional[str] = Field(None, description="无效原因") 