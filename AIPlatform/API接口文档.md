# AI API Platform 接口文档

## 概述

AI API Platform 提供统一的AI能力服务接口，主要包括自然语言转SQL、用户管理、API密钥管理、反馈收集等功能。

### 基础信息

- **Base URL**: `http://localhost:8000`
- **API版本**: `v1`
- **API前缀**: `/api/v1`
- **认证方式**: API Key (Header: `X-API-Key`)
- **数据格式**: JSON
- **字符编码**: UTF-8

### 通用响应格式

所有API接口都使用统一的响应格式：

```json
{
  "code": 200,
  "message": "success",
  "data": {},
  "request_id": "req_123456789",
  "timestamp": 1703001234.5
}
```

### 错误响应格式

```json
{
  "code": 400,
  "message": "error description",
  "detail": "detailed error information",
  "request_id": "req_123456789",
  "timestamp": 1703001234.5
}
```

### HTTP状态码

- `200` - 成功
- `400` - 请求参数错误
- `401` - 认证失败
- `403` - 权限不足
- `404` - 资源不存在
- `422` - 数据验证失败
- `429` - 请求频率限制
- `500` - 服务器内部错误

---

## 1. 健康检查接口

### 1.1 系统健康检查

**接口地址**: `GET /health`

**描述**: 检查系统整体健康状态

**请求参数**: 无

