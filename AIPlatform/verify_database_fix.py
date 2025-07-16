#!/usr/bin/env python3
"""
验证数据库修复脚本

@author malou
@since 2024-12-19
Note: 验证数据库连接和JSONB兼容性修复是否成功
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_config_loading():
    """测试配置加载"""
    print("1. 测试配置加载...")
    try:
        from app.core.config import get_settings
        settings = get_settings()
        print(f"   ✓ 配置加载成功")
        print(f"   数据库URL: {settings.DATABASE_URL}")
        return True
    except Exception as e:
        print(f"   ✗ 配置加载失败: {e}")
        return False

def test_model_imports():
    """测试模型导入"""
    print("2. 测试模型导入...")
    try:
        from app.models.user import User
        from app.models.agent import Agent
        from app.models.api_key import APIKey
        from app.models.api_log import APILog
        print("   ✓ 所有模型导入成功")
        return True
    except Exception as e:
        print(f"   ✗ 模型导入失败: {e}")
        return False

def test_database_connection():
    """测试数据库连接"""
    print("3. 测试数据库连接...")
    try:
        from sqlalchemy import create_engine, text
        from app.core.config import get_settings
        
        settings = get_settings()
        engine = create_engine(settings.DATABASE_URL)
        
        # 尝试连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            row = result.fetchone()
            assert row is not None and row[0] == 1
        
        print("   ✓ 数据库连接成功")
        return True
    except Exception as e:
        print(f"   ✗ 数据库连接失败: {e}")
        print("     请检查PostgreSQL服务是否启动，数据库配置是否正确")
        return False

def test_table_creation():
    """测试表创建"""
    print("4. 测试表创建...")
    try:
        from sqlalchemy import create_engine
        from app.core.config import get_settings
        from app.models.base import Base
        
        settings = get_settings()
        engine = create_engine(settings.DATABASE_URL)
        
        # 创建表
        Base.metadata.create_all(engine)
        print("   ✓ 表创建成功（包含JSONB兼容性修复）")
        return True
    except Exception as e:
        print(f"   ✗ 表创建失败: {e}")
        return False

def test_jsonb_fields():
    """测试JSONB字段"""
    print("5. 测试JSONB字段兼容性...")
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.core.config import get_settings
        from app.models.user import User
        from app.models.agent import Agent
        from app.models.api_key import APIKey
        from app.models.api_log import APILog
        import uuid
        
        settings = get_settings()
        engine = create_engine(settings.DATABASE_URL)
        Session = sessionmaker(bind=engine)
        
        with Session() as session:
            # 先创建测试用户
            test_user = User(
                name="JSONB测试用户",
                email="jsonb_test@example.com",
                department="测试部门",
                status="active"
            )
            session.add(test_user)
            session.flush()  # 获取用户ID但不提交事务
            
            # 测试Agent的config字段
            agent = Agent(
                name="测试Agent",
                type="test",
                config={"model": "test", "temperature": 0.7},
                status="active"
            )
            session.add(agent)
            session.flush()  # 获取Agent ID
            
            # 测试APIKey的permissions字段
            api_key = APIKey(
                user_id=test_user.id,  # 使用刚创建的用户ID
                key_value="test_key_jsonb",
                permissions={"read": True, "write": False},
                is_active=True
            )
            session.add(api_key)
            session.flush()  # 获取API Key ID
            
            # 测试APILog的JSON字段
            api_log = APILog(
                user_id=test_user.id,
                api_key_id=api_key.id,
                agent_id=agent.id,
                endpoint="/test",
                method="GET",
                request_data={"test": "data"},
                response_data={"result": "success"},
                status_code=200
            )
            session.add(api_log)
            
            # 一次性提交所有数据
            session.commit()
            
            # 验证JSONB数据正确存储
            saved_agent = session.query(Agent).filter_by(name="测试Agent").first()
            assert saved_agent is not None, "Agent should be saved"
            assert saved_agent.config is not None, "Agent config should not be None"
            assert saved_agent.config["model"] == "test"
            assert saved_agent.config["temperature"] == 0.7
            
            saved_api_key = session.query(APIKey).filter_by(key_value="test_key_jsonb").first()
            assert saved_api_key is not None, "API Key should be saved"
            assert saved_api_key.permissions is not None, "API Key permissions should not be None"
            assert saved_api_key.permissions["read"] is True
            assert saved_api_key.permissions["write"] is False
            
            saved_log = session.query(APILog).filter_by(endpoint="/test").first()
            assert saved_log is not None, "API Log should be saved"
            assert saved_log.request_data is not None, "Request data should not be None"
            assert saved_log.response_data is not None, "Response data should not be None"
            assert saved_log.request_data["test"] == "data"
            assert saved_log.response_data["result"] == "success"
            
            print("   ✓ JSONB字段兼容性测试成功")
            return True
    except Exception as e:
        print(f"   ✗ JSONB字段测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🔍 开始验证数据库修复...")
    print("=" * 50)
    
    tests = [
        test_config_loading,
        test_model_imports,
        test_database_connection,
        test_table_creation,
        test_jsonb_fields
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"   ✗ 测试异常: {e}")
        print()
    
    print("=" * 50)
    print(f"📊 测试结果: {passed}/{len(tests)} 通过")
    
    if passed == len(tests):
        print("🎉 所有测试通过！数据库修复成功！")
        print("\n📝 下一步操作:")
        print("1. 确保创建了正确的.env文件（从env.example复制）")
        print("2. 配置PostgreSQL连接参数")
        print("3. 运行: python -m app.services.user_service")
    else:
        print("❌ 部分测试失败，请检查配置和数据库连接")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 