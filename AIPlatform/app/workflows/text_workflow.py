"""
Text generation workflow implementation.

@author malou
@since 2025-01-08
Note: 文本生成工作流实现
"""

from typing import Dict, Any, Optional, AsyncGenerator

from langchain.prompts import PromptTemplate
from app.llms.ollama_llm import CleanOutputParser,JsonStructOutputParser
from langchain_core.output_parsers import StrOutputParser

from .base_workflow import BaseWorkflow
from app.llms.base_llm import BaseLLM
from app.utils.logger import logger


class SimpleTextWorkflow(BaseWorkflow):
    """
    Simple text generation workflow.
    
    Note: 简单文本生成工作流
    """
    
    def __init__(self, llm: BaseLLM, template: str, output_parser: Optional[StrOutputParser] = None):
        """
        @param llm BaseLLM LLM实例
        @param template str 提示模板
        @param output_parser Optional[StrOutputParser] 输出解析器
        Note: 初始化简单文本工作流
        """
        self.llm = llm
        self.template = template
        self.prompt_template = PromptTemplate.from_template(template)
        self.output_parser = CleanOutputParser()
        
        logger.info(f"Initialized SimpleTextWorkflow with template: {template[:50]}...")
    
    async def execute_async(self, inputs: Dict[str, Any]) -> str:
        """
        @param inputs Dict[str, Any] 输入参数
        @return str 执行结果
        Note: 非流式执行工作流
        """
        try:
            # 格式化提示
            prompt = self.prompt_template.format(**inputs)
            
            # 调用LLM
            response = await self.llm._acall(prompt)
            
            # 解析输出
            result = self.output_parser.parse(response)
            
            logger.info(f"Workflow executed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            raise
    
    async def execute_stream(self, inputs: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        @param inputs Dict[str, Any] 输入参数
        @return AsyncGenerator[str, None] 流式执行结果
        Note: 流式执行工作流
        """
        try:
            # 格式化提示
            prompt = self.prompt_template.format(**inputs)
            
            # 流式调用LLM
            async for chunk in self.llm._generate_stream(prompt):
                if chunk:
                    # 对每个chunk进行解析（如果需要）
                    parsed_chunk = self.output_parser.parse(chunk) if chunk.strip() else chunk
                    yield parsed_chunk
            
            logger.info(f"Stream workflow executed successfully")
            
        except Exception as e:
            logger.error(f"Stream workflow execution failed: {str(e)}") 