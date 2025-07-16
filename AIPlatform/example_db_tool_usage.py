"""
PostgreSQL数据库结构工具使用示例

@author malou
@since 2024-12-19
Note: 展示如何使用PostgreSQL数据库结构工具的各种功能
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.tools.db_tool import PostgreSQLStructureTool


async def example_basic_usage():
    """
    基本使用示例
    
    Note: 演示工具的基本用法
    """
    print("=== PostgreSQL数据库结构工具基本使用示例 ===\n")
    
    # 创建工具实例
    tool = PostgreSQLStructureTool()
    
    print("1. 获取所有表结构:")
    print("-" * 40)
    
    # 获取public schema中的所有表结构
    result = await tool.execute(schema_name="public")
    
    if result["success"]:
        print("✓ 成功获取所有表结构")
        print(f"数据长度: {len(result['data'])} 字符")
        
        # 将结果保存到文件
        with open("database_structure.md", "w", encoding="utf-8") as f:
            f.write(result['data'])
        print("✓ 结果已保存到 database_structure.md")
    else:
        print(f"✗ 失败: {result['message']}")


async def example_specific_table():
    """
    获取特定表结构示例
    
    Note: 演示如何获取特定表的结构
    """
    print("\n2. 获取特定表结构:")
    print("-" * 40)
    
    tool = PostgreSQLStructureTool()
    
    # 假设有一个名为users的表
    table_name = "users"
    result = await tool.execute(table_name=table_name, schema_name="public")
    
    if result["success"]:
        print(f"✓ 成功获取表 {table_name} 的结构")
        print(f"结构信息:\n{result['data']}")
    else:
        print(f"✗ 失败: {result['message']}")
        print("注意：如果表不存在，会返回失败")


async def example_without_foreign_keys():
    """
    不包含外键信息的示例
    
    Note: 演示如何获取不包含外键信息的表结构
    """
    print("\n3. 获取表结构(不包含外键信息):")
    print("-" * 40)
    
    tool = PostgreSQLStructureTool()
    
    # 获取表结构但不包含外键信息
    result = await tool.execute(
        schema_name="public", 
        include_foreign_keys=False
    )
    
    if result["success"]:
        print("✓ 成功获取表结构(不包含外键)")
        print(f"数据长度: {len(result['data'])} 字符")
        
        # 将结果保存到文件
        with open("database_structure_no_fk.md", "w", encoding="utf-8") as f:
            f.write(result['data'])
        print("✓ 结果已保存到 database_structure_no_fk.md")
    else:
        print(f"✗ 失败: {result['message']}")


async def example_custom_parameters():
    """
    自定义参数示例
    
    Note: 演示如何使用自定义参数
    """
    print("\n4. 使用自定义参数:")
    print("-" * 40)
    
    tool = PostgreSQLStructureTool()
    
    # 使用自定义参数
    result = await tool.execute(
        schema_name="public",
        include_foreign_keys=True,
        max_fk_values=5  # 限制外键值范围显示数量
    )
    
    if result["success"]:
        print("✓ 成功使用自定义参数获取表结构")
        print(f"数据长度: {len(result['data'])} 字符")
        print("✓ 外键值范围限制为最多5个")
    else:
        print(f"✗ 失败: {result['message']}")


async def example_different_schema():
    """
    不同schema示例
    
    Note: 演示如何获取不同schema的表结构
    """
    print("\n5. 获取不同schema的表结构:")
    print("-" * 40)
    
    tool = PostgreSQLStructureTool()
    
    # 获取information_schema的表结构
    result = await tool.execute(schema_name="information_schema")
    
    if result["success"]:
        print("✓ 成功获取information_schema的表结构")
        print(f"数据长度: {len(result['data'])} 字符")
        
        # 显示前500个字符
        print(f"数据预览:\n{result['data'][:500]}...")
    else:
        print(f"✗ 失败: {result['message']}")


async def example_error_handling():
    """
    错误处理示例
    
    Note: 演示工具的错误处理能力
    """
    print("\n6. 错误处理示例:")
    print("-" * 40)
    
    tool = PostgreSQLStructureTool()
    
    # 测试不存在的schema
    result = await tool.execute(schema_name="non_existing_schema")
    
    print(f"测试不存在的schema: {result['success']}")
    print(f"消息: {result['message']}")
    
    # 测试不存在的表
    result = await tool.execute(
        table_name="non_existing_table", 
        schema_name="public"
    )
    
    print(f"测试不存在的表: {result['success']}")
    print(f"消息: {result['message']}")


def display_tool_info():
    """
    显示工具信息
    
    Note: 展示工具的基本信息和schema
    """
    print("\n7. 工具信息:")
    print("-" * 40)
    
    tool = PostgreSQLStructureTool()
    
    print(f"工具名称: {tool.name}")
    print(f"工具描述: {tool.description}")
    
    schema = tool.get_schema()
    print(f"支持的参数:")
    for param, info in schema.get("properties", {}).items():
        print(f"  - {param}: {info.get('description', '无描述')}")
        if "default" in info:
            print(f"    默认值: {info['default']}")


async def main():
    """
    主函数 - 运行所有示例
    
    Note: 异步运行所有示例代码
    """
    print("PostgreSQL数据库结构工具使用示例")
    print("=" * 50)
    
    try:
        # 显示工具信息
        display_tool_info()
        
        # 运行异步示例
        await example_basic_usage()
        await example_specific_table()
        await example_without_foreign_keys()
        await example_custom_parameters()
        await example_different_schema()
        await example_error_handling()
        
        print("\n" + "="*50)
        print("✓ 所有示例运行完成！")
        print("✓ 生成的Markdown文件:")
        print("  - database_structure.md (包含外键信息)")
        print("  - database_structure_no_fk.md (不包含外键信息)")
        print("="*50)
        
    except Exception as e:
        print(f"\n✗ 运行示例时发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 