**响应示例**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": 1703001234.5,
  "database": "connected",
  "ollama": "connected"
}
```

---

## 2. AI Agent接口

### 2.1 自然语言转SQL

**接口地址**: `POST /api/v1/agents/nl2sql`

**描述**: 将自然语言查询转换为SQL语句

**请求头**:
```
Content-Type: application/json
X-API-Key: your-api-key
```

**请求参数**:
```json
{
  "query": "查询所有用户信息",
  "database_schema": "你的数据库架构信息（可选）",
  "context": {},
  "max_tokens": 1000,
  "temperature": 0.1
}
```

**参数说明**:
- `query` (string, 必填): 自然语言查询，最少1个字符
- `database_schema` (string, 可选): 数据库架构信息
- `context` (object, 可选): 上下文信息
- `max_tokens` (integer, 可选): 最大token数，范围100-4000，默认1000
- `temperature` (float, 可选): 温度参数，范围0.0-2.0，默认0.1

**响应示例**:
```json
{
  "code": 200,
  "message": "NL2SQL conversion completed successfully",
  "data": {
    "request_id": "req_123456",
    "sql": "SELECT name, SUM(sales_amount) FROM customers WHERE sales_date >= '2024-11-01' AND sales_date < '2024-12-01' GROUP BY name HAVING SUM(sales_amount) > 100000;",
    "explanation": "查询2024年11月份销售额超过10万元的客户姓名和总销售额",
    "confidence": 0.92,
    "execution_time": 1.5,
    "warnings": [],
    "metadata": {}
  },
  "request_id": "req_123456"
}
```

### 2.2 获取可用模型列表

**接口地址**: `GET /api/v1/agents/models`

**描述**: 获取OLLAMA服务中可用的AI模型列表

**请求头**:
```
X-API-Key: your-api-key
```

**响应示例**:
```json
{
  "code": 200,
  "message": "Models retrieved successfully",
  "data": {
    "models": [
      {
        "name": "llama3.2",
        "size": "4.7GB",
        "status": "available",
        "description": "Meta Llama 3.2 3B Instruct",
        "modified_at": "2024-12-19T10:00:00Z",
        "size_vram": 4096
      }
    ]
  },
  "request_id": "req_123456"
}
```

### 2.3 获取Agent列表

**接口地址**: `GET /api/v1/agents`

**描述**: 获取系统中可用的Agent列表

**请求头**:
```
X-API-Key: your-api-key
```

**响应示例**:
```json
{
  "code": 200,
  "message": "Agents retrieved successfully",
  "data": {
    "agents": [
      {
        "name": "NL2SQL Agent",
        "type": "nl2sql",
        "description": "Convert natural language queries to SQL statements",
        "status": "active",
        "capabilities": [
          "Natural language understanding",
          "SQL generation",
          "Query optimization",
          "Syntax validation"
        ]
      }
    ]
  },
  "request_id": "req_123456"
}
```

---

## 3. 用户管理接口

### 3.1 创建用户

**接口地址**: `POST /api/v1/users`

**描述**: 创建新用户

**请求头**:
```
Content-Type: application/json
X-API-Key: your-api-key
```

**请求参数**:
```json
{
  "name": "张三",
  "email": "zhangsan@example.com",
  "department": "财务部",
  "status": "active"
}
```

**参数说明**:
- `name` (string, 必填): 用户姓名，1-100个字符
- `email` (string, 必填): 用户邮箱，必须是有效邮箱格式
- `department` (string, 可选): 用户部门，最多50个字符
- `status` (string, 可选): 用户状态，默认"active"

**响应示例**:
```json
{
  "code": 200,
  "message": "User created successfully",
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "张三",
    "email": "zhangsan@example.com",
    "department": "财务部",
    "status": "active",
    "created_at": "2024-12-19T10:00:00Z",
    "updated_at": "2024-12-19T10:00:00Z"
  }
}
```

### 3.2 获取用户列表

**接口地址**: `GET /api/v1/users`

**描述**: 获取用户列表，支持分页和筛选

**请求头**:
```
X-API-Key: your-api-key
```

**查询参数**:
- `skip` (integer, 可选): 跳过的记录数，默认0，最小值0
- `limit` (integer, 可选): 返回的记录数，默认10，范围1-100
- `department` (string, 可选): 按部门筛选
- `is_active` (boolean, 可选): 按活跃状态筛选

**请求示例**:
```
GET /api/v1/users?skip=0&limit=10&department=财务部&is_active=true
```

**响应示例**:
```json
{
  "code": 200,
  "message": "Users retrieved successfully",
  "data": {
    "users": [
      {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "张三",
        "email": "zhangsan@example.com",
        "department": "财务部",
        "status": "active",
        "created_at": "2024-12-19T10:00:00Z",
        "updated_at": "2024-12-19T10:00:00Z"
      }
    ],
    "total": 1,
    "skip": 0,
    "limit": 10
  }
}
```

### 3.3 获取用户详情

**接口地址**: `GET /api/v1/users/{user_id}`

**描述**: 根据用户ID获取用户详细信息

**请求头**:
```
X-API-Key: your-api-key
```

**路径参数**:
- `user_id` (string, 必填): 用户UUID

**响应示例**:
```json
{
  "code": 200,
  "message": "User retrieved successfully",
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "张三",
    "email": "zhangsan@example.com",
    "department": "财务部",
    "status": "active",
    "created_at": "2024-12-19T10:00:00Z",
    "updated_at": "2024-12-19T10:00:00Z"
  }
}
```

### 3.4 更新用户信息

**接口地址**: `PUT /api/v1/users/{user_id}`

**描述**: 更新用户信息

**请求头**:
```
Content-Type: application/json
X-API-Key: your-api-key
```

**路径参数**:
- `user_id` (string, 必填): 用户UUID

**请求参数**:
```json
{
  "name": "李四",
  "email": "lisi@example.com",
  "department": "IT部",
  "status": "active"
}
```

**参数说明**:
- `name` (string, 可选): 用户姓名，1-100个字符
- `email` (string, 可选): 用户邮箱，必须是有效邮箱格式
- `department` (string, 可选): 用户部门，最多50个字符
- `status` (string, 可选): 用户状态

**响应示例**: 同获取用户详情

### 3.5 删除用户

**接口地址**: `DELETE /api/v1/users/{user_id}`

**描述**: 删除用户（软删除）

**请求头**:
```
X-API-Key: your-api-key
```

**路径参数**:
- `user_id` (string, 必填): 用户UUID

**响应示例**:
```json
{
  "code": 200,
  "message": "User deleted successfully",
  "data": {
    "user_id": "123e4567-e89b-12d3-a456-426614174000"
  }
}
```

### 3.6 获取用户统计

**接口地址**: `GET /api/v1/users/stats/overview`

**描述**: 获取用户统计信息

**请求头**:
```
X-API-Key: your-api-key
```

**响应示例**:
```json
{
  "code": 200,
  "message": "User statistics retrieved successfully",
  "data": {
    "total_users": 100,
    "active_users": 95,
    "inactive_users": 3,
    "suspended_users": 2,
    "departments": {
      "财务部": 20,
      "IT部": 15,
      "人事部": 10
    }
  }
}
```

### 3.7 根据邮箱获取用户

**接口地址**: `GET /api/v1/users/email/{email}`

**描述**: 根据邮箱地址获取用户信息

**请求头**:
```
X-API-Key: your-api-key
```

**路径参数**:
- `email` (string, 必填): 用户邮箱地址

**响应示例**: 同获取用户详情

---

## 4. API密钥管理接口

### 4.1 创建API密钥

**接口地址**: `POST /api/v1/api-keys`

**描述**: 为用户创建新的API密钥

**请求头**:
```
Content-Type: application/json
X-API-Key: your-api-key
```

**请求参数**:
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "财务部查询密钥",
  "permissions": ["read", "nl2sql"],
  "expires_days": 365
}
```

