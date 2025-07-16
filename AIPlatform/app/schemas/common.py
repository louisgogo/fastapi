"""
Common Pydantic schemas.

@author malou
@since 2024-12-19
Note: 公共Pydantic模式定义，包含通用响应格式
"""

from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

# 泛型数据类型
T = TypeVar('T')


class BaseResponse(BaseModel, Generic[T]):
    """
    Base response schema.
    
    Note: 基础响应模式，所有API响应的基类
    """
    
    code: int = Field(..., description="响应状态码")
    message: str = Field(..., description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")
    request_id: Optional[str] = Field(None, description="请求ID")


class SuccessResponse(BaseResponse[T]):
    """
    Success response schema.
    
    Note: 成功响应模式
    """
    
    code: int = Field(default=200, description="成功状态码")
    message: str = Field(default="success", description="成功消息")
    
    def __init__(self, data: Optional[T] = None, message: str = "success", 
                 code: int = 200, request_id: Optional[str] = None, **kwargs):
        """
        @param data Optional[T] 响应数据
        @param message str 响应消息
        @param code int 状态码
        @param request_id Optional[str] 请求ID
        Note: 初始化成功响应
        """
        super().__init__(
            code=code,
            message=message,
            data=data,
            request_id=request_id,
            **kwargs
        )


class ErrorResponse(BaseModel):
    """
    Error response schema.
    
    Note: 错误响应模式
    """
    
    code: int = Field(..., description="错误状态码")
    message: str = Field(..., description="错误消息")
    error: Optional[str] = Field(None, description="错误详情")
    timestamp: datetime = Field(default_factory=datetime.now, description="错误时间")
    request_id: Optional[str] = Field(None, description="请求ID")


class PaginationParams(BaseModel):
    """
    Pagination parameters schema.
    
    Note: 分页参数模式
    """
    
    page: int = Field(default=1, ge=1, description="页码")
    size: int = Field(default=20, ge=1, le=100, description="每页大小")
    
    def offset(self) -> int:
        """
        @return int 偏移量
        Note: 计算分页偏移量
        """
        return (self.page - 1) * self.size


class PaginationMeta(BaseModel):
    """
    Pagination metadata schema.
    
    Note: 分页元数据模式
    """
    
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Paginated response schema.
    
    Note: 分页响应模式
    """
    
    code: int = Field(default=200, description="响应状态码")
    message: str = Field(default="success", description="响应消息")
    data: list[T] = Field(..., description="数据列表")
    meta: PaginationMeta = Field(..., description="分页元数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")


class HealthCheckResponse(BaseModel):
    """
    Health check response schema.
    
    Note: 健康检查响应模式
    """
    
    status: str = Field(..., description="服务状态")
    timestamp: datetime = Field(default_factory=datetime.now, description="检查时间")
    version: str = Field(..., description="服务版本")
    uptime: float = Field(..., description="运行时间（秒）")
    database: bool = Field(..., description="数据库连接状态")
    ollama: bool = Field(..., description="OLLAMA服务状态") 