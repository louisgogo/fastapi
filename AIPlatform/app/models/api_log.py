"""
API Log model.

@author malou
@since 2024-12-19
Note: API调用日志数据模型，记录所有API调用信息
"""

import uuid
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String, JSON
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User
    from .api_key import APIKey
    from .agent import Agent


class APILog(Base):
    """
    API Log model for tracking API calls.
    
    Note: API调用日志模型，记录API调用的详细信息
    """
    
    __tablename__ = "api_logs"
    
    # 关联用户ID
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        comment="关联用户ID"
    )
    
    # 关联API密钥ID
    api_key_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("api_keys.id"),
        nullable=True,
        comment="关联API密钥ID"
    )
    
    # 关联Agent ID
    agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id"),
        nullable=True,
        comment="关联Agent ID"
    )
    
    # 请求端点
    endpoint: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="请求端点路径"
    )
    
    # 请求方法
    method: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="HTTP请求方法"
    )
    
    # 请求数据
    request_data: Mapped[Optional[dict]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"),
        nullable=True,
        comment="请求数据，JSON格式"
    )
    
    # 响应数据
    response_data: Mapped[Optional[dict]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"),
        nullable=True,
        comment="响应数据，JSON格式"
    )
    
    # 状态码
    status_code: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="HTTP状态码"
    )
    
    # 执行时间（秒）
    execution_time: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="执行时间（秒）"
    )
    
    # 客户端IP
    client_ip: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        comment="客户端IP地址"
    )
    
    # User-Agent
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="用户代理字符串"
    )
    
    # 关联关系
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="api_logs"
    )
    
    api_key: Mapped[Optional["APIKey"]] = relationship(
        "APIKey",
        back_populates="api_logs"
    )
    
    agent: Mapped[Optional["Agent"]] = relationship(
        "Agent",
        back_populates="api_logs"
    )
    
    def is_successful(self) -> bool:
        """
        @return bool 是否成功
        Note: 判断API调用是否成功（状态码2xx）
        """
        return 200 <= self.status_code < 300
    
    def __repr__(self) -> str:
        """
        @return str API日志字符串表示
        Note: 返回API日志的可读表示
        """
        return f"<APILog(id={self.id}, endpoint={self.endpoint}, status={self.status_code})>" 