#!/usr/bin/env python3
"""
测试OLLAMA服务修复

@author malou
@since 2024-12-19
Note: 验证ollama_service.py的修复是否成功
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.services.ollama_service import OllamaService, ChatMessage
    from app.core.config import get_settings
    print("✓ 模块导入成功")
except ImportError as e:
    print(f"✗ 模块导入失败: {e}")
    exit(1)

def test_ollama_service():
    """测试OLLAMA服务"""
    print("\n=== OLLAMA服务测试 ===")
    
    # 测试配置加载
    try:
        settings = get_settings()
        print(f"✓ 配置加载成功")
        print(f"  OLLAMA_BASE_URL: {settings.OLLAMA_BASE_URL}")
        print(f"  OLLAMA_DEFAULT_MODEL: {settings.OLLAMA_DEFAULT_MODEL}")
        print(f"  OLLAMA_MAX_RETRIES: {settings.OLLAMA_MAX_RETRIES}")
    except Exception as e:
        print(f"✗ 配置加载失败: {e}")
        return False
    
    # 测试服务初始化
    try:
        service = OllamaService()
        print("✓ OLLAMA服务初始化成功")
    except Exception as e:
        print(f"✗ OLLAMA服务初始化失败: {e}")
        return False
    
    # 测试健康检查
    try:
        print("\n--- 健康检查测试 ---")
        health = service.check_health()
        if health:
            print("✓ OLLAMA服务连接成功")
        else:
            print("✗ OLLAMA服务连接失败 (这是正常的，如果OLLAMA服务没有运行)")
    except Exception as e:
        print(f"✗ 健康检查出错: {e}")
    
    # 测试模型列表获取
    try:
        print("\n--- 模型列表测试 ---")
        models = service.list_models()
        print(f"✓ 模型列表获取成功，共 {len(models.models)} 个模型")
        for i, model in enumerate(models.models[:3]):  # 显示前3个
            print(f"  {i+1}. {model.name} ({model.size})")
    except Exception as e:
        print(f"✗ 模型列表获取失败: {e}")
    
    # 测试聊天功能（如果有可用模型）
    try:
        print("\n--- 聊天功能测试 ---")
        models = service.list_models()
        if models.models:
            messages = [ChatMessage(role="user", content="Hello, how are you?")]
            response = service.chat_completion(
                model=models.models[0].name,
                messages=messages,
                temperature=0.7,
                retries=1  # 减少重试次数以加快测试
            )
            print(f"✓ 聊天功能成功: {response.message.content[:50]}...")
        else:
            print("⚠ 没有可用模型，跳过聊天测试")
    except Exception as e:
        print(f"✗ 聊天功能失败: {e}")
    
    # 测试NL2SQL功能
    try:
        print("\n--- NL2SQL功能测试 ---")
        sql = service.generate_nl2sql(
            natural_language="查询用户表中的所有用户",
            database_schema="CREATE TABLE users (id INT, name VARCHAR(100), email VARCHAR(255));",
            model=None  # 使用默认模型
        )
        print(f"✓ NL2SQL功能成功: {sql}")
    except Exception as e:
        print(f"✗ NL2SQL功能失败: {e}")
    
    # 关闭服务
    try:
        service.close()
        print("\n✓ 服务关闭成功")
    except Exception as e:
        print(f"✗ 服务关闭失败: {e}")
    
    print("\n=== 测试完成 ===")
    return True

def main():
    """主函数"""
    print("开始测试OLLAMA服务修复...")
    
    try:
        # 运行异步测试
        result = asyncio.run(test_ollama_service())
        if result:
            print("\n🎉 测试完成！")
        else:
            print("\n❌ 测试失败！")
    except Exception as e:
        print(f"\n💥 测试过程中发生错误: {e}")

if __name__ == "__main__":
    main() 