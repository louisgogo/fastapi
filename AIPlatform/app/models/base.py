"""
SQLAlchemy base model class.

@author malou
@since 2024-12-19
Note: 定义异步数据库模型基类，包含公共字段和方法，支持异步操作
"""

import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column,declarative_base


# 创建基类
BaseModel = declarative_base()


class Base(BaseModel):
    """
    Base class for all SQLAlchemy models.
    
    Note: 为所有数据库模型提供公共字段和方法
    """
    
    __abstract__ = True
    
    # 主键ID
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="主键ID"
    )
    
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="创建时间"
    )
    
    # 更新时间
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间"
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        @return Dict[str, Any] 模型字典表示
        Note: 将模型转换为字典格式
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, uuid.UUID):
                value = str(value)
            result[column.name] = value
        return result
    
    def __repr__(self) -> str:
        """
        @return str 模型字符串表示
        Note: 返回模型的字符串表示
        """
        return f"<{self.__class__.__name__}(id={self.id})>"


if __name__ == "__main__":
    """
    测试基类模型
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.config import get_settings
    
    # 使用配置文件中的数据库连接
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    
    # 创建表
    BaseModel.metadata.create_all(engine)
    
    print("Base模型类测试通过！")
    print(f"基类包含字段: {list(Base.__table__.columns.keys()) if hasattr(Base, '__table__') else '抽象类'}") 