**参数说明**:
- `user_id` (string, 必填): 用户UUID
- `name` (string, 必填): API密钥名称，1-100个字符
- `permissions` (array, 可选): 权限列表
- `expires_days` (integer, 可选): 过期天数，默认365天

**响应示例**:
```json
{
  "code": 200,
  "message": "API key created successfully",
  "data": {
    "id": 1,
    "name": "财务部查询密钥",
    "key": "ak_1234567890abcdef",
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "permissions": ["read", "nl2sql"],
    "status": "active",
    "expires_at": "2025-12-19T10:00:00Z",
    "created_at": "2024-12-19T10:00:00Z",
    "updated_at": "2024-12-19T10:00:00Z"
  }
}
```

### 4.2 获取API密钥列表

**接口地址**: `GET /api/v1/api-keys`

**描述**: 获取API密钥列表，支持分页和筛选

**请求头**:
```
X-API-Key: your-api-key
```

**查询参数**:
- `skip` (integer, 可选): 跳过的记录数，默认0，最小值0
- `limit` (integer, 可选): 返回的记录数，默认10，范围1-100
- `user_id` (string, 可选): 按用户ID筛选
- `is_active` (boolean, 可选): 按活跃状态筛选

**响应示例**:
```json
{
  "code": 200,
  "message": "API keys retrieved successfully",
  "data": {
    "api_keys": [
      {
        "id": 1,
        "name": "财务部查询密钥",
        "key": "ak_1234567890abcdef",
        "user_id": "123e4567-e89b-12d3-a456-426614174000",
        "permissions": ["read", "nl2sql"],
        "status": "active",
        "expires_at": "2025-12-19T10:00:00Z",
        "created_at": "2024-12-19T10:00:00Z",
        "updated_at": "2024-12-19T10:00:00Z"
      }
    ],
    "total": 1,
    "skip": 0,
    "limit": 10
  }
}
```

### 4.3 轮换API密钥

**接口地址**: `POST /api/v1/api-keys/{api_key_id}/rotate`

**描述**: 轮换API密钥，生成新的密钥值

**请求头**:
```
X-API-Key: your-api-key
```

**路径参数**:
- `api_key_id` (integer, 必填): API密钥ID

**响应示例**: 同创建API密钥

### 4.4 激活/停用API密钥

**接口地址**: 
- 激活: `POST /api/v1/api-keys/{api_key_id}/activate`
- 停用: `POST /api/v1/api-keys/{api_key_id}/deactivate`

**描述**: 激活或停用API密钥

**请求头**:
```
X-API-Key: your-api-key
```

**路径参数**:
- `api_key_id` (integer, 必填): API密钥ID

