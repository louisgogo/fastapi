"""
Feedback service.

@author malou
@since 2024-12-19
Note: 用户反馈管理业务逻辑服务，支持异步操作
"""

import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.feedback import Feedback
from app.schemas.feedback import FeedbackCreate, FeedbackStatsResponse
from app.core.exceptions import ValidationException
from app.utils.logger import logger


class FeedbackService:
    """
    Feedback service class.
    
    Note: 用户反馈管理服务，提供反馈CRUD操作和统计功能，支持异步操作
    """
    
    def __init__(self, db: AsyncSession):
        """
        @param db AsyncSession 异步数据库会话
        Note: 初始化反馈服务
        """
        self.db = db
    
    async def create_feedback(self, feedback_data: FeedbackCreate) -> Feedback:
        """
        @param feedback_data FeedbackCreate 反馈创建数据
        @return Feedback 创建的反馈对象
        Note: 创建新的反馈
        """
        try:
            feedback = Feedback(
                request_id=feedback_data.request_id,
                user_id=feedback_data.user_id,
                agent_id=feedback_data.agent_id,
                rating=feedback_data.rating,
                feedback_text=feedback_data.feedback_text,
                is_sql_correct=feedback_data.is_sql_correct,
                suggestions=feedback_data.suggestions,
                feedback_type=feedback_data.feedback_type,
                priority=feedback_data.priority
            )
            
            self.db.add(feedback)
            await self.db.commit()
            await self.db.refresh(feedback)
            
            logger.info(f"Feedback created successfully: {feedback.id}")
            return feedback
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create feedback: {str(e)}")
            raise ValidationException(f"Failed to create feedback: {str(e)}")
    
    async def get_feedback_stats(self) -> FeedbackStatsResponse:
        """
        @return FeedbackStatsResponse 反馈统计信息
        Note: 获取反馈统计信息
        """
        # 总反馈数
        total_stmt = select(func.count(Feedback.id))
        total_result = await self.db.execute(total_stmt)
        total_feedback = total_result.scalar()
        
        # 待处理反馈数
        pending_stmt = select(func.count(Feedback.id)).where(
            Feedback.status == "pending"
        )
        pending_result = await self.db.execute(pending_stmt)
        pending_feedback = pending_result.scalar()
        
        # 已解决反馈数
        resolved_stmt = select(func.count(Feedback.id)).where(
            Feedback.status.in_(["resolved", "closed"])
        )
        resolved_result = await self.db.execute(resolved_stmt)
        resolved_feedback = resolved_result.scalar()
        
        # 计算平均评分
        avg_rating_stmt = select(func.avg(Feedback.rating))
        avg_rating_result = await self.db.execute(avg_rating_stmt)
        avg_rating_value = avg_rating_result.scalar()
        average_rating = float(avg_rating_value) if avg_rating_value else 0.0
        
        # 统计正面/负面反馈
        positive_stmt = select(func.count(Feedback.id)).where(
            Feedback.rating >= 4
        )
        positive_result = await self.db.execute(positive_stmt)
        positive_feedback = positive_result.scalar()
        
        negative_stmt = select(func.count(Feedback.id)).where(
            Feedback.rating <= 2
        )
        negative_result = await self.db.execute(negative_stmt)
        negative_feedback = negative_result.scalar()
        
        # 计算SQL正确率
        total_sql_stmt = select(func.count(Feedback.id)).where(
            Feedback.is_sql_correct.isnot(None)
        )
        total_sql_result = await self.db.execute(total_sql_stmt)
        total_sql_feedback = total_sql_result.scalar()
        
        correct_sql_stmt = select(func.count(Feedback.id)).where(
            Feedback.is_sql_correct == True
        )
        correct_sql_result = await self.db.execute(correct_sql_stmt)
        correct_sql_feedback = correct_sql_result.scalar()
        
        sql_correctness_rate = (
            (correct_sql_feedback or 0) / (total_sql_feedback or 1) 
            if (total_sql_feedback or 0) > 0 else 0.0
        )
        
        return FeedbackStatsResponse(
            total_feedback=total_feedback or 0,
            pending_feedback=pending_feedback or 0,
            resolved_feedback=resolved_feedback or 0,
            average_rating=average_rating,
            positive_feedback=positive_feedback or 0,
            negative_feedback=negative_feedback or 0,
            feedback_types={},  # TODO: 实现类型统计
            sql_correctness_rate=sql_correctness_rate
        )
    
    async def close(self):
        """
        Note: 关闭数据库会话
        """
        await self.db.close() 