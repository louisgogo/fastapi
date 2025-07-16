"""
API Key model.

@author malou
@since 2024-12-19
Note: API密钥数据模型，用于API认证管理
"""

import uuid
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, JSON
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User
    from .api_log import APILog


class APIKey(Base):
    """
    API Key model for authentication.
    
    Note: API密钥模型，用于身份认证和权限控制
    """
    
    __tablename__ = "api_keys"
    
    # 关联用户ID
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        comment="关联用户ID"
    )
    
    # 密钥值
    key_value: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="API密钥值"
    )
    
    # 密钥名称
    name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="密钥名称"
    )
    
    # 权限列表
    permissions: Mapped[Optional[dict]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"),
        nullable=True,
        comment="权限配置，JSON格式"
    )
    
    # 过期时间
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="过期时间"
    )
    
    # 是否激活
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否激活"
    )
    
    # 最后使用时间
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后使用时间"
    )
    
    # 关联关系
    user: Mapped["User"] = relationship(
        "User",
        back_populates="api_keys"
    )
    
    api_logs: Mapped[List["APILog"]] = relationship(
        "APILog",
        back_populates="api_key"
    )
    
    def is_expired(self) -> bool:
        """
        @return bool 是否已过期
        Note: 检查API密钥是否已过期
        """
        if self.expires_at is None:
            return False
        return datetime.now() >= self.expires_at
    
    def is_valid(self) -> bool:
        """
        @return bool 是否有效
        Note: 检查API密钥是否有效（激活且未过期）
        """
        return self.is_active and not self.is_expired()
    
    def __repr__(self) -> str:
        """
        @return str API密钥字符串表示
        Note: 返回API密钥的可读表示
        """
        return f"<APIKey(id={self.id}, name={self.name}, is_active={self.is_active})>"


if __name__ == "__main__":
    """
    测试APIKey模型
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
    
    # 测试创建API密钥
    api_key = APIKey(
        user_id=uuid.uuid4(),
        key_value="test_key_123",
        name="测试密钥",
        permissions={"read": True, "write": False},
        is_active=True
    )
    
    print("APIKey模型测试通过！")
    print(f"API密钥信息: {api_key}")
    print(f"是否有效: {api_key.is_valid()}")
    print(f"是否过期: {api_key.is_expired()}") 