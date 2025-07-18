from app.workflows.subgraph.base import State, SubGraph
from app.tools.db_tool import execute_sql_query
from langgraph.graph import StateGraph, START, END
from app.llms.factory import LLMFactory
from typing import Dict, Any, Optional, List
from app.utils.logger import logger
import json
import asyncio
import pandas as pd
from decimal import Decimal
from datetime import date, datetime

class FetchDataStep(SubGraph):
    """
    数据获取步骤
    
    @author malou
    @since 2025-01-08
    Note: 执行SQL查询并获取数据，同时生成Markdown格式
    """
    
    def __init__(self, model_name: str = "qwen3:32b"):
        """
        @param model_name str 模型名称
        Note: 初始化数据获取步骤
        """
        super().__init__()
        self.llm = LLMFactory.create_ollama_llm(model_name)
        self._compiled_graph = None
        
        logger.info(f"FetchDataStep initialized with model: {model_name}")

    def compile(self):
        """
        @return CompiledStateGraph 编译后的状态图
        Note: 编译状态图，如果已编译则返回缓存的版本
        """
        if self._compiled_graph is None:
            graph = StateGraph(State)
            graph.add_node("fetch_data", self._fetch_data)
            graph.add_node("generate_markdown", self._generate_markdown)
            
            graph.add_edge(START, "fetch_data")
            graph.add_edge("fetch_data", "generate_markdown")
            graph.add_edge("generate_markdown", END)
            
            self._compiled_graph = graph.compile()
            logger.info("FetchDataStep graph compiled")
        
        return self._compiled_graph

    async def _fetch_data(self, state: State) -> State:
        """
        @param state State 输入状态
        @return State 输出状态
        Note: 执行SQL查询并获取数据的核心逻辑
        """
        try:
            logger.info(f"开始执行 {len(state.sql)} 个SQL查询")
            
            raw_data = []
            
            for i, sql in enumerate(state.sql):
                logger.info(f"执行第 {i+1} 个SQL查询: {sql}")
                
                # 执行SQL查询
                result = await execute_sql_query(sql)
                
                if result.get('success', False):
                    data = result.get('data', [])
                    raw_data.append({
                        'sql_index': i,
                        'sql': sql,
                        'data': data,
                        'columns': result.get('columns', []),
                        'row_count': len(data)
                    })
                    logger.info(f"SQL查询 {i+1} 成功，返回 {len(data)} 行数据")
                else:
                    error_msg = f"SQL查询 {i+1} 失败: {result.get('error', '未知错误')}"
                    logger.error(error_msg)
                    state.sql_error = error_msg
                    return state
            
            # 将原始数据存储到状态中
            state.raw_data = raw_data
            
            logger.info("所有SQL查询执行完成")
            return state
            
        except Exception as e:
            logger.error(f"Error in _fetch_data: {str(e)}")
            state.sql_error = f"Failed to fetch data: {str(e)}"
            return state

    async def _generate_markdown(self, state: State) -> State:
        """
        @param state State 输入状态
        @return State 输出状态
        Note: 生成Markdown格式的数据报告
        """
        try:
            if not state.raw_data:
                logger.warning("No raw data available for markdown generation")
                state.md = "# 数据查询结果\n\n无数据返回"
                return state
            
            logger.info("开始生成Markdown格式的数据报告")
            
            markdown_content = "# 数据查询结果报告\n\n"
            markdown_content += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            markdown_content += f"**查询数量**: {len(state.raw_data)} 个SQL查询\n\n"
            
            total_rows = sum(dataset['row_count'] for dataset in state.raw_data)
            markdown_content += f"**总数据行数**: {total_rows} 行\n\n"
            
            # 为每个查询结果生成Markdown
            for i, dataset in enumerate(state.raw_data, 1):
                markdown_content += f"## 查询 {i}\n\n"
                markdown_content += f"**SQL语句**:\n```sql\n{dataset['sql']}\n```\n\n"
                markdown_content += f"**数据行数**: {dataset['row_count']} 行\n\n"
                markdown_content += f"**字段列表**: {', '.join(dataset['columns'])}\n\n"
                
                if dataset['data']:
                    # 使用Pandas生成数据表格（性能优化）
                    markdown_content += "### 数据表格\n\n"
                    
                    try:
                        # 创建DataFrame
                        df = pd.DataFrame(dataset['data'])
                        
                        # 限制显示前1000行
                        df = df.head(1000)
                        
                        # 生成Markdown表格
                        markdown_table = df.to_markdown(index=False, tablefmt="pipe")
                        markdown_content += markdown_table + "\n\n" if markdown_table else ""
                        
                        if len(dataset['data']) > 1000:
                            markdown_content += f"*注：仅显示前1000行数据，共 {len(dataset['data'])} 行*\n\n"
                        
                        
                        # 数值型字段统计
                        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
                        if numeric_columns:
                            markdown_content += f"- **数值型字段**: {', '.join(numeric_columns)}\n"
                        
                        # 添加基本统计信息
                        if not df.empty and numeric_columns:
                            markdown_content += "\n**数值字段统计**:\n"
                            for col in numeric_columns[:3]:  # 只显示前3个数值字段的统计
                                if col in df.columns:
                                    stats = df[col].describe()
                                    markdown_content += f"- {col}: 均值={stats['mean']:.2f}, 最大值={stats['max']:.2f}, 最小值={stats['min']:.2f}\n"
                        
                    except Exception as e:
                        logger.warning(f"Pandas处理失败，回退到手动处理: {str(e)}")
                        # 回退到原来的手动处理方式
                        markdown_content += self._generate_markdown_manual(dataset)
                    
                else:
                    markdown_content += "**查询结果**: 无数据返回\n\n"
                
                markdown_content += "---\n\n"  # 分隔线
            
            # 添加总结信息
            markdown_content += "## 总结\n\n"
            markdown_content += f"- 成功执行了 {len(state.raw_data)} 个SQL查询\n"
            markdown_content += f"- 总共获取了 {total_rows} 行数据\n"
            markdown_content += f"- 数据已转换为Markdown格式，便于AI分析和处理\n\n"
            
            state.md = markdown_content
            logger.info("Markdown格式的数据报告生成完成")
            return state
            
        except Exception as e:
            logger.error(f"Error in _generate_markdown: {str(e)}")
            state.sql_error = f"Failed to generate markdown: {str(e)}"
            return state

    def _generate_markdown_manual(self, dataset: Dict[str, Any]) -> str:
        """
        @param dataset Dict[str, Any] 数据集
        @return str Markdown内容
        Note: 手动生成Markdown的回退方案
        """
        markdown_content = ""
        
        # 表头
        markdown_content += "| " + " | ".join(dataset['columns']) + " |\n"
        markdown_content += "| " + " | ".join(["---"] * len(dataset['columns'])) + " |\n"
        
        # 数据行
        display_data = dataset['data'][:20]
        for row_dict in display_data:
            formatted_row = []
            for column_name in dataset['columns']:
                value = row_dict.get(column_name)
                formatted_value = self._format_value_for_markdown(value)
                formatted_row.append(formatted_value)
            markdown_content += "| " + " | ".join(formatted_row) + " |\n"
        
        return markdown_content

    def _format_value_for_markdown(self, value) -> str:
        """
        @param value Any 数据值
        @return str 格式化后的字符串
        Note: 将数据值格式化为Markdown友好的格式
        """
        if value is None:
            return "NULL"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, (date, datetime)):
            return str(value)
        elif isinstance(value, Decimal):
            return str(float(value))
        elif isinstance(value, str):
            # 转义Markdown特殊字符
            return value.replace("|", "\\|").replace("\n", "<br>")
        else:
            return str(value)

# 供外部调用的便捷函数
def build_fetch_data_graph():
    """
    @return CompiledStateGraph 编译后的图
    Note: 构建数据获取图的便捷函数
    """
    step = FetchDataStep()
    return step.compile()

# 全局实例，供外部调用
fetch_data_graph = build_fetch_data_graph()

async def main():
    state = State(sql=["SELECT unique_lvl,SUM(amt) FROM fact_profit WHERE DATE_PART('YEAR', acct_period) = 2025 GROUP BY unique_lvl;"])
    graph = build_fetch_data_graph()
    result = await graph.ainvoke(state)
    print("Fetch data result:", result)


if __name__ == "__main__":
    asyncio.run(main())