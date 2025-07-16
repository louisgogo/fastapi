"""
OLLAMA service.

@author malou
@since 2024-12-19
Note: 异步OLLAMA模型调用服务，提供与本地OLLAMA模型的异步交互功能
"""

import asyncio
import json
import time
from typing import Dict, List, Optional

import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.core.exceptions import OllamaException
from app.schemas.agent import ModelInfo, ModelListResponse
from app.utils.logger import logger


class ChatMessage(BaseModel):
    """
    Chat message schema.
    
    Note: 聊天消息模式
    """
    role: str  # system, user, assistant
    content: str


class ChatRequest(BaseModel):
    """
    Chat request schema.
    
    Note: 聊天请求模式
    """
    model: str
    messages: List[ChatMessage]
    stream: bool = False
    options: Optional[Dict] = None


class ChatResponse(BaseModel):
    """
    Chat response schema.
    
    Note: 聊天响应模式
    """
    model: str
    created_at: str
    message: ChatMessage
    done: bool
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    prompt_eval_duration: Optional[int] = None
    eval_count: Optional[int] = None
    eval_duration: Optional[int] = None


class OllamaService:
    """
    OLLAMA service class.
    
    Note: 异步OLLAMA服务类，封装OLLAMA API异步调用
    """
    
    def __init__(self):
        """
        Note: 初始化异步OLLAMA服务
        """
        # 导入并使用全局设置实例
        from app.core.config import get_settings
        config = get_settings()
        
        self.base_url = config.OLLAMA_BASE_URL
        self.timeout = config.OLLAMA_TIMEOUT
        self.default_model = config.OLLAMA_DEFAULT_MODEL
        self.max_retries = config.OLLAMA_MAX_RETRIES
        
        # 创建异步HTTP客户端
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout
        )
    
    async def check_health(self) -> bool:
        """
        @return bool OLLAMA服务是否健康
        Note: 异步检查OLLAMA服务健康状态
        """
        try:
            response = await self.client.get("/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"OLLAMA health check failed: {str(e)}")
            return False
    
    async def list_models(self) -> ModelListResponse:
        """
        @return ModelListResponse 模型列表响应
        @throws OllamaException OLLAMA服务异常
        Note: 异步获取可用模型列表
        """
        try:
            response = await self.client.get("/api/tags")
            if response.status_code != 200:
                raise OllamaException(f"Failed to list models: HTTP {response.status_code}")
            
            data = response.json()
            models = []
            
            for model_data in data.get("models", []):
                # 处理size字段 - 转换为字符串格式
                size = model_data.get("size", "")
                if isinstance(size, int):
                    # 将字节数转换为可读格式
                    if size >= 1024**3:
                        size = f"{size / (1024**3):.1f}GB"
                    elif size >= 1024**2:
                        size = f"{size / (1024**2):.1f}MB"
                    elif size >= 1024:
                        size = f"{size / 1024:.1f}KB"
                    else:
                        size = f"{size}B"
                elif not isinstance(size, str):
                    size = str(size) if size is not None else "Unknown"
                
                # 处理size_vram字段 - 更安全的参数大小解析
                size_vram = None
                details = model_data.get("details", {})
                parameter_size = details.get("parameter_size")
                
                if parameter_size:
                    try:
                        if isinstance(parameter_size, str):
                            # 处理类似 "3.2B", "7B", "13B" 的格式
                            param_str = parameter_size.upper().strip()
                            if param_str.endswith('B'):
                                # 以十亿为单位的参数
                                size_vram = int(float(param_str[:-1]) * 1000)  # 转换为百万参数
                            elif param_str.endswith('M'):
                                # 以百万为单位的参数
                                size_vram = int(float(param_str[:-1]))
                            elif param_str.endswith('K'):
                                # 以千为单位的参数
                                size_vram = int(float(param_str[:-1]) / 1000)
                            else:
                                size_vram = int(float(param_str))
                        elif isinstance(parameter_size, (int, float)):
                            size_vram = int(parameter_size)
                    except (ValueError, TypeError, AttributeError):
                        logger.warning(f"Failed to parse parameter_size: {parameter_size}")
                        size_vram = None
                
                model_info = ModelInfo(
                    name=model_data.get("name", ""),
                    size=size,
                    status="available",
                    description=model_data.get("details", {}).get("format", ""),
                    modified_at=model_data.get("modified_at"),
                    size_vram=size_vram
                )
                models.append(model_info)
            
            return ModelListResponse(models=models)
            
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to OLLAMA: {str(e)}")
            raise OllamaException(f"Connection error: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to list models: {str(e)}")
            raise OllamaException(f"Failed to list models: {str(e)}")
    
    async def chat_completion(
        self,
        model: str,
        messages: List[ChatMessage],
        stream: bool = False,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        retries: Optional[int] = None
    ) -> ChatResponse:
        """
        @param model str 模型名称
        @param messages List[ChatMessage] 消息列表
        @param stream bool 是否流式响应
        @param temperature float 温度参数
        @param max_tokens Optional[int] 最大token数
        @param retries Optional[int] 重试次数
        @return ChatResponse 聊天响应
        @throws OllamaException OLLAMA服务异常
        Note: 异步调用OLLAMA聊天完成API
        """
        if retries is None:
            retries = self.max_retries
            
        last_exception = None
        
        for attempt in range(retries + 1):
            try:
                # 构建请求参数
                request_data = {
                    "model": model,
                    "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
                    "stream": stream,
                    "options": {
                        "temperature": temperature,
                    }
                }
                
                if max_tokens:
                    request_data["options"]["num_predict"] = max_tokens
                
                logger.info(f"Sending request to OLLAMA (attempt {attempt + 1}/{retries + 1})")
                
                # 发送异步请求
                response = await self.client.post("/api/chat", json=request_data)
                
                if response.status_code != 200:
                    raise OllamaException(f"OLLAMA API error: HTTP {response.status_code} - {response.text}")
                
                # 解析响应
                response_data = response.json()
                
                # 构建响应对象
                message = ChatMessage(
                    role=response_data.get("message", {}).get("role", "assistant"),
                    content=response_data.get("message", {}).get("content", "")
                )
                
                chat_response = ChatResponse(
                    model=response_data.get("model", model),
                    created_at=response_data.get("created_at", ""),
                    message=message,
                    done=response_data.get("done", True),
                    total_duration=response_data.get("total_duration"),
                    load_duration=response_data.get("load_duration"),
                    prompt_eval_count=response_data.get("prompt_eval_count"),
                    prompt_eval_duration=response_data.get("prompt_eval_duration"),
                    eval_count=response_data.get("eval_count"),
                    eval_duration=response_data.get("eval_duration")
                )
                
                logger.info(f"OLLAMA chat completion successful")
                return chat_response
                
            except httpx.RequestError as e:
                last_exception = OllamaException(f"Connection error: {str(e)}")
                logger.warning(f"OLLAMA connection error (attempt {attempt + 1}): {str(e)}")
            except Exception as e:
                last_exception = OllamaException(f"OLLAMA error: {str(e)}")
                logger.warning(f"OLLAMA error (attempt {attempt + 1}): {str(e)}")
            
            # 如果不是最后一次尝试，等待后重试
            if attempt < retries:
                await asyncio.sleep(2 ** attempt)  # 指数退避
        
        # 所有重试都失败了
        logger.error(f"OLLAMA chat completion failed after {retries + 1} attempts")
        raise last_exception or OllamaException("Unknown error occurred")
    
    async def generate_nl2sql(
        self,
        natural_language: str,
        database_schema: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 1000
    ) -> str:
        """
        @param natural_language str 自然语言查询
        @param database_schema Optional[str] 数据库架构
        @param model Optional[str] 使用的模型
        @param temperature float 温度参数
        @param max_tokens int 最大token数
        @return str 生成的SQL语句
        @throws OllamaException OLLAMA服务异常
        Note: 异步生成自然语言转SQL
        """
        if model is None:
            model = self.default_model
        
        # 构建系统提示
        system_prompt = """你是一个专业的SQL查询助手。请根据用户的自然语言描述，生成对应的PostgreSQL查询语句。

要求：
1. 只返回SQL语句，不要包含任何解释或其他文本
2. SQL语句必须符合PostgreSQL语法
3. 使用标准的SQL命名约定
4. 确保查询的安全性，避免SQL注入"""

        if database_schema:
            system_prompt += f"\n\n数据库架构信息：\n{database_schema}"

        # 构建消息
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=f"请生成SQL查询：{natural_language}")
        ]
        
        # 调用聊天完成
        response = await self.chat_completion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # 提取并清理SQL
        sql = response.message.content.strip()
        
        # 移除可能的代码块标记
        if sql.startswith("```sql"):
            sql = sql[6:]
        elif sql.startswith("```"):
            sql = sql[3:]
        
        if sql.endswith("```"):
            sql = sql[:-3]
        
        return sql.strip()
    
    async def close(self):
        """
        Note: 异步关闭HTTP客户端
        """
        await self.client.aclose()


# 测试函数
async def test_ollama_service():
    """
    异步测试OLLAMA服务
    
    Note: 测试OLLAMA服务的各项功能
    """
    service = OllamaService()
    
    try:
        # 测试健康检查
        logger.info("Testing health check...")
        health = await service.check_health()
        logger.info(f"Health check result: {health}")
        
        if not health:
            logger.error("OLLAMA service is not healthy")
            return
        
        # 测试模型列表
        logger.info("Testing model list...")
        models = await service.list_models()
        logger.info(f"Available models: {len(models.models)}")
        for model in models.models:
            logger.info(f"  - {model.name}: {model.size}")
        
        # 测试NL2SQL
        if models.models:
            logger.info("Testing NL2SQL generation...")
            sql = await service.generate_nl2sql(
                "查询所有用户的姓名和邮箱",
                database_schema="CREATE TABLE users (id SERIAL PRIMARY KEY, name VARCHAR(100), email VARCHAR(255));",
                model=models.models[0].name
            )
            logger.info(f"Generated SQL: {sql}")
        
        logger.info("All tests passed!")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
    finally:
        await service.close()


if __name__ == "__main__":
    """
    运行测试
    """
    asyncio.run(test_ollama_service()) 