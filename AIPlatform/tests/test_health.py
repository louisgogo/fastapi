"""
Health check API tests.

@author malou
@since 2024-12-19
Note: 健康检查API的测试用例
"""

import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """
    Test health check endpoint.
    
    @param client TestClient 测试客户端
    Note: 测试健康检查端点
    """
    response = client.get("/api/v1/health/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "status" in data
    assert "timestamp" in data
    assert "version" in data
    assert "uptime" in data
    assert "database" in data
    assert "ollama" in data


def test_ping(client: TestClient):
    """
    Test ping endpoint.
    
    @param client TestClient 测试客户端
    Note: 测试ping端点
    """
    response = client.get("/api/v1/health/ping")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "ok"
    assert "timestamp" in data 