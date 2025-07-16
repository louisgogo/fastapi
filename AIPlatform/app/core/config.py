"""
配置管理模块

作者：malou
创建时间：2024-12-19
描述：应用配置管理，从环境变量读取配置信息
"""

import json
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    应用配置类
    
    从环境变量或.env文件中读取配置信息
    """
    
    # 应用基础配置
    APP_NAME: str = Field(default="AI API Platform", description="应用名称")
    APP_VERSION: str = Field(default="1.0.0", description="应用版本")
    APP_DEBUG: bool = Field(default=False, description="调试模式")
    APP_HOST: str = Field(default="0.0.0.0", description="应用主机")
    APP_PORT: int = Field(default=8000, description="应用端口")
    
    # API配置
    API_V1_STR: str = Field(default="/api/v1", description="API v1前缀")
    
    # 安全配置
    SECRET_KEY: str = Field(default="your-secret-key-here-change-in-production", description="密钥，用于JWT签名")
    API_KEY_EXPIRE_DAYS: int = Field(default=365, description="API Key过期天数")
    ALGORITHM: str = Field(default="HS256", description="JWT加密算法")
    
    # 数据库配置
    DATABASE_URL: str = Field(default="postgresql+psycopg2://postgres:123456@localhost:5432/postgres", description="数据库连接URL")
    ASYNC_DATABASE_URL: str = Field(default="postgresql+asyncpg://postgres:123456@localhost:5432/postgres", description="异步数据库连接URL")
    
    # PostgreSQL单独配置（用于工具类）
    PSQL_DB_HOST: str = Field(default="localhost", description="PostgreSQL数据库主机")
    PSQL_DB_PORT: int = Field(default=5432, description="PostgreSQL数据库端口")
    PSQL_DB_NAME: str = Field(default="postgres", description="PostgreSQL数据库名称")
    PSQL_DB_USER: str = Field(default="postgres", description="PostgreSQL数据库用户名")
    PSQL_DB_PASSWORD: str = Field(default="123456", description="PostgreSQL数据库密码")
    PSQL_DB_SCHEMA: str = Field(default="public", description="PostgreSQL数据库schema")
    
    DATABASE_ECHO: bool = Field(default=False, description="是否打印SQL语句")
    DATABASE_POOL_SIZE: int = Field(default=10, description="数据库连接池大小")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, description="数据库连接池最大溢出")
    DATABASE_POOL_RECYCLE: int = Field(default=3600, description="数据库连接池回收时间(秒)")
    DATABASE_POOL_PRE_PING: bool = Field(default=True, description="数据库连接池预检查")
    
    # OLLAMA配置
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", description="OLLAMA服务地址")
    OLLAMA_DEFAULT_MODEL: str = Field(default="llama3.2", description="默认模型")
    OLLAMA_TIMEOUT: int = Field(default=30, description="OLLAMA请求超时时间(秒)")
    OLLAMA_MAX_RETRIES: int = Field(default=3, description="OLLAMA请求最大重试次数")
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_FORMAT: str = Field(default="json", description="日志格式")
    LOG_FILE: str = Field(default="logs/app.log", description="日志文件路径")
    
    # CORS配置
    CORS_ORIGINS: List[str] = Field(
        default=["*"], 
        description="允许的跨域源"
    )
    CORS_CREDENTIALS: bool = Field(default=True, description="是否允许携带凭据")
    CORS_METHODS: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE"], 
        description="允许的HTTP方法"
    )
    CORS_HEADERS: List[str] = Field(default=["*"], description="允许的请求头")
    
    # 限流配置
    RATE_LIMIT_REQUESTS: int = Field(default=100, description="限流请求数")
    RATE_LIMIT_WINDOW: int = Field(default=60, description="限流时间窗口(秒)")
    
    # 监控配置
    ENABLE_METRICS: bool = Field(default=True, description="是否启用指标监控")
    METRICS_PATH: str = Field(default="/metrics", description="指标路径")
    
    # Redis配置
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis连接URL")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis密码")
    REDIS_MAX_CONNECTIONS: int = Field(default=10, description="Redis最大连接数")
    
    # 开发配置
    RELOAD: bool = Field(default=False, description="是否自动重载")
    ACCESS_LOG: bool = Field(default=True, description="是否启用访问日志")
    DEBUG_SQL: bool = Field(default=False, description="是否调试SQL")
    
    # 文件存储配置
    UPLOAD_DIR: str = Field(default="uploads", description="文件上传目录")
    MAX_FILE_SIZE: int = Field(default=10485760, description="最大文件大小(字节)")
    
    # 邮件配置
    SMTP_HOST: Optional[str] = Field(default=None, description="SMTP主机")
    SMTP_PORT: int = Field(default=587, description="SMTP端口")
    SMTP_USER: Optional[str] = Field(default=None, description="SMTP用户名")
    SMTP_PASSWORD: Optional[str] = Field(default=None, description="SMTP密码")
    EMAIL_FROM: Optional[str] = Field(default=None, description="发件人邮箱")
    
    # 外部服务配置
    EXTERNAL_API_TIMEOUT: int = Field(default=30, description="外部API超时时间")
    EXTERNAL_API_RETRIES: int = Field(default=3, description="外部API重试次数")
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        """
        解析CORS origins配置
        
        Args:
            v: 配置值
            
        Returns:
            List[str]: CORS origins列表
        """
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            if isinstance(v, str):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    return [v]
            return v
        raise ValueError(v)
        
    @field_validator("CORS_METHODS", mode="before")
    @classmethod
    def assemble_cors_methods(cls, v: Any) -> List[str]:
        """
        解析CORS methods配置
        
        Args:
            v: 配置值
            
        Returns:
            List[str]: CORS methods列表
        """
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            if isinstance(v, str):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    return [v]
            return v
        raise ValueError(v)
        
    @field_validator("CORS_HEADERS", mode="before")
    @classmethod
    def assemble_cors_headers(cls, v: Any) -> List[str]:
        """
        解析CORS headers配置
        
        Args:
            v: 配置值
            
        Returns:
            List[str]: CORS headers列表
        """
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            if isinstance(v, str):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    return [v]
            return v
        raise ValueError(v)
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """
        验证密钥长度
        
        Args:
            v: 密钥值
            
        Returns:
            str: 验证后的密钥
        """
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """
        验证日志级别
        
        Args:
            v: 日志级别
            
        Returns:
            str: 验证后的日志级别
        """
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True)


# 全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """
    获取配置实例
    
    Returns:
        Settings: 配置实例
    """
    return settings


def get_database_url() -> str:
    """
    获取数据库连接URL
    
    Returns:
        str: 数据库连接URL
    """
    return settings.DATABASE_URL


def get_async_database_url() -> str:
    """
    获取异步数据库连接URL
    
    Returns:
        str: 异步数据库连接URL
    """
    return settings.ASYNC_DATABASE_URL


def get_ollama_config() -> Dict[str, Any]:
    """
    获取OLLAMA配置
    
    Returns:
        Dict[str, Any]: OLLAMA配置字典
    """
    return {
        "base_url": settings.OLLAMA_BASE_URL,
        "default_model": settings.OLLAMA_DEFAULT_MODEL,
        "timeout": settings.OLLAMA_TIMEOUT,
        "max_retries": settings.OLLAMA_MAX_RETRIES,
    }


def get_redis_config() -> Dict[str, Any]:
    """
    获取Redis配置
    
    Returns:
        Dict[str, Any]: Redis配置字典
    """
    return {
        "url": settings.REDIS_URL,
        "password": settings.REDIS_PASSWORD,
        "max_connections": settings.REDIS_MAX_CONNECTIONS,
    }


if __name__ == "__main__":
    """
    测试配置模块
    """
    import os
    
    # 设置测试环境变量
    os.environ["SECRET_KEY"] = "test_secret_key_1234567890abcdef1234567890abcdef"
    os.environ["DATABASE_URL"] = "sqlite:///test.db"
    
    # 重新创建配置实例
    test_settings = Settings()
    
    print("配置模块测试通过！")
    print(f"应用名称: {test_settings.APP_NAME}")
    print(f"应用版本: {test_settings.APP_VERSION}")
    print(f"数据库URL: {test_settings.DATABASE_URL}")
    print(f"OLLAMA配置: {get_ollama_config()}")
    print(f"Redis配置: {get_redis_config()}")
    print(f"日志级别: {test_settings.LOG_LEVEL}")
    print(f"CORS配置: {test_settings.CORS_ORIGINS}") 