**响应示例**: 同创建API密钥

---

## 5. 反馈收集接口

### 5.1 提交反馈

**接口地址**: `POST /api/v1/feedback`

**描述**: 提交用户对AI服务的使用反馈

**请求头**:
```
Content-Type: application/json
X-API-Key: your-api-key
```

**请求参数**:
```json
{
  "request_id": "req_123456",
  "rating": 4,
  "is_sql_correct": true,
  "feedback_text": "生成的SQL语句正确，查询结果符合预期",
  "suggestions": "希望能够支持更复杂的聚合查询"
}
```

**参数说明**:
- `request_id` (string, 必填): 关联的请求ID
- `rating` (integer, 必填): 评分，范围1-5
- `is_sql_correct` (boolean, 可选): SQL是否正确
- `feedback_text` (string, 可选): 反馈文本
- `suggestions` (string, 可选): 改进建议

**响应示例**:
```json
{
  "code": 200,
  "message": "Feedback submitted successfully",
  "data": {
    "id": 1,
    "request_id": "req_123456",
    "rating": 4,
    "is_sql_correct": true,
    "feedback_text": "生成的SQL语句正确，查询结果符合预期",
    "suggestions": "希望能够支持更复杂的聚合查询",
    "created_at": "2024-12-19T10:00:00Z"
  }
}
```

### 5.2 获取反馈统计

**接口地址**: `GET /api/v1/feedback/stats`

**描述**: 获取反馈统计信息

**请求头**:
```
X-API-Key: your-api-key
```

**响应示例**:
```json
{
  "code": 200,
  "message": "Feedback statistics retrieved successfully",
  "data": {
    "total_feedback": 100,
    "average_rating": 4.2,
    "rating_distribution": {
      "1": 2,
      "2": 5,
      "3": 15,
      "4": 40,
      "5": 38
    },
    "sql_correctness_rate": 0.85
  }
}
```

---

## 6. 日志查询接口

### 6.1 查询API调用日志

**接口地址**: `GET /api/v1/logs`

**描述**: 查询API调用日志，支持筛选和分页

**请求头**:
```
X-API-Key: your-api-key
```

**查询参数**:
- `skip` (integer, 可选): 跳过的记录数，默认0
- `limit` (integer, 可选): 返回的记录数，默认10，范围1-100
- `status_code` (integer, 可选): 按HTTP状态码筛选
- `method` (string, 可选): 按HTTP方法筛选
- `path` (string, 可选): 按请求路径筛选
- `start_time` (string, 可选): 开始时间 (ISO 8601格式)
- `end_time` (string, 可选): 结束时间 (ISO 8601格式)

**请求示例**:
```
GET /api/v1/logs?limit=10&status_code=200&start_time=2024-12-19T00:00:00Z
```

**响应示例**:
```json
{
  "code": 200,
  "message": "Logs retrieved successfully",
  "data": {
    "logs": [
      {
        "id": 1,
        "method": "POST",
        "path": "/api/v1/agents/nl2sql",
        "status_code": 200,
        "response_time": 1.5,
        "user_id": "123e4567-e89b-12d3-a456-426614174000",
        "request_id": "req_123456",
        "created_at": "2024-12-19T10:00:00Z"
      }
    ],
    "total": 1,
    "skip": 0,
    "limit": 10
  }
}
```

### 6.2 获取日志统计

**接口地址**: `GET /api/v1/logs/stats`

**描述**: 获取API调用统计信息

**请求头**:
```
X-API-Key: your-api-key
```

**响应示例**:
```json
{
  "code": 200,
  "message": "Log statistics retrieved successfully",
  "data": {
    "total_requests": 1000,
    "success_rate": 0.95,
    "average_response_time": 1.2,
    "requests_by_status": {
      "200": 950,
      "400": 30,
      "500": 20
    },
    "requests_by_endpoint": {
      "/api/v1/agents/nl2sql": 500,
      "/api/v1/users": 300,
      "/api/v1/api-keys": 200
    }
  }
}
```

---

## 7. 数据验证规则

