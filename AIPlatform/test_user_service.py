#!/usr/bin/env python3
"""
用户服务测试脚本

@author malou
@since 2025-01-07
Note: 独立测试脚本，避免模块导入警告
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ.setdefault('ENVIRONMENT', 'development')

def test_user_service():
    """测试用户服务"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.base import Base
    from app.core.config import get_settings
    from app.services.user_service import UserService
    from app.schemas.user import UserCreate
    
    # 使用配置文件中的数据库连接
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL, echo=True)
    Base.metadata.create_all(engine)
    
    # 创建数据库会话
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 创建用户服务实例
        user_service = UserService(session)
        
        # 创建测试用户
        import time
        timestamp = int(time.time())
        user_data = UserCreate(
            name="测试用户",
            email=f"test_{timestamp}@example.com",  # 使用时间戳确保邮箱唯一
            department="技术部"
        )
        
        print("Creating user...")
        try:
            user = user_service.create_user(user_data)
            print(f"Created user: {user.id}")
        except Exception as e:
            print(f"用户创建异常（可能已存在）: {e}")
            # 尝试获取已存在的用户
            existing_user = user_service.get_user_by_email("test@example.com")
            if existing_user:
                print(f"使用已存在的用户: {existing_user.id}")
                user = existing_user
            else:
                raise
        
        # 获取用户统计
        print("Getting user stats...")
        stats = user_service.get_user_stats()
        print(f"User stats: total_users={stats.total_users} active_users={stats.active_users} inactive_users={stats.inactive_users} suspended_users={stats.suspended_users} departments={stats.departments}")
        
        print("✅ 用户服务测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    test_user_service() 