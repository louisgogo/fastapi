"""
Ollama LLM implementation for LANGGRAPH integration.

@author malou
@since 2025-01-08
Note: Ollama大语言模型实现，符合LANGGRAPH标准
"""

import asyncio
import json
import re
from typing import Any, Dict, List, Optional, AsyncGenerator

import aiohttp
import requests
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from .base_llm import BaseLLM, LLMConfig

from app.utils.logger import logger
from app.core.exceptions import ValidationException

class CleanOutputParser(StrOutputParser):
    """
    Clean output parser for LLM responses.
    
    Note: 清理LLM输出的解析器，去除标签和格式化内容
    """
    
    def parse(self, text: str) -> str:
        """
        @param text str 原始文本
        @return str 清理后的文本
        Note: 解析并清理LLM输出
        """
        # Remove any <think>...</think> tags and their content
        text = re.sub(r'<think>[\s\S]*?</think>', '', text, flags=re.DOTALL)
        # 使用正则表达式去除所有标签
        cleaned_text = re.sub(r'<.*?>', '', text).strip()
        return cleaned_text


class JsonStructOutputParser(StrOutputParser):
    """
    JSON structure output parser for LLM responses.
    
    Note: 用于清洗LLM输出的JSON结构，去除代码块、标签等杂质，返回纯净JSON字符串
    """
    
    def parse(self, text: str) -> str:
        """
        @param text str 原始文本
        @return str 清理后的JSON字符串
        Note: 解析并清理JSON格式的LLM输出
        """
        # 去除代码块标记
        text = re.sub(r"```json|```", "", text, flags=re.IGNORECASE).strip()
        # 去除所有HTML/XML标签
        text = re.sub(r'<.*?>', '', text).strip()
        # 只保留第一个大括号包裹的内容
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return match.group(0)
        return text


