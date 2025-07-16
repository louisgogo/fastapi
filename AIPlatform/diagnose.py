#!/usr/bin/env python3
"""
诊断脚本 - 检查当前环境和依赖

@author malou
@since 2024-12-19
Note: 诊断当前环境问题
"""

import sys
import os
import importlib.util

def check_package(package_name):
    """检查包是否已安装"""
    spec = importlib.util.find_spec(package_name)
    if spec is not None:
        print(f"✓ {package_name} 已安装")
        return True
    else:
        print(f"✗ {package_name} 未安装")
        return False

def main():
    """主函数"""
    print("=== 环境诊断 ===")
    print(f"Python 版本: {sys.version}")
    print(f"Python 路径: {sys.executable}")
    print(f"当前目录: {os.getcwd()}")
    
    print("\n=== 检查关键包 ===")
    packages = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'asyncpg',
        'pydantic',
        'python_dotenv'
    ]
    
    for pkg in packages:
        check_package(pkg)
    
    print("\n=== 检查文件 ===")
    files = [
        '.env',
        'test.env',
        'requirements.txt',
        'app/database/connection.py',
        'app/api/v1/health.py'
    ]
    
    for file in files:
        if os.path.exists(file):
            print(f"✓ {file} 存在")
        else:
            print(f"✗ {file} 不存在")
    
    print("\n=== 测试导入 ===")
    try:
        import app.database.connection
        print("✓ app.database.connection 导入成功")
    except Exception as e:
        print(f"✗ app.database.connection 导入失败: {e}")
    
    try:
        import app.api.v1.health
        print("✓ app.api.v1.health 导入成功")
    except Exception as e:
        print(f"✗ app.api.v1.health 导入失败: {e}")
    
    print("\n=== 环境变量 ===")
    env_vars = ['DATABASE_URL', 'SECRET_KEY', 'PYTHONPATH']
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            print(f"✓ {var} = {value}")
        else:
            print(f"✗ {var} 未设置")

if __name__ == "__main__":
    main() 