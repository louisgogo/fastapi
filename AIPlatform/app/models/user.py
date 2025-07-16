"""
User model.

@author malou
@since 2024-12-19
Note: 用户数据模型，存储用户基本信息
"""

from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .api_key import APIKey
    from .api_log import APILog
    from .feedback import Feedback


class User(Base):
    """
    User model representing system users.
    
    Note: 用户模型，包含用户基本信息和权限
    """
    
    __tablename__ = "users"
    
    # 用户姓名
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="用户姓名"
    )
    
    # 用户邮箱
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="用户邮箱"
    )
    
    # 部门
    department: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="用户部门"
    )
    
    # 用户状态
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        comment="用户状态：active/inactive/suspended"
    )
    
    # 关联关系
    api_keys: Mapped[List["APIKey"]] = relationship(
        "APIKey",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    api_logs: Mapped[List["APILog"]] = relationship(
        "APILog",
        back_populates="user"
    )
    
    feedback: Mapped[List["Feedback"]] = relationship(
        "Feedback",
        back_populates="user"
    )
    
    def __repr__(self) -> str:
        """
        @return str 用户字符串表示
        Note: 返回用户的可读表示
        """
        return f"<User(id={self.id}, name={self.name}, email={self.email})>"


if __name__ == "__main__":
    """
    测试User模型
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
    
    # 测试创建用户
    user = User(
        name="测试用户",
        email="test@example.com",
        department="技术部",
        status="active"
    )
    
    print("User模型测试通过！")
    print(f"用户信息: {user}")
    print(f"用户字典: {user.to_dict()}") 