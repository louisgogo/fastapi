#!/usr/bin/env python3
"""
Database initialization script.

@author malou
@since 2025-01-08
"""

import os
import sys
import secrets
import uuid
from datetime import datetime, timedelta
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
        return True
    else:
        print(f"Warning: No .env file found at {env_file}")
        print("Please create .env file with required environment variables")
        return False

def create_tables():
    """Create all database tables."""
    try:
        # 使用同步数据库连接，与主应用保持一致
        from app.database.connection import engine
        from app.models.base import Base
        
        # 导入所有模型以确保它们被注册到Base.metadata中
        from app.models.user import User
        from app.models.api_key import APIKey
        from app.models.agent import Agent
        from app.models.api_log import APILog
        from app.models.feedback import Feedback
        
        print("Creating database tables...")
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        
        print("✓ Database tables created successfully")
        print(f"✓ Database URL: {engine.url}")
        
        # 检查创建的表
        from sqlalchemy import inspect
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        print(f"✓ Created {len(table_names)} tables: {', '.join(table_names)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to create database tables: {e}")
        raise

def _generate_api_key() -> str:
    """Generate a secure API key."""
    return f"ak_{secrets.token_urlsafe(32)}"

def create_sample_data():
    """Create sample data for testing."""
    try:
        from app.database.connection import SessionLocal
        from app.models.user import User
        from app.models.api_key import APIKey
        
        print("Creating sample data...")
        
        # 使用同步会话
        db = SessionLocal()
        try:
            # 创建示例用户数据
            sample_users_data = [
                {
                    "name": "Admin User",
                    "email": "admin@company.com",
                    "department": "IT"
                },
                {
                    "name": "Finance User", 
                    "email": "finance@company.com",
                    "department": "Finance"
                },
                {
                    "name": "Test User",
                    "email": "test@company.com", 
                    "department": "Finance"
                }
            ]
            
            created_users = []
            for user_data in sample_users_data:
                try:
                    # 检查用户是否已存在
                    existing_user = db.query(User).filter(User.email == user_data["email"]).first()
                    if existing_user:
                        print(f"✓ User {user_data['email']} already exists, skipping...")
                        created_users.append(existing_user)
                        continue
                    
                    # 创建新用户
                    user = User(
                        name=user_data["name"],
                        email=user_data["email"],
                        department=user_data["department"],
                        status="active"
                    )
                    db.add(user)
                    db.flush()  # 获取用户ID但不提交事务
                    created_users.append(user)
                    print(f"✓ Created user: {user.email}")
                except Exception as e:
                    print(f"⚠ Warning: Could not create user {user_data['email']}: {e}")
            
            # 为每个用户创建示例API密钥
            for user in created_users:
                try:
                    # 检查是否已有API密钥
                    existing_keys = db.query(APIKey).filter(APIKey.user_id == user.id).all()
                    if existing_keys:
                        print(f"✓ User {user.email} already has {len(existing_keys)} API key(s), skipping...")
                        continue
                    
                    # 创建API密钥
                    key_value = _generate_api_key()
                    expires_at = datetime.now() + timedelta(days=365)  # 1年有效期
                    
                    api_key = APIKey(
                        user_id=user.id,
                        key_value=key_value,
                        name=f"Default API Key for {user.name}",
                        permissions=["nl2sql", "feedback"],
                        expires_at=expires_at,
                        is_active=True
                    )
                    
                    db.add(api_key)
                    print(f"✓ Created API key for user {user.email}")
                    print(f"  Key: {key_value}")
                except Exception as e:
                    print(f"⚠ Warning: Could not create API key for user {user.email}: {e}")
            
            # 提交事务
            db.commit()
            print("✓ Sample data created successfully")
            
        except Exception as e:
            db.rollback()
            print(f"✗ Failed to create sample data: {e}")
            raise
        finally:
            db.close()
            
    except Exception as e:
        print(f"✗ Error in create_sample_data: {e}")
        raise

def test_database_connection():
    """Test database connection."""
    try:
        from app.database.connection import engine
        
        print("Testing database connection...")
        
        # 测试连接
        with engine.connect() as conn:
            print("✓ Database connection successful")
            
        # 检查现有表
        from sqlalchemy import inspect
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        if existing_tables:
            print(f"✓ Found {len(existing_tables)} existing tables: {', '.join(existing_tables)}")
        else:
            print("✓ No existing tables found (fresh database)")
            
        return True
        
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def drop_all_tables():
    """Drop all tables (危险操作 - 仅用于重置数据库)."""
    try:
        from app.database.connection import engine
        from app.models.base import Base
        
        print("⚠ WARNING: Dropping all database tables...")
        response = input("Are you sure you want to drop all tables? (yes/no): ")
        
        if response.lower() != 'yes':
            print("Operation cancelled.")
            return False
            
        Base.metadata.drop_all(bind=engine)
        print("✓ All tables dropped successfully")
        return True
        
    except Exception as e:
        print(f"✗ Failed to drop tables: {e}")
        return False

def reset_database():
    """Reset database (drop and recreate tables)."""
    print("Resetting database...")
    if drop_all_tables():
        return create_tables()
    return False

def main():
    """Main initialization function."""
    print("Database Initialization Script")
    print("=" * 40)
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "reset":
            print("Database reset requested...")
            load_environment()
            if reset_database():
                print("Database reset completed. Run without 'reset' to add sample data.")
            return
        elif command == "drop":
            print("Drop tables requested...")
            load_environment()
            drop_all_tables()
            return
        elif command == "help":
            print("Usage:")
            print("  python scripts/init_db.py          # Initialize database with sample data")
            print("  python scripts/init_db.py reset    # Drop and recreate all tables")
            print("  python scripts/init_db.py drop     # Drop all tables (dangerous!)")
            print("  python scripts/init_db.py help     # Show this help")
            return
    
    try:
        # 1. 加载环境变量
        print("1. Loading environment variables...")
        if not load_environment():
            print("Environment loading failed, but continuing...")
        
        # 2. 测试数据库连接
        print("\n2. Testing database connection...")
        if not test_database_connection():
            print("Database connection failed. Please check your database configuration.")
            sys.exit(1)
        
        # 3. 创建数据库表
        print("\n3. Creating database tables...")
        create_tables()
        
        # 4. 创建示例数据
        print("\n4. Creating sample data...")
        create_sample_data()
        
        print("\n" + "=" * 40)
        print("✓ Database initialization completed successfully!")
        print("\nSample users created:")
        print("- admin@company.com (IT Department)")
        print("- finance@company.com (Finance Department)")  
        print("- test@company.com (Finance Department)")
        print("\nEach user has been assigned a default API key.")
        print("\nYou can now start the application with:")
        print("python scripts/start.py")
        
    except Exception as e:
        print(f"\n✗ Database initialization failed: {e}")
        print("\nPlease check:")
        print("1. Database connection configuration in .env file")
        print("2. Database server is running")
        print("3. Database credentials are correct")
        print("4. Required Python packages are installed")
        sys.exit(1)

if __name__ == "__main__":
    main() 