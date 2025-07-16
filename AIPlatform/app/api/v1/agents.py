"""
Agents API routes.

@author malou
@since 2024-12-19
Note: AI Agent相关的API接口
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.schemas.agent import NL2SQLRequest, NL2SQLResponse, ModelListResponse
from app.schemas.common import SuccessResponse
from app.services.agent_service import AgentService
from app.services.ollama_service import OllamaService
from app.utils.logger import logger

router = APIRouter()


def get_current_user_id(request: Request) -> str:
    """Get current user ID from request state."""
    return getattr(request.state, 'user_id', 'anonymous')


def get_request_id(request: Request) -> str:
    """Get current request ID from request state."""
    return getattr(request.state, 'request_id', str(uuid.uuid4()))


@router.post("/nl2sql", response_model=SuccessResponse[NL2SQLResponse])
async def natural_language_to_sql(
    nl2sql_request: NL2SQLRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_async_db),
    user_id: str = Depends(get_current_user_id),
    request_id: str = Depends(get_request_id)
):
    """
    Convert natural language to SQL.
    
    @param nl2sql_request NL2SQLRequest 自然语言转SQL请求
    @param http_request Request HTTP请求对象
    @param db AsyncSession 异步数据库会话
    @param user_id str 当前用户ID
    @param request_id str 请求ID
    @return SuccessResponse[NL2SQLResponse] NL2SQL响应
    Note: 将自然语言查询转换为SQL语句
    """
    try:
        # 初始化Agent服务
        agent_service = AgentService(db)
        
        # 转换user_id为UUID（如果不是anonymous）
        user_uuid = None
        if user_id != "anonymous":
            try:
                user_uuid = uuid.UUID(user_id)
            except ValueError:
                logger.warning(f"Invalid user_id format: {user_id}")
        
        # 处理NL2SQL请求
        result = await agent_service.process_nl2sql(nl2sql_request, user_uuid)
        
        # 关闭服务
        await agent_service.close()
        
        logger.info(f"NL2SQL request completed for user {user_id}")
        
        return SuccessResponse[NL2SQLResponse](
            data=result,
            message="NL2SQL conversion completed successfully",
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(f"NL2SQL request failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"NL2SQL processing failed: {str(e)}"
        )


@router.get("/models", response_model=SuccessResponse[ModelListResponse])
async def list_available_models(
    request_id: str = Depends(get_request_id)
):
    """
    List available OLLAMA models.
    
    @param request_id str 请求ID
    @return SuccessResponse[ModelListResponse] 可用模型列表响应
    Note: 获取OLLAMA服务中可用的模型列表
    """
    try:
        ollama_service = OllamaService()
        models = await ollama_service.list_models()
        await ollama_service.close()
        
        return SuccessResponse[ModelListResponse](
            data=models,
            message="Models retrieved successfully",
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(f"Failed to list models: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve models: {str(e)}"
        )


@router.get("/")
async def list_agents(
    request_id: str = Depends(get_request_id)
):
    """
    List available agents.
    
    @param request_id str 请求ID
    @return dict 可用Agent列表
    Note: 获取系统中可用的Agent列表
    """
    agents = [
        {
            "name": "NL2SQL Agent",
            "type": "nl2sql",
            "description": "Convert natural language queries to SQL statements",
            "status": "active",
            "capabilities": [
                "Natural language understanding",
                "SQL generation",
                "Query optimization",
                "Syntax validation"
            ]
        }
    ]
    
    return SuccessResponse(
        data={"agents": agents},
        message="Agents retrieved successfully",
        request_id=request_id
    ) 