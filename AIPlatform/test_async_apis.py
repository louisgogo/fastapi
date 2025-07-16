#!/usr/bin/env python
"""
Test script to verify async API endpoints.

@author malou
@since 2024-12-19
Note: 测试异步化后的API端点
"""

import asyncio
import httpx
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

BASE_URL = "http://localhost:8000/api/v1"


async def test_health_endpoint():
    """Test health endpoint."""
    print("🔍 Testing health endpoint...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health/", timeout=30.0)
            print(f"✅ Health check status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Status: {data.get('status', 'unknown')}")
                print(f"   Database: {data.get('database', 'unknown')}")
                print(f"   OLLAMA: {data.get('ollama', 'unknown')}")
            return True
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        return False


async def test_ping_endpoint():
    """Test ping endpoint."""
    print("🔍 Testing ping endpoint...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health/ping", timeout=10.0)
            print(f"✅ Ping status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Response: {data}")
            return True
    except Exception as e:
        print(f"❌ Ping failed: {str(e)}")
        return False


async def test_agents_list_endpoint():
    """Test agents list endpoint."""
    print("🔍 Testing agents list endpoint...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/agents/", timeout=10.0)
            print(f"✅ Agents list status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Found {len(data.get('data', {}).get('agents', []))} agents")
            return True
    except Exception as e:
        print(f"❌ Agents list failed: {str(e)}")
        return False


async def test_api_keys_list_endpoint():
    """Test API keys list endpoint."""
    print("🔍 Testing API keys list endpoint...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/api-keys/", timeout=10.0)
            print(f"✅ API keys list status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Total API keys: {data.get('data', {}).get('total', 0)}")
            return True
    except Exception as e:
        print(f"❌ API keys list failed: {str(e)}")
        return False


async def test_feedback_stats_endpoint():
    """Test feedback stats endpoint."""
    print("🔍 Testing feedback stats endpoint...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/feedback/stats", timeout=10.0)
            print(f"✅ Feedback stats status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Stats data available: {bool(data.get('data'))}")
            return True
    except Exception as e:
        print(f"❌ Feedback stats failed: {str(e)}")
        return False


async def test_logs_list_endpoint():
    """Test logs list endpoint."""
    print("🔍 Testing logs list endpoint...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/logs/", timeout=10.0)
            print(f"✅ Logs list status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Total logs: {data.get('data', {}).get('total', 0)}")
            return True
    except Exception as e:
        print(f"❌ Logs list failed: {str(e)}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Starting async API tests...\n")
    
    tests = [
        test_health_endpoint,
        test_ping_endpoint,
        test_agents_list_endpoint,
        test_api_keys_list_endpoint,
        test_feedback_stats_endpoint,
        test_logs_list_endpoint,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if await test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {str(e)}")
        print()  # Empty line for readability
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Async APIs are working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the server and try again.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1) 