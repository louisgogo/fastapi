from app.tools.db_tool import get_unique_lvl,validate_sql_query
from app.tools.data_tool import extract_json_from_text,extract_sql_from_text
from app.tools.db_tool import DatabaseSchemaTool

from langgraph.graph import StateGraph, START, END

from app.llms.factory import LLMFactory

from app.workflows.base_workflow import BaseWorkflow
from app.workflows.sql_workflow import SQLGenerationWorkflow

from pydantic import BaseModel, Field
from typing import Optional,Dict,Any
import json
import asyncio

llm=LLMFactory.create_ollama_llm()

class State(BaseModel):
    query: Optional[str] = Field(default=None, description="用户的问题")
    plan: list = Field(default_factory=list, description="问题的规划步骤")
    current_plan_idx:int= Field(default=0, description="当前规划步骤的索引")
    sql: list = Field(default_factory=list, description="执行的SQL语句")
    sql_error: Optional[str] = Field(default=None, description="SQL执行错误信息")
    db_struc: Optional[str] = Field(default=None, description="数据库结构")
    history: list = Field(default_factory=list, description="历史对话")

async def call_model(state:State):
    system_prompt = """
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

    chain = await llm.create_json_chain(system_prompt)
    text = await chain.ainvoke({"query":state.query})
    # 使用改进的JSON解析
    state.plan=extract_json_from_text(text)
    state.current_plan_idx = 0
    print('plan:',state.plan)
    return state

async def get_knowledge(state:State):
    # 判断用户的问题涉及那一张表，同时从知识库中返回表和字段相关信息
    system_prompt = """
你是一个智能的意图识别助手。 你的任务是分析用户输入的自然语言查询，并从中提取以下关键信息。
请严格按照以下 JSON 格式输出：

{{
  "intent_type": "[用户查询的主要目的，例如 "查询利润", "查询费用", "查询收入" 等。 如果是计算总和、平均值等，也请明确指出，例如 "计算总收入"]",
  "table_name": "[涉及的表格名称，必须在fact_profit，fact_revenue，fact_expense，其他中选择]
}}

请根据以上要求，分析以下用户查询，并提取关键信息:

用户查询：{plan}
    """
    chain = await llm.create_json_chain(system_prompt)
    text = await chain.ainvoke({"plan":state.plan[state.current_plan_idx]})
    print(f"LLM返回的原始文本: {text}")
    content = json.loads(text)['table_name']
    result=await DatabaseSchemaTool().execute_async(table_filter=content) 
    state.db_struc=result['markdown_content']
    return state

async def generate_sql(state:State):
    workflow = SQLGenerationWorkflow(llm, state.db_struc)
    result = await workflow.execute_async({"query": state.plan[state.current_plan_idx]})
    print(f"生成SQL: {result}")
    state.sql.append(result)
    return state

async def test_sql(state:State):
    sql = state.sql[-1]  # 获取最后生成的SQL
    resp_data = await validate_sql_query(sql)
    if 'valid' in resp_data and resp_data['valid'] == True:
        print("SQL测试通过")
        state.current_plan_idx += 1
        state.sql_error = None
    else:
        print("SQL测试失败")
        state.sql_error = resp_data['message']+"\nSQL语句："+sql
        state.sql.pop()
    return state

async def reflect(state:State):
    system_prompt = """
    你是一个智能助手，请结合用户上一次生成SQL的错误提示重新生成PSQL语句。
    
    错误提示和SQL语句：{sql_error}
    
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
    {query}
    数据库结构如下：
    {db_struc}
    唯一层级：unique_lvl的规则如下：
    {get_unique_lvl}
    """
    llm_chain = await llm.create_json_chain(system_prompt)
    raw_sql = await llm_chain.ainvoke({"query":state.plan[state.current_plan_idx],"sql_error":state.sql_error,"db_struc":state.db_struc,"get_unique_lvl":get_unique_lvl()})
    print(f"根据错误反馈生成的LLM: {raw_sql}")
    
    # 使用SQL提取工具提取完整的SQL语句
    extracted_sql =extract_sql_from_text(raw_sql) 
    if extracted_sql:
        print(f"提取并清理后的SQL: {extracted_sql}")
        state.sql.append(extracted_sql)
    else:
        print("警告：无法提取有效的SQL语句")
        # 如果提取失败，使用原始文本作为备选
        state.sql.append(raw_sql.strip())
    
    return state
  
def should_reflect(state:State):
    if state.sql_error is not None:
        return "reflect"
    else:
        return "next"
      
def should_next(state:State):
    if state.current_plan_idx < len(state.plan):
        return "get_knowledge"
    else:
        print('state:',state)
        return "end"

def next_node(state: State):
    # 只是一个占位节点，直接返回 state
    state.db_struc=None
    return state

# 构建工作流
workflow=StateGraph(State)
workflow.add_node('agent',call_model)
workflow.add_node('get_knowledge',get_knowledge)
workflow.add_node('generate_sql',generate_sql)
workflow.add_node('test',test_sql)
workflow.add_node('reflect',reflect)
workflow.add_node('next', next_node)

workflow.add_edge(START,'agent')
workflow.add_edge('agent','get_knowledge')
workflow.add_edge('get_knowledge','generate_sql')
workflow.add_edge('generate_sql','test')
workflow.add_conditional_edges('test',should_reflect,{'reflect':'reflect','next':'next'})
workflow.add_edge('reflect','test')
workflow.add_conditional_edges('next',should_next,{'get_knowledge':'get_knowledge','end':END})
compiled_graph=workflow.compile()


class NL2SQLWorkflow(BaseWorkflow): 
    async def execute_async(self,inputs:Dict[str,Any]):
        state=State(sql=[],sql_error=None, query=inputs['query'], plan=[],current_plan_idx=0,history=[])
        result = await compiled_graph.ainvoke(state)
        print("执行结果:", result) 
        return result


if __name__ == "__main__":
    # 测试工作流
    workflow=NL2SQLWorkflow()
    result=asyncio.run(workflow.execute_async({"query":"请导出能源事业中心25年1-4月的损益表数据，以EXCEL形式输出，分月列示"}))  