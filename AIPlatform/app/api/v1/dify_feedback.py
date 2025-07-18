# app/api/v1/dify_feedback.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from app.database.connection import get_db
from app.schemas.dify_feedback import (
    DifyFeedbackCreate, 
    DifyFeedbackUpdate, 
    DifyFeedbackResponse,
    DifyFeedbackListResponse
)
from app.services.dify_feedback_service import DifyFeedbackService

router = APIRouter()

@router.post("/", response_model=DifyFeedbackResponse)
def create_dify_feedback(
    feedback: DifyFeedbackCreate,  # 自动验证输入数据
    db: Session = Depends(get_db)
):
    """创建Dify反馈"""
    service = DifyFeedbackService(db)
    return service.create_feedback(feedback)

@router.get("/", response_model=DifyFeedbackListResponse)
def get_dify_feedbacks(db: Session = Depends(get_db)):
    """获取Dify反馈列表"""
    service = DifyFeedbackService(db)
    feedbacks = service.get_all_feedbacks()
    return DifyFeedbackListResponse(dify_feedback=[DifyFeedbackResponse(**feedback.to_dict()) for feedback in feedbacks])

@router.put("/{workflow_run_id}", response_model=DifyFeedbackResponse)
def update_dify_feedback(
    workflow_run_id: str,
    feedback_update: DifyFeedbackUpdate,  # 自动验证更新数据
    db: Session = Depends(get_db)
):
    """更新Dify反馈"""
    service = DifyFeedbackService(db)
    return service.update_feedback(workflow_run_id, feedback_update)