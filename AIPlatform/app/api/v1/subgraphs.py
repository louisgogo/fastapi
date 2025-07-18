"""
SubGraph API endpoints.

@author malou
@since 2025-01-08
Note: 子图相关的API端点
"""

from typing import Dict, Any, List, Union, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.services.subgraph_service import subgraph_service, SubGraph
from app.workflows.subgraph.base import State
from app.utils.logger import logger

router = APIRouter(tags=["subgraphs"])


class SubGraphExecuteRequest(BaseModel):
    """
    子图执行请求模型
    """
    query: Optional[str] = Field(default=None, description="用户的问题")
    plan: Optional[list] = Field(default_factory=list, description="问题的规划步骤")
    sql: Optional[list] = Field(default_factory=list, description="执行的SQL语句")
    db_struc: Optional[str] = Field(default=None, description="数据库结构")


class SubGraphResponse(BaseModel):
    """
    子图响应模型
    """
    subgraph_name: str = Field(..., description="子图名称")
    result: Dict[str, Any] = Field(..., description="执行结果")
    success: bool = Field(..., description="是否成功")
    error: str = Field(default="", description="错误信息")


class SubGraphListResponse(BaseModel):
    """
    子图列表响应模型
    """
    subgraphs: List[str] = Field(..., description="子图名称列表")
    count: int = Field(..., description="子图数量")


@router.post("/{subgraph_name}/execute", response_model=SubGraphResponse)
async def execute_subgraph(subgraph_name: str, request: SubGraphExecuteRequest):
    """
    执行指定子图（非流式）
    
    @param subgraph_name str 子图名称
    @param request SubGraphExecuteRequest 执行请求
    @return SubGraphResponse 执行结果
    Note: 执行指定的子图并返回完整结果
    """
    try:
        # 构建状态对象
        state = State(query=request.query)
        
        # 设置plan字段 - 这是关键修复
        if request.plan:
            state.plan = request.plan
        else:
            # 如果没有提供plan，将query作为plan的第一个元素
            state.plan = [request.query] if request.query else []
            state.current_plan_idx = 0
            
        if request.db_struc:
            state.db_struc = request.db_struc
        if request.sql:
            state.sql = request.sql if isinstance(request.sql, list) else [request.sql]
        
        # 执行子图
        result = await subgraph_service.execute_subgraph(subgraph_name, state)
        
        logger.info(f"Executed subgraph: {subgraph_name}")
        
        return SubGraphResponse(
            subgraph_name=subgraph_name,
            result=dict(result),
            success=True
        )
        
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"SubGraph '{subgraph_name}' not found"
        )
    except Exception as e:
        logger.error(f"Failed to execute subgraph {subgraph_name}: {str(e)}")
        return SubGraphResponse(
            subgraph_name=subgraph_name,
            result={},
            success=False,
            error=str(e)
        )


@router.post("/{subgraph_name}/execute/stream")
async def execute_subgraph_stream(subgraph_name: str, request: SubGraphExecuteRequest):
    """
    执行指定子图（流式输出）
    
    @param subgraph_name str 子图名称
    @param request SubGraphExecuteRequest 执行请求
    @return StreamingResponse 流式响应
    Note: 执行指定的子图并返回流式结果
    """
    try:
        # 检查子图是否存在
        if subgraph_name not in subgraph_service.list_subgraphs():
            raise HTTPException(
                status_code=404,
                detail=f"SubGraph '{subgraph_name}' not found"
            )
        
        # 构建状态对象
        state = State(query=request.query)
        if request.db_struc:
            state.db_struc = request.db_struc
        if request.sql:
            state.sql = [request.sql]
        
        async def stream_generator():
            """流式生成器"""
            try:
                async for chunk in subgraph_service.execute_subgraph_stream(
                    subgraph_name, 
                    state
                ):
                    if chunk:
                        # 将State对象转换为字典
                        chunk_dict = chunk.model_dump()
                        yield f"data: {chunk_dict}\n\n"
                
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                logger.error(f"Stream execution error: {str(e)}")
                yield f"data: ERROR: {str(e)}\n\n"
        
        logger.info(f"Started stream execution for subgraph: {subgraph_name}")
        
        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to execute subgraph stream {subgraph_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
