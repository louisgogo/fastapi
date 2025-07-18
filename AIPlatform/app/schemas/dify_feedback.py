"""
DifyFeedback Pydantic schemas.

@author malou
@since 2024-12-19
Note: Dify反馈相关的Pydantic模式定义
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict


class DifyFeedbackBase(BaseModel):
    """
    DifyFeedback base schema.
    
    Note: Dify反馈基础模式
    """
    
    app_id: str = Field(..., description="应用ID")
    app_name: str = Field(..., description="应用名称")
    user_id: str = Field(..., description="关联用户ID")
    workflow_run_id: str = Field(..., description="工作流运行ID")
    query: str = Field(..., description="用户查询")
    sub_query: str = Field(..., description="子查询")
    answer: str = Field(..., description="AI回答")
    rating: int = Field(..., ge=1, le=5, description="用户评分（1-5分）")


class DifyFeedbackCreate(DifyFeedbackBase):
    """
    DifyFeedback creation schema.
    
    Note: Dify反馈创建模式
    """
    
    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v):
        """验证评分范围"""
        if not 1 <= v <= 5:
            raise ValueError("评分必须在1-5之间")
        return v


class DifyFeedbackUpdate(BaseModel):
    """
    DifyFeedback update schema.
    
    Note: Dify反馈更新模式
    """
    
    rating: Optional[int] = Field(None, ge=1, le=5, description="用户评分（1-5分）")
    query: Optional[str] = Field(None, description="用户查询")
    answer: Optional[str] = Field(None, description="AI回答")


class DifyFeedbackResponse(DifyFeedbackBase):
    """
    DifyFeedback response schema.
    
    Note: Dify反馈响应模式
    """
    
    id: uuid.UUID = Field(..., description="反馈ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)


class DifyFeedbackListResponse(BaseModel):
    """
    DifyFeedback list response schema.
    
    Note: Dify反馈列表响应模式
    """
    
    dify_feedback: list[DifyFeedbackResponse] = Field(..., description="Dify反馈列表")


class DifyFeedbackStatsResponse(BaseModel):
    """
    DifyFeedback statistics response schema.
    
    Note: Dify反馈统计响应模式
    """
    
    total_feedback: int = Field(..., description="总反馈数")
    average_rating: float = Field(..., description="平均评分")
    app_performance: dict[str, dict] = Field(..., description="各应用性能统计")
    rating_distribution: dict[int, int] = Field(..., description="评分分布")