"""
Natural Language to SQL Agent.

@author malou
@since 2024-12-19
Note: 自然语言转SQL的Agent实现，基于LangGraph工作流
"""

import re
import time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from app.agents.base_agent import BaseAgent, AgentState
from app.core.exceptions import AgentException
from app.services.ollama_service import OllamaService, ChatMessage
from app.tools.data_tool import extract_sql_from_text
from app.utils.logger import logger


class SQLValidationResult(BaseModel):
    """SQL validation result schema."""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    suggestions: List[str] = []


class NL2SQLAgent(BaseAgent):
    """Natural Language to SQL Agent."""
    
    def __init__(self, name: str = "NL2SQL Agent", config: Optional[Dict] = None):
        """Initialize NL2SQL Agent."""
        super().__init__(name, "nl2sql", config)
        
        # 初始化OLLAMA服务（OllamaService不接受参数，直接从配置获取）
        self.ollama_service = OllamaService()
        
        # 获取生成配置
        generation_config = self.get_generation_config()
        self.default_model = self.get_config("model")
        self.default_temperature = generation_config["temperature"]
        self.max_tokens = generation_config["max_tokens"]
        
        logger.info(f"NL2SQL Agent initialized with model: {self.default_model}")
        logger.info(f"Generation config: {generation_config}")
    
    async def process(self, state: AgentState) -> AgentState:
        """Process natural language to SQL conversion."""
        try:
            start_time = time.time()
            
            # Step 1: Validate input
            if not self.validate_input(state.user_input):
                return self.set_error(state, "Invalid input for NL2SQL conversion")
            
            self.add_step(state, "validate_input", {"input": state.user_input})
            
            # Step 2: Generate SQL - 添加 await
            sql = await self._generate_sql(state)  # ✅ 修复：添加 await
            if not sql:
                return self.set_error(state, "Failed to generate SQL")
            
            # Step 3: Validate SQL
            validation_result = self._validate_sql_syntax(sql)
            self.add_step(state, "validate_sql", validation_result.dict())
            
            # Step 4: Generate explanation - 添加 await
            explanation = await self._generate_explanation(sql)  # ✅ 修复：添加 await
            
            # Step 5: Format result
            result_data = {
                "sql": sql,
                "explanation": explanation,
                "confidence": self._calculate_confidence(validation_result),
                "warnings": validation_result.warnings
            }
            
            execution_time = time.time() - start_time
            result_data["execution_time"] = execution_time
            
            self.set_result(state, sql, result_data)
            
            logger.info(f"NL2SQL processing completed in {execution_time:.2f}s")
            return state
            
        except Exception as e:
            logger.error(f"NL2SQL processing failed: {str(e)}")
            return self.handle_error(state, e)
    
    def validate_input(self, user_input: str) -> bool:
        """Validate user input for NL2SQL processing."""
        if not user_input or len(user_input.strip()) < 3:
            return False
        
        # Check for query intent keywords
        query_keywords = [
            "查询", "统计", "计算", "求", "获取", "显示", "列出", "找出", 
            "select", "count", "sum", "avg", "max", "min", "group", "where"
        ]
        
        user_input_lower = user_input.lower()
        return any(keyword in user_input_lower for keyword in query_keywords)
    
    async def _generate_sql(self, state: AgentState) -> str:
        """Generate SQL from natural language."""
        try:
            database_schema = state.context.get("database_schema")
            
            # Step 1: Generate raw SQL from natural language
            raw_sql = await self.ollama_service.generate_nl2sql(
                natural_language=state.user_input,
                database_schema=database_schema,
                model=self.default_model,
                temperature=self.default_temperature,
                max_tokens=self.max_tokens
            )
            
            self.add_step(state, "generate_raw_sql", {"raw_sql": raw_sql})
            
            # Step 2: Clean and extract SQL using tool
            try:
                # 调用工具清理SQL - 注意：execute方法不是异步的，直接调用
                result = extract_sql_from_text(text=raw_sql)
                
                if result:
                    self.add_step(state, "clean_sql", {
                        "cleaned_sql": result,
                    })
                    return result
                else:
                    logger.warning(f"SQL cleaning failed: {result}, using raw SQL")
                    return raw_sql 
            except Exception as tool_error:
                logger.warning(f"SQL cleaning tool failed: {str(tool_error)}, using raw SQL")
                # 如果工具调用失败，使用原始SQL
                return raw_sql
            
        except Exception as e:
            logger.error(f"SQL generation failed: {str(e)}")
            raise AgentException(f"SQL generation failed: {str(e)}")
    
    async def _generate_explanation(self, sql: str) -> str:
        """Generate explanation for the SQL query."""
        try:
            explanation_prompt = f"""请为以下SQL查询提供简洁的中文解释：

{sql}

请说明这个查询的目的和主要逻辑。"""
            
            messages = [
                ChatMessage(role="system", content="你是数据库专家，善于解释SQL查询。"),
                ChatMessage(role="user", content=explanation_prompt)
            ]
            
            response = await self.ollama_service.chat_completion(
                model=self.default_model,
                messages=messages,
                temperature=0.3,
                max_tokens=300
            )
            
            return response.message.content.strip()
            
        except Exception as e:
            logger.warning(f"Failed to generate explanation: {str(e)}")
            return "无法生成SQL解释"
    
    def _validate_sql_syntax(self, sql: str) -> SQLValidationResult:
        """Validate SQL syntax."""
        errors = []
        warnings = []
        suggestions = []
        
        if not sql or not sql.strip():
            errors.append("Empty SQL statement")
            return SQLValidationResult(is_valid=False, errors=errors)
        
        sql_lower = sql.lower().strip()
        
        # Basic SQL keyword check
        if not any(keyword in sql_lower for keyword in ["select", "insert", "update", "delete"]):
            errors.append("No valid SQL statement found")
        
        # Security check
        dangerous_keywords = ["drop", "delete", "truncate", "alter", "create"]
        if any(keyword in sql_lower for keyword in dangerous_keywords):
            warnings.append("SQL contains potentially dangerous operations")
        
        # Performance suggestions
        if "select *" in sql_lower:
            suggestions.append("Consider specifying column names instead of using SELECT *")
        
        if "order by" not in sql_lower and "limit" in sql_lower:
            suggestions.append("Consider adding ORDER BY clause when using LIMIT")
        
        is_valid = len(errors) == 0
        
        return SQLValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _calculate_confidence(self, validation_result: SQLValidationResult) -> float:
        """Calculate confidence score for SQL generation."""
        confidence = 1.0
        
        if not validation_result.is_valid:
            confidence *= 0.3
        if validation_result.warnings:
            confidence *= 0.8
        if validation_result.suggestions:
            confidence *= 0.9
        
        return max(0.1, min(1.0, confidence))
    
    async def close(self):
        """Close Agent resources."""
        if hasattr(self.ollama_service, 'close'):
            await self.ollama_service.close()
        logger.info(f"NL2SQL Agent {self.name} closed") 