#!/usr/bin/env python3
"""
Test script for verifying scripts functionality.

@author malou
@since 2025-01-08
"""

import os
import sys
import importlib.util
from pathlib import Path

# 获取项目根目录的正确路径
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))
os.chdir(project_root)

def test_environment_loading():
    """Test environment variable loading."""
    print("Testing environment loading...")
    
    # 检查.env文件是否存在
    env_file = project_root / ".env"
    if not env_file.exists():
        print("⚠ Warning: .env file not found, creating a test version...")
        # 创建一个测试用的.env文件
        test_env_content = """
# Test environment variables
APP_NAME=AI API Platform
APP_VERSION=1.0.0
APP_DEBUG=true
SECRET_KEY=test-secret-key-at-least-32-characters-long
DATABASE_URL=sqlite:///./test.db
OLLAMA_BASE_URL=http://localhost:11434
"""
        with open(env_file, 'w') as f:
            f.write(test_env_content.strip())
        print("✓ Created test .env file")
    
    # 测试加载环境变量
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file)
        print("✓ Environment variables loaded successfully")
    except ImportError:
        print("⚠ python-dotenv not available, manual loading test...")
        # 手动加载测试
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        print("✓ Manual environment loading successful")
    
    return True

def test_database_imports():
    """Test database related imports."""
    print("Testing database imports...")
    
    try:
        from app.core.config import get_settings
        settings = get_settings()
        print(f"✓ Configuration loaded: {settings.APP_NAME}")
        
        from app.database.connection import engine
        print("✓ Database engine imported successfully")
        
        from app.models.base import Base
        from app.models.user import User
        from app.models.api_key import APIKey
        from app.models.agent import Agent
        from app.models.api_log import APILog
        from app.models.feedback import Feedback
        print("✓ All models imported successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Database import failed: {e}")
        return False

def test_start_script_imports():
    """Test start script imports and functions."""
    print("Testing start script...")
    
    try:
        # 加载start脚本模块
        start_script_path = project_root / "scripts" / "start.py"
        spec = importlib.util.spec_from_file_location("start", start_script_path)
        start_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(start_module)
        
        # 测试函数是否存在
        assert hasattr(start_module, 'load_environment'), "load_environment function missing"
        assert hasattr(start_module, 'check_dependencies'), "check_dependencies function missing"
        assert hasattr(start_module, 'check_database'), "check_database function missing"
        assert hasattr(start_module, 'check_ollama_service'), "check_ollama_service function missing"
        
        print("✓ Start script functions available")
        
        # 测试环境加载
        start_module.load_environment()
        print("✓ Start script environment loading works")
        
        return True
        
    except Exception as e:
        print(f"✗ Start script test failed: {e}")
        return False

def test_init_db_script_imports():
    """Test init_db script imports and functions."""
    print("Testing init_db script...")
    
    try:
        # 加载init_db脚本模块
        init_db_script_path = project_root / "scripts" / "init_db.py"
        spec = importlib.util.spec_from_file_location("init_db", init_db_script_path)
        init_db_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(init_db_module)
        
        # 测试函数是否存在
        assert hasattr(init_db_module, 'load_environment'), "load_environment function missing"
        assert hasattr(init_db_module, 'create_tables'), "create_tables function missing"
        assert hasattr(init_db_module, 'test_database_connection'), "test_database_connection function missing"
        assert hasattr(init_db_module, '_generate_api_key'), "_generate_api_key function missing"
        
        print("✓ Init_db script functions available")
        
        # 测试API密钥生成
        api_key = init_db_module._generate_api_key()
        assert api_key.startswith('ak_'), "API key should start with 'ak_'"
        assert len(api_key) > 20, "API key should be long enough"
        print(f"✓ API key generation works: {api_key[:10]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ Init_db script test failed: {e}")
        return False

def test_dependency_check():
    """Test dependency availability."""
    print("Testing dependencies...")
    
    required_packages = [
        "fastapi",
        "uvicorn", 
        "sqlalchemy",
        "pydantic",
        "pydantic_settings"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} available")
        except ImportError:
            missing_packages.append(package)
            print(f"✗ {package} missing")
    
    if missing_packages:
        print(f"⚠ Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("✓ All required dependencies available")
    return True

def cleanup_test_files():
    """Clean up test files."""
    test_files = [
        project_root / "test.db",
        project_root / "test.db-journal"
    ]
    
    for file_path in test_files:
        if file_path.exists():
            try:
                file_path.unlink()
                print(f"✓ Cleaned up {file_path.name}")
            except Exception as e:
                print(f"⚠ Could not clean up {file_path.name}: {e}")

def main():
    """Main test function."""
    print("Script Functionality Test")
    print("=" * 40)
    
    tests = [
        ("Environment Loading", test_environment_loading),
        ("Dependencies", test_dependency_check),
        ("Database Imports", test_database_imports),
        ("Start Script", test_start_script_imports),
        ("Init DB Script", test_init_db_script_imports),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 30)
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name} PASSED")
            else:
                failed += 1
                print(f"✗ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"✗ {test_name} ERROR: {e}")
    
    print("\n" + "=" * 40)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Scripts should work correctly.")
        print("\nNext steps:")
        print("1. Run: python scripts/init_db.py")
        print("2. Run: python scripts/start.py")
    else:
        print("⚠ Some tests failed. Please check the issues above.")
    
    # 清理测试文件
    print("\nCleaning up test files...")
    cleanup_test_files()
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 