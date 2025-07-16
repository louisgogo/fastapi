"""
Workflows package for LANGGRAPH integration.

@author malou
@since 2025-01-08
Note: 工作流包，包含各种工作流的实现
"""

# 延迟导入以避免循环依赖
def get_base_workflow():
    from .base_workflow import BaseWorkflow
    return BaseWorkflow

def get_text_workflow():
    from .text_workflow import SimpleTextWorkflow
    return SimpleTextWorkflow

__all__ = [
    "get_base_workflow",
    "get_text_workflow",
] 