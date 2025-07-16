"""
Health check API routes.

@author malou
@since 2024-12-19
Note: 系统健康检查API接口，使用异步数据库连接
"""

import time
from datetime import datetime
import httpx

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_async_db
from app.schemas.common import HealthCheckResponse
from app.core.config import get_settings
from app.utils.logger import logger

router = APIRouter()

# 服务启动时间
start_time = time.time()


@router.get("/", response_model=HealthCheckResponse)
async def health_check(db: AsyncSession = Depends(get_async_db)):
    """
    Health check endpoint.
    
    @param db AsyncSession 异步数据库会话
    @return HealthCheckResponse 健康检查响应
    Note: 检查系统各组件的健康状态
    """
    try:
        # 检查数据库连接
        database_healthy = True
        try:
            await db.execute(text("SELECT 1"))
        except Exception as e:
            database_healthy = False
            logger.error(f"Database health check failed: {str(e)}")
        
        # 检查OLLAMA服务
        ollama_healthy = False
        try:
            settings = get_settings()
            ollama_url = f"{settings.OLLAMA_BASE_URL}/api/tags"
            async with httpx.AsyncClient() as client:
                response = await client.get(ollama_url, timeout=5.0)
                ollama_healthy = response.status_code == 200
        except Exception as e:
            logger.error(f"OLLAMA health check failed: {str(e)}")
        
        # 计算运行时间
        uptime = time.time() - start_time
        
        # 确定整体状态
        overall_status = "healthy" if database_healthy and ollama_healthy else "unhealthy"
        
        return HealthCheckResponse(
            status=overall_status,
            timestamp=datetime.now(),
            version="1.0.0",
            uptime=uptime,
            database=database_healthy,
            ollama=ollama_healthy
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthCheckResponse(
            status="error",
            timestamp=datetime.now(),
            version="unknown",
            uptime=time.time() - start_time,
            database=False,
            ollama=False
        )


@router.get("/ping")
async def ping():
    """
    Simple ping endpoint.
    
    @return dict 简单响应
    Note: 最简单的健康检查，用于负载均衡器探针
    """
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    """
    Direct execution for testing health check functionality.
    """
    import uvicorn
    from fastapi import FastAPI
    
    # 创建临时应用用于测试
    app = FastAPI(title="Health Check Test")
    app.include_router(router, prefix="/health", tags=["health"])
    
    print("Starting health check test server...")
    print("Access endpoints at:")
    print("  - http://localhost:8001/health/")
    print("  - http://localhost:8001/health/ping")
    print("Press Ctrl+C to stop")
    
    uvicorn.run(app, host="0.0.0.0", port=8001) 