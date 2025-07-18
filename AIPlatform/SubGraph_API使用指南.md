# SubGraph API 使用指南

## 概述

SubGraph API 提供了对 LANGGRAPH 子图的独立调用功能，允许您单独执行工作流中的各个子图组件。这对于调试、测试和灵活组合工作流非常有用。

## 基础信息

- **API 前缀**: `/api/v1/subgraphs`
- **认证**: 需要 API Key（通过 X-API-Key 头部）
- **内容类型**: `application/json`

## 可用的子图类型

1. **split_query**: 查询拆分子图 - 将复杂查询拆分为针对单张表的子查询
2. **generate_sql**: SQL生成子图 - 根据自然语言查询生成SQL语句
3. **fetch_data**: 数据获取子图 - 执行SQL查询并获取数据

## API 端点

### 1. 获取子图列表

**GET** `/api/v1/subgraphs/list`

获取所有已注册的子图列表。

**响应示例**:
```json
{
  "subgraphs": ["split_query", "generate_sql", "fetch_data"],
  "count": 3
}
```

### 2. 创建自定义子图

**POST** `/api/v1/subgraphs/create`

创建新的子图实例。

**请求体**:
```json
{
  "name": "my_split_query",
  "subgraph_type": "split_query",
  "model_name": "qwen3:32b"
}
```

**响应示例**:
```json
{
  "message": "SubGraph 'my_split_query' created successfully",
  "subgraph_name": "my_split_query",
  "subgraph_type": "split_query"
}
```

### 3. 执行子图

**POST** `/api/v1/subgraphs/{subgraph_name}/execute`

执行指定的子图。

**请求体**:
```json
{
  "query": "请查询2025年1月的利润表",
  "db_structure": "数据库结构信息（可选）",
  "sql": "SQL语句（可选）"
}
```

**响应示例**:
```json
{
  "subgraph_name": "split_query",
  "result": {
    "query": "请查询2025年1月的利润表",
    "plan": ["查询2025年1月的利润表"],
    "current_plan_idx": 0,
    "sql": [],
    "sql_error": null,
    "db_struc": null,
    "raw_data": [],
    "md": "",
    "history": []
  },
  "success": true,
  "error": ""
}
```

### 4. 流式执行子图

**POST** `/api/v1/subgraphs/{subgraph_name}/execute/stream`

流式执行指定的子图。

**响应**: Server-Sent Events (SSE) 格式

### 5. 删除子图

**DELETE** `/api/v1/subgraphs/{subgraph_name}`

删除指定的子图。

**响应示例**:
```json
{
  "message": "SubGraph 'my_split_query' deleted successfully"
}
```

### 6. 获取子图信息

**GET** `/api/v1/subgraphs/{subgraph_name}/info`

获取指定子图的详细信息。

**响应示例**:
```json
{
  "name": "split_query",
  "type": "SplitQueryStep",
  "module": "app.workflows.subgraph.split_query",
  "compiled": true
}
```

## 便捷端点

### 1. 查询拆分

**POST** `/api/v1/subgraphs/split-query`

直接执行查询拆分功能。

**请求体**:
```json
{
  "query": "请查询2025年1月的利润表和费用表"
}
```

**响应示例**:
```json
{
  "query": "请查询2025年1月的利润表和费用表",
  "plan": [
    "查询2025年1月的利润表",
    "查询2025年1月的费用表"
  ],
  "current_plan_idx": 0,
  "success": true
}
```

### 1.1. 查询拆分（直接调用）

**POST** `/api/v1/subgraphs/split-query/direct`

直接执行查询拆分功能，使用预编译的图实例，性能更好。

**请求体**:
```json
{
  "query": "请查询2025年1月的利润表和费用表"
}
```

**响应示例**:
```json
{
  "query": "请查询2025年1月的利润表和费用表",
  "plan": [
    "查询2025年1月的利润表",
    "查询2025年1月的费用表"
  ],
  "current_plan_idx": 0,
  "success": true,
  "method": "direct"
}
```

