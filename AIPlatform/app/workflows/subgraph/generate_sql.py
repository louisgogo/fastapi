from app.workflows.subgraph.base import State, SubGraph
from app.llms.factory import LLMFactory
from langgraph.graph import StateGraph, START, END
import json
from app.tools.db_tool import get_unique_lvl, validate_sql_query
from app.tools.data_tool import extract_sql_from_text
from app.workflows.sql_workflow import SQLGenerationWorkflow
from app.tools.db_tool import DatabaseSchemaTool
from typing import Dict, Any, Optional
from app.utils.logger import logger
import asyncio

class GenerateSQLStep(SubGraph):
    """
    SQL生成步骤
    
    @author malou
    @since 2025-01-08
    Note: 根据用户查询生成SQL语句
    """
    
    def __init__(self, model_name: str = "qwen3:32b"):
        """
        @param model_name str 模型名称
        Note: 初始化SQL生成步骤
        """
        super().__init__()
        self.llm = LLMFactory.create_ollama_llm(model_name)
        self._compiled_graph = None
        
        logger.info(f"GenerateSQLStep initialized with model: {model_name}")

    def compile(self):
        """
        @return CompiledStateGraph 编译后的状态图
        Note: 编译状态图，如果已编译则返回缓存的版本
        """
        if self._compiled_graph is None:
            graph = StateGraph(State)
            graph.add_node("get_knowledge", self._get_knowledge)
            graph.add_node("generate_sql", self._generate_sql)
            graph.add_node("test", self._test_sql)
            graph.add_node("reflect", self._reflect)
            graph.add_node("next", self._next_node)
            
            graph.add_edge(START, "get_knowledge")
            graph.add_edge("get_knowledge", "generate_sql")
            graph.add_edge("generate_sql", "test")
            graph.add_conditional_edges("test", self._should_reflect, {"reflect": "reflect", "next": "next"})
            graph.add_edge("reflect", "test")
            graph.add_conditional_edges("next", self._should_next, {"get_knowledge": "get_knowledge", "end": END})
            
            self._compiled_graph = graph.compile()
            logger.info("GenerateSQLStep graph compiled")
        
        return self._compiled_graph
            

    async def _get_knowledge(self, state: State) -> State:
        """
        @param state State 输入状态
        @return State 输出状态
        Note: 获取数据库知识
        """
        try:
            system_prompt = self._build_knowledge_prompt()
            chain = await self.llm.create_json_chain(system_prompt)
            text = await chain.ainvoke({"plan": state.plan[state.current_plan_idx]})
            
            logger.debug(f"LLM返回的原始文本: {text}")
            content = json.loads(text)['table_name']
            result = await DatabaseSchemaTool().execute_async(table_filter=content)
            state.db_struc = result['markdown_content']
            
            logger.info(f"Database knowledge retrieved for table: {content}")
            return state
            
        except Exception as e:
            logger.error(f"Error in _get_knowledge: {str(e)}")
            state.sql_error = f"Failed to get database knowledge: {str(e)}"
            return state

    async def _generate_sql(self, state: State) -> State:
        """
        @param state State 输入状态
        @return State 输出状态
        Note: 生成SQL语句
        """
        try:
            workflow = SQLGenerationWorkflow(self.llm, state.db_struc)
            result = await workflow.execute_async({"query": state.plan[state.current_plan_idx]})
            
            logger.info(f"Generated SQL: {result}")
            state.sql.append(result)
            return state
            
        except Exception as e:
            logger.error(f"Error in _generate_sql: {str(e)}")
            state.sql_error = f"Failed to generate SQL: {str(e)}"
            return state

    async def _test_sql(self, state: State) -> State:
        """
        @param state State 输入状态
        @return State 输出状态
        Note: 测试SQL语句
        """
        try:
            sql = state.sql[-1]  # 获取最后生成的SQL
            resp_data = await validate_sql_query(sql)
            
            if 'valid' in resp_data and resp_data['valid'] is True:
                logger.info("SQL测试通过")
                state.current_plan_idx += 1
                state.sql_error = None
            else:
                logger.warning("SQL测试失败")
                state.sql_error = resp_data['message'] + "\nSQL语句：" + sql
                state.sql.pop()
            
            return state
            
        except Exception as e:
            logger.error(f"Error in _test_sql: {str(e)}")
            state.sql_error = f"Failed to test SQL: {str(e)}"
            return state

    async def _reflect(self, state: State) -> State:
        """
        @param state State 输入状态
        @return State 输出状态
        Note: 反思修正SQL
        """
        try:
            system_prompt = self._build_reflect_prompt()
            chain = await self.llm.create_json_chain(system_prompt)
            raw_sql = await chain.ainvoke({
                "query": state.plan[state.current_plan_idx],
                "sql_error": state.sql_error,
                "db_struc": state.db_struc,
                "get_unique_lvl": get_unique_lvl()
            })
            
            logger.debug(f"根据错误反馈生成的LLM: {raw_sql}")
            extracted_sql = extract_sql_from_text(raw_sql)
            
            if extracted_sql:
                logger.info(f"提取并清理后的SQL: {extracted_sql}")
                state.sql.append(extracted_sql)
            else:
                logger.warning("警告：无法提取有效的SQL语句")
                state.sql.append(raw_sql.strip())
            
            return state
            
        except Exception as e:
            logger.error(f"Error in _reflect: {str(e)}")
            state.sql_error = f"Failed to reflect SQL: {str(e)}"
            return state

    def _next_node(self, state: State) -> State:
        """
        @param state State 输入状态
        @return State 输出状态
        Note: 下一个节点处理
        """
        state.db_struc = None
        return state

    def _should_reflect(self, state: State) -> str:
        """
        @param state State 当前状态
        @return str 下一个节点名称
        Note: 判断是否需要反思
        """
        return "reflect" if state.sql_error is not None else "next"

    def _should_next(self, state: State) -> str:
        """
        @param state State 当前状态
        @return str 下一个节点名称
        Note: 判断下一步操作
        """
        return "get_knowledge" if state.current_plan_idx < len(state.plan) else "end"

    def _build_knowledge_prompt(self) -> str:
        """
        @return str 知识获取提示模板
        Note: 构建知识获取提示
        """
        return """
你是一个智能的意图识别助手。 你的任务是分析用户输入的自然语言查询，并从中提取以下关键信息。
请严格按照以下 JSON 格式输出：

{{
  "intent_type": "[用户查询的主要目的，例如 '查询利润', '查询费用', '查询收入' 等。 如果是计算总和、平均值等，也请明确指出，例如 '计算总收入']",
  "table_name": "[涉及的表格名称，必须在fact_profit，fact_revenue，fact_expense，其他中选择]"
}}

请根据以上要求，分析以下用户查询，并提取关键信息:

用户查询：{plan}
"""

    def _build_reflect_prompt(self) -> str:
        """
        @return str 反思提示模板
        Note: 构建反思提示
        """
        return f"""
你是一个智能助手，请结合用户上一次生成SQL的错误提示重新生成PSQL语句。

错误提示和SQL语句：{{sql_error}}

请严格按照以下格式输出：
```sql
SELECT * FROM table_name WHERE condition;
```
或者直接输出SQL语句：
SELECT * FROM table_name WHERE condition;

注意：
1. 根据错误提示修正SQL语法
2. 使用具体的表名和字段名
3. 确保SQL语法正确
4. 以分号结尾
5. 不要输出任何解释、说明、备注

用户问题：
{{query}}
数据库结构如下：
{{db_struc}}
唯一层级：unique_lvl的规则如下：
{get_unique_lvl()}
"""

# 供外部调用的便捷函数
def build_generate_sql_graph():
    """
    @return CompiledStateGraph 编译后的图
    Note: 构建SQL生成图的便捷函数
    """
    step = GenerateSQLStep()
    return step.compile()


# 全局实例，供外部调用
generate_sql_graph = build_generate_sql_graph()

async def main():
    state=State(query="请查询2025年1月的利润表",plan=["请查询2025年1月的利润表"])
    graph=build_generate_sql_graph()
    result=await graph.ainvoke(state)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())