from app.tools.db_tool import execute_sql_query
from app.tools.data_tool import extract_json_from_text
from app.workflows.base_workflow import BaseWorkflow
from app.workflows.langgraph.nl2sql import NL2SQLWorkflow

from langgraph.graph import StateGraph, START, END
from app.llms.factory import LLMFactory

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import pandas as pd
import json
import asyncio
import logging
from decimal import Decimal
from datetime import date, datetime  # 添加date和datetime导入

# 设置日志
logger = logging.getLogger(__name__)

# 创建LLM实例
llm = LLMFactory.create_ollama_llm()

class DataAnalysisState(BaseModel):
    """数据分析工作流状态"""
    query: Optional[str] = Field(default=None, description="原始用户查询")
    sql_list: List[str] = Field(default_factory=list, description="SQL语句列表")
    raw_data: List[Dict[str, Any]] = Field(default_factory=list, description="原始查询数据")
    processed_data: Optional[str] = Field(default=None, description="处理后的数据格式")
    analysis_report: Optional[str] = Field(default=None, description="生成的分析报告")
    error_message: Optional[str] = Field(default=None, description="错误信息")

async def execute_sql_queries(state: DataAnalysisState) -> DataAnalysisState:
    """执行SQL查询并获取数据"""
    try:
        logger.info(f"开始执行 {len(state.sql_list)} 个SQL查询")
        
        for i, sql in enumerate(state.sql_list):
            logger.info(f"执行第 {i+1} 个SQL查询: {sql}")
            
            # 执行SQL查询
            result = await execute_sql_query(sql)
            
            if result.get('success', False):
                data = result.get('data', [])
                state.raw_data.append({
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
                state.error_message = error_msg
                return state
        
        logger.info("所有SQL查询执行完成")
        return state
        
    except Exception as e:
        error_msg = f"执行SQL查询时发生异常: {str(e)}"
        logger.error(error_msg)
        state.error_message = error_msg
        return state

async def process_data_with_pandas(state: DataAnalysisState) -> DataAnalysisState:
    """使用pandas处理数据并转换为AI友好的格式"""
    try:
        logger.info("开始使用pandas处理数据")
        
        # 定义序列化函数 - 完善所有数据类型处理
        def serialize_value(value):
            """序列化值为JSON兼容格式"""
            if pd.isna(value):
                return None
            elif isinstance(value, (pd.Timestamp, pd.Timedelta)):
                return str(value)
            elif hasattr(value, 'item'):  # numpy数据类型
                return value.item()
            elif isinstance(value, (Decimal, float)):  # 添加Decimal类型处理
                return float(value)  # 转换为float
            elif isinstance(value, (date, datetime)):  # 添加date和datetime类型处理
                return str(value)
            elif isinstance(value, (int, str, bool)):  # 基本类型直接返回
                return value
            else:
                return str(value)  # 其他类型转换为字符串
        
        processed_datasets = []
        
        for dataset in state.raw_data:
            if not dataset['data']:
                continue
            
            # 创建DataFrame
            df = pd.DataFrame(dataset['data'])
            
            # 数据基本信息
            dataset_info = {
                'sql_index': dataset['sql_index'],
                'sql': dataset['sql'],
                'shape': df.shape,
                'columns': list(df.columns),
                'data_types': {col: str(dtype) for col, dtype in df.dtypes.to_dict().items()},
                'summary_stats': {}
            }
            
            # 生成数据摘要统计
            try:
                # 数值型数据统计
                numeric_cols = df.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 0:
                    numeric_stats = df[numeric_cols].describe().to_dict()
                    # 确保所有数值都能序列化为JSON
                    dataset_info['summary_stats']['numeric'] = {
                        col: {stat: float(val) if pd.notna(val) else None 
                              for stat, val in stats.items()} 
                        for col, stats in numeric_stats.items()
                    }
                
                # 分类型数据统计 - 修复序列化问题
                categorical_cols = df.select_dtypes(include=['object', 'category']).columns
                if len(categorical_cols) > 0:
                    dataset_info['summary_stats']['categorical'] = {}
                    for col in categorical_cols:
                        value_counts = df[col].value_counts().head(10)
                        # 确保键值都是可序列化的
                        top_values = {}
                        for key, value in value_counts.items():
                            # 处理键
                            serialized_key = serialize_value(key)
                            # 处理值
                            serialized_value = serialize_value(value)
                            top_values[serialized_key] = serialized_value
                        
                        dataset_info['summary_stats']['categorical'][col] = {
                            'unique_count': int(df[col].nunique()),
                            'top_values': top_values
                        }
                
                # 将前10行数据转换为字典格式供LLM分析
                sample_data = df.head(10).to_dict('records')
                # 确保所有数据都能序列化为JSON
                dataset_info['sample_data'] = [
                    {k: serialize_value(v) for k, v in record.items()} 
                    for record in sample_data
                ]
                
                # 如果数据包含时间相关字段，进行时间序列分析
                date_cols = df.select_dtypes(include=['datetime64']).columns
                if len(date_cols) > 0:
                    dataset_info['time_analysis'] = {}
                    for col in date_cols:
                        dataset_info['time_analysis'][col] = {
                            'date_range': [str(df[col].min()), str(df[col].max())],
                            'date_count': df[col].nunique()
                        }
                
            except Exception as e:
                logger.warning(f"生成统计信息时发生错误: {str(e)}")
            
            processed_datasets.append(dataset_info)
        
        # 将处理后的数据转换为JSON字符串 - 完善json_serializer
        def json_serializer(obj):
            """自定义JSON序列化器"""
            if pd.isna(obj):
                return None
            elif isinstance(obj, (pd.Timestamp, pd.Timedelta)):
                return str(obj)
            elif hasattr(obj, 'item'):  # numpy数据类型
                return obj.item()
            elif isinstance(obj, Decimal):  # 添加Decimal类型处理
                return float(obj)
            elif isinstance(obj, (date, datetime)):  # 添加date和datetime类型处理
                return str(obj)
            else:
                return str(obj)
        
        state.processed_data = json.dumps(processed_datasets, ensure_ascii=False, indent=2, default=json_serializer)
        
        logger.info(f"数据处理完成，共处理 {len(processed_datasets)} 个数据集")
        return state
        
    except Exception as e:
        error_msg = f"处理数据时发生异常: {str(e)}"
        logger.error(error_msg)
        state.error_message = error_msg
        return state

async def generate_analysis_report(state: DataAnalysisState) -> DataAnalysisState:
    """生成财务分析报告"""
    try:
        logger.info("开始生成财务分析报告")
        
        system_prompt ="""
你是一位资深的财务专家，具备卓越的财务分析和沟通能力。 你的任务是严格根据用户的问题以及提供的参考资料，提供准确、客观、专业的财务解答、分析、建议和风险提示。 参考资料的数据均为实际财务数值，单位自动判断。你的分析必须完全基于参考资料中的数据，不得自行补充或假设数据。

**行为准则:**

*  *   **客观公正:** 保持客观、公正的立场，避免带有个人偏见。
*   **避免过度解读:**  不要过度解读数据，避免提出没有依据的推测和主观臆断。  所有分析和结论必须有明确的数据支持。
*   **专业术语:**  使用规范、标准的财务专业术语。
*   **简洁明了:** 在回复中突出重点，避免使用过于复杂的语言和冗长的句子。 使用清晰的段落和列表来组织信息。
*   **无法解答的处理:** 如果用户的问题无法用参考资料中的数据直接回答，请礼貌地说明情况，并尝试提供其他可能的分析方向或信息来源。  不要捏造数据。

**输出要求:**

*   **回复示例:** **（务必按照以下示例结构和格式输出，不得缺失任何部分。每个分析步骤 (数据解读、趋势分析等) 必须以 明确的标题开头，例如 '数据解读:'。 标题必须与示例中的完全一致。数据解读必须使用列表形式呈现，每条数据占据一个列表项。）**

    用户问题： "请分析一下2023年和2024年Q1的销售数据。"
    参考资料：
    2023年Q1 销售额：800000元
    2023年Q1 销售成本：500000元
    2024年Q1 销售额：1200000元
    2024年Q1 销售成本：700000元
    回复：

    "根据参考资料，2023年Q1的销售额为800000元，销售成本为500000元； 2024年Q1的销售额为1200000元，销售成本为700000元。

    *   **数据解读:**
        *   2023年Q1销售额800000元意味着该季度通过销售产品或服务获得的收入总额为800000元。单位：元。
        *   销售成本500000元是指与销售这些产品或服务直接相关的成本，例如原材料、人工等。单位：元。

    *   **趋势分析:** 2024年Q1销售额相比2023年Q1增长了50% ( (1200000-800000)/800000 = 0.5 )，这是一个显著的增长。 这可能得益于市场推广活动的成功，或者产品/服务更受市场欢迎。

    *   **对比分析:** 2024年Q1销售成本也相应增长了40% ((700000-500000)/500000 = 0.4)。 虽然销售额增长更快，但仍需要关注成本控制。

    *   **财务建议:**  建议继续保持和优化当前的市场推广策略，以维持销售增长的势头。 同时，需要密切关注销售成本的变化，分析成本增长的原因，并采取措施控制成本。

    *   **风险提示:** 虽然销售额大幅增长，但销售成本的增长也比较明显。如果销售成本持续以高于销售额增长率的速度增长，可能会侵蚀利润空间，影响盈利能力。 需要定期审查成本结构，找出可以降低成本的环节。

原始查询：{query}

数据分析结果：
{processed_data}

请基于以上数据生成详细的财务分析报告。
        """
        
        # 使用LLM生成分析报告
        chain = await llm.create_json_chain(system_prompt)
        report = await chain.ainvoke({"query": state.query,"processed_data":state.processed_data})
        
        state.analysis_report = report
        
        logger.info("财务分析报告生成完成")
        return state
        
    except Exception as e:
        error_msg = f"生成分析报告时发生异常: {str(e)}"
        logger.error(error_msg)
        state.error_message = error_msg
        return state

def check_error(state: DataAnalysisState) -> str:
    """检查是否有错误"""
    if state.error_message:
        return "error"
    else:
        return "continue"

async def handle_error(state: DataAnalysisState) -> DataAnalysisState:
    """处理错误情况"""
    logger.error(f"工作流执行失败: {state.error_message}")
    return state

# 构建数据分析工作流
data_workflow = StateGraph(DataAnalysisState)

# 添加节点
data_workflow.add_node('execute_sql', execute_sql_queries)
data_workflow.add_node('process_data', process_data_with_pandas)
data_workflow.add_node('generate_report', generate_analysis_report)
data_workflow.add_node('handle_error', handle_error)

# 添加边
data_workflow.add_edge(START, 'execute_sql')
data_workflow.add_conditional_edges(
    'execute_sql',
    check_error,
    {'error': 'handle_error', 'continue': 'process_data'}
)
data_workflow.add_conditional_edges(
    'process_data',
    check_error,
    {'error': 'handle_error', 'continue': 'generate_report'}
)
data_workflow.add_edge('generate_report', END)
data_workflow.add_edge('handle_error', END)

# 编译工作流
compiled_data_workflow = data_workflow.compile()

class SQL2DataWorkflow(BaseWorkflow):
    """SQL到数据分析报告的完整工作流"""
    
    async def execute_async(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行完整的工作流：NL2SQL -> 数据查询 -> 数据处理 -> 分析报告生成
        
        Args:
            inputs: 输入参数（可选）
            
        Returns:
            包含分析报告和相关数据的字典
        """
        try:
            logger.info(f"开始执行SQL2Data工作流，用户查询: {inputs['query']}")
            
            # 第一步：使用NL2SQL工作流生成SQL
            nl2sql_workflow = NL2SQLWorkflow()
            nl2sql_result = await nl2sql_workflow.execute_async(inputs)
            
            if not nl2sql_result['sql'] or len(nl2sql_result['sql']) == 0:
                return {
                    'success': False,
                    'error': '未能生成有效的SQL语句',
                    'query': inputs['query']
                }
            
            logger.info(f"NL2SQL生成了 {len(nl2sql_result['sql'])} 个SQL语句")
            
            # 第二步：执行数据分析工作流
            initial_state = DataAnalysisState(
                query=inputs['query'],
                sql_list=nl2sql_result['sql']
            )
            
            result = await compiled_data_workflow.ainvoke(initial_state)
            
            # 构建返回结果 - 修复：使用字典访问，因为LangGraph返回的是AddableValuesDict
            if result.get('error_message'):
                return {
                    'success': False,
                    'error': result.get('error_message'),
                    'query': inputs['query'],
                    'sql_list': result.get('sql_list', [])
                }
            else:
                return {
                    'success': True,
                    'query': inputs['query'],
                    'sql_list': result.get('sql_list', []),
                    'raw_data_count': len(result.get('raw_data', [])),
                    'processed_data': result.get('processed_data'),
                    'analysis_report': result.get('analysis_report')
                }
                
        except Exception as e:
            error_msg = f"SQL2Data工作流执行异常: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'query': inputs['query']
            }

# 便利函数：直接生成分析报告
async def generate_financial_analysis_report(user_query: str) -> Dict[str, Any]:
    """
    便利函数：从自然语言查询直接生成财务分析报告
    
    Args:
        user_query: 用户的自然语言查询
        
    Returns:
        包含分析报告的字典
    """
    workflow = SQL2DataWorkflow()
    return await workflow.execute_async({"query": user_query})

if __name__ == "__main__":
    # 测试工作流
    async def test_workflow():
        query = "请分析国际渠道事业群2024年的费用表的情况"
        result = await generate_financial_analysis_report(query)
        print("="*50)
        print("工作流执行结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        if result.get('success') and result.get('analysis_report'):
            print("\n" + "="*50)
            print("财务分析报告:")
            print(result['analysis_report'])
    
    # 运行测试
    asyncio.run(test_workflow())
