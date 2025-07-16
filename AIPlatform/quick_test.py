#!/usr/bin/env python3
"""
快速测试脚本

@author malou
@since 2024-12-19
Note: 快速验证系统各个组件的功能
"""

import sys
import os
import traceback

print("=" * 50)
print("AI Platform 快速测试")
print("=" * 50)

# 1. 测试Python基础环境
print("\n1. Python环境测试...")
print(f"Python版本: {sys.version}")
print(f"当前目录: {os.getcwd()}")

# 2. 测试依赖包导入
print("\n2. 依赖包导入测试...")
packages = ['fastapi', 'uvicorn', 'sqlalchemy', 'pydantic', 'httpx', 'asyncio']
for package in packages:
    try:
        __import__(package)
        print(f"✓ {package}")
    except ImportError as e:
        print(f"✗ {package}: {e}")

# 3. 测试项目模块导入
print("\n3. 项目模块导入测试...")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

modules = [
    'app.core.config',
    'app.services.ollama_service',
    'app.main',
    'app.api.v1.health'
]

for module in modules:
    try:
        __import__(module)
        print(f"✓ {module}")
    except Exception as e:
        print(f"✗ {module}: {e}")
        traceback.print_exc()

# 4. 测试配置加载
print("\n4. 配置加载测试...")
try:
    from app.core.config import get_settings
    settings = get_settings()
    print(f"✓ 配置加载成功")
    print(f"  APP_NAME: {settings.APP_NAME}")
    print(f"  APP_PORT: {settings.APP_PORT}")
    print(f"  OLLAMA_BASE_URL: {settings.OLLAMA_BASE_URL}")
    print(f"  DATABASE_URL: {settings.DATABASE_URL}")
except Exception as e:
    print(f"✗ 配置加载失败: {e}")
    traceback.print_exc()

# 5. 测试FastAPI应用创建
print("\n5. FastAPI应用创建测试...")
try:
    from app.main import app
    print(f"✓ FastAPI应用创建成功")
    print(f"  Title: {app.title}")
    print(f"  Version: {app.version}")
except Exception as e:
    print(f"✗ FastAPI应用创建失败: {e}")
    traceback.print_exc()

# 6. 测试OLLAMA服务初始化
print("\n6. OLLAMA服务初始化测试...")
try:
    from app.services.ollama_service import OllamaService
    service = OllamaService()
    print(f"✓ OLLAMA服务初始化成功")
    print(f"  Base URL: {service.base_url}")
    print(f"  Default Model: {service.default_model}")
    print(f"  Max Retries: {service.max_retries}")
except Exception as e:
    print(f"✗ OLLAMA服务初始化失败: {e}")
    traceback.print_exc()

print("\n" + "=" * 50)
print("测试完成！")
print("=" * 50)

# 如果想要启动服务，取消下面的注释
print("\n如果要启动FastAPI服务，请运行:")
print("python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload") 