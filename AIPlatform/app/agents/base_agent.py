"""
Base Agent class.

@author malou
@since 2024-12-19
Note: 基础Agent类，定义Agent的通用接口和行为模式
"""

import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from app.core.config import get_settings, get_ollama_config
from app.core.exceptions import AgentException
from app.utils.logger import logger


class AgentState(BaseModel):
    """
    Agent state schema.
    
    Note: Agent状态模式，用于在LangGraph中传递状态
    """
    
    request_id: str
    user_input: str
    agent_type: str
    context: Dict[str, Any] = {}
    messages: List[Dict[str, str]] = []
    intermediate_steps: List[Dict[str, Any]] = []
    result: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}


class BaseAgent(ABC):
    """
    Base Agent class.
    
    Note: 基础Agent抽象类，定义所有Agent的通用接口
    """
    
    def __init__(self, name: str, agent_type: str, config: Optional[Dict] = None):
        """
        @param name str Agent名称
        @param agent_type str Agent类型
        @param config Optional[Dict] Agent配置
        Note: 初始化基础Agent
        """
        self.name = name
        self.agent_type = agent_type
        
        # 获取环境配置
        self.settings = get_settings()
        self.ollama_config = get_ollama_config()
        
        # 合并配置：环境配置 + 传入配置
        self.config = self._merge_config(config or {})
        self.agent_id = str(uuid.uuid4())
        
        logger.info(f"Initialized {self.agent_type} agent: {self.name}")
        logger.info(f"Agent config: {self.config}")
    
    def _merge_config(self, custom_config: Dict) -> Dict:
        """
        @param custom_config Dict 自定义配置
        @return Dict 合并后的配置
        Note: 合并环境配置和自定义配置，自定义配置优先级更高
        """
        # 基础配置从环境变量获取
        base_config = {
            "model": self.ollama_config.get("default_model", "llama3.2"),
            "base_url": self.ollama_config.get("base_url", "http://localhost:11434"),
            "timeout": self.ollama_config.get("timeout", 30),
            "max_retries": self.ollama_config.get("max_retries", 3),
            "temperature": 0.1,
            "max_tokens": 1000,
            "top_p": 0.9,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        }
        
        # 自定义配置覆盖基础配置
        base_config.update(custom_config)
        
        return base_config
    
    def get_model_config(self) -> Dict[str, Any]:
        """
        @return Dict[str, Any] 模型配置
        Note: 获取当前Agent使用的模型配置
        """
        return {
            "model": self.get_config("model"),
            "base_url": self.get_config("base_url"),
            "timeout": self.get_config("timeout"),
            "max_retries": self.get_config("max_retries"),
        }
    
    def get_generation_config(self) -> Dict[str, Any]:
        """
        @return Dict[str, Any] 生成配置
        Note: 获取文本生成相关的配置参数
        """
        return {
            "temperature": self.get_config("temperature", 0.1),
            "max_tokens": self.get_config("max_tokens", 1000),
            "top_p": self.get_config("top_p", 0.9),
            "frequency_penalty": self.get_config("frequency_penalty", 0.0),
            "presence_penalty": self.get_config("presence_penalty", 0.0),
        }
    
    @abstractmethod
    async def process(self, state: AgentState) -> AgentState:
        """
        @param state AgentState Agent状态
        @return AgentState 处理后的状态
        @throws AgentException Agent处理异常
        Note: 处理用户输入的抽象方法，需要子类实现
        """
        pass
    
    @abstractmethod
    def validate_input(self, user_input: str) -> bool:
        """
        @param user_input str 用户输入
        @return bool 输入是否有效
        Note: 验证用户输入的抽象方法
        """
        pass
    
    def create_state(self, user_input: str, context: Optional[Dict] = None) -> AgentState:
        """
        @param user_input str 用户输入
        @param context Optional[Dict] 上下文信息
        @return AgentState 初始化的Agent状态
        Note: 创建初始Agent状态
        """
        return AgentState(
            request_id=str(uuid.uuid4()),
            user_input=user_input,
            agent_type=self.agent_type,
            context=context or {},
            messages=[],
            intermediate_steps=[],
            metadata={
                "agent_name": self.name,
                "agent_id": self.agent_id,
                "config": self.config
            }
        )
    
    def add_message(self, state: AgentState, role: str, content: str) -> AgentState:
        """
        @param state AgentState Agent状态
        @param role str 消息角色
        @param content str 消息内容
        @return AgentState 更新后的状态
        Note: 添加消息到状态中
        """
        state.messages.append({
            "role": role,
            "content": content,
            "timestamp": str(uuid.uuid4())  # 简化的时间戳
        })
        return state
    
    def add_step(self, state: AgentState, step_name: str, step_data: Any) -> AgentState:
        """
        @param state AgentState Agent状态
        @param step_name str 步骤名称
        @param step_data Any 步骤数据
        @return AgentState 更新后的状态
        Note: 添加中间步骤到状态中
        """
        state.intermediate_steps.append({
            "step": step_name,
            "data": step_data,
            "timestamp": str(uuid.uuid4())  # 简化的时间戳
        })
        return state
    
    def set_result(self, state: AgentState, result: str, metadata: Optional[Dict] = None) -> AgentState:
        """
        @param state AgentState Agent状态
        @param result str 处理结果
        @param metadata Optional[Dict] 结果元数据
        @return AgentState 更新后的状态
        Note: 设置处理结果
        """
        state.result = result
        if metadata:
            state.metadata.update(metadata)
        return state
    
    def set_error(self, state: AgentState, error: str) -> AgentState:
        """
        @param state AgentState Agent状态
        @param error str 错误信息
        @return AgentState 更新后的状态
        Note: 设置错误信息
        """
        state.error = error
        logger.error(f"Agent {self.name} error: {error}")
        return state
    
    def handle_error(self, state: AgentState, error: Exception) -> AgentState:
        """
        @param state AgentState Agent状态
        @param error Exception 异常对象
        @return AgentState 处理错误后的状态
        Note: 处理Agent执行过程中的错误
        """
        error_msg = f"Agent {self.name} failed: {str(error)}"
        logger.error(error_msg, exc_info=True)
        
        return self.set_error(state, error_msg)
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        @param key str 配置键
        @param default Any 默认值
        @return Any 配置值
        Note: 获取Agent配置
        """
        return self.config.get(key, default)
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        @param updates Dict[str, Any] 配置更新
        Note: 更新Agent配置
        """
        self.config.update(updates)
        logger.info(f"Updated config for agent {self.name}: {updates}")
    
    def __str__(self) -> str:
        """
        @return str Agent字符串表示
        Note: Agent的字符串表示
        """
        return f"{self.agent_type}Agent(name={self.name}, id={self.agent_id})"
    
    def __repr__(self) -> str:
        """
        @return str Agent的详细表示
        Note: Agent的详细字符串表示
        """
        return f"{self.__class__.__name__}(name='{self.name}', type='{self.agent_type}', config={self.config})" 