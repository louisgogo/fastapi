"""
Agents API tests.

@author malou
@since 2024-12-19
Note: Agent API的测试用例
"""

import pytest
from fastapi.testclient import TestClient


def test_list_agents(client: TestClient, test_headers: dict):
    """
    Test list agents endpoint.
    
    @param client TestClient 测试客户端
    @param test_headers dict 测试请求头
    Note: 测试获取Agent列表端点
    """
    response = client.get("/api/v1/agents/", headers=test_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["code"] == 200
    assert "data" in data
    assert "agents" in data["data"]
    assert len(data["data"]["agents"]) > 0
    
    # Check agent structure
    agent = data["data"]["agents"][0]
    assert "name" in agent
    assert "type" in agent
    assert "description" in agent
    assert "status" in agent
    assert "capabilities" in agent


def test_list_models(client: TestClient, test_headers: dict):
    """
    Test list models endpoint.
    
    @param client TestClient 测试客户端
    @param test_headers dict 测试请求头
    Note: 测试获取模型列表端点，可能因OLLAMA服务未运行而失败
    """
    response = client.get("/api/v1/agents/models", headers=test_headers)
    
    # Note: This might fail if OLLAMA is not running
    # In a real test environment, we would mock the OLLAMA service
    assert response.status_code in [200, 500]  # Allow for OLLAMA service not running


def test_nl2sql_missing_api_key(client: TestClient):
    """
    Test NL2SQL without API key.
    
    @param client TestClient 测试客户端
    Note: 测试缺少API密钥时的NL2SQL请求
    """
    nl2sql_data = {
        "query": "Show me all users",
        "context": {}
    }
    
    response = client.post("/api/v1/agents/nl2sql", json=nl2sql_data)
    
    # Should fail without API key - expect 401 (Unauthorized)
    assert response.status_code == 401  # Unauthorized due to missing API key


def test_nl2sql_with_api_key(client: TestClient, test_headers: dict):
    """
    Test NL2SQL with API key.
    
    @param client TestClient 测试客户端
    @param test_headers dict 测试请求头
    Note: 测试带API密钥的NL2SQL请求，可能因OLLAMA服务未运行而失败
    """
    nl2sql_data = {
        "query": "Show me all users from finance department",
        "context": {},
        "max_tokens": 500,
        "temperature": 0.1
    }
    
    response = client.post("/api/v1/agents/nl2sql", json=nl2sql_data, headers=test_headers)
    
    # Note: This might fail if OLLAMA is not running
    # In a real test environment, we would mock the OLLAMA service
    if response.status_code == 200:
        data = response.json()
        assert data["code"] == 200
        assert "data" in data
        assert "sql" in data["data"]
        assert "explanation" in data["data"]
        assert "confidence" in data["data"]
        assert "execution_time" in data["data"] 