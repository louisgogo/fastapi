"""
Feedback Pydantic schemas.

@author malou
@since 2024-12-19
Note: 反馈相关的Pydantic模式定义
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict


class FeedbackBase(BaseModel):
    """
    Feedback base schema.
    
    Note: 反馈基础模式，包含反馈公共字段
    """
    
    request_id: Optional[str] = Field(None, description="关联的API请求ID")
    rating: Optional[int] = Field(None, ge=1, le=5, description="用户评分（1-5分）")
    feedback_text: Optional[str] = Field(None, description="反馈文本")
    is_sql_correct: Optional[bool] = Field(None, description="SQL是否正确")
    suggestions: Optional[str] = Field(None, description="改进建议")
    feedback_type: Optional[str] = Field(None, description="反馈类型")
    priority: Optional[str] = Field(default="medium", description="优先级")


class FeedbackCreate(FeedbackBase):
    """
    Feedback creation schema.
    
    Note: 反馈创建模式
    """
    
    user_id: Optional[uuid.UUID] = Field(None, description="关联用户ID")
    agent_id: Optional[uuid.UUID] = Field(None, description="关联Agent ID")
    
    @field_validator('feedback_type')
    @classmethod
    def validate_feedback_type(cls, v):
        """
        @param v str 反馈类型
        @return str 验证后的反馈类型
        Note: 验证反馈类型是否在允许的范围内
        """
        if v is not None:
            allowed_types = ["bug", "suggestion", "praise", "complaint", "other"]
            if v not in allowed_types:
                raise ValueError(f"feedback_type must be one of {allowed_types}")
        return v
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        """
        @param v str 优先级
        @return str 验证后的优先级
        Note: 验证优先级是否在允许的范围内
        """
        if v is not None:
            allowed_priorities = ["low", "medium", "high", "urgent"]
            if v not in allowed_priorities:
                raise ValueError(f"priority must be one of {allowed_priorities}")
        return v


class FeedbackUpdate(BaseModel):
    """
    Feedback update schema.
    
    Note: 反馈更新模式
    """
    
    rating: Optional[int] = Field(None, ge=1, le=5, description="用户评分（1-5分）")
    feedback_text: Optional[str] = Field(None, description="反馈文本")
    is_sql_correct: Optional[bool] = Field(None, description="SQL是否正确")
    suggestions: Optional[str] = Field(None, description="改进建议")
    feedback_type: Optional[str] = Field(None, description="反馈类型")
    priority: Optional[str] = Field(None, description="优先级")
    status: Optional[str] = Field(None, description="处理状态")


class FeedbackResponse(FeedbackBase):
    """
    Feedback response schema.
    
    Note: 反馈响应模式
    """
    
    id: uuid.UUID = Field(..., description="反馈ID")
    user_id: Optional[uuid.UUID] = Field(None, description="关联用户ID")
    agent_id: Optional[uuid.UUID] = Field(None, description="关联Agent ID")
    status: str = Field(..., description="处理状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)


class FeedbackListResponse(BaseModel):
    """
    Feedback list response schema.
    
    Note: 反馈列表响应模式
    """
    
    feedbacks: list[FeedbackResponse] = Field(..., description="反馈列表")


class FeedbackStatsResponse(BaseModel):
    """
    Feedback statistics response schema.
    
    Note: 反馈统计响应模式
    """
    
    total_feedback: int = Field(..., description="总反馈数")
    pending_feedback: int = Field(..., description="待处理反馈数")
    resolved_feedback: int = Field(..., description="已解决反馈数")
    average_rating: float = Field(..., description="平均评分")
    positive_feedback: int = Field(..., description="正面反馈数")
    negative_feedback: int = Field(..., description="负面反馈数")
    feedback_types: dict[str, int] = Field(..., description="各类型反馈数量")
    sql_correctness_rate: float = Field(..., description="SQL正确率")


class FeedbackSummaryResponse(BaseModel):
    """
    Feedback summary response schema.
    
    Note: 反馈摘要响应模式
    """
    
    period: str = Field(..., description="统计周期")
    total_feedback: int = Field(..., description="总反馈数")
    average_rating: float = Field(..., description="平均评分")
    improvement_suggestions: list[str] = Field(..., description="改进建议")
    common_issues: list[str] = Field(..., description="常见问题")
    top_positive_feedback: list[str] = Field(..., description="优秀反馈")


class FeedbackStats(BaseModel):
    """
    Feedback statistics schema.
    
    Note: 反馈统计模式
    """
    
    total_count: int = Field(..., description="总反馈数")
    average_rating: Optional[float] = Field(None, description="平均评分")
    rating_distribution: dict = Field(..., description="评分分布")
    feedback_type_distribution: dict = Field(..., description="反馈类型分布")
    priority_distribution: dict = Field(..., description="优先级分布")
    status_distribution: dict = Field(..., description="状态分布") 