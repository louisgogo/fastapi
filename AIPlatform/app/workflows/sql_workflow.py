"""
SQL generation workflow implementation.

@author malou
@since 2025-01-08
Note: SQL生成工作流实现（示例，展示扩展性）
"""

from typing import Dict, Any, AsyncGenerator, Optional
import asyncio
from .base_workflow import BaseWorkflow
from app.llms.ollama_llm import OllamaLLM
from app.utils.logger import logger
from app.tools.data_tool import extract_sql_from_text
from app.llms.base_llm import LLMConfig
from app.llms.factory import LLMFactory


class SQLGenerationWorkflow(BaseWorkflow):
    """
    SQL generation workflow.
    
    Note: SQL生成工作流，将自然语言转换为SQL查询
    """
    
    def __init__(self, llm: OllamaLLM,  database_schema: Optional[str] = None):
        """
        @param llm BaseLLM LLM实例
        @param database_schema str 数据库模式描述
        Note: 初始化SQL生成工作流
        """
        self.llm = llm
        self.database_schema = database_schema
        self.system_prompt = self._build_system_prompt()
        
        logger.info("Initialized SQLGenerationWorkflow")
    
    def _build_system_prompt(self) -> str:
        """
        @return str 系统提示
        Note: 构建SQL生成的系统提示
        """
        return f"""
你是一位精通SQL语言的数据库专家，熟悉PostgreSQL数据库。你的任务是根据用户的自然语言输入，编写出可直接执行的SQL查询语句。输出内容必须是可以执行的SQL语句，不能包含任何多余的信息。

核心规则：
1.  根据用户的查询需求，结合数据库结构和参考案例，确定涉及的表和字段。
2.  确保SQL语句的语法符合PostgreSQL的规范。
3.  输出的SQL语句必须完整且可执行，不包含注释或多余的换行符。

关键技巧：
*   WHERE 子句： 用于过滤数据。例如，`WHERE column_name = 'value'`。
*   **聚合函数：** 如`COUNT`、`SUM`、`AVG`等，用于计算汇总信息。
*   **除法处理：** 在进行除法运算时，需考虑除数为零的情况，避免错误，可以使用`NULLIF(denominator, 0)`。
*   **日期范围：** 查询特定日期范围的数据时，使用`DATE_PART`函数。例如， `DATE_PART('MONTH', acct_period) = 1 `，DATE_PART('YEAR', acct_period) = 2025 `。

注意事项：
1.  确保字段名和表名的正确性，避免拼写错误。
2.  对于字符串类型的字段，使用单引号括起来。例如，`'sample_text'`。
3.  对所有字段类型为数值的，都使用聚合函数，同时对非数值类型的字段，都使用`GROUP BY`子句。
4.  在进行除法运算时，需判断除数是否为零，以避免运行时错误。
5.  生成的sql语句不能有换行符，比如 `\n`。
6.  强制模糊查询：所有 WHERE 子句中涉及文本列（VARCHAR, TEXT 等）的查询条件必须使用模糊查询 ( LIKE '%...%' 或 ILIKE '%...%')。 除非特别指定，否则默认使用 ILIKE 进行不区分大小写的模糊匹配。
7. IN 操作符转换：如果自然语言需求中包含 IN 操作符，则将其转换为多个 OR 组合的模糊查询，例如：column1 IN ('value1', 'value2') 转换为 column1 ILIKE '%value1%' OR column1 ILIKE '%value2%'。
8. 查询的字段：请根据用户问题和数据库的结构，在给定的数据库列名中进行选择，禁止直接使用“*”进行全部字段选择。

数据库Schema:
{self.database_schema}

规则：
1. 只返回SQL查询，不要包含其他解释
2. 确保SQL语法正确
3. 使用适当的JOIN和WHERE条件
4. 考虑性能优化
"""
    
    async def execute_async(self, inputs: Dict[str, Any]) -> str:
        """
        @param inputs Dict[str, Any] 输入参数，应包含'query'字段
        @return str SQL查询结果
        Note: 执行SQL生成工作流
        """
        try:
            user_query = inputs.get('query', '')
            if not user_query:
                raise ValueError("Missing 'query' field in inputs")
            
            prompt = f"{self.system_prompt}\n\n用户查询: {user_query}\n\nSQL:"
            
            # 调用LLM
            chain = await self.llm.create_chain(prompt)
            response = await chain.ainvoke({"query":user_query})
            
            # 清理SQL输出
            sql_query = extract_sql_from_text(response)
            
            logger.info(f"Generated SQL query successfully")
            return sql_query or ""  # 确保返回字符串
            
        except Exception as e:
            logger.error(f"SQL generation failed: {str(e)}")
            raise
    
    async def execute_stream(self, inputs: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        @param inputs Dict[str, Any] 输入参数
        @return AsyncGenerator[str, None] 流式SQL生成结果
        Note: 流式执行SQL生成工作流
        """
        try:
            user_query = inputs.get('query', '')
            if not user_query:
                raise ValueError("Missing 'query' field in inputs")
            
            prompt = f"{self.system_prompt}\n\n用户查询: {user_query}\n\nSQL:"
            
            # 流式调用LLM
            async for chunk in self.llm._generate_stream(prompt):
                if chunk:
                    yield chunk
            
            logger.info(f"Stream SQL generation completed successfully")
            
        except Exception as e:
            logger.error(f"Stream SQL generation failed: {str(e)}") 

if __name__ == "__main__":
    async def main():
        llm = LLMFactory.create_ollama_llm()
        workflow = SQLGenerationWorkflow(llm, "SELECT * FROM users")
        result = await workflow.execute({"query": "查询用户信息"})
        print(result)
    asyncio.run(main())