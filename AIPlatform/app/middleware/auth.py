"""
认证中间件

作者：malou
创建时间：2024-12-19
描述：API-KEY认证中间件，验证请求的API密钥
"""

import time
import uuid
from typing import Callable, List, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import APIKeyException, RateLimitException
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    API-KEY认证中间件
    
    验证请求中的API-KEY，并进行限流控制
    """

    def __init__(
        self,
        app,
        exclude_paths: Optional[List[str]] = None,
        rate_limit_requests: int = 100,
        rate_limit_window: int = 60,
    ) -> None:
        """
        初始化认证中间件
        
        Args:
            app: FastAPI应用实例
            exclude_paths: 排除认证的路径列表
            rate_limit_requests: 限流请求数
            rate_limit_window: 限流时间窗口(秒)
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]
        self.rate_limit_requests = rate_limit_requests
        self.rate_limit_window = rate_limit_window
        
        # 简单的内存限流存储（生产环境应使用Redis）
        self.rate_limit_storage = {}

    def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求的中间件主逻辑
        
        Args:
            request: HTTP请求对象
            call_next: 下一个处理器
            
        Returns:
            Response: HTTP响应对象
        """
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        start_time = time.time()
        
        try:
            # 检查是否需要认证
            if self._should_authenticate(request):
                self._authenticate_request(request)
                self._check_rate_limit(request)
            
            # 调用下一个处理器
            response = call_next(request)
            
            # 记录请求日志
            process_time = time.time() - start_time
            self._log_request(request, response, process_time)
            
            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # 记录错误日志
            process_time = time.time() - start_time
            logger.error(
                f"认证中间件处理请求失败: {str(e)}",
                request_id=request_id,
                path=request.url.path,
                method=request.method,
                process_time=process_time,
                error=str(e),
            )
            raise

    def _should_authenticate(self, request: Request) -> bool:
        """
        判断是否需要进行认证
        
        Args:
            request: HTTP请求对象
            
        Returns:
            bool: 是否需要认证
        """
        path = request.url.path
        
        # 检查排除路径
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return False
                
        # 以/api开头的路径需要认证
        if path.startswith("/api"):
            return True
            
        return False

    def _authenticate_request(self, request: Request) -> None:
        """
        验证请求的API-KEY
        
        Args:
            request: HTTP请求对象
            
        Raises:
            APIKeyException: API Key验证失败
        """
        # 从请求头中获取API-KEY
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            logger.warning(
                "请求缺少API-KEY",
                request_id=request.state.request_id,
                path=request.url.path,
                method=request.method,
            )
            raise APIKeyException("请求头中缺少 X-API-Key")

        try:
            # TODO: 这里需要实现API-KEY验证逻辑
            # 暂时模拟验证成功
            request.state.api_key = api_key
            request.state.api_key_id = "test-key-id"
            request.state.user_id = "test-user-id"
            request.state.permissions = ["nl2sql", "feedback"]
            
            logger.debug(
                "API-KEY验证成功",
                request_id=request.state.request_id,
                api_key_id="test-key-id",
                user_id="test-user-id",
                path=request.url.path,
                method=request.method,
            )
            
        except Exception as e:
            logger.warning(
                f"API-KEY验证失败: {str(e)}",
                request_id=request.state.request_id,
                api_key=api_key[:8] + "..." if len(api_key) > 8 else api_key,
                path=request.url.path,
                method=request.method,
                error=str(e),
            )
            raise APIKeyException("API Key无效或已过期")

    def _check_rate_limit(self, request: Request) -> None:
        """
        检查限流
        
        Args:
            request: HTTP请求对象
            
        Raises:
            RateLimitException: 超出限流限制
        """
        api_key = request.state.api_key
        current_time = time.time()
        
        # 清理过期的记录
        self._cleanup_rate_limit_storage(current_time)
        
        # 获取当前API-KEY的请求记录
        if api_key not in self.rate_limit_storage:
            self.rate_limit_storage[api_key] = []
        
        request_times = self.rate_limit_storage[api_key]
        
        # 过滤时间窗口内的请求
        window_start = current_time - self.rate_limit_window
        recent_requests = [t for t in request_times if t > window_start]
        
        # 检查是否超过限制
        if len(recent_requests) >= self.rate_limit_requests:
            logger.warning(
                "API请求频率超过限制",
                request_id=request.state.request_id,
                api_key=api_key[:8] + "..." if len(api_key) > 8 else api_key,
                requests_count=len(recent_requests),
                limit=self.rate_limit_requests,
                window=self.rate_limit_window,
            )
            raise RateLimitException(
                f"请求频率超过限制: {self.rate_limit_requests}次/{self.rate_limit_window}秒"
            )
        
        # 记录当前请求时间
        recent_requests.append(current_time)
        self.rate_limit_storage[api_key] = recent_requests

    def _cleanup_rate_limit_storage(self, current_time: float) -> None:
        """
        清理过期的限流记录
        
        Args:
            current_time: 当前时间戳
        """
        window_start = current_time - self.rate_limit_window * 2
        
        for api_key in list(self.rate_limit_storage.keys()):
            request_times = self.rate_limit_storage[api_key]
            recent_requests = [t for t in request_times if t > window_start]
            
            if recent_requests:
                self.rate_limit_storage[api_key] = recent_requests
            else:
                del self.rate_limit_storage[api_key]

    def _log_request(
        self, request: Request, response: Response, process_time: float
    ) -> None:
        """
        记录请求日志
        
        Args:
            request: HTTP请求对象
            response: HTTP响应对象
            process_time: 处理时间
        """
        method = request.method
        path = request.url.path
        status_code = response.status_code
        user_agent = request.headers.get("User-Agent", "")
        client_ip = self._get_client_ip(request)
        
        api_key = getattr(request.state, "api_key", None)
        user_id = getattr(request.state, "user_id", None)
        
        logger.info(
            f"{method} {path} - {status_code}",
            request_id=request.state.request_id,
            method=method,
            path=path,
            status_code=status_code,
            process_time=process_time,
            client_ip=client_ip,
            user_agent=user_agent,
            api_key=api_key[:8] + "..." if api_key and len(api_key) > 8 else api_key,
            user_id=str(user_id) if user_id else None,
        )

    def _get_client_ip(self, request: Request) -> str:
        """
        获取客户端IP地址
        
        Args:
            request: HTTP请求对象
            
        Returns:
            str: 客户端IP地址
        """
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        if request.client:
            return request.client.host
        
        return "unknown" 