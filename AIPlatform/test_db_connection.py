"""
数据库连接测试脚本

@author malou
@since 2024-12-19
Note: 测试数据库连接和基本查询
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import AsyncSessionLocal, async_engine
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

async def test_database_connection():
    """
    测试数据库连接
    
    Note: 测试异步数据库连接是否正常
    """
    print("=== 测试数据库连接 ===")
    
    try:
        # 测试连接
        async with AsyncSessionLocal() as session:
            print("数据库连接成功")
            
            # 测试SQLite版本查询
            try:
                result = await session.execute(text("SELECT sqlite_version()"))
                version = result.fetchone()
                if version:
                    print(f"SQLite版本: {version[0]}")
                    return "sqlite"
            except Exception as e:
                print(f"SQLite版本查询失败: {e}")
            
            # 测试PostgreSQL版本查询
            try:
                result = await session.execute(text("SELECT version()"))
                version = result.fetchone()
                if version:
                    print(f"PostgreSQL版本: {version[0]}")
                    return "postgresql"
            except Exception as e:
                print(f"PostgreSQL版本查询失败: {e}")
            
            # 测试基本查询
            try:
                result = await session.execute(text("SELECT 1"))
                test_result = result.fetchone()
                if test_result:
                    print(f"基本查询成功: {test_result[0]}")
            except Exception as e:
                print(f"基本查询失败: {e}")
            
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None

async def test_database_tables():
    """
    测试数据库表查询
    
    Note: 测试数据库表查询
    """
    print("\n=== 测试数据库表查询 ===")
    
    try:
        async with AsyncSessionLocal() as session:
            # 尝试SQLite表查询
            try:
                result = await session.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """))
                tables = [row[0] for row in result.fetchall()]
                print(f"SQLite表列表: {tables}")
                return tables
            except Exception as e:
                print(f"SQLite表查询失败: {e}")
            
            # 尝试PostgreSQL表查询
            try:
                result = await session.execute(text("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_type='BASE TABLE'
                    ORDER BY table_name
                """))
                tables = [row[0] for row in result.fetchall()]
                print(f"PostgreSQL表列表: {tables}")
                return tables
            except Exception as e:
                print(f"PostgreSQL表查询失败: {e}")
                
    except Exception as e:
        print(f"数据库表查询失败: {e}")
        return None

async def main():
    """
    主函数
    """
    db_type = await test_database_connection()
    tables = await test_database_tables()
    
    print(f"\n检测到的数据库类型: {db_type}")
    print(f"检测到的表数量: {len(tables) if tables else 0}")

if __name__ == "__main__":
    asyncio.run(main()) 