from app.workflows.subgraph.base import State, SubGraph
from app.llms.factory import LLMFactory
from app.tools.data_tool import extract_json_from_text
from langgraph.graph import StateGraph, START, END
from typing import Dict, Any, Optional
from app.utils.logger import logger
import asyncio

class SplitQueryStep(SubGraph):
    """
    查询拆分步骤
    
    @author malou
    @since 2025-01-08
    Note: 将用户查询拆分为针对单张表的问题
    """
    
    def __init__(self, model_name: str = "qwen3:32b"):
        """
        @param model_name str 模型名称
        Note: 初始化查询拆分步骤
        """
        super().__init__()
        self.llm = LLMFactory.create_ollama_llm(model_name)
        self._compiled_graph = None
        
        logger.info(f"SplitQueryStep initialized with model: {model_name}")

    def compile(self):
        """
        @return CompiledStateGraph 编译后的状态图
        Note: 编译状态图，如果已编译则返回缓存的版本
        """
        if self._compiled_graph is None:
            graph = StateGraph(State)
            graph.add_node("split_query", self._split_query)
            graph.add_edge(START, "split_query")
            graph.add_edge("split_query", END)
            
            self._compiled_graph = graph.compile()
            logger.info("SplitQueryStep graph compiled")
        
        return self._compiled_graph

    async def _split_query(self, state: State) -> State:
        """
        @param state State 输入状态
        @return State 输出状态
        Note: 执行查询拆分的核心逻辑
        """
        try:
            # 构建系统提示
            system_prompt = self._build_system_prompt()
            
            # 调用LLM
            chain = await self.llm.create_json_chain(system_prompt)
            text = await chain.ainvoke({"query": state.query})
            
            # 解析结果
            plan = extract_json_from_text(text)
            if not plan:
                logger.warning("Failed to extract plan from LLM response")
                plan = [state.query]  # 降级处理
            
            # 更新状态
            state.plan = plan
            state.current_plan_idx = 0
            
            logger.info(f"Query split completed, generated {len(plan)} sub-queries")
            return state
            
        except Exception as e:
            logger.error(f"Error in _split_query: {str(e)}")
            state.sql_error = f"Failed to split query: {str(e)}"
            return state

    def _build_system_prompt(self) -> str:
        """
        @return str 系统提示模板
        Note: 构建系统提示模板
        """
        return """
角色：
你是一名自然语言转PSQL的专家，负责判断用户的问题涉及几张表格，并将用户的问题，根据涉及到的表格，分解成几个问题（一个表只对应一个问题）。你的目标是生成可以直接用于转换为 PSQL 查询语句的、针对单张表的清晰问题。

已知数据库包含以下表格：
* fact_profit (利润表): 记录各会计科目的数据。
* fact_expense (费用明细表): 记录费用的明细数据。
* fact_revenue (收入成本明细表): 记录收入的明细数据。

请分析以下用户问题，判断是否需要针对不同的表格分别进行提问。

你的判断依据：
* 如果问题涉及本年，去年，前年，本月，上月等信息，则根据提供的当前日期，将上述信息转换为具体的年月信息，如2025年等。
* 如果问题可以直接针对单张表进行查询，则不需要拆分，直接优化为针对单张表的清晰问题。
* 如果问题需要同时从多张表中获取信息才能回答，则需要拆分。
* 拆分后的子问题，应该能够单独针对对应的表格进行查询，并且子问题集合能够完整覆盖原始问题的意图。
* 拆分后的子问题，应该尽可能清晰明确，方便后续转换为 PSQL 查询语句。

输出要求：
* 如果问题不需要拆分，输出：["优化后的问题"]
* 如果问题需要拆分，输出：["拆分后的问题1"，"拆分后的问题2"]....
* 严格按照列表输出，不要输出任何其他文字。

用户问题：{query}
"""


# 供外部调用的便捷函数
def build_split_query_graph():
    """
    @return CompiledStateGraph 编译后的图
    Note: 构建查询拆分图的便捷函数
    """
    step = SplitQueryStep()
    return step.compile()


# 全局实例，供外部调用
split_query_graph = build_split_query_graph()

async def main():
    state=State(query="请查询2025年1月的利润表")
    graph=build_split_query_graph()
    result=await graph.ainvoke(state)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())