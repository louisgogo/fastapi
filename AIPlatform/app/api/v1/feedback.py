"""
Feedback API routes.

@author malou
@since 2024-12-19
Note: 用户反馈相关的API接口
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.schemas.feedback import FeedbackCreate, FeedbackResponse, FeedbackStatsResponse
from app.schemas.common import SuccessResponse
from app.services.feedback_service import FeedbackService
from app.utils.logger import logger

router = APIRouter()


def get_current_user_id(request: Request) -> str:
    """Get current user ID from request state."""
    return getattr(request.state, 'user_id', 'anonymous')


def get_request_id(request: Request) -> str:
    """Get current request ID from request state."""
    return getattr(request.state, 'request_id', str(uuid.uuid4()))


@router.post("/", response_model=SuccessResponse[FeedbackResponse])
async def create_feedback(
    feedback_data: FeedbackCreate,
    http_request: Request,
    db: AsyncSession = Depends(get_async_db),
    user_id: str = Depends(get_current_user_id),
    request_id: str = Depends(get_request_id)
):
    """
    Create new feedback.
    
    @param feedback_data FeedbackCreate 反馈创建数据
    @param http_request Request HTTP请求对象
    @param db AsyncSession 异步数据库会话
    @param user_id str 当前用户ID
    @param request_id str 请求ID
    @return SuccessResponse[FeedbackResponse] 反馈响应
    Note: 创建新的用户反馈
    """
    try:
        # 初始化反馈服务
        feedback_service = FeedbackService(db)
        
        # 如果没有提供user_id，从认证信息中获取
        if not feedback_data.user_id and user_id != "anonymous":
            try:
                feedback_data.user_id = uuid.UUID(user_id)
            except ValueError:
                logger.warning(f"Invalid user_id format: {user_id}")
        
        # 创建反馈
        feedback = await feedback_service.create_feedback(feedback_data)
        
        logger.info(f"Feedback created successfully: {feedback.id}")
        
        return SuccessResponse[FeedbackResponse](
            data=FeedbackResponse.from_orm(feedback),
            message="Feedback created successfully",
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(f"Failed to create feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create feedback: {str(e)}"
        )


@router.get("/stats", response_model=SuccessResponse[FeedbackStatsResponse])
async def get_feedback_stats(
    db: AsyncSession = Depends(get_async_db),
    request_id: str = Depends(get_request_id)
):
    """
    Get feedback statistics.
    
    @param db AsyncSession 异步数据库会话
    @param request_id str 请求ID
    @return SuccessResponse[FeedbackStatsResponse] 反馈统计响应
    Note: 获取反馈统计信息
    """
    try:
        feedback_service = FeedbackService(db)
        stats = await feedback_service.get_feedback_stats()
        
        return SuccessResponse[FeedbackStatsResponse](
            data=stats,
            message="Feedback statistics retrieved successfully",
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(f"Failed to get feedback stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve feedback statistics: {str(e)}"
        ) 