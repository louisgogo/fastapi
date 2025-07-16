"""
FastAPI应用主入口文件

作者：malou
创建时间：2024-12-19
描述：AI API接口平台的主要应用入口，配置FastAPI实例、中间件、路由等
      使用同步数据库连接
"""

import logging
import time
from typing import Dict, Any
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.exceptions import AppException
from app.database.connection import create_tables
from app.utils.logger import logger

# 获取配置
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理器
    
    Args:
        app: FastAPI应用实例
    """
    # 启动事件
    logger.info("应用启动中...")
    try:
        # 创建数据库表
        await create_tables()
        logger.info("数据库表创建完成")
        logger.info("应用启动完成")
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        raise
    
    yield
    
    # 关闭事件
    logger.info("应用关闭中...")
    logger.info("应用已关闭")


def create_app() -> FastAPI:
    """
    创建FastAPI应用实例
    
    Returns:
        FastAPI: 配置完成的FastAPI应用实例
    """
    # 创建FastAPI实例
    app = FastAPI(
        title=settings.APP_NAME,
        description="AI API接口平台 - 为财务部门提供统一的AI API接口",
        version=settings.APP_VERSION,
        docs_url="/docs" if settings.APP_DEBUG else None,
        redoc_url="/redoc" if settings.APP_DEBUG else None,
        openapi_url="/openapi.json" if settings.APP_DEBUG else None,
        lifespan=lifespan,  # 现在可以正确引用lifespan函数
    )

    # 配置CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_CREDENTIALS,
        allow_methods=settings.CORS_METHODS,
        allow_headers=settings.CORS_HEADERS,
    )

    # 注册路由
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # 全局异常处理器
    @app.exception_handler(AppException)
    def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        """
        应用异常处理器
        
        Args:
            request: HTTP请求对象
            exc: 应用异常
            
        Returns:
            JSONResponse: 错误响应
        """
        logger.error(f"应用异常: {exc.message}, 状态码: {exc.status_code}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.status_code,
                "message": exc.message,
                "data": None,
                "timestamp": time.time(),
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    @app.exception_handler(Exception)
    def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        全局异常处理器
        
        Args:
            request: HTTP请求对象
            exc: 未捕获的异常
            
        Returns:
            JSONResponse: 错误响应
        """
        logger.error(f"未捕获的异常: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "message": "内部服务器错误",
                "data": None,
                "timestamp": time.time(),
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    # 根路径重定向
    @app.get("/", tags=["根路径"])
    def root() -> Dict[str, Any]:
        """
        根路径响应
        
        Returns:
            dict: API信息
        """
        return {
            "message": "AI API接口平台",
            "version": settings.APP_VERSION,
            "docs_url": "/docs" if settings.APP_DEBUG else None,
        }

    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    """
    直接运行时的入口点
    """
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=True,  # 开发环境启用热重载
        log_level="info",
    ) 