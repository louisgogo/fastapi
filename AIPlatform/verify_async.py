#!/usr/bin/env python
"""
Verify async implementation.

@author malou
@since 2024-12-19
Note: 验证异步化实现是否正确
"""

import inspect


def check_async_functions():
    """Check if key functions are properly async."""
    print("🔍 Checking async function implementations...\n")
    
    # Test database functions
    try:
        from app.database import get_async_db
        print(f"✅ get_async_db imported: {inspect.iscoroutinefunction(get_async_db)}")
    except ImportError as e:
        print(f"❌ Failed to import get_async_db: {e}")
    
    # Test services
    try:
        from app.services.user_service import UserService
        user_service = UserService(None)
        print(f"✅ UserService.get_user_by_id is async: {inspect.iscoroutinefunction(user_service.get_user_by_id)}")
        print(f"✅ UserService.create_user is async: {inspect.iscoroutinefunction(user_service.create_user)}")
    except Exception as e:
        print(f"❌ UserService async check failed: {e}")
    
    try:
        from app.services.ollama_service import OllamaService
        ollama_service = OllamaService()
        print(f"✅ OllamaService.list_models is async: {inspect.iscoroutinefunction(ollama_service.list_models)}")
        print(f"✅ OllamaService.generate is async: {inspect.iscoroutinefunction(ollama_service.generate)}")
    except Exception as e:
        print(f"❌ OllamaService async check failed: {e}")
    
    try:
        from app.services.agent_service import AgentService
        agent_service = AgentService(None)
        print(f"✅ AgentService.process_nl2sql is async: {inspect.iscoroutinefunction(agent_service.process_nl2sql)}")
    except Exception as e:
        print(f"❌ AgentService async check failed: {e}")
    
    try:
        from app.services.api_key_service import APIKeyService
        api_key_service = APIKeyService(None)
        print(f"✅ APIKeyService.create_api_key is async: {inspect.iscoroutinefunction(api_key_service.create_api_key)}")
        print(f"✅ APIKeyService.get_api_keys is async: {inspect.iscoroutinefunction(api_key_service.get_api_keys)}")
    except Exception as e:
        print(f"❌ APIKeyService async check failed: {e}")
    
    try:
        from app.services.feedback_service import FeedbackService
        feedback_service = FeedbackService(None)
        print(f"✅ FeedbackService.create_feedback is async: {inspect.iscoroutinefunction(feedback_service.create_feedback)}")
        print(f"✅ FeedbackService.get_feedback_stats is async: {inspect.iscoroutinefunction(feedback_service.get_feedback_stats)}")
    except Exception as e:
        print(f"❌ FeedbackService async check failed: {e}")
    
    # Test API routes
    print("\n🔍 Checking API route functions...\n")
    
    try:
        from app.api.v1.health import health_check, ping
        print(f"✅ health_check is async: {inspect.iscoroutinefunction(health_check)}")
        print(f"✅ ping is async: {inspect.iscoroutinefunction(ping)}")
    except Exception as e:
        print(f"❌ Health routes async check failed: {e}")
    
    try:
        from app.api.v1.users import create_user, get_users
        print(f"✅ create_user is async: {inspect.iscoroutinefunction(create_user)}")
        print(f"✅ get_users is async: {inspect.iscoroutinefunction(get_users)}")
    except Exception as e:
        print(f"❌ User routes async check failed: {e}")
    
    try:
        from app.api.v1.agents import natural_language_to_sql, list_available_models, list_agents
        print(f"✅ natural_language_to_sql is async: {inspect.iscoroutinefunction(natural_language_to_sql)}")
        print(f"✅ list_available_models is async: {inspect.iscoroutinefunction(list_available_models)}")
        print(f"✅ list_agents is async: {inspect.iscoroutinefunction(list_agents)}")
    except Exception as e:
        print(f"❌ Agent routes async check failed: {e}")
    
    try:
        from app.api.v1.feedback import create_feedback, get_feedback_stats
        print(f"✅ create_feedback is async: {inspect.iscoroutinefunction(create_feedback)}")
        print(f"✅ get_feedback_stats is async: {inspect.iscoroutinefunction(get_feedback_stats)}")
    except Exception as e:
        print(f"❌ Feedback routes async check failed: {e}")
    
    try:
        from app.api.v1.api_keys import create_api_key, list_api_keys
        print(f"✅ create_api_key is async: {inspect.iscoroutinefunction(create_api_key)}")
        print(f"✅ list_api_keys is async: {inspect.iscoroutinefunction(list_api_keys)}")
    except Exception as e:
        print(f"❌ API key routes async check failed: {e}")
    
    try:
        from app.api.v1.logs import get_api_logs, get_api_log, get_log_stats
        print(f"✅ get_api_logs is async: {inspect.iscoroutinefunction(get_api_logs)}")
        print(f"✅ get_api_log is async: {inspect.iscoroutinefunction(get_api_log)}")
        print(f"✅ get_log_stats is async: {inspect.iscoroutinefunction(get_log_stats)}")
    except Exception as e:
        print(f"❌ Log routes async check failed: {e}")


def main():
    """Main function."""
    print("🚀 Starting async implementation verification...\n")
    check_async_functions()
    print("\n🎉 Async verification completed!")


if __name__ == "__main__":
    main() 