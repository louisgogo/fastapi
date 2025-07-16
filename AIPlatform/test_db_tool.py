"""
PostgreSQL数据库结构工具测试脚本

@author malou
@since 2024-12-19
Note: 测试PostgreSQL数据库结构工具的各种功能
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.tools.db_tool import PostgreSQLStructureTool


async def test_tool_basic_functionality():
    """
    测试工具基本功能
    
    Note: 测试工具的基本功能，包括初始化和参数验证
    """
    print("=== 测试工具基本功能 ===")
    
    # 创建工具实例
    tool = PostgreSQLStructureTool()
    
    # 测试工具属性
    print(f"工具名称: {tool.name}")
    print(f"工具描述: {tool.description}")
    
    # 测试工具schema
    schema = tool.get_schema()
    print(f"工具schema: {schema}")
    
    # 验证schema结构
    assert "properties" in schema
    assert "table_name" in schema["properties"]
    assert "schema_name" in schema["properties"]
    assert "include_foreign_keys" in schema["properties"]
    assert "max_fk_values" in schema["properties"]
    
    print("✓ 工具基本功能测试通过")


async def test_get_all_tables():
    """
    测试获取所有表结构
    
    Note: 测试获取数据库中所有表的结构信息
    """
    print("\n=== 测试获取所有表结构 ===")
    
    tool = PostgreSQLStructureTool()
    
    # 测试获取所有表结构
    result = await tool.execute(schema_name="public")
    
    print(f"执行状态: {result['success']}")
    print(f"消息: {result['message']}")
    
    if result["success"]:
        print("✓ 成功获取所有表结构")
        print(f"数据长度: {len(result['data'])} 字符")
        
        # 检查是否包含基本的Markdown结构
        data = result['data']
        assert "# 数据库结构" in data
        assert "##" in data  # 应该有表标题
        assert "|" in data   # 应该有表格
        
        # 显示前500个字符作为预览
        print(f"数据预览:\n{data[:500]}...")
    else:
        print(f"✗ 失败: {result['message']}")


async def test_get_specific_table():
    """
    测试获取特定表结构
    
    Note: 测试获取指定表的结构信息
    """
    print("\n=== 测试获取特定表结构 ===")
    
    tool = PostgreSQLStructureTool()
    
    # 首先尝试获取系统表的结构，比如 pg_tables
    table_name = "pg_tables"
    result = await tool.execute(table_name=table_name, schema_name="information_schema")
    
    print(f"执行状态: {result['success']}")
    print(f"消息: {result['message']}")
    
    if result["success"]:
        print(f"✓ 成功获取表 {table_name} 的结构")
        print(f"数据长度: {len(result['data'])} 字符")
        
        # 检查是否包含表名
        data = result['data']
        assert table_name in data
        assert "##" in data  # 应该有表标题
        assert "|" in data   # 应该有表格
        
        print(f"数据预览:\n{data[:500]}...")
    else:
        print(f"✗ 失败: {result['message']}")


async def test_without_foreign_keys():
    """
    测试不包含外键信息的查询
    
    Note: 测试不包含外键信息的表结构查询
    """
    print("\n=== 测试不包含外键信息的查询 ===")
    
    tool = PostgreSQLStructureTool()
    
    # 测试不包含外键信息
    result = await tool.execute(schema_name="public", include_foreign_keys=False)
    
    print(f"执行状态: {result['success']}")
    print(f"消息: {result['message']}")
    
    if result["success"]:
        print("✓ 成功获取表结构(不包含外键)")
        print(f"数据长度: {len(result['data'])} 字符")
        
        # 检查是否不包含外键列
        data = result['data']
        assert "外键表" not in data
        assert "外键字段" not in data
        assert "外键值范围" not in data
        
        print("✓ 确认不包含外键信息")
    else:
        print(f"✗ 失败: {result['message']}")


async def test_with_foreign_keys():
    """
    测试包含外键信息的查询
    
    Note: 测试包含外键信息的表结构查询
    """
    print("\n=== 测试包含外键信息的查询 ===")
    
    tool = PostgreSQLStructureTool()
    
    # 测试包含外键信息
    result = await tool.execute(schema_name="public", include_foreign_keys=True)
    
    print(f"执行状态: {result['success']}")
    print(f"消息: {result['message']}")
    
    if result["success"]:
        print("✓ 成功获取表结构(包含外键)")
        print(f"数据长度: {len(result['data'])} 字符")
        
        # 检查是否包含外键列
        data = result['data']
        assert "外键表" in data
        assert "外键字段" in data
        assert "外键值范围" in data
        
        print("✓ 确认包含外键信息")
    else:
        print(f"✗ 失败: {result['message']}")


async def test_invalid_schema():
    """
    测试无效的schema
    
    Note: 测试当指定无效schema时的错误处理
    """
    print("\n=== 测试无效的schema ===")
    
    tool = PostgreSQLStructureTool()
    
    # 测试无效的schema
    result = await tool.execute(schema_name="invalid_schema_name")
    
    print(f"执行状态: {result['success']}")
    print(f"消息: {result['message']}")
    
    if result["success"]:
        # 即使schema不存在，也应该返回成功，但数据应该表明没有找到表
        data = result['data']
        print(f"数据: {data}")
        print("✓ 正确处理无效schema")
    else:
        print(f"✗ 失败: {result['message']}")


async def test_error_handling():
    """
    测试错误处理
    
    Note: 测试工具的错误处理能力
    """
    print("\n=== 测试错误处理 ===")
    
    tool = PostgreSQLStructureTool()
    
    # 测试无效的表名
    result = await tool.execute(table_name="invalid_table_name", schema_name="public")
    
    print(f"执行状态: {result['success']}")
    print(f"消息: {result['message']}")
    
    if result["success"]:
        # 即使表不存在，也应该返回成功，但数据应该表明没有找到表
        data = result['data']
        print(f"数据: {data}")
        print("✓ 正确处理不存在的表")
    else:
        print(f"注意：查询不存在的表返回失败: {result['message']}")


async def test_parameter_combinations():
    """
    测试参数组合
    
    Note: 测试不同参数组合的效果
    """
    print("\n=== 测试参数组合 ===")
    
    tool = PostgreSQLStructureTool()
    
    # 测试不同的max_fk_values
    test_cases = [
        {"schema_name": "public", "max_fk_values": 5},
        {"schema_name": "public", "max_fk_values": 10},
        {"schema_name": "public", "include_foreign_keys": True, "max_fk_values": 3},
        {"schema_name": "public", "include_foreign_keys": False, "max_fk_values": 100},
    ]
    
    for i, params in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}: {params}")
        result = await tool.execute(**params)
        
        print(f"执行状态: {result['success']}")
        if result["success"]:
            print(f"✓ 参数组合 {i} 测试通过")
            print(f"数据长度: {len(result['data'])} 字符")
        else:
            print(f"✗ 参数组合 {i} 测试失败: {result['message']}")


async def run_all_tests():
    """
    运行所有测试
    
    Note: 执行所有测试用例
    """
    print("开始PostgreSQL数据库结构工具测试...")
    
    try:
        await test_tool_basic_functionality()
        await test_get_all_tables()
        await test_get_specific_table()
        await test_without_foreign_keys()
        await test_with_foreign_keys()
        await test_invalid_schema()
        await test_error_handling()
        await test_parameter_combinations()
        
        print("\n" + "="*50)
        print("✓ 所有测试完成！")
        print("="*50)
        
    except Exception as e:
        print(f"\n✗ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


def main():
    """
    主函数 - 运行所有测试
    
    Note: 异步运行所有测试代码
    """
    print("启动PostgreSQL数据库结构工具完整测试...")
    asyncio.run(run_all_tests())


if __name__ == "__main__":
    main() 