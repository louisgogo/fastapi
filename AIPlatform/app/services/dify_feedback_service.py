# app/services/dify_feedback_service.py
from sqlalchemy.orm import Session
from app.models.dify_feedback import DifyFeedback
from app.schemas.dify_feedback import DifyFeedbackCreate, DifyFeedbackUpdate
import uuid

class DifyFeedbackService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_feedback(self, feedback_data: DifyFeedbackCreate) -> DifyFeedback:
        """创建反馈"""
        # Pydantic模型自动转换为字典
        feedback_dict = feedback_data.model_dump()
        
        # 创建数据库模型实例
        db_feedback = DifyFeedback(**feedback_dict)
        
        self.db.add(db_feedback)
        self.db.commit()
        self.db.refresh(db_feedback)
        
        return db_feedback
    
    def update_feedback(self, workflow_run_id: str, update_data: DifyFeedbackUpdate) -> DifyFeedback:
        """更新反馈"""
        feedback = self.db.query(DifyFeedback).filter(DifyFeedback.workflow_run_id == workflow_run_id).first()
        if not feedback:
            raise ValueError("反馈不存在")
        
        # 只更新提供的字段
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(feedback, field, value)
        
        self.db.commit()
        self.db.refresh(feedback)
        
        return feedback

    def get_all_feedbacks(self) -> list[DifyFeedback]:
        """获取所有反馈"""
        return self.db.query(DifyFeedback).all()
    
    def get_feedback_by_id(self, feedback_id: uuid.UUID) -> DifyFeedback:
        """根据ID获取反馈"""
        return self.db.query(DifyFeedback).filter(DifyFeedback.id == feedback_id).first()
    
    def get_feedback_by_user_id(self, user_id: uuid.UUID) -> list[DifyFeedback]:
        """根据用户ID获取反馈"""
        return self.db.query(DifyFeedback).filter(DifyFeedback.user_id == user_id).all()
    