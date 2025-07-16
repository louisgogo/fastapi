"""
Agent Pydantic schemas.

@author malou
@since 2024-12-19
Note: Agent相关的Pydantic模式定义
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, ConfigDict


class AgentBase(BaseModel):
    """
    Agent base schema.
    
    Note: Agent基础模式，包含Agent公共字段
    """
    
    name: str = Field(..., min_length=1, max_length=100, description="Agent名称")
    type: str = Field(..., max_length=50, description="Agent类型")
    description: Optional[str] = Field(None, description="Agent描述")
    config: Optional[dict] = Field(default_factory=dict, description="Agent配置")
    version: Optional[str] = Field(None, max_length=20, description="Agent版本")


class AgentCreate(AgentBase):
    """
    Agent creation schema.
    
    Note: Agent创建模式
    """
    
    status: Optional[str] = Field(default="active", description="Agent状态")


class AgentUpdate(BaseModel):
    """
    Agent update schema.
    
    Note: Agent更新模式
    """
    
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Agent名称")
    description: Optional[str] = Field(None, description="Agent描述")
    config: Optional[dict] = Field(None, description="Agent配置")
    status: Optional[str] = Field(None, description="Agent状态")
    version: Optional[str] = Field(None, max_length=20, description="Agent版本")


class AgentResponse(AgentBase):
    """
    Agent response schema.
    
    Note: Agent响应模式
    """
    
    id: uuid.UUID = Field(..., description="Agent ID")
    status: str = Field(..., description="Agent状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)


class AgentListResponse(BaseModel):
    """
    Agent list response schema.
    
    Note: Agent列表响应模式
    """
    
    agents: list[AgentResponse] = Field(..., description="Agent列表")


class NL2SQLRequest(BaseModel):
    """
    Natural Language to SQL request schema.
    
    Note: 自然语言转SQL请求模式
    """
    
    query: str = Field(..., min_length=1, description="自然语言查询")
    database_schema: Optional[str] = Field(None, description="数据库架构")
    context: Optional[dict] = Field(default_factory=dict, description="上下文信息")
    max_tokens: Optional[int] = Field(default=1000, ge=100, le=4000, description="最大token数")
    temperature: Optional[float] = Field(default=0.1, ge=0.0, le=2.0, description="温度参数")


class NL2SQLResponse(BaseModel):
    """
    Natural Language to SQL response schema.
    
    Note: 自然语言转SQL响应模式
    """
    
    request_id: str = Field(..., description="请求ID")
    sql: str = Field(..., description="生成的SQL语句")
    explanation: Optional[str] = Field(None, description="SQL解释")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="置信度")
    execution_time: float = Field(..., description="执行时间（秒）")
    warnings: list[str] = Field(default_factory=list, description="警告信息")
    metadata: Optional[dict] = Field(default_factory=dict, description="元数据")


class ModelInfo(BaseModel):
    """
    Model information schema.
    
    Note: 模型信息模式
    """
    
    name: str = Field(..., description="模型名称")
    size: Optional[str] = Field(None, description="模型大小")
    status: str = Field(..., description="模型状态")
    description: Optional[str] = Field(None, description="模型描述")
    modified_at: Optional[datetime] = Field(None, description="修改时间")
    size_vram: Optional[int] = Field(None, description="显存占用（MB）")


class ModelListResponse(BaseModel):
    """
    Model list response schema.
    
    Note: 模型列表响应模式
    """
    
    models: list[ModelInfo] = Field(..., description="模型列表")


class AgentStatsResponse(BaseModel):
    """
    Agent statistics response schema.
    
    Note: Agent统计响应模式
    """
    
    total_agents: int = Field(..., description="总Agent数")
    active_agents: int = Field(..., description="活跃Agent数")
    inactive_agents: int = Field(..., description="非活跃Agent数")
    types: dict[str, int] = Field(..., description="各类型Agent数量") 