"""
Base LLM class for LANGGRAPH integration.

@author malou
@since 2025-01-08
Note: 符合LANGGRAPH标准的大语言模型基类
"""

import json
import time
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, AsyncGenerator

from pydantic import BaseModel, Field
from langchain_core.language_models.llms import LLM
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.outputs import LLMResult, Generation

from app.utils.logger import logger
from app.core.exceptions import ValidationException


class LLMConfig(BaseModel):
    """
    LLM configuration schema.
    
    Note: LLM配置模型，定义大语言模型的配置参数
    """
    
    model_name: str = Field(..., description="模型名称")
    base_url: str = Field(..., description="模型服务地址")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0, description="温度参数")
    max_tokens: int = Field(default=1000, gt=0, description="最大生成token数")
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="核采样参数")
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="频率惩罚")
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="存在惩罚")
    timeout: int = Field(default=30, gt=0, description="请求超时时间(秒)")
    max_retries: int = Field(default=3, ge=0, description="最大重试次数")
    stream: bool = Field(default=False, description="是否流式输出")
    
    # LANGGRAPH specific configurations
    enable_tools: bool = Field(default=False, description="是否启用工具调用")
    enable_memory: bool = Field(default=False, description="是否启用记忆功能")
    enable_planning: bool = Field(default=False, description="是否启用规划功能")
    
    def validate_config(self) -> None:
        """
        @throws ValidationException 配置验证异常
        Note: 验证配置参数的有效性
        """
        if not self.model_name:
            raise ValidationException("model_name cannot be empty")
        if not self.base_url:
            raise ValidationException("base_url cannot be empty")


class LLMResponse(BaseModel):
    """
    LLM response schema.
    
    Note: LLM响应模型，标准化LLM的响应格式
    """
    
    request_id: str = Field(..., description="请求ID")
    model_name: str = Field(..., description="使用的模型名称")
    prompt: str = Field(..., description="输入提示")
    response: str = Field(..., description="模型响应")
    
    # 性能指标
    prompt_tokens: int = Field(default=0, description="提示token数")
    completion_tokens: int = Field(default=0, description="完成token数")
    total_tokens: int = Field(default=0, description="总token数")
    
    # 时间指标
    start_time: float = Field(..., description="开始时间戳")
    end_time: float = Field(..., description="结束时间戳")
    duration: float = Field(..., description="处理时长(秒)")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="附加元数据")
    
    # 错误信息
    error: Optional[str] = Field(default=None, description="错误信息")
    
    @classmethod
    def create_success_response(
        cls,
        request_id: str,
        model_name: str,
        prompt: str,
        response: str,
        start_time: float,
        end_time: float,
        **kwargs
    ) -> "LLMResponse":
        """
        @param request_id str 请求ID
        @param model_name str 模型名称
        @param prompt str 输入提示
        @param response str 模型响应
        @param start_time float 开始时间
        @param end_time float 结束时间
        @param kwargs 其他参数
        @return LLMResponse 成功响应
        Note: 创建成功响应
        """
        return cls(
            request_id=request_id,
            model_name=model_name,
            prompt=prompt,
            response=response,
            start_time=start_time,
            end_time=end_time,
            duration=end_time - start_time,
            **kwargs
        )
    
    @classmethod
    def create_error_response(
        cls,
        request_id: str,
        model_name: str,
        prompt: str,
        error: str,
        start_time: float,
        end_time: float,
        **kwargs
    ) -> "LLMResponse":
        """
        @param request_id str 请求ID
        @param model_name str 模型名称
        @param prompt str 输入提示
        @param error str 错误信息
        @param start_time float 开始时间
        @param end_time float 结束时间
        @param kwargs 其他参数
        @return LLMResponse 错误响应
        Note: 创建错误响应
        """
        return cls(
            request_id=request_id,
            model_name=model_name,
            prompt=prompt,
            response="",
            error=error,
            start_time=start_time,
            end_time=end_time,
            duration=end_time - start_time,
            **kwargs
        )


