"""
工具模块测试

@author malou
@since 2025-01-08
Note: 工具模块功能测试，使用pytest框架
"""

import pytest
from unittest.mock import Mock, patch
from app.tools.registry import ToolRegistry
from app.tools.data_tool import SQLExtractionTool
from app.tools.base_tool import BaseTool


class TestToolRegistry:
    """测试工具注册中心"""

    @pytest.fixture
    def registry(self):
        """创建工具注册中心实例"""
        return ToolRegistry()

    def test_registry_initialization(self, registry):
        """测试注册中心初始化"""
        assert registry is not None
        tools = registry.list_tools()
        assert isinstance(tools, dict)
        assert len(tools) > 0

    def test_get_tool_success(self, registry):
        """测试成功获取工具"""
        sql_tool = registry.get_tool("sql_extraction")
        assert sql_tool is not None
        assert sql_tool.name == "sql_extraction"
        assert "SQL" in sql_tool.description

    def test_get_nonexistent_tool(self, registry):
        """测试获取不存在的工具"""
        tool = registry.get_tool("nonexistent_tool")
        assert tool is None

    def test_get_tool_schema_success(self, registry):
        """测试成功获取工具schema"""
        schema = registry.get_tool_schema("sql_extraction")
        assert schema is not None
        assert "properties" in schema
        assert "text" in schema["properties"]
        assert schema["properties"]["text"]["type"] == "string"

    def test_get_tool_schema_nonexistent(self, registry):
        """测试获取不存在工具的schema"""
        schema = registry.get_tool_schema("nonexistent_tool")
        assert schema is None

    def test_list_tools(self, registry):
        """测试列出所有工具"""
        tools = registry.list_tools()
        assert isinstance(tools, dict)
        assert len(tools) >= 1  # 至少有一个SQL提取工具
        
        # 验证工具的基本属性
        for name, tool in tools.items():
            assert isinstance(name, str)
            assert isinstance(tool, BaseTool)
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description')
            assert hasattr(tool, 'get_schema')

    def test_register_new_tool(self, registry):
        """测试注册新工具"""
        # 创建模拟工具
        mock_tool = Mock(spec=BaseTool)
        mock_tool.name = "test_tool"
        mock_tool.description = "测试工具"
        mock_tool.get_schema.return_value = {"type": "object"}
        
        # 注册工具
        registry.register(mock_tool)
        
        # 验证工具已注册
        retrieved_tool = registry.get_tool("test_tool")
        assert retrieved_tool is not None
        assert retrieved_tool.name == "test_tool"
        
        # 验证工具列表包含新工具
        tools = registry.list_tools()
        assert "test_tool" in tools

    def test_register_duplicate_tool(self, registry):
        """测试注册重复工具（应该覆盖）"""
        # 创建两个同名工具
        tool1 = Mock(spec=BaseTool)
        tool1.name = "duplicate_tool"
        tool1.description = "工具1"
        
        tool2 = Mock(spec=BaseTool)
        tool2.name = "duplicate_tool"
        tool2.description = "工具2"
        
        # 注册第一个工具
        registry.register(tool1)
        assert registry.get_tool("duplicate_tool").description == "工具1"
        
        # 注册第二个工具（应该覆盖第一个）
        registry.register(tool2)
        assert registry.get_tool("duplicate_tool").description == "工具2"