### 2. SQL生成

**POST** `/api/v1/subgraphs/generate-sql`

直接执行SQL生成功能。

**请求体**:
```json
{
  "query": "查询2025年1月的利润",
  "db_structure": "fact_profit表结构：\n- unique_lvl: 科目编码\n- amt: 金额"
}
```

**响应示例**:
```json
{
  "query": "查询2025年1月的利润",
  "sql": [
    "SELECT unique_lvl, SUM(amt) FROM fact_profit WHERE DATE_PART('YEAR', acct_period) = 2025 AND DATE_PART('MONTH', acct_period) = 1 GROUP BY unique_lvl;"
  ],
  "sql_error": null,
  "success": true
}
```

### 2.1. SQL生成（直接调用）

**POST** `/api/v1/subgraphs/generate-sql/direct`

直接执行SQL生成功能，使用预编译的图实例，性能更好。

**请求体**:
```json
{
  "query": "查询2025年1月的利润",
  "db_structure": "fact_profit表结构：\n- unique_lvl: 科目编码\n- amt: 金额"
}
```

**响应示例**:
```json
{
  "query": "查询2025年1月的利润",
  "sql": [
    "SELECT unique_lvl, SUM(amt) FROM fact_profit WHERE DATE_PART('YEAR', acct_period) = 2025 AND DATE_PART('MONTH', acct_period) = 1 GROUP BY unique_lvl;"
  ],
  "sql_error": null,
  "success": true,
  "method": "direct"
}
```

### 3. 数据获取

**POST** `/api/v1/subgraphs/fetch-data`

直接执行数据获取功能。

**请求体**:
```json
{
  "sql": "SELECT unique_lvl, SUM(amt) FROM fact_profit WHERE DATE_PART('YEAR', acct_period) = 2025 GROUP BY unique_lvl LIMIT 5;"
}
```

**响应示例**:
```json
{
  "sql": "SELECT unique_lvl, SUM(amt) FROM fact_profit WHERE DATE_PART('YEAR', acct_period) = 2025 GROUP BY unique_lvl LIMIT 5;",
  "raw_data": [
    {
      "sql_index": 0,
      "sql": "SELECT unique_lvl, SUM(amt) FROM fact_profit WHERE DATE_PART('YEAR', acct_period) = 2025 GROUP BY unique_lvl LIMIT 5;",
      "data": [
        ["1001", 1000000.00],
        ["1002", 500000.00]
      ],
      "columns": ["unique_lvl", "sum"],
      "row_count": 2
    }
  ],
  "md": "# 数据查询结果报告\n\n...",
  "success": true
}
```

### 3.1. 数据获取（直接调用）

**POST** `/api/v1/subgraphs/fetch-data/direct`

直接执行数据获取功能，使用预编译的图实例，性能更好。

**请求体**:
```json
{
  "sql": "SELECT unique_lvl, SUM(amt) FROM fact_profit WHERE DATE_PART('YEAR', acct_period) = 2025 GROUP BY unique_lvl LIMIT 5;"
}
```

**响应示例**:
```json
{
  "sql": "SELECT unique_lvl, SUM(amt) FROM fact_profit WHERE DATE_PART('YEAR', acct_period) = 2025 GROUP BY unique_lvl LIMIT 5;",
  "raw_data": [
    {
      "sql_index": 0,
      "sql": "SELECT unique_lvl, SUM(amt) FROM fact_profit WHERE DATE_PART('YEAR', acct_period) = 2025 GROUP BY unique_lvl LIMIT 5;",
      "data": [
        ["1001", 1000000.00],
        ["1002", 500000.00]
      ],
      "columns": ["unique_lvl", "sum"],
      "row_count": 2
    }
  ],
  "md": "# 数据查询结果报告\n\n...",
  "success": true,
  "method": "direct"
}
```