class BaseLLM(LLM, ABC):
    """
    Base LLM class for LANGGRAPH integration.
    
    Note: 符合LANGGRAPH标准的大语言模型基类，继承自LangChain的LLM
    """
    
    config: LLMConfig = Field(..., description="LLM配置")
    llm_id: str = Field(..., description="LLM实例ID")
    
    def __init__(self, config: LLMConfig,**kwargs):
        """
        @param config LLMConfig LLM配置
        @param kwargs 其他参数
        Note: 初始化基础LLM
        """
        # 验证配置
        config.validate_config()
        
        # 生成 LLM ID
        llm_id = str(uuid.uuid4())
        
        # 准备初始化数据，将所有需要的参数传递给父类
        init_data = {
            'config': config,
            'llm_id': llm_id,
            **kwargs
        }
        
        # 先调用LangChain LLM的初始化
        super().__init__(**init_data)
        
        logger.info(f"Initialized LLM: {self.config.model_name}")
        logger.info(f"LLM config: {self.config.model_dump()}")
    
    @property
    def _llm_type(self) -> str:
        """
        @return str LLM类型
        Note: 返回LLM类型标识
        """
        return "base_llm"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """
        @param prompt str 输入提示
        @param stop Optional[List[str]] 停止词列表
        @param run_manager Optional[CallbackManagerForLLMRun] 回调管理器
        @param kwargs 其他参数
        @return str 模型响应
        Note: 同步调用LLM，LangChain标准接口
        """
        # 生成请求ID
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # 调用子类实现的同步方法
            response = self._generate_sync(prompt, stop, **kwargs)
            end_time = time.time()
            
            # 记录成功响应
            llm_response = LLMResponse.create_success_response(
                request_id=request_id,
                model_name=self.config.model_name,
                prompt=prompt,
                response=response,
                start_time=start_time,
                end_time=end_time,
                metadata=kwargs
            )
            
            logger.info(f"LLM call completed: {request_id}, duration: {llm_response.duration:.2f}s")
            
            return response
            
        except Exception as e:
            end_time = time.time()
            error_msg = str(e)
            
            # 记录错误响应
            llm_response = LLMResponse.create_error_response(
                request_id=request_id,
                model_name=self.config.model_name,
                prompt=prompt,
                error=error_msg,
                start_time=start_time,
                end_time=end_time,
                metadata=kwargs
            )
            
            logger.error(f"LLM call failed: {request_id}, error: {error_msg}")
            raise
    
    async def _acall(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """
        @param prompt str 输入提示
        @param stop Optional[List[str]] 停止词列表
        @param run_manager Optional[CallbackManagerForLLMRun] 回调管理器
        @param kwargs 其他参数
        @return str 模型响应
        Note: 异步调用LLM，LangChain标准接口
        """
        # 生成请求ID
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # 调用子类实现的异步方法
            response = await self._generate_async(prompt, stop, **kwargs)
            end_time = time.time()
            
            # 记录成功响应
            llm_response = LLMResponse.create_success_response(
                request_id=request_id,
                model_name=self.config.model_name,
                prompt=prompt,
                response=response,
                start_time=start_time,
                end_time=end_time,
                metadata=kwargs
            )
            
            logger.info(f"Async LLM call completed: {request_id}, duration: {llm_response.duration:.2f}s")
            
            return response
            
        except Exception as e:
            end_time = time.time()
            error_msg = str(e)
            
            # 记录错误响应
            llm_response = LLMResponse.create_error_response(
                request_id=request_id,
                model_name=self.config.model_name,
                prompt=prompt,
                error=error_msg,
                start_time=start_time,
                end_time=end_time,
                metadata=kwargs
            )
            
            logger.error(f"Async LLM call failed: {request_id}, error: {error_msg}")
            raise
    
    @abstractmethod
    def _generate_sync(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> str:
        """
        @param prompt str 输入提示
        @param stop Optional[List[str]] 停止词列表
        @param kwargs 其他参数
        @return str 模型响应
        Note: 同步生成方法，需要子类实现
        """
        pass
    
    @abstractmethod
    async def _generate_async(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> str:
        """
        @param prompt str 输入提示
        @param stop Optional[List[str]] 停止词列表
        @param kwargs 其他参数
        @return str 模型响应
        Note: 异步生成方法，需要子类实现
        """
        pass
    
    async def _generate_stream(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """
        @param prompt str 输入提示
        @param stop Optional[List[str]] 停止词列表
        @param kwargs 其他参数
        @return AsyncGenerator[str, None] 流式响应生成器
        Note: 流式生成方法，子类可选择实现
        """
        # 默认实现：将非流式响应转换为流式
        response = await self._generate_async(prompt, stop, **kwargs)
        yield response
    
    def get_config(self) -> LLMConfig:
        """
        @return LLMConfig LLM配置
        Note: 获取LLM配置
        """
        return self.config
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        @param updates Dict[str, Any] 配置更新
        Note: 更新LLM配置
        """
        for key, value in updates.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        self.config.validate_config()
        logger.info(f"Updated LLM config: {updates}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        @return Dict[str, Any] 模型信息
        Note: 获取模型信息
        """
        return {
            "llm_id": self.llm_id,
            "model_name": self.config.model_name,
            "base_url": self.config.base_url,
            "llm_type": self._llm_type,
            "config": self.config.model_dump()
        }
    
    def __str__(self) -> str:
        """
        @return str 字符串表示
        Note: 返回LLM的字符串表示
        """
        return f"{self.__class__.__name__}(model={self.config.model_name}, id={self.llm_id})"
    
    def __repr__(self) -> str:
        """
        @return str 详细字符串表示
        Note: 返回LLM的详细字符串表示
        """
        return f"{self.__class__.__name__}(config={self.config.model_dump()})"
