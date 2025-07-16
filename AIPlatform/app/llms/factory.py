"""
LLM Factory for creating and managing LLM instances.

@author malou
@since 2025-01-08
Note: LLM工厂类，用于创建和管理不同类型的LLM实例
"""

from typing import Any, Dict, Optional, Type, Union
from enum import Enum

from .base_llm import BaseLLM, LLMConfig
from .ollama_llm import OllamaLLM


from app.core.config import get_settings, get_ollama_config
from app.utils.logger import logger
from app.core.exceptions import ValidationException



class LLMType(Enum):
    """
    LLM type enumeration.
    
    Note: LLM类型枚举，定义支持的LLM类型
    """
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"


class LLMFactory:
    """
    LLM Factory for creating and managing LLM instances.
    
    Note: LLM工厂类，提供统一的LLM创建和管理接口
    """
    
    # 注册的LLM类型映射
    _llm_registry: Dict[LLMType, Type[BaseLLM]] = {
        LLMType.OLLAMA: OllamaLLM,
        # 可以在这里添加其他LLM类型
        # LLMType.OPENAI: OpenAILLM,
        # LLMType.ANTHROPIC: AnthropicLLM,
    }
    
    # LLM实例缓存
    _llm_cache: Dict[str, BaseLLM] = {}
    
    @classmethod
    def create_llm(
        cls,
        llm_type: Union[LLMType, str],
        config: Optional[Union[LLMConfig, Dict[str, Any]]] = None,
        cache_key: Optional[str] = None
    ) -> BaseLLM:
        """
        @param llm_type Union[LLMType, str] LLM类型
        @param config Optional[Union[LLMConfig, Dict[str, Any]]] LLM配置
        @param cache_key Optional[str] 缓存键，如果提供则会缓存实例
        @return BaseLLM LLM实例
        @throws ValidationException 创建异常
        Note: 创建LLM实例
        """
        # 类型转换
        if isinstance(llm_type, str):
            try:
                llm_type = LLMType(llm_type.lower())
            except ValueError:
                raise ValidationException(f"Unsupported LLM type: {llm_type}")
        
        # 检查缓存
        if cache_key and cache_key in cls._llm_cache:
            logger.info(f"Using cached LLM instance: {cache_key}")
            return cls._llm_cache[cache_key]
        
        # 检查LLM类型是否支持
        if llm_type not in cls._llm_registry:
            raise ValidationException(f"Unsupported LLM type: {llm_type}")
        
        # 获取LLM类
        llm_class = cls._llm_registry[llm_type]
        
        # 准备配置
        if config is None:
            config = cls._get_default_config(llm_type)
        elif isinstance(config, dict):
            # 合并默认配置和用户配置
            default_config = cls._get_default_config(llm_type)
            merged_config = default_config.model_copy()
            
            # 更新配置
            for key, value in config.items():
                if hasattr(merged_config, key):
                    setattr(merged_config, key, value)
            
            config = merged_config
        
        # 创建LLM实例
        try:
            llm_instance = llm_class(config)
            
            # 缓存实例
            if cache_key:
                cls._llm_cache[cache_key] = llm_instance
                logger.info(f"Cached LLM instance: {cache_key}")
            
            logger.info(f"Created LLM instance: {llm_type.value}")
            return llm_instance
            
        except Exception as e:
            error_msg = f"Failed to create LLM instance: {str(e)}"
            logger.error(error_msg)
            raise ValidationException(error_msg)
    
    @classmethod
    def create_ollama_llm(
        cls,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
        stream: Optional[bool] = None,
        **kwargs
    ) -> OllamaLLM:
        """
        @param model_name Optional[str] 模型名称
        @param base_url Optional[str] 服务地址
        @param kwargs 其他配置参数
        @return OllamaLLM Ollama LLM实例
        Note: 创建Ollama LLM实例的便捷方法
        """
        # 获取默认配置
        default_config = cls._get_default_config(LLMType.OLLAMA)
        
        # 更新配置
        if model_name:
            default_config.model_name = model_name
        if base_url:
            default_config.base_url = base_url
        if stream:
            default_config.stream = stream
        
        # 更新其他配置
        for key, value in kwargs.items():
            if hasattr(default_config, key):
                setattr(default_config, key, value)
        
        llm_instance = OllamaLLM(default_config)
        
        return llm_instance
    
    @classmethod
    def get_cached_llm(cls, cache_key: str) -> Optional[BaseLLM]:
        """
        @param cache_key str 缓存键
        @return Optional[BaseLLM] 缓存的LLM实例
        Note: 获取缓存的LLM实例
        """
        return cls._llm_cache.get(cache_key)
    
    @classmethod
    def clear_cache(cls, cache_key: Optional[str] = None) -> None:
        """
        @param cache_key Optional[str] 缓存键，如果为None则清空所有缓存
        Note: 清除LLM实例缓存
        """
        if cache_key:
            if cache_key in cls._llm_cache:
                del cls._llm_cache[cache_key]
                logger.info(f"Cleared LLM cache: {cache_key}")
        else:
            cls._llm_cache.clear()
            logger.info("Cleared all LLM cache")
    
    @classmethod
    def list_cached_llms(cls) -> Dict[str, str]:
        """
        @return Dict[str, str] 缓存的LLM实例信息
        Note: 列出所有缓存的LLM实例
        """
        return {
            cache_key: str(llm_instance)
            for cache_key, llm_instance in cls._llm_cache.items()
        }
    
    @classmethod
    def register_llm_type(cls, llm_type: LLMType, llm_class: Type[BaseLLM]) -> None:
        """
        @param llm_type LLMType LLM类型
        @param llm_class Type[BaseLLM] LLM类
        Note: 注册新的LLM类型
        """
        cls._llm_registry[llm_type] = llm_class
        logger.info(f"Registered LLM type: {llm_type.value}")
    
    @classmethod
    def get_supported_types(cls) -> list[str]:
        """
        @return list[str] 支持的LLM类型列表
        Note: 获取所有支持的LLM类型
        """
        return [llm_type.value for llm_type in cls._llm_registry.keys()]
    
    @classmethod
    def _get_default_config(cls, llm_type: LLMType) -> LLMConfig:
        """
        @param llm_type LLMType LLM类型
        @return LLMConfig 默认配置
        Note: 获取指定LLM类型的默认配置
        """
        settings = get_settings()
        
        if llm_type == LLMType.OLLAMA:
            ollama_config = get_ollama_config()
            return LLMConfig(
                model_name=ollama_config.get("default_model", "llama3.2"),
                base_url=ollama_config.get("base_url", "http://localhost:11434"),
                temperature=0.1,
                max_tokens=1000,
                top_p=0.9,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                timeout=ollama_config.get("timeout", 200),
                max_retries=ollama_config.get("max_retries", 3),
                stream=False,
                enable_tools=False,
                enable_memory=False,
                enable_planning=False
            )
        
        # 可以在这里添加其他LLM类型的默认配置
        # elif llm_type == LLMType.OPENAI:
        #     return LLMConfig(
        #         model_name="gpt-3.5-turbo",
        #         base_url="https://api.openai.com/v1",
        #         ...
        #     )
        
        else:
            raise ValidationException(f"No default config for LLM type: {llm_type}")