class OllamaLLM(BaseLLM):
    """
    Ollama LLM implementation for LANGGRAPH integration.
    
    Note: Ollama大语言模型实现，支持同步和异步调用
    """
    
    generate_url: str = ""
    chat_url: str = ""
    
    def __init__(self, config: LLMConfig,**kwargs):
        """
        @param config LLMConfig LLM配置
        Note: 初始化Ollama LLM
        """
        super().__init__(config,**kwargs)
        
        # 构建API端点
        self.generate_url = f"{self.config.base_url}/api/generate"
        self.chat_url = f"{self.config.base_url}/api/chat"
        
        # 验证Ollama服务连接
        self._validate_connection()
        
        logger.info(f"Ollama LLM initialized with endpoint: {self.generate_url}")
    
    @property
    def _llm_type(self) -> str:
        """
        @return str LLM类型
        Note: 返回Ollama LLM类型标识
        """
        return "ollama_llm"
    
    def _validate_connection(self) -> None:
        """
        @throws ValidationException 连接验证异常
        Note: 验证Ollama服务连接
        """
        try:
            # 测试连接
            response = requests.get(
                f"{self.config.base_url}/api/tags",
                timeout=5
            )
            response.raise_for_status()
            logger.info("Ollama service connection validated successfully")
        except Exception as e:
            error_msg = f"Failed to connect to Ollama service at {self.config.base_url}: {str(e)}"
            logger.error(error_msg)
            raise ValidationException(error_msg)
    
    def _prepare_request_data(self, prompt: str, stop: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
        """
        @param prompt str 输入提示
        @param stop Optional[List[str]] 停止词列表
        @param kwargs 其他参数
        @return Dict[str, Any] 请求数据
        Note: 准备Ollama API请求数据
        """
        request_data = {
            "model": self.config.model_name,
            "prompt": prompt,
            "stream": self.config.stream,
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
                "top_p": kwargs.get("top_p", self.config.top_p),
                "frequency_penalty": kwargs.get("frequency_penalty", self.config.frequency_penalty),
                "presence_penalty": kwargs.get("presence_penalty", self.config.presence_penalty),
            }
        }
        
        if stop:
            request_data["options"]["stop"] = stop
        
        return request_data
    
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
        @throws Exception 生成异常
        Note: 同步生成方法实现
        """
        request_data = self._prepare_request_data(prompt, stop, **kwargs)
        
        try:
            response = requests.post(
                self.generate_url,
                json=request_data,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            if self.config.stream:
                # 处理流式响应
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line.decode('utf-8'))
                            if "response" in data:
                                full_response += data["response"]
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
                return full_response
            else:
                # 处理非流式响应
                data = response.json()
                return data.get('response', '')
                
        except requests.RequestException as e:
            error_msg = f"Ollama API request failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Ollama generation failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
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
        @throws Exception 生成异常
        Note: 异步生成方法实现
        """
        request_data = self._prepare_request_data(prompt, stop, **kwargs)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.generate_url,
                    json=request_data,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as response:
                    response.raise_for_status()
                    
                    if self.config.stream:
                        # 处理流式响应
                        full_response = ""
                        async for line in response.content:
                            if line:
                                try:
                                    data = json.loads(line.decode('utf-8'))
                                    if "response" in data:
                                        full_response += data["response"]
                                    if data.get("done", False):
                                        break
                                except json.JSONDecodeError:
                                    continue
                        return full_response
                    else:
                        # 处理非流式响应
                        data = await response.json()
                        return data.get('response', '')
                        
        except aiohttp.ClientError as e:
            error_msg = f"Ollama async API request failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Ollama async generation failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
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
        @throws Exception 生成异常
        Note: 流式生成方法实现
        """
        request_data = self._prepare_request_data(prompt, stop, **kwargs)
        request_data["stream"] = True  # 强制启用流式输出
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.generate_url,
                    json=request_data,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.content:
                        if line:
                            try:
                                data = json.loads(line.decode('utf-8'))
                                if "response" in data:
                                    yield data["response"]
                                if data.get("done", False):
                                    break
                            except json.JSONDecodeError:
                                continue
                                
        except aiohttp.ClientError as e:
            error_msg = f"Ollama stream API request failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Ollama stream generation failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    async def create_chain(self, template: str, output_parser: Optional[StrOutputParser] = None):
        """
        @param template str 提示模板
        @param output_parser Optional[StrOutputParser] 输出解析器
        @return 链式调用对象
        Note: 创建LangChain链式调用对象
        """
        prompt_template = PromptTemplate.from_template(template)
        
        if output_parser is None:
            output_parser = CleanOutputParser()
        
        # 创建链式调用
        chain = prompt_template | self | output_parser
        
        logger.info(f"Created chain with template: {template[:50]}...")
        return chain
    
    async def create_json_chain(self, template: str):
        """
        @param template str 提示模板
        @return 链式调用对象
        Note: 创建JSON输出的链式调用对象
        """
        prompt_template = PromptTemplate.from_template(template)
        
        # 创建链式调用
        chain = prompt_template | self | CleanOutputParser()|JsonStructOutputParser()
        
        logger.info(f"Created chain with template: {template[:50]}...")
        return chain
    
    def get_available_models(self) -> List[str]:
        """
        @return List[str] 可用模型列表
        @throws Exception 获取模型列表异常
        Note: 获取Ollama服务可用的模型列表
        """
        try:
            response = requests.get(
                f"{self.config.base_url}/api/tags",
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            models = [model["name"] for model in data.get("models", [])]
            
            logger.info(f"Available models: {models}")
            return models
            
        except Exception as e:
            error_msg = f"Failed to get available models: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    async def get_available_models_async(self) -> List[str]:
        """
        @return List[str] 可用模型列表
        @throws Exception 获取模型列表异常
        Note: 异步获取Ollama服务可用的模型列表
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.config.base_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as response:
                    response.raise_for_status()
                    
                    data = await response.json()
                    models = [model["name"] for model in data.get("models", [])]
                    
                    logger.info(f"Available models: {models}")
                    return models
                    
        except Exception as e:
            error_msg = f"Failed to get available models: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def pull_model(self, model_name: str) -> bool:
        """
        @param model_name str 模型名称
        @return bool 是否成功拉取
        Note: 拉取指定模型到本地
        """
        try:
            response = requests.post(
                f"{self.config.base_url}/api/pull",
                json={"name": model_name},
                timeout=300  # 拉取模型可能需要较长时间
            )
            response.raise_for_status()
            
            logger.info(f"Successfully pulled model: {model_name}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to pull model {model_name}: {str(e)}"
            logger.error(error_msg)
            return False


# 兼容性函数，保持向后兼容
def create_ollama_llm(
    model_name: str,
    base_url: str = "http://localhost:11434",
    **kwargs
) -> OllamaLLM:
    """
    @param model_name str 模型名称
    @param base_url str 服务地址
    @param kwargs 其他配置参数
    @return OllamaLLM Ollama LLM实例
    Note: 创建Ollama LLM实例的便捷函数
    """
    config = LLMConfig(
        model_name=model_name,
        base_url=base_url,
        **kwargs
    )
    return OllamaLLM(config)


# 向后兼容的类别名
CustomOllamaLLM = OllamaLLM
