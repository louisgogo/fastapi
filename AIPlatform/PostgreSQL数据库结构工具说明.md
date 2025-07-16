# PostgreSQL数据库结构工具说明

## 概述

PostgreSQL数据库结构工具是一个专门用于获取PostgreSQL数据库表结构信息的工具类，能够将数据库结构信息整理为Markdown格式，方便文档化和分析。

## 主要功能

- ✅ **获取所有表结构**：获取指定schema中所有表的结构信息
- ✅ **获取单个表结构**：获取指定表的详细结构信息
- ✅ **外键信息支持**：可选择包含或不包含外键信息
- ✅ **外键值范围展示**：显示外键字段的值范围
- ✅ **多schema支持**：支持不同schema的查询
- ✅ **Markdown格式输出**：结构化的Markdown表格格式
- ✅ **异步支持**：完整的异步操作支持
- ✅ **错误处理**：完善的错误处理和日志记录

## 技术特点

- 基于SQLAlchemy异步引擎
- 专门针对PostgreSQL优化
- 使用information_schema标准视图
- 支持自定义参数配置
- 完整的类型提示

## 文件结构

```
AIPlatform/
├── app/tools/db_tool.py              # 主工具类
├── test_db_tool.py                   # 完整测试脚本
├── example_db_tool_usage.py          # 使用示例
└── PostgreSQL数据库结构工具说明.md    # 本说明文件
```

## 类结构

### PostgreSQLStructureTool

继承自`BaseTool`，提供以下主要方法：

#### `__init__()`
初始化工具实例

#### `execute(**kwargs) -> Dict[str, Any]`
执行数据库结构获取操作

**参数：**
- `table_name` (str, 可选): 指定表名，不指定则查询所有表
- `schema_name` (str, 可选): 指定schema名称，默认为"public"
- `include_foreign_keys` (bool, 可选): 是否包含外键信息，默认为True
- `max_fk_values` (int, 可选): 外键值最大显示数量，默认为30

**返回值：**
```python
{
    "success": bool,        # 是否成功
    "data": str,           # Markdown格式的表结构
    "message": str         # 执行消息
}
```

#### `get_schema() -> Dict[str, Any]`
获取工具参数schema定义

## 使用方法

### 基本使用

```python
from app.tools.db_tool import PostgreSQLStructureTool

# 创建工具实例
tool = PostgreSQLStructureTool()

# 获取所有表结构
result = await tool.execute(schema_name="public")

if result["success"]:
    print(result["data"])  # 输出Markdown格式的表结构
else:
    print(f"错误: {result['message']}")
```

### 获取特定表结构

```python
# 获取users表的结构
result = await tool.execute(
    table_name="users", 
    schema_name="public"
)
```

### 不包含外键信息

```python
# 获取表结构但不包含外键信息
result = await tool.execute(
    schema_name="public", 
    include_foreign_keys=False
)
```

### 自定义参数

```python
# 使用自定义参数
result = await tool.execute(
    schema_name="public",
    include_foreign_keys=True,
    max_fk_values=5  # 限制外键值范围显示数量
)
```

## 输出格式

### 包含外键信息的表格

```markdown
## users

| 字段名 | 数据类型 | 是否可空 | 默认值 | 约束 | 注释 | 外键表 | 外键字段 | 外键值范围 |
|--------|----------|----------|--------|------|------|--------|----------|----------|
| id | integer | 否 | nextval('users_id_seq'::regclass) | PK | 用户ID | - | - | - |
| name | varchar(100) | 否 | - | - | 用户名 | - | - | - |
| role_id | integer | 是 | - | FK | 角色ID | public.roles | id | 1, 2, 3 |
```

### 不包含外键信息的表格

```markdown
## users

| 字段名 | 数据类型 | 是否可空 | 默认值 | 约束 | 注释 |
|--------|----------|----------|--------|------|------|
| id | integer | 否 | nextval('users_id_seq'::regclass) | PK | 用户ID |
| name | varchar(100) | 否 | - | - | 用户名 |
| role_id | integer | 是 | - | FK | 角色ID |
```

## 运行测试

### 运行完整测试

```bash
cd AIPlatform
python test_db_tool.py
```

### 运行使用示例

```bash
cd AIPlatform
python example_db_tool_usage.py
```

### 运行内置测试

```bash
cd AIPlatform
python -m app.tools.db_tool
```

## 测试覆盖

测试脚本包含以下测试用例：

1. **基本功能测试**：验证工具初始化和schema
2. **获取所有表结构**：测试获取schema中所有表
3. **获取特定表结构**：测试获取单个表结构
4. **不包含外键信息**：测试不包含外键的查询
5. **包含外键信息**：测试包含外键的查询
6. **无效schema测试**：测试错误处理能力
7. **错误处理测试**：测试异常情况处理
8. **参数组合测试**：测试不同参数组合

## 依赖项

- SQLAlchemy (异步支持)
- PostgreSQL数据库
- asyncpg (PostgreSQL异步驱动)
- Python 3.7+

## 配置要求

工具使用项目的数据库配置，确保以下配置正确：

```python
# app/core/config.py
DATABASE_URL = "postgresql+psycopg2://user:password@localhost:5432/dbname"
ASYNC_DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/dbname"
```

## 错误处理

工具提供完善的错误处理：

- **数据库连接错误**：返回连接失败信息
- **权限错误**：返回权限不足信息
- **表不存在**：返回适当的提示信息
- **Schema不存在**：返回空结果而非错误
- **SQL执行错误**：返回详细的错误信息

## 日志记录

工具使用项目的日志系统记录：

- 成功操作的信息日志
- 错误操作的错误日志
- 警告信息的警告日志

## 性能考虑

- 使用异步操作提高性能
- 合理限制外键值范围查询
- 使用高效的PostgreSQL系统视图
- 支持连接池管理

## 扩展性

工具设计具有良好的扩展性：

- 可以轻松添加新的输出格式
- 可以扩展支持更多数据库元数据
- 可以添加缓存机制
- 可以集成到更大的工具链中

## 注意事项

1. **权限要求**：需要对查询的schema有SELECT权限
2. **大表处理**：对于大表，外键值范围查询可能较慢
3. **网络延迟**：远程数据库可能存在网络延迟
4. **内存使用**：大量表的结构信息可能占用较多内存

## 许可证

本工具遵循项目的整体许可证。

## 作者

- malou
- 创建时间：2024-12-19

## 更新日志

### v1.0.0 (2024-12-19)
- 初始版本发布
- 支持PostgreSQL数据库结构获取
- 支持Markdown格式输出
- 完整的异步支持
- 完善的测试覆盖 