"""
异常处理模块

作者：malou
创建时间：2024-12-19
描述：定义应用中使用的自定义异常类
"""

from typing import Any, Dict, Optional


class AppException(Exception):
    """
    应用基础异常类
    
    所有应用自定义异常的基类
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        初始化应用异常
        
        Args:
            message: 异常消息
            status_code: HTTP状态码
            details: 异常详细信息
        """
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(AppException):
    """
    数据验证异常
    
    用于数据验证失败的场景
    """

    def __init__(
        self,
        message: str = "数据验证失败",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, status_code=400, details=details)


class AuthenticationException(AppException):
    """
    认证异常
    
    用于身份认证失败的场景
    """

    def __init__(
        self,
        message: str = "认证失败",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, status_code=401, details=details)


class AuthorizationException(AppException):
    """
    授权异常
    
    用于权限不足的场景
    """

    def __init__(
        self,
        message: str = "权限不足",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, status_code=403, details=details)


class NotFoundException(AppException):
    """
    资源未找到异常
    
    用于请求的资源不存在的场景
    """

    def __init__(
        self,
        message: str = "资源未找到",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, status_code=404, details=details)


class ConflictException(AppException):
    """
    资源冲突异常
    
    用于资源已存在或冲突的场景
    """

    def __init__(
        self,
        message: str = "资源冲突",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, status_code=409, details=details)


class RateLimitException(AppException):
    """
    限流异常
    
    用于请求频率超过限制的场景
    """

    def __init__(
        self,
        message: str = "请求过于频繁",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, status_code=429, details=details)


class ExternalServiceException(AppException):
    """
    外部服务异常
    
    用于调用外部服务失败的场景
    """

    def __init__(
        self,
        message: str = "外部服务调用失败",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, status_code=503, details=details)


class DatabaseException(AppException):
    """
    数据库异常
    
    用于数据库操作失败的场景
    """

    def __init__(
        self,
        message: str = "数据库操作失败",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, status_code=500, details=details)


class BusinessException(AppException):
    """
    业务逻辑异常
    
    用于业务逻辑处理失败的场景
    """

    def __init__(
        self,
        message: str = "业务处理失败",
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, status_code=status_code, details=details)


class APIKeyException(AuthenticationException):
    """
    API Key异常
    
    用于API Key相关的认证失败场景
    """

    def __init__(
        self,
        message: str = "API Key无效或已过期",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details=details)


class AgentException(AppException):
    """
    Agent异常
    
    用于AI Agent处理失败的场景
    """

    def __init__(
        self,
        message: str = "Agent处理失败",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, status_code=500, details=details)


class OllamaException(ExternalServiceException):
    """
    OLLAMA服务异常
    
    用于OLLAMA服务调用失败的场景
    """

    def __init__(
        self,
        message: str = "OLLAMA服务调用失败",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details=details)


# 异常工厂函数
def create_validation_error(field: str, value: Any, message: str) -> ValidationException:
    """
    创建字段验证错误
    
    Args:
        field: 字段名
        value: 字段值
        message: 错误消息
        
    Returns:
        ValidationException: 验证异常
    """
    return ValidationException(
        message=f"字段 '{field}' 验证失败: {message}",
        details={"field": field, "value": value, "validation_message": message},
    )


def create_not_found_error(resource: str, identifier: Any) -> NotFoundException:
    """
    创建资源未找到错误
    
    Args:
        resource: 资源类型
        identifier: 资源标识符
        
    Returns:
        NotFoundException: 未找到异常
    """
    return NotFoundException(
        message=f"{resource}未找到",
        details={"resource": resource, "identifier": str(identifier)},
    )


def create_conflict_error(resource: str, field: str, value: Any) -> ConflictException:
    """
    创建资源冲突错误
    
    Args:
        resource: 资源类型
        field: 冲突字段
        value: 冲突值
        
    Returns:
        ConflictException: 冲突异常
    """
    return ConflictException(
        message=f"{resource}已存在",
        details={"resource": resource, "conflict_field": field, "value": str(value)},
    ) 