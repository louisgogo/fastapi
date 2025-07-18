"""
Workflow Service for LANGGRAPH integration.

@author malou
@since 2025-01-08
Note: 工作流服务，专注于工作流的管理和编排
"""

import asyncio
from typing import Dict, Any, Optional, AsyncGenerator, List

from app.workflows.base_workflow import BaseWorkflow
from app.workflows.text_workflow import SimpleTextWorkflow
from app.workflows.sql_workflow import SQLGenerationWorkflow

from app.llms.factory import LLMFactory
from app.llms.ollama_llm import OllamaLLM
from app.utils.logger import logger


class WorkflowService:
    """
    Workflow service for managing and executing workflows.
    
    Note: 工作流服务，管理和执行各种工作流
    """
    
    def __init__(self):
        """
        Note: 初始化工作流服务
        """
        self.workflows: Dict[str, BaseWorkflow] = {}
        self.default_llm_config = {
            "model_name": "deepseek-r1:32b",
            "temperature": 0.1,
            "max_tokens": 5000,
            "top_p": 0.9,
            "timeout": 60,
            "stream": True
        }
        
        # 注册默认工作流
        self._register_default_workflows()
        
        logger.info("WorkflowService initialized")
    
    def _register_default_workflows(self):
        """
        Note: 注册默认的工作流
        """
        try:
            # 导入并注册所有工作流
            from app.workflows.graph.nl2sql import NL2SQLWorkflow
            
            # 注册工作流实例
            self.register_workflow("NL2SQL", NL2SQLWorkflow())
            
            logger.info("Default workflows registered successfully")
            
        except ImportError as e:
            logger.warning(f"Failed to import some workflow modules: {e}")
        except Exception as e:
            logger.error(f"Failed to register default workflows: {e}")
    
    def create_llm(self, **config_overrides) -> OllamaLLM:
        """
        @param config_overrides 配置覆盖参数
        @return BaseLLM LLM实例
        Note: 创建LLM实例
        """
        config = {**self.default_llm_config, **config_overrides}
        return LLMFactory.create_ollama_llm(**config)
    
    def register_workflow(self, name: str, workflow: BaseWorkflow) -> None:
        """
        @param name str 工作流名称
        @param workflow BaseWorkflow 工作流实例
        Note: 注册工作流
        """
        self.workflows[name] = workflow
        logger.info(f"Registered workflow: {name}")
    
    def create_text_workflow(
        self, 
        name: str, 
        template: str, 
        llm_config: Optional[Dict[str, Any]] = None
    ) -> BaseWorkflow:
        """
        @param name str 工作流名称
        @param template str 提示模板
        @param llm_config Optional[Dict[str, Any]] LLM配置
        @return BaseWorkflow 工作流实例
        Note: 创建并注册文本生成工作流
        """
        llm = self.create_llm(**(llm_config or {}))
        workflow = SimpleTextWorkflow(llm, template)
        self.register_workflow(name, workflow)
        return workflow

    def create_sql_workflow(
        self, 
        name: str, 
        database_schema: str,
        llm_config: Optional[Dict[str, Any]] = None
    ) -> SQLGenerationWorkflow:
        """
        @param name str 工作流名称
        @param template str 提示模板
        @param llm_config Optional[Dict[str, Any]] LLM配置
        @return BaseWorkflow 工作流实例
        Note: 创建并注册文本生成工作流
        """
        llm = self.create_llm(**(llm_config or {}))
        workflow = SQLGenerationWorkflow(llm, database_schema)
        self.register_workflow(name, workflow)
        return workflow
    
    async def execute_workflow(self, name: str, inputs: Optional[Dict[str, Any]] = None) -> str:
        """
        @param name str 工作流名称
        @param inputs Optional[Dict[str, Any]] 输入参数（可选）
        @return str 执行结果
        @throws KeyError 工作流不存在
        Note: 执行指定工作流
        """
        if name not in self.workflows:
            raise KeyError(f"Workflow '{name}' not found")
        
        workflow = self.workflows[name]
        return await workflow.execute_async(inputs or {})

    
    async def execute_workflow_stream(
        self, 
        name: str, 
        inputs: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """
        @param name str 工作流名称
        @param inputs Dict[str, Any] 输入参数
        @return AsyncGenerator[str, None] 流式执行结果
        @throws KeyError 工作流不存在
        Note: 流式执行指定工作流
        """
        if name not in self.workflows:
            raise KeyError(f"Workflow '{name}' not found")
        
        workflow = self.workflows[name]
        # 直接迭代异步生成器
        async for chunk in workflow.execute_stream(inputs): # type: ignore
            yield chunk
    
    def list_workflows(self) -> List[str]:
        """
        @return List[str] 工作流名称列表
        Note: 获取所有已注册的工作流名称
        """
        return list(self.workflows.keys())
    
    def get_workflow(self, name: str) -> Optional[BaseWorkflow]:
        """
        @param name str 工作流名称
        @return Optional[BaseWorkflow] 工作流实例
        Note: 获取指定工作流
        """
        return self.workflows.get(name)
    
    def remove_workflow(self, name: str) -> bool:
        """
        @param name str 工作流名称
        @return bool 是否成功移除
        Note: 移除指定工作流
        """
        if name in self.workflows:
            del self.workflows[name]
            logger.info(f"Removed workflow: {name}")
            return True
        return False
    
    def clear_workflows(self) -> None:
        """
        Note: 清空所有工作流
        """
        self.workflows.clear()
        logger.info("Cleared all workflows")

# 全局工作流服务实例
workflow_service = WorkflowService()

async def main():
    """
    Note: 主函数，演示工作流服务的使用
    """
    try:
        await workflow_service.execute_workflow("SQL2Data",{"query":"帮我查询下今年的费用支出"})
        # await demo_stream_workflow()
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}")  
        raise


if __name__ == "__main__":
    asyncio.run(main())
