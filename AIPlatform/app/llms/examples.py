"""
LLM usage examples for LANGGRAPH integration.

@author malou
@since 2025-01-08
Note: LLM使用示例，展示如何使用符合LANGGRAPH标准的LLM模块
"""

import asyncio
from typing import Dict, Any

from . import (
    LLMFactory, 
    LLMType, 
    LLMConfig, 
    create_ollama_llm, 
    get_default_llm,
    CleanOutputParser,
    JsonStructOutputParser
)
from app.utils.logger import logger


async def basic_usage_example():
    """
    基础使用示例
    
    Note: 展示如何创建和使用LLM实例
    """
    print("=== 基础使用示例 ===")
    
    # 方式1：使用工厂类创建
    llm = LLMFactory.create_ollama_llm(
        model_name="llama3.2",
        base_url="http://localhost:11434",
        temperature=0.1,
        max_tokens=500
    )
    
    # 同步调用
    response = llm("请简要介绍一下Python编程语言")
    print(f"同步响应: {response}")
    
    # 异步调用
    async_response = await llm.ainvoke("请简要介绍一下FastAPI框架")
    print(f"异步响应: {async_response}")


async def chain_usage_example():
    """
    链式调用示例
    
    Note: 展示如何使用LangChain链式调用
    """
    print("\n=== 链式调用示例 ===")
    
    # 创建LLM实例
    llm = create_ollama_llm(
        model_name="llama3.2",
        cache_key="example_llm"
    )
    
    # 创建普通链
    chain = llm.create_chain("帮我给{product}写一段广告词")
    result = chain.invoke({"product": "伊利牛奶"})
    print(f"广告词: {result}")
    
    # 创建JSON输出链
    json_chain = llm.create_json_chain(
        "请以JSON格式返回{city}的基本信息，包含name、population、area等字段"
    )
    json_result = json_chain.invoke({"city": "北京"})
    print(f"JSON结果: {json_result}")


async def stream_usage_example():
    """
    流式输出示例
    
    Note: 展示如何使用流式输出
    """
    print("\n=== 流式输出示例 ===")
    
    # 创建支持流式输出的LLM
    config = LLMConfig(
        model_name="llama3.2",
        base_url="http://localhost:11434",
        stream=True,
        temperature=0.1,
        max_tokens=200
    )
    
    llm = LLMFactory.create_llm(LLMType.OLLAMA, config)
    
    print("流式输出: ", end="")
    async for chunk in llm._generate_stream("请写一首关于春天的诗"):
        print(chunk, end="", flush=True)
    print()


async def factory_usage_example():
    """
    工厂类使用示例
    
    Note: 展示如何使用工厂类管理LLM实例
    """
    print("\n=== 工厂类使用示例 ===")
    
    # 创建并缓存LLM实例
    llm1 = LLMFactory.create_llm(
        LLMType.OLLAMA,
        {"model_name": "llama3.2", "temperature": 0.1},
        cache_key="llm_creative"
    )
    
    llm2 = LLMFactory.create_llm(
        LLMType.OLLAMA,
        {"model_name": "llama3.2", "temperature": 0.8},
        cache_key="llm_analytical"
    )
    
    # 查看缓存的LLM实例
    cached_llms = LLMFactory.list_cached_llms()
    print(f"缓存的LLM实例: {cached_llms}")
    
    # 获取缓存的实例
    cached_llm = LLMFactory.get_cached_llm("llm_creative")
    if cached_llm:
        response = cached_llm("请创作一个有趣的故事开头")
        print(f"创意响应: {response}")
    
    # 清除特定缓存
    LLMFactory.clear_cache("llm_analytical")
    
    # 获取支持的LLM类型
    supported_types = LLMFactory.get_supported_types()
    print(f"支持的LLM类型: {supported_types}")


async def config_usage_example():
    """
    配置使用示例
    
    Note: 展示如何使用不同的配置选项
    """
    print("\n=== 配置使用示例 ===")
    
    # 创建高创意配置
    creative_config = LLMConfig(
        model_name="llama3.2",
        base_url="http://localhost:11434",
        temperature=0.9,
        max_tokens=300,
        top_p=0.95,
        frequency_penalty=0.1,
        presence_penalty=0.1
    )
    
    # 创建分析配置
    analytical_config = LLMConfig(
        model_name="llama3.2",
        base_url="http://localhost:11434",
        temperature=0.1,
        max_tokens=500,
        top_p=0.9,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )
    
    # 使用不同配置
    creative_llm = LLMFactory.create_llm(LLMType.OLLAMA, creative_config)
    analytical_llm = LLMFactory.create_llm(LLMType.OLLAMA, analytical_config)
    
    prompt = "请分析人工智能的发展趋势"
    
    creative_response = creative_llm(prompt)
    analytical_response = analytical_llm(prompt)
    
    print(f"创意响应: {creative_response}")
    print(f"分析响应: {analytical_response}")


async def error_handling_example():
    """
    错误处理示例
    
    Note: 展示如何处理LLM调用中的错误
    """
    print("\n=== 错误处理示例 ===")
    
    try:
        # 使用错误的配置
        bad_config = LLMConfig(
            model_name="non_existent_model",
            base_url="http://localhost:11434",
            temperature=0.1,
            max_tokens=100
        )
        
        llm = LLMFactory.create_llm(LLMType.OLLAMA, bad_config)
        response = llm("测试消息")
        print(f"响应: {response}")
        
    except Exception as e:
        print(f"捕获到错误: {str(e)}")
        logger.error(f"LLM调用失败: {str(e)}")


async def model_management_example():
    """
    模型管理示例
    
    Note: 展示如何管理Ollama模型
    """
    print("\n=== 模型管理示例 ===")
    
    try:
        # 创建Ollama LLM实例
        llm = create_ollama_llm("llama3.2")
        
        # 获取可用模型列表
        models = await llm.get_available_models_async()
        print(f"可用模型: {models}")
        
        # 获取模型信息
        model_info = llm.get_model_info()
        print(f"模型信息: {model_info}")
        
        # 更新配置
        llm.update_config({"temperature": 0.5, "max_tokens": 800})
        print(f"更新后配置: {llm.get_config()}")
        
    except Exception as e:
        print(f"模型管理操作失败: {str(e)}")


async def main():
    """
    主函数，运行所有示例
    
    Note: 依次运行所有使用示例
    """
    print("LLM使用示例演示")
    print("=" * 50)
    
    try:
        await basic_usage_example()
        await chain_usage_example()
        await stream_usage_example()
        await factory_usage_example()
        await config_usage_example()
        await error_handling_example()
        await model_management_example()
        
    except Exception as e:
        print(f"示例运行失败: {str(e)}")
        logger.error(f"示例运行失败: {str(e)}")
    
    finally:
        # 清理缓存
        LLMFactory.clear_cache()
        print("\n示例演示完成")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main()) 