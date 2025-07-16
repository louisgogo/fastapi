"""
API Key service.

@author malou
@since 2024-12-19
Note: API密钥管理业务逻辑服务，支持异步操作
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.api_key import APIKey
from app.schemas.api_key import APIKeyCreate, APIKeyUpdate, APIKeyStatsResponse
from app.core.exceptions import NotFoundException, ValidationException
from app.utils.logger import logger


class APIKeyService:
    """
    API Key service class.
    
    Note: API密钥管理服务，提供API密钥CRUD操作和统计功能，支持异步操作
    """
    
    def __init__(self, db: AsyncSession):
        """
        @param db AsyncSession 异步数据库会话
        Note: 初始化API密钥服务
        """
        self.db = db
    
    def _generate_api_key(self) -> str:
        """
        @return str 生成的API密钥
        Note: 生成安全的API密钥
        """
        return f"ak_{secrets.token_urlsafe(32)}"
    
    async def create_api_key(self, api_key_data: APIKeyCreate) -> APIKey:
        """
        @param api_key_data APIKeyCreate API密钥创建数据
        @return APIKey 创建的API密钥对象
        Note: 创建新的API密钥
        """
        try:
            # 生成密钥值
            key_value = self._generate_api_key()
            
            # 计算过期时间
            expires_at = None
            if api_key_data.expires_days:
                expires_at = datetime.now() + timedelta(days=api_key_data.expires_days)
            
            # 创建API密钥
            api_key = APIKey(
                user_id=api_key_data.user_id,
                key_value=key_value,
                name=api_key_data.name,
                permissions=api_key_data.permissions,
                expires_at=expires_at
            )
            
            self.db.add(api_key)
            await self.db.commit()
            await self.db.refresh(api_key)
            
            logger.info(f"API key created successfully: {api_key.id}")
            return api_key
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create API key: {str(e)}")
            raise ValidationException(f"Failed to create API key: {str(e)}")
    
    async def get_api_keys(
        self, 
        skip: int = 0, 
        limit: int = 10, 
        user_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[APIKey], int]:
        """
        @param skip int 跳过数量
        @param limit int 限制数量
        @param user_id Optional[uuid.UUID] 用户ID过滤
        @param is_active Optional[bool] 活跃状态过滤
        @return Tuple[List[APIKey], int] API密钥列表和总数
        Note: 获取API密钥列表，支持分页和过滤
        """
        # 构建查询条件
        where_conditions = []
        
        if user_id is not None:
            where_conditions.append(APIKey.user_id == user_id)
        if is_active is not None:
            where_conditions.append(APIKey.is_active == is_active)
        
        # 获取总数
        count_stmt = select(func.count(APIKey.id))
        if where_conditions:
            count_stmt = count_stmt.where(and_(*where_conditions))
        
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()
        
        # 获取数据
        data_stmt = select(APIKey)
        if where_conditions:
            data_stmt = data_stmt.where(and_(*where_conditions))
        
        data_stmt = data_stmt.offset(skip).limit(limit)
        data_result = await self.db.execute(data_stmt)
        api_keys = data_result.scalars().all()
        
        return list(api_keys), total or 0
    
    async def get_api_key_by_id(self, api_key_id: int) -> Optional[APIKey]:
        """
        @param api_key_id int API密钥ID
        @return Optional[APIKey] API密钥对象
        Note: 根据ID获取API密钥
        """
        stmt = select(APIKey).where(APIKey.id == api_key_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_api_key_by_value(self, key_value: str) -> Optional[APIKey]:
        """
        @param key_value str API密钥值
        @return Optional[APIKey] API密钥对象
        Note: 根据密钥值获取API密钥
        """
        stmt = select(APIKey).where(APIKey.key_value == key_value)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_api_key(self, api_key_id: int, api_key_data: APIKeyUpdate) -> Optional[APIKey]:
        """
        @param api_key_id int API密钥ID
        @param api_key_data APIKeyUpdate API密钥更新数据
        @return Optional[APIKey] 更新后的API密钥对象
        Note: 更新API密钥
        """
        try:
            api_key = await self.get_api_key_by_id(api_key_id)
            
            if not api_key:
                return None
            
            # 更新字段
            update_data = api_key_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(api_key, field, value)
            
            api_key.updated_at = datetime.now()
            
            await self.db.commit()
            await self.db.refresh(api_key)
            
            logger.info(f"API key updated successfully: {api_key_id}")
            return api_key
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update API key: {str(e)}")
            raise ValidationException(f"Failed to update API key: {str(e)}")
    
    async def delete_api_key(self, api_key_id: int) -> bool:
        """
        @param api_key_id int API密钥ID
        @return bool 删除是否成功
        Note: 删除API密钥（软删除）
        """
        try:
            api_key = await self.get_api_key_by_id(api_key_id)
            
            if not api_key:
                return False
            
            # 软删除，通过停用实现
            api_key.is_active = False
            api_key.updated_at = datetime.now()
            
            await self.db.commit()
            
            logger.info(f"API key deleted successfully: {api_key_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete API key: {str(e)}")
            raise ValidationException(f"Failed to delete API key: {str(e)}")
    
    async def rotate_api_key(self, api_key_id: int) -> Optional[APIKey]:
        """
        @param api_key_id int API密钥ID
        @return Optional[APIKey] 更新后的API密钥对象
        Note: 轮换API密钥（生成新的密钥值）
        """
        try:
            api_key = await self.get_api_key_by_id(api_key_id)
            
            if not api_key:
                return None
            
            # 生成新的密钥值
            api_key.key_value = self._generate_api_key()
            api_key.updated_at = datetime.now()
            
            await self.db.commit()
            await self.db.refresh(api_key)
            
            logger.info(f"API key rotated successfully: {api_key_id}")
            return api_key
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to rotate API key: {str(e)}")
            raise ValidationException(f"Failed to rotate API key: {str(e)}")
    
    async def activate_api_key(self, api_key_id: int) -> Optional[APIKey]:
        """
        @param api_key_id int API密钥ID
        @return Optional[APIKey] 更新后的API密钥对象
        Note: 激活API密钥
        """
        try:
            api_key = await self.get_api_key_by_id(api_key_id)
            
            if not api_key:
                return None
            
            api_key.is_active = True
            api_key.updated_at = datetime.now()
            
            await self.db.commit()
            await self.db.refresh(api_key)
            
            logger.info(f"API key activated successfully: {api_key_id}")
            return api_key
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to activate API key: {str(e)}")
            raise ValidationException(f"Failed to activate API key: {str(e)}")
    
    async def deactivate_api_key(self, api_key_id: int) -> Optional[APIKey]:
        """
        @param api_key_id int API密钥ID
        @return Optional[APIKey] 更新后的API密钥对象
        Note: 停用API密钥
        """
        try:
            api_key = await self.get_api_key_by_id(api_key_id)
            
            if not api_key:
                return None
            
            api_key.is_active = False
            api_key.updated_at = datetime.now()
            
            await self.db.commit()
            await self.db.refresh(api_key)
            
            logger.info(f"API key deactivated successfully: {api_key_id}")
            return api_key
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to deactivate API key: {str(e)}")
            raise ValidationException(f"Failed to deactivate API key: {str(e)}")

    async def validate_api_key(self, key_value: str) -> Optional[APIKey]:
        """
        @param key_value str API密钥值
        @return Optional[APIKey] 验证通过的API密钥对象
        Note: 验证API密钥并返回有效的密钥对象
        """
        api_key = await self.get_api_key_by_value(key_value)
        
        if not api_key:
            return None
        
        if not api_key.is_valid():
            return None
        
        # 更新最后使用时间
        api_key.last_used_at = datetime.now()
        await self.db.commit()
        
        return api_key
    
    async def get_api_key_stats(self) -> APIKeyStatsResponse:
        """
        @return APIKeyStatsResponse API密钥统计信息
        Note: 获取API密钥统计信息
        """
        # 总密钥数
        total_stmt = select(func.count(APIKey.id))
        total_result = await self.db.execute(total_stmt)
        total_keys = total_result.scalar()
        
        # 活跃密钥数
        active_stmt = select(func.count(APIKey.id)).where(APIKey.is_active == True)
        active_result = await self.db.execute(active_stmt)
        active_keys = active_result.scalar()
        
        # 过期密钥数
        expired_stmt = select(func.count(APIKey.id)).where(
            APIKey.expires_at < datetime.now()
        )
        expired_result = await self.db.execute(expired_stmt)
        expired_keys = expired_result.scalar()
        
        inactive_keys = (total_keys or 0) - (active_keys or 0)
        
        return APIKeyStatsResponse(
            total_keys=total_keys or 0,
            active_keys=active_keys or 0,
            expired_keys=expired_keys or 0,
            inactive_keys=inactive_keys or 0
        )
    
    async def close(self):
        """
        Note: 关闭数据库会话
        """
        await self.db.close() 