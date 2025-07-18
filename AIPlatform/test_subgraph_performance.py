"""
SubGraph 性能测试脚本

@author malou
@since 2025-01-08
Note: 测试子图服务的性能差异
"""

import asyncio
import time
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.subgraph_service import subgraph_service
from app.workflows.subgraph.base import State
from app.utils.logger import logger


async def test_performance():
    """
    测试子图服务的性能
    """
    try:
        logger.info("开始性能测试...")
        
        # 测试数据
        test_query = "请查询2025年1月的利润表和费用表"
        test_db_structure = """
        fact_profit表结构：
        - unique_lvl: 科目编码
        - amt: 金额
        - acct_period: 会计期间
        """
        test_sql = "SELECT unique_lvl, SUM(amt) FROM fact_profit WHERE DATE_PART('YEAR', acct_period) = 2025 GROUP BY unique_lvl LIMIT 5;"
        
        # 1. 测试查询拆分性能
        logger.info("1. 测试查询拆分性能")
        
        # 服务层调用
        start_time = time.time()
        result1 = await subgraph_service.execute_split_query(test_query)
        service_time = time.time() - start_time
        
        # 直接调用
        start_time = time.time()
        result2 = await subgraph_service.execute_split_query_direct(test_query)
        direct_time = time.time() - start_time
        
        logger.info(f"查询拆分 - 服务层调用: {service_time:.4f}秒")
        logger.info(f"查询拆分 - 直接调用: {direct_time:.4f}秒")
        logger.info(f"性能提升: {((service_time - direct_time) / service_time * 100):.2f}%")
        
        # 2. 测试SQL生成性能
        logger.info("2. 测试SQL生成性能")
        
        # 服务层调用
        start_time = time.time()
        result3 = await subgraph_service.execute_generate_sql(test_query, test_db_structure)
        service_time = time.time() - start_time
        
        # 直接调用
        start_time = time.time()
        result4 = await subgraph_service.execute_generate_sql_direct(test_query, test_db_structure)
        direct_time = time.time() - start_time
        
        logger.info(f"SQL生成 - 服务层调用: {service_time:.4f}秒")
        logger.info(f"SQL生成 - 直接调用: {direct_time:.4f}秒")
        logger.info(f"性能提升: {((service_time - direct_time) / service_time * 100):.2f}%")
        
        # 3. 测试数据获取性能
        logger.info("3. 测试数据获取性能")
        
        # 服务层调用
        start_time = time.time()
        result5 = await subgraph_service.execute_fetch_data(test_sql)
        service_time = time.time() - start_time
        
        # 直接调用
        start_time = time.time()
        result6 = await subgraph_service.execute_fetch_data_direct(test_sql)
        direct_time = time.time() - start_time
        
        logger.info(f"数据获取 - 服务层调用: {service_time:.4f}秒")
        logger.info(f"数据获取 - 直接调用: {direct_time:.4f}秒")
        logger.info(f"性能提升: {((service_time - direct_time) / service_time * 100):.2f}%")
        
        # 4. 测试重复调用性能（缓存效果）
        logger.info("4. 测试重复调用性能（缓存效果）")
        
        # 重复调用直接方法
        times = []
        for i in range(5):
            start_time = time.time()
            await subgraph_service.execute_split_query_direct(test_query)
            call_time = time.time() - start_time
            times.append(call_time)
            logger.info(f"第{i+1}次调用: {call_time:.4f}秒")
        
        avg_time = sum(times) / len(times)
        logger.info(f"平均调用时间: {avg_time:.4f}秒")
        logger.info(f"最快调用时间: {min(times):.4f}秒")
        logger.info(f"最慢调用时间: {max(times):.4f}秒")
        
        logger.info("性能测试完成！")
        
    except Exception as e:
        logger.error(f"性能测试过程中发生错误: {str(e)}")
        raise


async def test_memory_usage():
    """
    测试内存使用情况
    """
    try:
        logger.info("开始内存使用测试...")
        
        # 获取当前内存使用情况
        import psutil
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        logger.info(f"初始内存使用: {initial_memory:.2f} MB")
        
        # 执行多次调用
        test_query = "请查询2025年1月的利润表"
        for i in range(10):
            await subgraph_service.execute_split_query_direct(test_query)
            
            if i % 3 == 0:  # 每3次检查一次内存
                current_memory = process.memory_info().rss / 1024 / 1024
                logger.info(f"第{i+1}次调用后内存使用: {current_memory:.2f} MB")
        
        final_memory = process.memory_info().rss / 1024 / 1024
        logger.info(f"最终内存使用: {final_memory:.2f} MB")
        logger.info(f"内存增长: {final_memory - initial_memory:.2f} MB")
        
        logger.info("内存使用测试完成！")
        
    except ImportError:
        logger.warning("psutil未安装，跳过内存使用测试")
    except Exception as e:
        logger.error(f"内存使用测试过程中发生错误: {str(e)}")
        raise


async def main():
    """
    主测试函数
    """
    try:
        await test_performance()
        await test_memory_usage()
        
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 