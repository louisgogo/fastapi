"""
Tests for LLM module functionality.

@author malou
@since 2025-01-08
Note: LLM模块功能测试
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from app.llms import (
    BaseLLM,
    LLMConfig,
    LLMResponse,
    OllamaLLM,
    LLMFactory,
    LLMType,
    CleanOutputParser,
    JsonStructOutputParser,
    create_ollama_llm,
    get_default_llm
)
from app.core.exceptions import ValidationException


class TestLLMConfig:
    """Test LLM configuration."""
    
    @pytest.mark.asyncio
    async def test_valid_config(self):
        """
        Test valid LLM configuration creation.
        
        Note: 测试有效的LLM配置创建
        """
        config = LLMConfig(
            model_name="test_model",
            base_url="http://localhost:11434",
            temperature=0.5,
            max_tokens=1000
        )
        
        assert config.model_name == "test_model"
        assert config.base_url == "http://localhost:11434"
        assert config.temperature == 0.5
        assert config.max_tokens == 1000
        
        # 验证配置应该不抛出异常
        config.validate_config()
    
    @pytest.mark.asyncio
    async def test_invalid_config(self):
        """
        Test invalid LLM configuration.
        
        Note: 测试无效的LLM配置
        """
        with pytest.raises(ValidationException):
            config = LLMConfig(
                model_name="",  # 空模型名
                base_url="http://localhost:11434"
            )
            config.validate_config()
        
        with pytest.raises(ValidationException):
            config = LLMConfig(
                model_name="test_model",
                base_url=""  # 空URL
            )
            config.validate_config()


class TestLLMResponse:
    """Test LLM response models."""
    
    @pytest.mark.asyncio
    async def test_success_response(self):
        """
        Test successful LLM response creation.
        
        Note: 测试成功响应创建
        """
        response = LLMResponse.create_success_response(
            request_id="test_123",
            model_name="test_model",
            prompt="Hello",
            response="Hi there!",
            start_time=1000.0,
            end_time=1001.5,
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30
        )
        
        assert response.request_id == "test_123"
        assert response.model_name == "test_model"
        assert response.prompt == "Hello"
        assert response.response == "Hi there!"
        assert response.duration == 1.5
        assert response.error is None
        assert response.prompt_tokens == 10
        assert response.completion_tokens == 20
        assert response.total_tokens == 30
    
    @pytest.mark.asyncio
    async def test_error_response(self):
        """
        Test error LLM response creation.
        
        Note: 测试错误响应创建
        """
        response = LLMResponse.create_error_response(
            request_id="test_456",
            model_name="test_model",
            prompt="Hello",
            error="Connection failed",
            start_time=1000.0,
            end_time=1001.0
        )
        
        assert response.request_id == "test_456"
        assert response.error == "Connection failed"
        assert response.response == ""
        assert response.duration == 1.0


class TestOutputParsers:
    """Test output parsers."""
    
    @pytest.mark.asyncio
    async def test_clean_output_parser(self):
        """
        Test clean output parser.
        
        Note: 测试清理输出解析器
        """
        parser = CleanOutputParser()
        
        # 测试移除think标签
        text_with_think = "Some text <think>internal thoughts</think> more text"
        cleaned = parser.parse(text_with_think)
        assert "internal thoughts" not in cleaned
        assert "Some text  more text" == cleaned
        
        # 测试移除HTML标签
        text_with_tags = "Hello <b>world</b> <i>test</i>"
        cleaned = parser.parse(text_with_tags)
        assert cleaned == "Hello world test"
    
    @pytest.mark.asyncio
    async def test_json_struct_output_parser(self):
        """
        Test JSON structure output parser.
        
        Note: 测试JSON结构输出解析器
        """
        parser = JsonStructOutputParser()
        
        # 测试移除代码块
        text_with_code = '```json\n{"name": "test", "value": 123}\n```'
        cleaned = parser.parse(text_with_code)
        assert cleaned == '{"name": "test", "value": 123}'
        
        # 测试提取JSON
        text_with_json = 'Some text {"key": "value"} more text'
        cleaned = parser.parse(text_with_json)
        assert cleaned == '{"key": "value"}'


class TestLLMFactory:
    """Test LLM factory functionality."""
    
    def setup_method(self):
        """Setup test method."""
        # 清除缓存
        LLMFactory.clear_cache()
    
    @pytest.mark.asyncio
    async def test_create_ollama_llm(self):
        """
        Test creating Ollama LLM through factory.
        
        Note: 测试通过工厂创建Ollama LLM
        """
        with patch('app.llms.ollama_llm.requests.get') as mock_get:
            # Mock连接验证
            mock_get.return_value.raise_for_status.return_value = None
            mock_get.return_value.json.return_value = {"models": []}
            
            llm = LLMFactory.create_ollama_llm(
                model_name="test_model",
                base_url="http://localhost:11434"
            )
            
            assert isinstance(llm, OllamaLLM)
            assert llm.config.model_name == "test_model"
            assert llm.config.base_url == "http://localhost:11434"
    
    @pytest.mark.asyncio
    async def test_llm_caching(self):
        """
        Test LLM instance caching.
        
        Note: 测试LLM实例缓存
        """
        with patch('app.llms.ollama_llm.requests.get') as mock_get:
            mock_get.return_value.raise_for_status.return_value = None
            mock_get.return_value.json.return_value = {"models": []}
            
            # 创建并缓存LLM
            llm1 = LLMFactory.create_llm(
                LLMType.OLLAMA,
                {"model_name": "test_model", "base_url": "http://localhost:11434"},
                cache_key="test_llm"
            )
            
            # 获取缓存的LLM
            llm2 = LLMFactory.get_cached_llm("test_llm")
            
            assert llm1 is llm2
            
            # 测试缓存列表
            cached_llms = LLMFactory.list_cached_llms()
            assert "test_llm" in cached_llms
            
            # 清除特定缓存
            LLMFactory.clear_cache("test_llm")
            llm3 = LLMFactory.get_cached_llm("test_llm")
            assert llm3 is None
    
    @pytest.mark.asyncio
    async def test_unsupported_llm_type(self):
        """
        Test creating unsupported LLM type.
        
        Note: 测试创建不支持的LLM类型
        """
        with pytest.raises(ValidationException):
            LLMFactory.create_llm("unsupported_type")
    
    @pytest.mark.asyncio
    async def test_get_supported_types(self):
        """
        Test getting supported LLM types.
        
        Note: 测试获取支持的LLM类型
        """
        supported_types = LLMFactory.get_supported_types()
        assert "ollama" in supported_types


class TestOllamaLLM:
    """Test Ollama LLM implementation."""
    
    @pytest.mark.asyncio
    async def test_ollama_llm_creation(self):
        """
        Test Ollama LLM creation.
        
        Note: 测试Ollama LLM创建
        """
        with patch('app.llms.ollama_llm.requests.get') as mock_get:
            mock_get.return_value.raise_for_status.return_value = None
            mock_get.return_value.json.return_value = {"models": []}
            
            config = LLMConfig(
                model_name="test_model",
                base_url="http://localhost:11434"
            )
            
            llm = OllamaLLM(config)
            
            assert llm._llm_type == "ollama_llm"
            assert llm.config.model_name == "test_model"
            assert llm.generate_url == "http://localhost:11434/api/generate"
    
    @pytest.mark.asyncio
    async def test_sync_generation(self):
        """
        Test synchronous text generation.
        
        Note: 测试同步文本生成
        """
        with patch('app.llms.ollama_llm.requests.get') as mock_get, \
             patch('app.llms.ollama_llm.requests.post') as mock_post:
            
            # Mock连接验证
            mock_get.return_value.raise_for_status.return_value = None
            mock_get.return_value.json.return_value = {"models": []}
            
            # Mock生成响应
            mock_post.return_value.raise_for_status.return_value = None
            mock_post.return_value.json.return_value = {"response": "Generated text"}
            
            config = LLMConfig(
                model_name="test_model",
                base_url="http://localhost:11434"
            )
            
            llm = OllamaLLM(config)
            response = llm._generate_sync("Test prompt")
            
            assert response == "Generated text"
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_async_generation(self):
        """
        Test asynchronous text generation.
        
        Note: 测试异步文本生成
        """
        with patch('app.llms.ollama_llm.requests.get') as mock_get, \
             patch('app.llms.ollama_llm.aiohttp.ClientSession.post') as mock_post:
            
            # Mock连接验证
            mock_get.return_value.raise_for_status.return_value = None
            mock_get.return_value.json.return_value = {"models": []}
            
            # Mock异步响应
            mock_response = AsyncMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"response": "Async generated text"}
            mock_post.return_value.__aenter__.return_value = mock_response
            
            config = LLMConfig(
                model_name="test_model",
                base_url="http://localhost:11434"
            )
            
            llm = OllamaLLM(config)
            response = await llm._generate_async("Test prompt")
            
            assert response == "Async generated text"
    
    @pytest.mark.asyncio
    async def test_connection_validation_failure(self):
        """
        Test connection validation failure.
        
        Note: 测试连接验证失败
        """
        with patch('app.llms.ollama_llm.requests.get') as mock_get:
            mock_get.side_effect = Exception("Connection failed")
            
            config = LLMConfig(
                model_name="test_model",
                base_url="http://localhost:11434"
            )
            
            with pytest.raises(ValidationException):
                OllamaLLM(config)
    
    @pytest.mark.asyncio
    async def test_chain_creation(self):
        """
        Test chain creation.
        
        Note: 测试链式调用创建
        """
        with patch('app.llms.ollama_llm.requests.get') as mock_get:
            mock_get.return_value.raise_for_status.return_value = None
            mock_get.return_value.json.return_value = {"models": []}
            
            config = LLMConfig(
                model_name="test_model",
                base_url="http://localhost:11434"
            )
            
            llm = OllamaLLM(config)
            
            # 测试普通链创建
            chain = llm.create_chain("Test template: {input}")
            assert chain is not None
            
            # 测试JSON链创建
            json_chain = llm.create_json_chain("JSON template: {input}")
            assert json_chain is not None


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    @pytest.mark.asyncio
    async def test_create_ollama_llm_function(self):
        """
        Test create_ollama_llm convenience function.
        
        Note: 测试create_ollama_llm便捷函数
        """
        with patch('app.llms.ollama_llm.requests.get') as mock_get:
            mock_get.return_value.raise_for_status.return_value = None
            mock_get.return_value.json.return_value = {"models": []}
            
            llm = create_ollama_llm(
                model_name="test_model",
                base_url="http://localhost:11434"
            )
            
            assert isinstance(llm, OllamaLLM)
            assert llm.config.model_name == "test_model"
    
    @pytest.mark.asyncio
    async def test_get_default_llm_function(self):
        """
        Test get_default_llm convenience function.
        
        Note: 测试get_default_llm便捷函数
        """
        with patch('app.llms.ollama_llm.requests.get') as mock_get:
            mock_get.return_value.raise_for_status.return_value = None
            mock_get.return_value.json.return_value = {"models": []}
            
            # 清除缓存
            LLMFactory.clear_cache()
            
            llm1 = get_default_llm()
            llm2 = get_default_llm()
            
            # 应该返回相同的缓存实例
            assert llm1 is llm2
            assert isinstance(llm1, OllamaLLM) 