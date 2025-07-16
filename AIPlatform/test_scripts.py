#!/usr/bin/env python3
"""
Test script for validating scripts functionality.

@author malou
@since 2025-01-08
"""

import os
import sys
from pathlib import Path

# 获取项目根目录的正确路径
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# 确保工作目录正确
os.chdir(project_root)

def test_environment_loading():
    """Test environment variable loading."""
    print("Testing environment loading...")
    try:
        # 测试环境变量文件是否存在
        env_file = project_root / ".env"
        if env_file.exists():
            print(f"✓ .env file found at {env_file}")
            
            # 测试python-dotenv导入
            try:
                from dotenv import load_dotenv
                load_dotenv(env_file)
                print("✓ python-dotenv import successful")
            except ImportError:
                print("⚠ python-dotenv not available, testing manual loading")
                
            return True
        else:
            print(f"✗ .env file not found at {env_file}")
            return False
    except Exception as e:
        print(f"✗ Environment loading test failed: {e}")
        return False

def test_dependencies():
    """Test dependency imports."""
    print("\nTesting dependency imports...")
    
    required_packages = [
        "uvicorn",
        "fastapi", 
        "sqlalchemy",
        "pydantic",
        "pydantic_settings",
        "dotenv"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        return False
    else:
        print("✓ All required packages available")
        return True

def test_database_imports():
    """Test database related imports."""
    print("\nTesting database imports...")
    
    try:
        from app.core.config import get_settings
        print("✓ Configuration import successful")
        
        from app.database.connection import engine, SessionLocal
        print("✓ Database connection import successful")
        
        from app.models.base import Base
        print("✓ Base model import successful")
        
        # 测试所有模型导入
        from app.models.user import User
        from app.models.api_key import APIKey
        from app.models.agent import Agent
        from app.models.api_log import APILog
        from app.models.feedback import Feedback
        print("✓ All model imports successful")
        
        return True
        
    except Exception as e:
        print(f"✗ Database import failed: {e}")
        return False

def test_script_functions():
    """Test script functions availability."""
    print("\nTesting script functions...")
    
    try:
        # 添加scripts目录到路径
        scripts_path = project_root / "scripts"
        sys.path.insert(0, str(scripts_path))
        
        # 测试start.py中的函数
        from start import load_environment, check_dependencies, check_database
        print("✓ start.py functions available")
        
        # 测试init_db.py中的函数
        from init_db import create_tables, test_database_connection
        print("✓ init_db.py functions available")
        
        return True
        
    except Exception as e:
        print(f"✗ Script functions test failed: {e}")
        return False

def test_api_key_generation():
    """Test API key generation function."""
    print("\nTesting API key generation...")
    
    try:
        import secrets
        
        def _generate_api_key() -> str:
            """Generate a secure API key."""
            return f"ak_{secrets.token_urlsafe(32)}"
        
        # 生成测试API密钥
        api_key = _generate_api_key()
        
        if api_key.startswith("ak_") and len(api_key) > 40:
            print(f"✓ API key generation successful: {api_key[:20]}...")
            return True
        else:
            print(f"✗ API key format incorrect: {api_key}")
            return False
            
    except Exception as e:
        print(f"✗ API key generation failed: {e}")
        return False

def main():
    """Main test function."""
    print("Scripts Functionality Test")
    print("=" * 40)
    
    tests = [
        test_environment_loading,
        test_dependencies,
        test_database_imports,
        test_script_functions,
        test_api_key_generation
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 40)
    print("Test Results Summary:")
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed! Scripts should work correctly.")
    else:
        print("✗ Some tests failed. Please check the issues above.")
        
        # 提供修复建议
        print("\nTroubleshooting suggestions:")
        print("1. Ensure all dependencies are installed: pip install -r requirements.txt")
        print("2. Check .env file exists and has correct configuration")
        print("3. Verify database connection settings")
        print("4. Make sure you're in the correct directory")

if __name__ == "__main__":
    main() 