### 7.1 用户数据验证

- **name**: 1-100个字符，不能为空
- **email**: 必须是有效的邮箱格式
- **department**: 最多50个字符
- **status**: 枚举值 ["active", "inactive", "suspended"]

### 7.2 API密钥数据验证

- **name**: 1-100个字符，不能为空
- **permissions**: 数组，可选值 ["read", "write", "admin", "nl2sql"]
- **expires_days**: 正整数，范围1-3650

### 7.3 NL2SQL请求验证

- **query**: 最少1个字符，不能为空；必须包含以下查询意图关键词之一：
中文：查询、统计、计算、求、获取、显示、列出、找出
英文：select、count、sum、avg、max、min、group、where
- **max_tokens**: 整数，范围100-4000
- **temperature**: 浮点数，范围0.0-2.0

### 7.4 分页参数验证

- **skip**: 非负整数，默认0
- **limit**: 正整数，范围1-100，默认10

---

## 8. 错误代码说明

### 8.1 业务错误代码

- `E001`: 用户不存在
- `E002`: 邮箱已存在
- `E003`: API密钥无效
- `E004`: API密钥已过期
- `E005`: 权限不足
- `E006`: 请求频率过高
- `E007`: OLLAMA服务不可用
- `E008`: 模型不存在
- `E009`: SQL生成失败
- `E010`: 数据库连接失败

### 8.2 验证错误示例

```json
{
  "code": 422,
  "message": "Validation error",
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    },
    {
      "loc": ["body", "name"],
      "msg": "ensure this value has at least 1 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

---

## 9. 认证和权限

### 9.1 API密钥认证

所有API接口都需要在请求头中包含有效的API密钥：

```
X-API-Key: your-api-key-here
```

### 9.2 权限级别

- **read**: 只读权限，可以查询数据
- **write**: 写权限，可以创建和修改数据
- **admin**: 管理员权限，可以管理用户和API密钥
- **nl2sql**: NL2SQL转换权限

### 9.3 权限检查

不同的接口需要不同的权限：

- 用户管理接口: `admin` 权限
- NL2SQL接口: `nl2sql` 权限
- 查询接口: `read` 权限
- 创建/修改接口: `write` 权限

---

## 10. 限流规则

- 默认限流: 每分钟100个请求
- NL2SQL接口: 每分钟10个请求
- 超出限制时返回HTTP 429状态码

---

## 11. 示例代码

### 11.1 Python示例

```python
import requests

# 配置
base_url = "http://localhost:8000"
api_key = "your-api-key"
headers = {"X-API-Key": api_key, "Content-Type": "application/json"}

# NL2SQL转换
def nl2sql_convert(query):
    url = f"{base_url}/api/v1/agents/nl2sql"
    data = {
        "query": query,
        "database_schema": "CREATE TABLE sales (id INT, amount DECIMAL(10,2));"
    }
    response = requests.post(url, json=data, headers=headers)
    return response.json()

# 创建用户
def create_user(name, email, department):
    url = f"{base_url}/api/v1/users"
    data = {
        "name": name,
        "email": email,
        "department": department
    }
    response = requests.post(url, json=data, headers=headers)
    return response.json()
```

### 11.2 cURL示例

```bash
# NL2SQL转换
curl -X POST http://localhost:8000/api/v1/agents/nl2sql \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "query": "查询销售金额大于1000的记录",
    "database_schema": "CREATE TABLE sales (id INT, amount DECIMAL(10,2));"
  }'

# 创建用户
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "name": "张三",
    "email": "zhangsan@example.com",
    "department": "财务部"
  }'
```

---

## 12. 更新日志

### v1.0.0 (2024-12-19)
- 初始版本发布
- 支持NL2SQL转换
- 支持用户管理
- 支持API密钥管理
- 支持反馈收集
- 支持日志查询

---

## 13. 联系方式

- **技术支持**: support@example.com
- **API文档**: http://localhost:8000/docs
- **GitHub**: https://github.com/your-repo/ai-platform 