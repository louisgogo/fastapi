"""
Agent model.

@author malou
@since 2024-12-19
Note: Agent配置数据模型，用于管理AI Agent配置信息
"""

from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import String, Text, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .api_log import APILog
    from .feedback import Feedback


class Agent(Base):
    """
    Agent model for AI capabilities.
    
    Note: Agent模型，存储AI Agent的配置和状态信息
    """
    
    __tablename__ = "agents"
    
    # Agent名称
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Agent名称"
    )
    
    # Agent类型
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Agent类型：nl2sql/chat/analysis等"
    )
    
    # Agent描述
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Agent功能描述"
    )
    
    # 配置信息
    config: Mapped[Optional[dict]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"),
        nullable=True,
        comment="Agent配置信息，JSON格式"
    )
    
    # 状态
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        comment="Agent状态：active/inactive/maintenance"
    )
    
    # 版本
    version: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Agent版本"
    )
    
    # 关联关系
    api_logs: Mapped[List["APILog"]] = relationship(
        "APILog",
        back_populates="agent"
    )
    
    feedback: Mapped[List["Feedback"]] = relationship(
        "Feedback",
        back_populates="agent"
    )
    
    def is_active(self) -> bool:
        """
        @return bool 是否激活
        Note: 检查Agent是否处于激活状态
        """
        return self.status == "active"
    
    def __repr__(self) -> str:
        """
        @return str Agent字符串表示
        Note: 返回Agent的可读表示
        """
        return f"<Agent(id={self.id}, name={self.name}, type={self.type}, status={self.status})>"


if __name__ == "__main__":
    """
    测试Agent模型
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.config import get_settings
    
    # 使用配置文件中的数据库连接
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    
    # 创建表
    Base.metadata.create_all(engine)
    
    # 测试创建Agent
    agent = Agent(
        name="NL2SQL Agent",
        type="nl2sql",
        description="自然语言转SQL查询Agent",
        config={"model": "llama3.2", "temperature": 0.7},
        status="active",
        version="1.0.0"
    )
    
    print("Agent模型测试通过！")
    print(f"Agent信息: {agent}")
    print(f"是否激活: {agent.is_active()}")
    print(f"Agent字典: {agent.to_dict()}") 