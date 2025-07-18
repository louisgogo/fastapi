"""
测试SubGraph Service功能

@author malou
@since 2025-01-08
Note: 测试子图服务的各项功能
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.subgraph_service import subgraph_service
from app.workflows.subgraph.base import State
from app.utils.logger import logger


async def test_subgraph_service():
    """
    测试子图服务的各项功能
    """
    try:
        logger.info("开始测试SubGraph Service...")
        
        # 1. 测试列出所有子图
        logger.info("1. 测试列出所有子图")
        subgraphs = subgraph_service.list_subgraphs()
        logger.info(f"已注册的子图: {subgraphs}")
        
        # 2. 测试查询拆分子图
        logger.info("2. 测试查询拆分子图")
        query = "请查询2025年1月的利润表和费用表"
        result = await subgraph_service.execute_split_query(query)
        logger.info(f"查询拆分结果: {result.plan}")
        
        # 3. 测试SQL生成子图（需要数据库结构）
        logger.info("3. 测试SQL生成子图")
        db_structure = """
        fact_profit表结构：
        - unique_lvl: 科目编码
        - amt: 金额
        - acct_period: 会计期间
        """
        sql_result = await subgraph_service.execute_generate_sql(
            "查询2025年1月的利润", 
            db_structure
        )
        logger.info(f"SQL生成结果: {sql_result.sql}")
        
        # 4. 测试数据获取子图
        logger.info("4. 测试数据获取子图")
        test_sql = "SELECT unique_lvl, SUM(amt) FROM fact_profit WHERE DATE_PART('YEAR', acct_period) = 2025 GROUP BY unique_lvl LIMIT 5;"
        data_result = await subgraph_service.execute_fetch_data(test_sql)
        logger.info(f"数据获取结果: 获取到 {len(data_result.raw_data)} 个查询结果")
        
        # 5. 测试获取子图信息
        logger.info("5. 测试获取子图信息")
        for subgraph_name in subgraphs:
            subgraph = subgraph_service.get_subgraph(subgraph_name)
            if subgraph:
                logger.info(f"子图 {subgraph_name} 类型: {type(subgraph).__name__}")
        
        logger.info("SubGraph Service测试完成！")
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")
        raise


async def test_subgraph_api():
    """
    测试子图API接口
    """
    try:
        logger.info("开始测试SubGraph API...")
        
        # 这里可以添加API测试代码
        # 例如使用httpx或requests库测试HTTP接口
        
        logger.info("SubGraph API测试完成！")
        
    except Exception as e:
        logger.error(f"API测试过程中发生错误: {str(e)}")
        raise


async def main():
    """
    主测试函数
    """
    try:
        await test_subgraph_service()
        await test_subgraph_api()
        
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 