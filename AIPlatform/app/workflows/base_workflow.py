"""
Base workflow implementation.

@author malou
@since 2025-01-08
Note: 工作流基类，定义工作流的基本接口
"""

from typing import Dict, Any, AsyncGenerator, Optional
from abc import ABC, abstractmethod


class BaseWorkflow(ABC):
    """
    Base workflow class.
    
    Note: 工作流基类，定义工作流的基本接口
    """
    
    async def execute(self, inputs: Dict[str, Any]):
        """
        @param inputs Dict[str, Any] 输入参数
        @return str 执行结果
        Note: 执行工作流
        """
        pass

    @abstractmethod
    async def execute_async(self, inputs: Dict[str, Any]) -> str:
        """
        @param inputs Dict[str, Any] 输入参数
        @return str 执行结果
        Note: 执行工作流
        """
        pass


    async def execute_stream(self, inputs: Dict[str, Any]):
        """
        @param inputs Dict[str, Any] 输入参数
        @return AsyncGenerator[str, None] 流式执行结果
        Note: 流式执行工作流
        """
        pass 