class TestSQLExtractionTool:
    """测试SQL提取工具"""

    @pytest.fixture
    def sql_tool(self):
        """创建SQL提取工具实例"""
        return SQLExtractionTool()

    def test_tool_initialization(self, sql_tool):
        """测试工具初始化"""
        assert sql_tool.name == "sql_extraction"
        assert "SQL" in sql_tool.description
        assert "提取" in sql_tool.description

    def test_get_schema(self, sql_tool):
        """测试获取工具schema"""
        schema = sql_tool.get_schema()
        assert schema is not None
        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "text" in schema["properties"]
        assert "required" in schema
        assert "text" in schema["required"]

    def test_execute_empty_input(self, sql_tool):
        """测试空输入"""
        result = sql_tool.execute("")
        assert result["success"] is False
        assert result["error"] == "输入文本为空"
        assert result["confidence"] == 0.0

    def test_execute_none_input(self, sql_tool):
        """测试None输入"""
        result = sql_tool.execute(None)
        assert result["success"] is False
        assert result["error"] == "输入文本为空"
        assert result["confidence"] == 0.0

    def test_extract_sql_from_code_block(self, sql_tool):
        """测试从代码块中提取SQL"""
        text = """
        这是一个查询用户的SQL：
        ```sql
        SELECT * FROM users WHERE status = 'active';
        ```
        """
        result = sql_tool.execute(text)
        assert result["success"] is True
        assert "SELECT * FROM users" in result["extracted_sql"]
        assert result["is_valid"] is True
        assert result["confidence"] > 0.0

    def test_extract_sql_from_text(self, sql_tool):
        """测试从文本中提取SQL"""
        text = "SELECT name, email FROM users WHERE department = 'IT'"
        result = sql_tool.execute(text)
        assert result["success"] is True
        assert "SELECT name, email" in result["extracted_sql"]
        assert result["is_valid"] is True

    def test_extract_sql_no_sql_found(self, sql_tool):
        """测试没有找到SQL的情况"""
        text = "这是一段普通文本，没有SQL语句"
        result = sql_tool.execute(text)
        assert result["success"] is False
        assert "未找到有效的SQL语句" in result["error"]
        assert result["confidence"] == 0.0

    def test_extract_sql_with_psql_block(self, sql_tool):
        """测试从psql代码块中提取SQL"""
        text = """
        使用PostgreSQL查询：
        ```psql
        SELECT id, name FROM employees WHERE salary > 5000;
        ```
        """
        result = sql_tool.execute(text)
        assert result["success"] is True
        assert "SELECT id, name FROM employees" in result["extracted_sql"]

    def test_extract_sql_with_generic_block(self, sql_tool):
        """测试从通用代码块中提取SQL"""
        text = """
        ```
        SELECT COUNT(*) FROM orders WHERE order_date >= '2024-01-01';
        ```
        """
        result = sql_tool.execute(text)
        assert result["success"] is True
        assert "SELECT COUNT(*)" in result["extracted_sql"]

    def test_extract_sql_with_multiple_statements(self, sql_tool):
        """测试提取多个SQL语句"""
        text = """
        ```sql
        SELECT * FROM users;
        SELECT * FROM orders;
        ```
        """
        result = sql_tool.execute(text)
        assert result["success"] is True
        # 应该返回第一个SQL语句
        assert "SELECT * FROM users" in result["extracted_sql"]

    def test_extract_sql_with_complex_query(self, sql_tool):
        """测试复杂SQL查询提取"""
        text = """
        ```sql
        SELECT u.name, u.email, COUNT(o.id) as order_count
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id
        WHERE u.status = 'active'
        GROUP BY u.id, u.name, u.email
        HAVING COUNT(o.id) > 5
        ORDER BY order_count DESC;
        ```
        """
        result = sql_tool.execute(text)
        assert result["success"] is True
        assert "SELECT u.name" in result["extracted_sql"]
        assert "LEFT JOIN" in result["extracted_sql"]
        assert "GROUP BY" in result["extracted_sql"]

    def test_extract_sql_with_insert_statement(self, sql_tool):
        """测试INSERT语句提取"""
        text = "INSERT INTO users (name, email) VALUES ('John', 'john@example.com')"
        result = sql_tool.execute(text)
        assert result["success"] is True
        assert "INSERT INTO users" in result["extracted_sql"]

    def test_extract_sql_with_update_statement(self, sql_tool):
        """测试UPDATE语句提取"""
        text = "UPDATE users SET status = 'inactive' WHERE last_login < '2023-01-01'"
        result = sql_tool.execute(text)
        assert result["success"] is True
        assert "UPDATE users" in result["extracted_sql"]

    def test_extract_sql_with_delete_statement(self, sql_tool):
        """测试DELETE语句提取"""
        text = "DELETE FROM users WHERE status = 'deleted'"
        result = sql_tool.execute(text)
        assert result["success"] is True
        assert "DELETE FROM users" in result["extracted_sql"]

    def test_execute_with_exception(self, sql_tool):
        """测试异常处理"""
        # 使用mock来模拟异常
        with patch.object(sql_tool, '_extract_sql_from_text', side_effect=Exception("测试异常")):
            result = sql_tool.execute("SELECT * FROM users")
            assert result["success"] is False
            assert "提取过程中发生错误" in result["error"]
            assert result["confidence"] == 0.0


class TestToolIntegration:
    """测试工具集成"""

    @pytest.fixture
    def registry_with_tools(self):
        """创建包含工具的注册中心"""
        registry = ToolRegistry()
        # 注册表默认已经包含SQL提取工具
        return registry

    def test_tool_registry_integration(self, registry_with_tools):
        """测试工具注册中心集成"""
        # 验证注册中心包含工具
        tools = registry_with_tools.list_tools()
        assert len(tools) > 0
        
        # 验证可以获取SQL工具
        sql_tool = registry_with_tools.get_tool("sql_extraction")
        assert sql_tool is not None
        
        # 验证工具可以执行
        result = sql_tool.execute("SELECT * FROM test")
        assert isinstance(result, dict)
        assert "success" in result

    def test_tool_execution_workflow(self, registry_with_tools):
        """测试工具执行工作流"""
        # 获取工具
        tool_name = "sql_extraction"
        tool = registry_with_tools.get_tool(tool_name)
        assert tool is not None
        
        # 获取工具schema
        schema = registry_with_tools.get_tool_schema(tool_name)
        assert schema is not None
        
        # 执行工具
        test_input = "SELECT id, name FROM users WHERE active = true"
        result = tool.execute(test_input)
        
        # 验证结果
        assert result["success"] is True
        assert "extracted_sql" in result
        assert result["is_valid"] is True


@pytest.mark.parametrize("input_text,expected_success", [
    ("SELECT * FROM users", True),
    ("", False),
    ("这是一段普通文本", False),
    ("INSERT INTO users (name) VALUES ('test')", True),
    ("UPDATE users SET status = 'active'", True),
    ("DELETE FROM users WHERE id = 1", True),
])
def test_sql_extraction_parametrized(input_text, expected_success):
    """
    参数化测试SQL提取功能
    
    @param input_text str 输入文本
    @param expected_success bool 期望的成功状态
    Note: 使用参数化测试多种输入情况
    """
    tool = SQLExtractionTool()
    result = tool.execute(input_text)
    assert result["success"] == expected_success