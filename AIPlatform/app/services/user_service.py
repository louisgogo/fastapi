"""
User service.

@author malou
@since 2024-12-19
Note: 用户管理业务逻辑服务，使用异步数据库连接
"""

import uuid
from typing import Optional, Tuple, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserStatsResponse
from app.core.exceptions import NotFoundException, ValidationException
from app.utils.logger import logger


class UserService:
    """
    User service class.
    
    Note: 用户管理服务，提供用户CRUD操作和统计功能，支持异步操作
    """
    
    def __init__(self, db: AsyncSession):
        """
        @param db AsyncSession 异步数据库会话
        Note: 初始化用户服务
        """
        self.db = db
    
    async def create_user(self, user_data: UserCreate) -> User:
        """
        @param user_data UserCreate 用户创建数据
        @return User 创建的用户对象
        Note: 创建新用户
        """
        # 检查邮箱是否已存在
        stmt = select(User).where(User.email == user_data.email)
        result = await self.db.execute(stmt)
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise ValidationException(f"Email {user_data.email} already exists")
        
        # 创建用户
        user = User(
            name=user_data.name,
            email=user_data.email,
            department=user_data.department,
            status=user_data.status or "active"
        )
        
        try:
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            
            logger.info(f"User created successfully: {user.id}")
            return user
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create user: {str(e)}")
            raise ValidationException(f"Failed to create user: {str(e)}")
    
    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """
        @param user_id uuid.UUID 用户ID
        @return Optional[User] 用户对象
        Note: 根据ID获取用户
        """
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        @param email str 用户邮箱
        @return Optional[User] 用户对象
        Note: 根据邮箱获取用户
        """
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_users(self, skip: int = 0, limit: int = 100, 
                       department: Optional[str] = None, 
                       is_active: Optional[bool] = None) -> Tuple[List[User], int]:
        """
        @param skip int 跳过数量
        @param limit int 限制数量
        @param department Optional[str] 部门过滤
        @param is_active Optional[bool] 活跃状态过滤
        @return Tuple[List[User], int] 用户列表和总数
        Note: 获取用户列表
        """
        # 构建查询条件
        where_conditions = []
        
        if department:
            where_conditions.append(User.department == department)
        
        if is_active is not None:
            status = "active" if is_active else "inactive"
            where_conditions.append(User.status == status)
        
        # 获取总数
        count_stmt = select(func.count(User.id))
        if where_conditions:
            count_stmt = count_stmt.where(and_(*where_conditions))
        
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()
        
        # 获取数据
        data_stmt = select(User)
        if where_conditions:
            data_stmt = data_stmt.where(and_(*where_conditions))
        
        data_stmt = data_stmt.offset(skip).limit(limit)
        data_result = await self.db.execute(data_stmt)
        users = data_result.scalars().all()
        
        return list(users), total or 0
    
    async def update_user(self, user_id: uuid.UUID, user_data: UserUpdate) -> Optional[User]:
        """
        @param user_id uuid.UUID 用户ID
        @param user_data UserUpdate 用户更新数据
        @return Optional[User] 更新后的用户对象
        Note: 更新用户信息
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        # 检查邮箱是否被其他用户使用
        if user_data.email and user_data.email != user.email:
            stmt = select(User).where(
                and_(
                    User.email == user_data.email,
                    User.id != user_id
                )
            )
            result = await self.db.execute(stmt)
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                raise ValidationException(f"Email {user_data.email} already exists")
        
        # 更新字段
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        try:
            await self.db.commit()
            await self.db.refresh(user)
            
            logger.info(f"User updated successfully: {user.id}")
            return user
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update user {user_id}: {str(e)}")
            raise ValidationException(f"Failed to update user: {str(e)}")
    
    async def delete_user(self, user_id: uuid.UUID) -> bool:
        """
        @param user_id uuid.UUID 用户ID
        @return bool 删除是否成功
        Note: 删除用户
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        try:
            await self.db.delete(user)
            await self.db.commit()
            
            logger.info(f"User deleted successfully: {user_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete user {user_id}: {str(e)}")
            raise ValidationException(f"Failed to delete user: {str(e)}")
    
    async def list_users(self, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> List[User]:
        """
        @param skip int 跳过数量
        @param limit int 限制数量
        @param status Optional[str] 状态过滤
        @return List[User] 用户列表
        Note: 获取用户列表
        """
        stmt = select(User)
        
        if status:
            stmt = stmt.where(User.status == status)
        
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        users = result.scalars().all()
        
        return list(users)
    
    async def get_user_stats(self) -> UserStatsResponse:
        """
        @return UserStatsResponse 用户统计信息
        Note: 获取用户统计信息
        """
        # 总用户数
        total_stmt = select(func.count(User.id))
        total_result = await self.db.execute(total_stmt)
        total_users = total_result.scalar()
        
        # 各状态用户数
        active_stmt = select(func.count(User.id)).where(User.status == "active")
        active_result = await self.db.execute(active_stmt)
        active_users = active_result.scalar()
        
        inactive_stmt = select(func.count(User.id)).where(User.status == "inactive")
        inactive_result = await self.db.execute(inactive_stmt)
        inactive_users = inactive_result.scalar()
        
        suspended_stmt = select(func.count(User.id)).where(User.status == "suspended")
        suspended_result = await self.db.execute(suspended_stmt)
        suspended_users = suspended_result.scalar()
        
        # 各部门用户数
        department_stats = {}
        dept_stmt = select(
            User.department, 
            func.count(User.id)
        ).group_by(User.department)
        
        dept_result = await self.db.execute(dept_stmt)
        dept_results = dept_result.all()
        
        for dept, count in dept_results:
            department_stats[dept or "未分配"] = count
        
        return UserStatsResponse(
            total_users=total_users or 0,
            active_users=active_users or 0,
            inactive_users=inactive_users or 0,
            suspended_users=suspended_users or 0,
            departments=department_stats
        )
    
    async def close(self):
        """
        Note: 关闭数据库会话
        """
        await self.db.close()


if __name__ == "__main__":
    """
    测试UserService
    """
    import asyncio
    from app.database.connection import async_engine, AsyncSessionLocal
    from app.models.base import Base
    from app.core.config import get_settings
    
    async def test_user_service():
        """
        异步测试用户服务
        """
        # 使用配置文件中的数据库连接
        settings = get_settings()
        
        # 创建表
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # 使用异步会话
        async with AsyncSessionLocal() as db:
            try:
                service = UserService(db)
                
                # 创建测试用户
                user_data = UserCreate(
                    name="测试用户",
                    email="test@example.com",
                    department="技术部"
                )
                
                user = await service.create_user(user_data)
                print(f"Created user: {user.id}")
                
                # 获取用户统计
                stats = await service.get_user_stats()
                print(f"User stats: {stats}")
                
            except Exception as e:
                print(f"Test failed: {e}")
    
    # 运行异步测试
    asyncio.run(test_user_service()) 