# 便捷函数，用于快速创建LLM实例
def create_llm(
    llm_type: Union[LLMType, str],
    config: Optional[Union[LLMConfig, Dict[str, Any]]] = None,
    cache_key: Optional[str] = None
) -> BaseLLM:
    """
    @param llm_type Union[LLMType, str] LLM类型
    @param config Optional[Union[LLMConfig, Dict[str, Any]]] LLM配置
    @param cache_key Optional[str] 缓存键
    @return BaseLLM LLM实例
    Note: 创建LLM实例的便捷函数
    """
    return LLMFactory.create_llm(llm_type, config, cache_key)


def create_ollama_llm(
    model_name: Optional[str] = None,
    base_url: Optional[str] = None,
    cache_key: Optional[str] = None,
    **kwargs
) -> OllamaLLM:
    """
    @param model_name Optional[str] 模型名称
    @param base_url Optional[str] 服务地址
    @param cache_key Optional[str] 缓存键
    @param kwargs 其他配置参数
    @return OllamaLLM Ollama LLM实例
    Note: 创建Ollama LLM实例的便捷函数
    """
    llm = LLMFactory.create_ollama_llm(model_name, base_url, **kwargs)
    
    if cache_key:
        LLMFactory._llm_cache[cache_key] = llm
    
    return llm


def get_default_llm(cache_key: str = "default") -> BaseLLM:
    """
    @param cache_key str 缓存键
    @return BaseLLM 默认LLM实例
    Note: 获取默认LLM实例
    """
    return LLMFactory.create_llm(LLMType.OLLAMA, cache_key=cache_key) 