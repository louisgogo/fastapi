"""
API Log management API routes.

@author malou
@since 2025-01-08
"""

from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database.connection import get_async_db
from app.schemas.common import SuccessResponse
from app.models.api_log import APILog
from app.utils.logger import LoggerAdapter

logger = LoggerAdapter(__name__)
router = APIRouter(tags=["logs"])


@router.get("/", response_model=SuccessResponse[dict])
async def get_api_logs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of records to return"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    session: AsyncSession = Depends(get_async_db)
):
    """
    Get API logs with filtering and pagination.
    
    @param skip: int - Number of records to skip
    @param limit: int - Number of records to return
    @param user_id: Optional[str] - Filter by user ID (UUID string)
    @param session: AsyncSession - 异步数据库会话
    @return SuccessResponse[dict] - List of API logs
    """
    try:
        logger.info(f"Getting API logs: skip={skip}, limit={limit}")
        
        # Build query
        query = select(APILog)
        if user_id:
            try:
                import uuid
                user_uuid = uuid.UUID(user_id)
                query = query.where(APILog.user_id == user_uuid)
            except ValueError:
                logger.warning(f"Invalid UUID format for user_id: {user_id}")
                # Return empty result for invalid UUID
                return SuccessResponse(
                    data={
                        "logs": [],
                        "total": 0,
                        "skip": skip,
                        "limit": limit
                    },
                    message="API logs retrieved successfully"
                )
        
        # Get total count
        count_query = select(func.count()).select_from(APILog)
        if user_id:
            try:
                import uuid
                user_uuid = uuid.UUID(user_id)
                count_query = count_query.where(APILog.user_id == user_uuid)
            except ValueError:
                pass
            
        total = await session.scalar(count_query) or 0
        
        # Get logs with pagination
        logs_result = await session.execute(
            query.order_by(APILog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        logs = logs_result.scalars().all()
        
        log_data = []
        for log in logs:
            log_dict = {
                "id": log.id,
                "user_id": str(log.user_id) if log.user_id else None,
                "api_key_id": str(log.api_key_id) if log.api_key_id else None,
                "method": log.method,
                "endpoint": log.endpoint,
                "status_code": log.status_code,
                "execution_time": log.execution_time,
                "client_ip": log.client_ip,
                "user_agent": log.user_agent,
                "created_at": log.created_at
            }
            log_data.append(log_dict)
        
        return SuccessResponse(
            data={
                "logs": log_data,
                "total": total,
                "skip": skip,
                "limit": limit
            },
            message="API logs retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Failed to get API logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{log_id}", response_model=SuccessResponse[dict])
async def get_api_log(
    log_id: int,
    session: AsyncSession = Depends(get_async_db)
):
    """
    Get API log by ID.
    
    @param log_id: int - Log ID
    @param session: AsyncSession - 异步数据库会话
    @return SuccessResponse[dict] - API log details
    @throws HTTPException - If log not found
    """
    try:
        logger.info(f"Getting API log: {log_id}")
        
        log = await session.get(APILog, log_id)
        
        if not log:
            logger.warning(f"API log not found: {log_id}")
            raise HTTPException(status_code=404, detail="API log not found")
        
        log_data = {
            "id": log.id,
            "user_id": str(log.user_id) if log.user_id else None,
            "api_key_id": str(log.api_key_id) if log.api_key_id else None,
            "agent_id": str(log.agent_id) if log.agent_id else None,
            "method": log.method,
            "endpoint": log.endpoint,
            "request_data": log.request_data,
            "response_data": log.response_data,
            "status_code": log.status_code,
            "execution_time": log.execution_time,
            "client_ip": log.client_ip,
            "user_agent": log.user_agent,
            "created_at": log.created_at,
            "updated_at": log.updated_at
        }
        
        return SuccessResponse(
            data=log_data,
            message="API log retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get API log: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats/overview", response_model=SuccessResponse[dict])
async def get_log_stats(
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze"),
    session: AsyncSession = Depends(get_async_db)
):
    """
    Get API log statistics overview.
    
    @param days: int - Number of days to analyze
    @param session: AsyncSession - 异步数据库会话
    @return SuccessResponse[dict] - Log statistics
    """
    try:
        logger.info(f"Getting log statistics for {days} days")
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Total requests
        total_requests_result = await session.scalar(
            select(func.count()).select_from(APILog)
            .where(APILog.created_at >= start_date)
        )
        total_requests = total_requests_result or 0
        
        # Success requests
        success_requests_result = await session.scalar(
            select(func.count()).select_from(APILog)
            .where(APILog.created_at >= start_date)
            .where(APILog.status_code < 400)
        )
        success_requests = success_requests_result or 0
        
        success_rate = (success_requests / total_requests * 100) if total_requests > 0 else 0
        
        # Average execution time
        avg_execution_time_result = await session.scalar(
            select(func.avg(APILog.execution_time))
            .where(APILog.created_at >= start_date)
            .where(APILog.execution_time.is_not(None))
        )
        avg_execution_time = avg_execution_time_result or 0
        
        stats = {
            "total_requests": total_requests,
            "success_requests": success_requests,
            "success_rate": round(success_rate, 2),
            "average_execution_time": round(avg_execution_time, 4),
            "period_days": days
        }
        
        return SuccessResponse(
            data=stats,
            message="Log statistics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Failed to get log statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error") 