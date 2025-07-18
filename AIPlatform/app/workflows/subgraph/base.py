from pydantic import BaseModel, Field
from typing import Optional
from abc import ABC, abstractmethod

class State(BaseModel):
    query: Optional[str] = Field(default=None, description="用户的问题")
    plan: list = Field(default_factory=list, description="问题的规划步骤")
    current_plan_idx:int= Field(default=0, description="当前规划步骤的索引")
    sql: list = Field(default_factory=list, description="执行的SQL语句")
    sql_error: Optional[str] = Field(default=None, description="SQL执行错误信息")
    db_struc: Optional[str] = Field(default=None, description="数据库结构")
    raw_data: list = Field(default_factory=list, description="原始数据")
    md: str = Field(default="", description="Markdown格式的数据报告")
    history: list = Field(default_factory=list, description="历史对话")

class SubGraph(ABC):
    def __init__(self):
      pass

    @abstractmethod
    def compile(self):
      pass