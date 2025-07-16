#!/usr/bin/env python3
"""
Application startup script.

@author malou
@since 2025-01-08
"""

import os
import sys
import subprocess
from pathlib import Path

# 获取项目根目录的正确路径
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

# 确保工作目录正确
os.chdir(project_root)

def load_environment():
    """Load environment variables from .env file."""
    env_file = project_root / ".env"
    if env_file.exists():
        # 使用python-dotenv加载环境变量
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            print(f"✓ Environment variables loaded from {env_file}")
        except ImportError:
            print("Warning: python-dotenv not installed, loading .env manually")
            # 手动加载.env文件
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip().strip('"').strip("'")
    else:
        print(f"Warning: No .env file found at {env_file}")
        print("Please create .env file with required environment variables")

def check_database():
    """Check database connection and initialize if needed."""
    try:
        # 动态导入以避免配置问题
        from app.core.config import get_settings
        from app.database.connection import engine
        from app.models.base import Base
        
        settings = get_settings()
        print(f"✓ Configuration loaded successfully")
        print(f"✓ Database URL: {settings.DATABASE_URL}")
        
        # 测试数据库连接
        with engine.connect() as conn:
            print("✓ Database connection successful")
        
        # 检查表是否存在，如果不存在则创建
        from sqlalchemy import inspect
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        if not existing_tables:
            print("No tables found, creating database tables...")
            Base.metadata.create_all(bind=engine)
            print("✓ Database tables created successfully")
        else:
            print(f"✓ Found {len(existing_tables)} existing tables")
            
    except Exception as e:
        print(f"✗ Database check failed: {e}")
        print("You may need to run: python scripts/init_db.py")
        return False
    
    return True

def check_ollama_service():
    """Check if OLLAMA service is running."""
    try:
        import httpx
        from app.core.config import get_settings
        
        settings = get_settings()
        response = httpx.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            print("✓ OLLAMA service is running")
            return True
        else:
            print(f"⚠ OLLAMA service responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠ OLLAMA service check failed: {e}")
        print("OLLAMA service may not be running. Some AI features may not work.")
        return False

def run_uvicorn():
    """Run the application with uvicorn."""
    try:
        # 检查是否在虚拟环境中
        in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        
        cmd = [
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
            "--log-level", "info"
        ]
        
        print("Starting AI API Platform...")
        print(f"Python executable: {sys.executable}")
        print(f"Virtual environment: {'Yes' if in_venv else 'No'}")
        print(f"Working directory: {os.getcwd()}")
        print(f"Command: {' '.join(cmd)}")
        print("=" * 50)
        print("Access the API at: http://localhost:8000")
        print("API Documentation: http://localhost:8000/docs")
        print("Health Check: http://localhost:8000/health")
        print("Press Ctrl+C to stop the server")
        print("=" * 50)
        
        subprocess.run(cmd, check=True, cwd=project_root)
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to start application: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n✓ Application stopped by user")
        sys.exit(0)

def check_dependencies():
    """Check if required dependencies are installed."""
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
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("✗ Missing required packages:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nPlease install missing packages:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    
    print("✓ All required dependencies found")

def main():
    """Main startup function."""
    print("AI API Platform Startup Script")
    print("=" * 40)
    
    # 1. 加载环境变量
    print("1. Loading environment variables...")
    load_environment()
    
    # 2. 检查依赖
    print("\n2. Checking dependencies...")
    check_dependencies()
    
    # 3. 检查数据库
    print("\n3. Checking database...")
    if not check_database():
        print("Database check failed. Please fix database issues and try again.")
        sys.exit(1)
    
    # 4. 检查OLLAMA服务（非阻塞）
    print("\n4. Checking OLLAMA service...")
    check_ollama_service()
    
    # 5. 启动应用
    print("\n5. Starting application...")
    run_uvicorn()

if __name__ == "__main__":
    main() 