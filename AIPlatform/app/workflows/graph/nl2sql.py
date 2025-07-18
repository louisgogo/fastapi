from app.workflows.subgraph.split_query import split_query_graph
from app.workflows.subgraph.generate_sql import generate_sql_graph
from app.workflows.base_workflow import BaseWorkflow
from app.workflows.subgraph.base import State

from langgraph.graph import StateGraph, START, END
from typing import Dict, Any, Optional
from app.utils.logger import logger
import asyncio

class NL2SQLWorkflow(BaseWorkflow):
    """
    NL2SQL工作流
    
    @author malou
    @since 2025-01-08
    Note: 将自然语言转换为SQL查询的工作流
    """
    
    def __init__(self):
        """
        Note: 初始化NL2SQL工作流
        """
        super().__init__()
        self._compiled_graph = None
        logger.info("NL2SQLWorkflow initialized")

    def compile(self):
        """
        @return CompiledStateGraph 编译后的状态图
        Note: 编译状态图，如果已编译则返回缓存的版本
        """
        if self._compiled_graph is None:
            graph = StateGraph(State)
            
            # 添加子图节点
            graph.add_node("split_query", split_query_graph)
            graph.add_node("generate_sql", generate_sql_graph)
            
            # 添加边连接
            graph.add_edge(START, "split_query")
            graph.add_edge("split_query", "generate_sql")
            graph.add_edge("generate_sql", END)
            
            self._compiled_graph = graph.compile()
            logger.info("NL2SQLWorkflow graph compiled")
        
        return self._compiled_graph

    async def execute_async(self, inputs: Dict[str, Any]) -> State:
        """
        @param inputs Dict[str, Any] 输入参数
        @return State 执行结果
        Note: 异步执行NL2SQL工作流
        """
        try:
            # 初始化状态
            state = State(
                query=inputs.get('query'),
                plan=[],
                current_plan_idx=0,
                sql=[],
                sql_error=None,
                db_struc=None,
                history=[]
            )
            
            logger.info(f"Starting NL2SQL workflow with query: {state.query}")
            
            # 执行编译后的图
            result_dict = await self.compile().ainvoke(state)
            
            # 将字典结果转换为State对象
            result = State(**result_dict)
            
            logger.info("NL2SQL workflow completed successfully")
            logger.info(f"Generated {len(result.sql)} SQL queries")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in NL2SQL workflow: {str(e)}")
            # 返回错误状态
            error_state = State(
                query=inputs.get('query'),
                plan=[],
                current_plan_idx=0,
                sql=[],
                sql_error=f"Workflow execution failed: {str(e)}",
                db_struc=None,
                history=[]
            )
            return error_state

# 供外部调用的便捷函数
def build_nl2sql_workflow():
    """
    @return NL2SQLWorkflow NL2SQL工作流实例
    Note: 构建NL2SQL工作流的便捷函数
    """
    return NL2SQLWorkflow()

# 全局实例，供外部调用
nl2sql_workflow = build_nl2sql_workflow()

async def main():
    """
    Note: 测试NL2SQL工作流
    """
    # 测试用例
    test_query = "请导出能源事业中心25年1-4月的损益表数据，以EXCEL形式输出，分月列示"
    
    workflow = build_nl2sql_workflow()
    result = await workflow.execute_async({"query": test_query})
    
    print("="*50)
    print("NL2SQL Workflow Result:")
    print("="*50)
    print(f"Original Query: {result.query}")
    print(f"Split Plan: {result.plan}")
    print(f"Generated SQL: {result.sql}")
    print(f"SQL Error: {result.sql_error}")
    print(f"Current Plan Index: {result.current_plan_idx}")
    
    if result.sql:
        print("\n" + "="*50)
        print("Generated SQL Queries:")
        print("="*50)
        for i, sql in enumerate(result.sql, 1):
            print(f"SQL {i}: {sql}")
            print("-" * 30)

if __name__ == "__main__":
    asyncio.run(main())  