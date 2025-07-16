"""
Feedback model.

@author malou
@since 2024-12-19
Note: 用户反馈数据模型，收集用户对AI服务的反馈信息
"""

import uuid
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .user import User
from .agent import Agent


class Feedback(Base):
    """
    Feedback model for user feedback on AI services.
    
    Note: 反馈模型，存储用户对AI服务的使用反馈
    """
    
    __tablename__ = "feedback"
    
    # 请求ID（关联API调用）
    request_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="关联的API请求ID"
    )
    
    # 关联用户ID
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        comment="关联用户ID"
    )
    
    # 关联Agent ID
    agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id"),
        nullable=True,
        comment="关联Agent ID"
    )
    
    # 评分（1-5星）
    rating: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="用户评分（1-5分）"
    )
    
    # 反馈文本
    feedback_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="用户反馈文本"
    )
    
    # SQL正确性
    is_sql_correct: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
        comment="生成的SQL是否正确"
    )
    
    # 改进建议
    suggestions: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="用户改进建议"
    )
    
    # 反馈类型
    feedback_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="反馈类型：bug/suggestion/praise/complaint"
    )
    
    # 优先级
    priority: Mapped[Optional[str]] = mapped_column(
        String(20),
        default="medium",
        comment="优先级：low/medium/high/urgent"
    )
    
    # 处理状态
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        comment="处理状态：pending/in_progress/resolved/closed"
    )
    
    # 关联关系
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="feedback"
    )
    
    agent: Mapped[Optional["Agent"]] = relationship(
        "Agent",
        back_populates="feedback"
    )
    
    # 约束条件
    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
    )
    
    def is_positive(self) -> bool:
        """
        @return bool 是否正面反馈
        Note: 判断反馈是否为正面评价（评分>=4）
        """
        return self.rating is not None and self.rating >= 4
    
    def is_resolved(self) -> bool:
        """
        @return bool 是否已解决
        Note: 判断反馈是否已处理完成
        """
        return self.status in ["resolved", "closed"]
    
    def __repr__(self) -> str:
        """
        @return str 反馈字符串表示
        Note: 返回反馈的可读表示
        """
        return f"<Feedback(id={self.id}, rating={self.rating}, status={self.status})>" 

