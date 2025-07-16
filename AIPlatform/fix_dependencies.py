#!/usr/bin/env python3
"""
修复依赖问题的脚本

@author malou
@since 2024-12-19
Note: 卸载asyncpg依赖并重新安装正确的依赖
"""

import subprocess
import sys
import os

def run_command(cmd):
    """运行命令并显示结果"""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"Success: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return False

def main():
    """主函数"""
    print("正在修复依赖问题...")
    
    # 1. 卸载 asyncpg
    print("\n1. 卸载 asyncpg...")
    run_command("pip uninstall asyncpg -y")
    
    # 2. 重新安装依赖
    print("\n2. 重新安装依赖...")
    run_command("pip install -r requirements.txt")
    
    # 3. 创建 .env 文件
    print("\n3. 创建 .env 文件...")
    env_content = """# 应用配置
APP_NAME=AI API Platform
APP_VERSION=1.0.0
APP_DEBUG=true
APP_HOST=0.0.0.0
APP_PORT=8000

# 安全配置
SECRET_KEY=development-secret-key-at-least-32-chars-long-12345678
API_KEY_EXPIRE_DAYS=365

# 数据库配置（使用 SQLite）
DATABASE_URL=sqlite:///./app.db
DATABASE_ECHO=false
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# OLLAMA配置
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=llama3.2
OLLAMA_TIMEOUT=30

# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=logs/app.log

# CORS配置
CORS_ORIGINS=["*"]
CORS_CREDENTIALS=true

# 开发配置
RELOAD=true
ACCESS_LOG=true
DEBUG_SQL=false
"""
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    print("✓ .env 文件创建成功")
    
    # 4. 测试导入
    print("\n4. 测试导入...")
    try:
        from app.database import get_db
        print("✓ 数据库模块导入成功")
    except Exception as e:
        print(f"✗ 数据库模块导入失败: {e}")
    
    print("\n修复完成！")
    print("现在可以尝试运行:")
    print("  python -m app.api.v1.health")
    print("  或者")
    print("  python -m uvicorn app.main:app --reload")

if __name__ == "__main__":
    main() 