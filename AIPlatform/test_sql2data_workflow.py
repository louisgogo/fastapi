"""
SQL2Data工作流测试脚本

测试从自然语言查询到财务分析报告生成的完整流程

@author malou
@since 2025-01-08
"""

import asyncio
import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.tools.db_tool import execute_sql_query, validate_sql_query
from app.utils.logger import logger

async def test_database_connection():
    """测试数据库连接"""
    print("=" * 60)
    print("🔍 测试数据库连接...")
    
    try:
        # 测试简单查询
        test_query = "SELECT 1 as test_connection;"
        result = await execute_sql_query(test_query)
        
        if result.get('success'):
            print("✅ 数据库连接成功")
            print(f"   测试查询结果: {result.get('data')}")
            return True
        else:
            print("❌ 数据库连接失败")
            print(f"   错误信息: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ 数据库连接异常: {str(e)}")
        return False

async def test_sql_execution():
    """测试SQL执行"""
    print("=" * 60)
    print("🔄 测试SQL执行...")
    
    # 测试一些基本的SQL查询
    test_sqls = [
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' LIMIT 5;",
        "SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = 'public';"
    ]
    
    for i, sql in enumerate(test_sqls, 1):
        print(f"\n📝 测试SQL {i}: {sql}")
        
        try:
            result = await execute_sql_query(sql)
            
            if result.get('success'):
                print(f"✅ SQL执行成功")
                print(f"   返回行数: {result.get('row_count')}")
                print(f"   列名: {result.get('columns')}")
                data = result.get('data', [])
                if data:
                    print(f"   前3行数据: {data[:3]}")
            else:
                print(f"❌ SQL执行失败: {result.get('error')}")
                
        except Exception as e:
            print(f"❌ SQL执行异常: {str(e)}")

async def test_pandas_processing():
    """测试pandas数据处理"""
    print("=" * 60)
    print("🔄 测试pandas数据处理...")
    
    try:
        import pandas as pd
        
        # 获取一些测试数据
        test_sql = "SELECT table_name, table_type FROM information_schema.tables WHERE table_schema = 'public' LIMIT 10;"
        result = await execute_sql_query(test_sql)
        
        if result.get('success') and result.get('data'):
            # 创建DataFrame
            df = pd.DataFrame(result.get('data'))
            
            print(f"✅ 成功创建DataFrame")
            print(f"   数据形状: {df.shape}")
            print(f"   列名: {list(df.columns)}")
            print(f"   数据类型: {df.dtypes.to_dict()}")
            
            # 生成一些基本统计
            if len(df) > 0:
                print(f"   前5行数据:")
                print(df.head().to_string(index=False))
                
                # 测试数据转换为JSON
                json_data = df.to_dict('records')
                print(f"   转换为JSON格式: {len(json_data)} 条记录")
            
        else:
            print("❌ 无法获取测试数据进行pandas处理")
            
    except ImportError:
        print("❌ pandas包未安装")
    except Exception as e:
        print(f"❌ pandas数据处理异常: {str(e)}")

async def test_financial_analysis_api():
    """测试财务分析API"""
    print("=" * 60)
    print("🚀 测试财务分析功能...")
    
    try:
        from app.workflows.langgraph.sql2data import generate_financial_analysis_report
        
        # 使用简单的查询进行测试
        test_query = "查询系统中有哪些数据表"
        
        print(f"📝 测试查询: {test_query}")
        
        result = await generate_financial_analysis_report(test_query)
        
        print(f"📊 工作流执行结果:")
        print(f"   成功状态: {result.get('success')}")
        
        if result.get('success'):
            print(f"   查询语句: {result.get('query')}")
            
            sql_list = result.get('sql_list', [])
            if sql_list:
                print(f"   生成SQL数量: {len(sql_list)}")
                for i, sql in enumerate(sql_list, 1):
                    print(f"     SQL {i}: {sql[:100]}...")
            
            # 检查分析报告
            report = result.get('analysis_report')
            if report:
                print(f"\n📋 生成的分析报告:")
                print("   " + "=" * 50)
                print(f"   {report[:500]}...")  # 只显示前500个字符
                print("   " + "=" * 50)
            else:
                print("   ⚠️  未生成分析报告")
                
        else:
            print(f"   ❌ 工作流执行失败: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 财务分析功能异常: {str(e)}")

async def test_manual_data_workflow():
    """测试手动数据工作流"""
    print("=" * 60)
    print("🔧 测试手动数据工作流...")
    
    try:
        from app.workflows.langgraph.sql2data import DataAnalysisState, compiled_data_workflow
        
        # 创建一个手动SQL测试
        manual_sql = "SELECT table_name, table_type FROM information_schema.tables WHERE table_schema = 'public' LIMIT 5;"
        
        initial_state = DataAnalysisState(
            query="手动测试查询：获取数据库表信息",
            sql_list=[manual_sql]
        )
        
        result = await compiled_data_workflow.ainvoke(initial_state)
        
        print(f"📊 手动数据工作流执行结果:")
        
        error_msg = getattr(result, 'error_message', None)
        if error_msg:
            print(f"   ❌ 执行失败: {error_msg}")
        else:
            print(f"   ✅ 执行成功")
            
            query = getattr(result, 'query', '未知')
            sql_list = getattr(result, 'sql_list', [])
            raw_data = getattr(result, 'raw_data', [])
            
            print(f"   查询语句: {query}")
            print(f"   SQL语句: {sql_list}")
            print(f"   数据集数量: {len(raw_data)}")
            
            processed_data = getattr(result, 'processed_data', None)
            if processed_data:
                print(f"   ✅ 数据处理完成")
                try:
                    processed = json.loads(processed_data)
                    print(f"   处理后的数据集数量: {len(processed)}")
                except:
                    print(f"   数据处理结果: {processed_data[:200]}...")
            
            analysis_report = getattr(result, 'analysis_report', None)
            if analysis_report:
                print(f"\n📋 生成的分析报告:")
                print("   " + "=" * 50)
                print(f"   {analysis_report[:500]}...")  # 只显示前500个字符
                print("   " + "=" * 50)
                
    except Exception as e:
        print(f"❌ 手动数据工作流异常: {str(e)}")

async def main():
    """主测试函数"""
    print("🚀 SQL2Data工作流测试开始")
    print("=" * 60)
    
    # 1. 测试数据库连接
    db_ok = await test_database_connection()
    if not db_ok:
        print("❌ 数据库连接失败，终止测试")
        return
    
    # 2. 测试SQL执行
    await test_sql_execution()
    
    # 3. 测试pandas数据处理
    await test_pandas_processing()
    
    # 4. 测试手动数据工作流
    await test_manual_data_workflow()
    
    # 5. 测试财务分析API
    await test_financial_analysis_api()
    
    print("=" * 60)
    print("✅ SQL2Data工作流测试完成")

if __name__ == "__main__":
    # 运行测试
    asyncio.run(main()) 