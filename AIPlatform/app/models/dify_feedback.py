"""
DifyFeedback model.

@author malou
@since 2024-12-19
Note: Dify反馈数据模型，存储Dify的反馈信息
"""

import uuid
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Text, Integer, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base  # 使用项目统一的Base类


class DifyFeedback(Base):
    """
    Dify feedback model.
    
    Note: Dify反馈模型，存储Dify的反馈信息
    """
    
    __tablename__ = "dify_feedback"
    
    # 业务字段（id、created_at、updated_at自动继承自Base类）
    app_id: Mapped[str] = mapped_column(
        String(255), 
        nullable=False,
        comment="应用ID"
    )
    app_name: Mapped[str] = mapped_column(
        String(255), 
        nullable=False,
        comment="应用名称"
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id"), 
        nullable=False,
        comment="关联用户ID"
    )
    workflow_run_id: Mapped[str] = mapped_column(
        String(255), 
        nullable=False,
        comment="工作流运行ID"
    )
    query: Mapped[str] = mapped_column(
        Text, 
        nullable=False,
        comment="用户查询"
    )
    sub_query: Mapped[str] = mapped_column(
        Text, 
        nullable=False,
        comment="子查询"
    )
    answer: Mapped[str] = mapped_column(
        Text, 
        nullable=False,
        comment="AI回答"
    )
    rating: Mapped[int] = mapped_column(
        Integer, 
        nullable=False,
        comment="用户评分（1-5分）"
    )
    
    # 约束条件
    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
    )
    
    def update_rating(self, rating: int) -> None:
        """
        @param rating int 新评分
        Note: 更新评分
        """
        if 1 <= rating <= 5:
            self.rating = rating
        else:
            raise ValueError("评分必须在1-5之间")
    
    def __repr__(self) -> str:
        """
        @return str 模型字符串表示
        Note: 返回模型的可读表示
        """
        return f"<DifyFeedback(id={self.id}, app_name={self.app_name}, rating={self.rating})>"
