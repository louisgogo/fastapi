"""
Workflow API endpoints.

@author malou
@since 2025-01-08
Note: 工作流相关的API端点
"""

from typing import Dict, Any, List, Union
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.services.workflow_service import workflow_service, BaseWorkflow
from app.utils.logger import logger

router = APIRouter(tags=["workflows"])


class WorkflowCreateRequest(BaseModel):
    """
    工作流创建请求模型
    """
    name: str = Field(..., description="工作流名称")
    template: str = Field(..., description="提示模板")
    llm_config: Dict[str, Any] = Field(default_factory=dict, description="LLM配置")


class WorkflowExecuteRequest(BaseModel):
    """
    工作流执行请求模型
    """
    input: Dict[str, Any] = Field(..., description="输入参数")


class WorkflowResponse(BaseModel):
    """
    工作流响应模型
    """
    workflow_name: str = Field(..., description="工作流名称")
    result: Union[str, dict] = Field(..., description="执行结果")
    success: bool = Field(..., description="是否成功")
    error: str = Field(default="", description="错误信息")


class WorkflowListResponse(BaseModel):
    """
    工作流列表响应模型
    """
    workflows: List[str] = Field(..., description="工作流名称列表")
    count: int = Field(..., description="工作流数量")


class FinancialAnalysisRequest(BaseModel):
    """
    财务分析请求模型
    """
    query: str = Field(..., description="用户的自然语言查询", min_length=1, max_length=1000)


@router.post("/create", response_model=Dict[str, str])
async def create_workflow(request: WorkflowCreateRequest):
    """
    创建新的工作流
    
    @param request WorkflowCreateRequest 创建请求
    @return Dict[str, str] 创建结果
    Note: 创建并注册新的工作流
    """
    try:
        # 检查工作流是否已存在
        if request.name in workflow_service.list_workflows():
            raise HTTPException(
                status_code=400,
                detail=f"Workflow '{request.name}' already exists"
            )
        
        # 创建工作流
        workflow = workflow_service.create_text_workflow(
            name=request.name,
            template=request.template,
            llm_config=request.llm_config
        )
        
        logger.info(f"Created workflow: {request.name}")
        
        return {
            "message": f"Workflow '{request.name}' created successfully",
            "workflow_name": request.name
        }
        
    except Exception as e:
        logger.error(f"Failed to create workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=WorkflowListResponse)
async def list_workflows():
    """
    获取所有工作流列表
    
    @return WorkflowListResponse 工作流列表
    Note: 返回所有已注册的工作流
    """
    try:
        workflows = workflow_service.list_workflows()
        
        return WorkflowListResponse(
            workflows=workflows,
            count=len(workflows)
        )
        
    except Exception as e:
        logger.error(f"Failed to list workflows: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_name}/execute", response_model=WorkflowResponse)
async def execute_workflow(workflow_name: str, request: WorkflowExecuteRequest):
    """
    执行指定工作流（非流式）
    
    @param workflow_name str 工作流名称
    @param request WorkflowExecuteRequest 执行请求
    @return WorkflowResponse 执行结果
    Note: 执行指定的工作流并返回完整结果
    """
    try:
        # 执行工作流
        result = await workflow_service.execute_workflow(
            workflow_name, 
            request.input
        )
        
        logger.info(f"Executed workflow: {workflow_name}")
        
        return WorkflowResponse(
            workflow_name=workflow_name,
            result=result,
            success=True
        )
        
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow '{workflow_name}' not found"
        )
    except Exception as e:
        logger.error(f"Failed to execute workflow {workflow_name}: {str(e)}")
        return WorkflowResponse(
            workflow_name=workflow_name,
            result="",
            success=False,
            error=str(e)
        )


@router.post("/{workflow_name}/execute/stream")
async def execute_workflow_stream(workflow_name: str, request: WorkflowExecuteRequest):
    """
    执行指定工作流（流式输出）
    
    @param workflow_name str 工作流名称
    @param request WorkflowExecuteRequest 执行请求
    @return StreamingResponse 流式响应
    Note: 执行指定的工作流并返回流式结果
    """
    try:
        # 检查工作流是否存在
        if workflow_name not in workflow_service.list_workflows():
            raise HTTPException(
                status_code=404,
                detail=f"Workflow '{workflow_name}' not found"
            )
        
        async def stream_generator():
            """流式生成器"""
            try:
                async for chunk in workflow_service.execute_workflow_stream(
                    workflow_name, 
                    request.input
                ):
                    if chunk:
                        yield f"data: {chunk}\n\n"
                
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                logger.error(f"Stream execution error: {str(e)}")
                yield f"data: ERROR: {str(e)}\n\n"
        
        logger.info(f"Started stream execution for workflow: {workflow_name}")
        
        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start stream execution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{workflow_name}")
async def delete_workflow(workflow_name: str):
    """
    删除指定工作流
    
    @param workflow_name str 工作流名称
    @return Dict[str, str] 删除结果
    Note: 删除指定的工作流
    """
    try:
        if workflow_name not in workflow_service.list_workflows():
            raise HTTPException(
                status_code=404,
                detail=f"Workflow '{workflow_name}' not found"
            )
        
        # 删除工作流（需要在workflow_service中添加delete方法）
        del workflow_service.workflows[workflow_name]
        
        logger.info(f"Deleted workflow: {workflow_name}")
        
        return {
            "message": f"Workflow '{workflow_name}' deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_name}/info")
async def get_workflow_info(workflow_name: str):
    """
    获取工作流信息
    
    @param workflow_name str 工作流名称
    @return Dict[str, Any] 工作流信息
    Note: 获取指定工作流的详细信息
    """
    try:
        workflow = workflow_service.get_workflow(workflow_name)
        
        if not workflow:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow '{workflow_name}' not found"
            )
        
        # 获取工作流信息
        info = {
            "name": workflow_name,
            "type": workflow.__class__.__name__,
        }
        
        # 如果是SimpleTextWorkflow，添加模板信息
        template = getattr(workflow, 'template', None)
        if template:
            info["template"] = template
        
        return info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 


@router.post("/financial-analysis", response_model=Dict[str, Any])
async def generate_financial_analysis(request: FinancialAnalysisRequest):
    """
    生成财务分析报告
    
    根据用户的自然语言查询，自动生成SQL语句，执行查询，
    处理数据并生成专业的财务分析报告。
    
    Args:
        request: 包含用户查询的请求对象
        
    Returns:
        Dict[str, Any]: 包含分析报告和相关数据的响应
    """
    try:
        from app.workflows.langgraph.sql2data import generate_financial_analysis_report
        
        logger.info(f"开始生成财务分析报告，用户查询: {request.query}")
        
        # 执行SQL2Data工作流
        result = await generate_financial_analysis_report(request.query)
        
        if result.get('success'):
            logger.info("财务分析报告生成成功")
            return {
                "success": True,
                "message": "财务分析报告生成成功",
                "data": {
                    "query": result.get('query'),
                    "sql_count": len(result.get('sql_list', [])),
                    "data_count": result.get('raw_data_count', 0),
                    "analysis_report": result.get('analysis_report'),
                    "sql_list": result.get('sql_list', [])
                }
            }
        else:
            logger.error(f"财务分析报告生成失败: {result.get('error')}")
            return {
                "success": False,
                "message": f"财务分析报告生成失败: {result.get('error')}",
                "data": None
            }
            
    except Exception as e:
        logger.error(f"财务分析报告API异常: {str(e)}")
        return {
            "success": False,
            "message": f"财务分析报告生成异常: {str(e)}",
            "data": None
        } 