### 4. 清空所有子图

**POST** `/api/v1/subgraphs/clear`

清空所有已注册的子图。

**响应示例**:
```json
{
  "message": "All subgraphs cleared successfully"
}
```

## 使用示例

### Python 示例

```python
import httpx
import json

# 配置
API_BASE_URL = "http://localhost:8000/api/v1/subgraphs"
API_KEY = "your-api-key"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

async def test_subgraph_api():
    async with httpx.AsyncClient() as client:
        # 1. 获取子图列表
        response = await client.get(f"{API_BASE_URL}/list", headers=headers)
        print("子图列表:", response.json())
        
        # 2. 执行查询拆分
        split_data = {
            "query": "请查询2025年1月的利润表和费用表"
        }
        response = await client.post(
            f"{API_BASE_URL}/split-query", 
            json=split_data, 
            headers=headers
        )
        print("查询拆分结果:", response.json())
        
        # 3. 执行SQL生成
        sql_data = {
            "query": "查询2025年1月的利润",
            "db_structure": "fact_profit表结构：\n- unique_lvl: 科目编码\n- amt: 金额"
        }
        response = await client.post(
            f"{API_BASE_URL}/generate-sql", 
            json=sql_data, 
            headers=headers
        )
        print("SQL生成结果:", response.json())

# 运行测试
import asyncio
asyncio.run(test_subgraph_api())
```

### cURL 示例

```bash
# 获取子图列表
curl -X GET "http://localhost:8000/api/v1/subgraphs/list" \
  -H "X-API-Key: your-api-key"

# 执行查询拆分
curl -X POST "http://localhost:8000/api/v1/subgraphs/split-query" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "请查询2025年1月的利润表和费用表"
  }'

# 执行SQL生成
curl -X POST "http://localhost:8000/api/v1/subgraphs/generate-sql" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "查询2025年1月的利润",
    "db_structure": "fact_profit表结构：\n- unique_lvl: 科目编码\n- amt: 金额"
  }'
```

## 错误处理

API 使用标准的 HTTP 状态码：

- **200**: 成功
- **400**: 请求参数错误
- **404**: 子图不存在
- **500**: 服务器内部错误

错误响应格式：
```json
{
  "detail": "错误描述信息"
}
```

## 性能优化

### 直接调用 vs 服务层调用

为了优化性能，我们提供了两种调用方式：

1. **直接调用** (`/direct` 端点)：
   - 使用预编译的图实例
   - 避免重复实例化和编译
   - 响应更快，资源消耗更少
   - 推荐用于高频调用场景

2. **服务层调用** (标准端点)：
   - 通过服务层管理
   - 支持动态配置和扩展
   - 适合需要灵活配置的场景

### 性能对比

| 调用方式 | 首次调用 | 后续调用 | 内存占用 | 适用场景 |
|---------|---------|---------|---------|---------|
| 直接调用 | 较快 | 最快 | 低 | 高频调用、生产环境 |
| 服务层调用 | 较慢 | 中等 | 中等 | 开发调试、灵活配置 |

## 注意事项

1. **认证**: 所有请求都需要提供有效的 API Key
2. **模型配置**: 创建子图时可以指定不同的模型名称
3. **状态管理**: 子图执行会维护状态对象，包含查询、计划、SQL等信息
4. **错误处理**: 子图执行过程中的错误会记录在 `sql_error` 字段中
5. **性能**: 对于复杂查询，建议使用流式执行接口
6. **缓存**: 直接调用使用预编译的图实例，避免重复编译

## 最佳实践

1. **子图命名**: 使用有意义的名称，便于管理和识别
2. **错误处理**: 始终检查响应的 `success` 字段和错误信息
3. **资源清理**: 不再需要的自定义子图应及时删除
4. **测试**: 在生产环境使用前，充分测试子图功能
5. **监控**: 关注子图执行的性能和错误率 