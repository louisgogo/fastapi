"""
API v1 routes package.

Note: 简化版API路由，只包含核心功能
"""

from fastapi import APIRouter

# Create v1 API router
api_router = APIRouter()

# 懒加载路由，避免循环导入
def setup_routes():
    """
    Setup API routes using lazy loading.
    """
    from .health import router as health_router
    from .users import router as users_router
    from .agents import router as agents_router
    from .api_keys import router as api_keys_router
    from .logs import router as logs_router
    from .feedback import router as feedback_router
    from .workflows import router as workflows_router
    from .subgraphs import router as subgraphs_router
    from .dify_feedback import router as dify_feedback_router 
    
    # Include route modules
    api_router.include_router(health_router, prefix="/health", tags=["health"])
    api_router.include_router(users_router, prefix="/users", tags=["users"])
    api_router.include_router(agents_router, prefix="/agents", tags=["agents"])
    api_router.include_router(api_keys_router, prefix="/api-keys", tags=["api-keys"])
    api_router.include_router(logs_router, prefix="/logs", tags=["logs"])
    api_router.include_router(feedback_router, prefix="/feedback", tags=["feedback"])
    api_router.include_router(workflows_router, prefix="/workflows", tags=["workflows"])
    api_router.include_router(subgraphs_router, prefix="/subgraphs", tags=["subgraphs"])
    api_router.include_router(dify_feedback_router, prefix="/dify-feedback", tags=["dify-feedback"])
# 在模块导入时设置路由
setup_routes()

__all__ = ["api_router"] 