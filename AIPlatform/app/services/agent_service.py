"""
Agent service.

@author malou
@since 2024-12-19
Note: 异步Agent管理和调用业务逻辑服务
"""

import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.nl2sql_agent import NL2SQLAgent
from app.agents.base_agent import AgentState
from app.schemas.agent import NL2SQLRequest, NL2SQLResponse
from app.core.exceptions import AgentException, NotFoundException
from app.utils.logger import logger


class AgentService:
    """Agent service class."""
    
    def __init__(self, db: AsyncSession):
        """Initialize Agent service."""
        self.db = db
        self.agents = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize available agents."""
        # Initialize NL2SQL Agent
        self.agents["nl2sql"] = NL2SQLAgent()
        logger.info("Agent service initialized with available agents")
    
    async def process_nl2sql(
        self, 
        request: NL2SQLRequest, 
        user_id: Optional[uuid.UUID] = None
    ) -> NL2SQLResponse:
        """
        Process natural language to SQL request.
        
        @param request NL2SQLRequest 自然语言转SQL请求
        @param user_id Optional[uuid.UUID] 用户ID
        @return NL2SQLResponse NL2SQL响应
        @throws AgentException Agent处理异常
        @throws NotFoundException Agent不存在异常
        Note: 异步处理自然语言转SQL请求
        """
        try:
            agent = self.agents.get("nl2sql")
            if not agent:
                raise NotFoundException("NL2SQL agent not available")
            
            # Create agent state
            context = {
                "database_schema": request.database_schema,
                "user_id": str(user_id) if user_id else None,
            }
            if request.context:
                context.update(request.context)
            
            state = agent.create_state(request.query, context)
            
            # Process request asynchronously
            result_state = await agent.process(state)
            
            if result_state.error:
                raise AgentException(f"NL2SQL processing failed: {result_state.error}")
            
            # Format response
            response = NL2SQLResponse(
                request_id=result_state.request_id,
                sql=result_state.result or "",
                explanation=result_state.metadata.get("explanation", ""),
                confidence=result_state.metadata.get("confidence", 0.0),
                execution_time=result_state.metadata.get("execution_time", 0.0),
                warnings=result_state.metadata.get("warnings", []),
                metadata=result_state.metadata
            )
            
            logger.info(f"NL2SQL request processed: {result_state.request_id}")
            return response
            
        except Exception as e:
            logger.error(f"NL2SQL processing failed: {str(e)}")
            raise AgentException(f"NL2SQL processing failed: {str(e)}")
    
    async def close(self):
        """
        Close all agents.
        
        Note: 异步关闭所有agent资源
        """
        for agent in self.agents.values():
            if hasattr(agent, 'close'):
                if hasattr(agent.close, '__call__'):
                    # 检查是否是异步方法
                    if hasattr(agent.close, '__await__'):
                        await agent.close()
                    else:
                        agent.close()
        logger.info("Agent service closed") 