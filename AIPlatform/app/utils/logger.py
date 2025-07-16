"""
日志工具模块

作者：malou
创建时间：2024-12-19
描述：提供统一的日志配置和工具函数
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
from loguru import logger


def setup_logger(name: Optional[str] = None) -> logging.Logger:
    """
    设置并返回logger实例
    
    Args:
        name: logger名称，默认为None
        
    Returns:
        logging.Logger: 配置好的logger实例
    """
    # 创建logger
    if name:
        log = logging.getLogger(name)
    else:
        log = logging.getLogger()
        
    # 如果已经配置过handler，则直接返回
    if log.handlers:
        return log
        
    # 设置日志级别
    log.setLevel(logging.INFO)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    log.addHandler(console_handler)
    
    return log


def setup_structured_logger(
    log_level: str = "INFO",
    log_format: str = "json",
    log_file: Optional[str] = None,
) -> None:
    """
    设置结构化日志
    
    Args:
        log_level: 日志级别
        log_format: 日志格式 (json/console)
        log_file: 日志文件路径
    """
    # 配置处理器
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    if log_format == "console":
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        processors.append(structlog.processors.JSONRenderer())
    
    # 配置structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # 配置标准库logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    # 如果指定了日志文件，则添加文件处理器
    if log_file:
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        
        # 为文件使用JSON格式
        if log_format == "json":
            file_formatter = logging.Formatter('%(message)s')
        else:
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        file_handler.setFormatter(file_formatter)
        
        # 添加到根logger
        logging.getLogger().addHandler(file_handler)


def setup_loguru_logger(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    rotation: str = "100 MB",
    retention: str = "30 days",
) -> None:
    """
    设置Loguru日志
    
    Args:
        log_level: 日志级别
        log_file: 日志文件路径
        rotation: 日志轮转大小
        retention: 日志保留时间
    """
    # 移除默认handler
    logger.remove()
    
    # 添加控制台handler
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
        colorize=True,
    )
    
    # 如果指定了日志文件，则添加文件handler
    if log_file:
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_file,
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation=rotation,
            retention=retention,
            compression="zip",
            serialize=False,
        )


class LoggerAdapter:
    """
    日志适配器
    
    提供统一的日志接口，支持结构化日志
    """
    
    def __init__(self, logger_name: str) -> None:
        """
        初始化日志适配器
        
        Args:
            logger_name: logger名称
        """
        self.logger = structlog.get_logger(logger_name)
        self.loguru_logger = logger.bind(name=logger_name)
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """记录DEBUG级别日志"""
        self.logger.debug(message, **kwargs)
        self.loguru_logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """记录INFO级别日志"""
        self.logger.info(message, **kwargs)
        self.loguru_logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """记录WARNING级别日志"""
        self.logger.warning(message, **kwargs)
        self.loguru_logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """记录ERROR级别日志"""
        self.logger.error(message, **kwargs)
        self.loguru_logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs: Any) -> None:
        """记录CRITICAL级别日志"""
        self.logger.critical(message, **kwargs)
        self.loguru_logger.critical(message, **kwargs)
    
    def bind(self, **kwargs: Any) -> "LoggerAdapter":
        """
        绑定上下文信息
        
        Args:
            **kwargs: 上下文键值对
            
        Returns:
            LoggerAdapter: 新的日志适配器实例
        """
        new_adapter = LoggerAdapter(self.logger.name)
        new_adapter.logger = self.logger.bind(**kwargs)
        new_adapter.loguru_logger = self.loguru_logger.bind(**kwargs)
        return new_adapter


def get_logger(name: str) -> LoggerAdapter:
    """
    获取日志适配器实例
    
    Args:
        name: logger名称
        
    Returns:
        LoggerAdapter: 日志适配器实例
    """
    return LoggerAdapter(name)


def log_function_call(func_name: str, args: tuple, kwargs: Dict[str, Any]) -> None:
    """
    记录函数调用日志
    
    Args:
        func_name: 函数名称
        args: 位置参数
        kwargs: 关键字参数
    """
    logger_adapter = get_logger("function_call")
    logger_adapter.debug(
        f"调用函数: {func_name}",
        function=func_name,
        args=str(args),
        kwargs=str(kwargs),
    )


def log_api_request(
    method: str,
    url: str,
    headers: Dict[str, str],
    body: Optional[str] = None,
) -> None:
    """
    记录API请求日志
    
    Args:
        method: HTTP方法
        url: 请求URL
        headers: 请求头
        body: 请求体
    """
    logger_adapter = get_logger("api_request")
    logger_adapter.info(
        f"API请求: {method} {url}",
        method=method,
        url=url,
        headers=headers,
        body=body,
    )


def log_api_response(
    status_code: int,
    headers: Dict[str, str],
    body: Optional[str] = None,
    duration: Optional[float] = None,
) -> None:
    """
    记录API响应日志
    
    Args:
        status_code: HTTP状态码
        headers: 响应头
        body: 响应体
        duration: 响应时间(秒)
    """
    logger_adapter = get_logger("api_response")
    logger_adapter.info(
        f"API响应: {status_code}",
        status_code=status_code,
        headers=headers,
        body=body,
        duration=duration,
    )


def log_database_query(
    query: str,
    params: Optional[Dict[str, Any]] = None,
    duration: Optional[float] = None,
) -> None:
    """
    记录数据库查询日志
    
    Args:
        query: SQL查询语句
        params: 查询参数
        duration: 查询时间(秒)
    """
    logger_adapter = get_logger("database")
    logger_adapter.debug(
        "数据库查询",
        query=query,
        params=params,
        duration=duration,
    ) 