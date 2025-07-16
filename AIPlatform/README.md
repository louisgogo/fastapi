# AI API Platform

基于FastAPI和OLLAMA的AI API接口平台，专为财务部门提供AI能力服务。

## 技术架构

- **后端框架**: FastAPI 0.104.1
- **本地模型**: OLLAMA
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **ORM**: SQLAlchemy 2.0 (同步模式)
- **认证**: API-KEY
- **部署**: Docker + Docker Compose
- **LLM集成**: LANGGRAPH标准兼容

## 核心特性

### 架构设计原则
- **同步数据库连接**: 使用同步SQLAlchemy，简化代码复杂度
- **统一数据访问**: 统一使用 `get_db()` 函数进行数据库访问
- **简化异步处理**: 减少异步复杂性，提高代码可维护性
- **LANGGRAPH兼容**: 符合LANGGRAPH标准的LLM集成模式

### 主要功能
- **用户管理系统**: 用户注册、认证、权限管理
- **API密钥管理**: 密钥生成、验证、轮换
- **健康检查**: 系统状态监控
- **AI集成**: OLLAMA本地模型调用
- **LLM工具链**: 符合LANGGRAPH标准的大语言模型调用接口

## 项目结构

```
AIPlatform/
├── app/                    # 主应用目录
│   ├── main.py            # FastAPI应用入口
│   ├── core/              # 核心配置
│   │   ├── config.py      # 应用配置 (Pydantic V2)
│   │   └── exceptions.py  # 异常定义
│   ├── models/            # SQLAlchemy数据模型
│   │   ├── base.py        # 基础模型
│   │   ├── user.py        # 用户模型
│   │   ├── api_key.py     # API密钥模型
│   │   ├── agent.py       # Agent模型
│   │   ├── api_log.py     # API日志模型
│   │   └── feedback.py    # 反馈模型
│   ├── schemas/           # Pydantic模式 (V2)
│   │   ├── common.py      # 通用响应模式
│   │   ├── user.py        # 用户模式
│   │   ├── api_key.py     # API密钥模式
│   │   ├── agent.py       # Agent模式
│   │   └── feedback.py    # 反馈模式
│   ├── services/          # 业务逻辑层 (同步)
│   │   ├── user_service.py     # 用户服务
│   │   ├── api_key_service.py  # API密钥服务
│   │   ├── agent_service.py    # Agent服务
│   │   ├── feedback_service.py # 反馈服务
│   │   └── ollama_service.py   # OLLAMA服务
│   ├── agents/            # AI Agent实现
│   │   ├── base_agent.py  # 基础Agent类
│   │   └── nl2sql_agent.py # NL2SQL Agent
│   ├── llms/              # LLM集成模块 (LANGGRAPH兼容)
│   │   ├── __init__.py    # 模块导出
│   │   ├── base_llm.py    # 基础LLM类
│   │   ├── ollama_llm.py  # Ollama LLM实现
│   │   ├── factory.py     # LLM工厂类
│   │   └── examples.py    # 使用示例
│   ├── tools/             # 工具模块
│   │   ├── base_tool.py   # 基础工具类
│   │   ├── data_tool.py   # 数据处理工具
│   │   └── registry.py    # 工具注册中心
│   ├── api/               # API路由层 (同步)
│   │   └── v1/            # v1版本API
│   │       ├── health.py  # 健康检查
│   │       ├── users.py   # 用户管理API
│   │       ├── agents.py  # Agent API
│   │       ├── api_keys.py # API密钥管理
│   │       └── tools.py   # 工具API
│   ├── database/          # 数据访问层
│   │   ├── __init__.py    # 包导出
│   │   └── connection.py  # 数据库连接 (同步)
│   └── utils/             # 工具类
│       └── logger.py      # 日志工具
├── tests/                 # 测试文件
│   ├── test_users.py      # 用户测试
│   ├── test_agents.py     # Agent测试
│   ├── test_llms.py       # LLM测试
│   └── conftest.py        # 测试配置
├── scripts/               # 脚本目录
├── docker-compose.yml     # Docker Compose配置
├── Dockerfile            # Docker镜像配置
├── requirements.txt      # Python依赖
└── README.md             # 项目文档
```

## LLM集成模块

### 设计理念
LLM模块采用LANGGRAPH标准设计，提供统一的大语言模型调用接口：

- **标准化接口**: 符合LANGGRAPH标准的LLM基类
- **多模型支持**: 支持Ollama、OpenAI、Anthropic等多种LLM
- **工厂模式**: 统一的LLM实例创建和管理
- **缓存机制**: 智能的LLM实例缓存和复用
- **异步支持**: 完整的同步和异步调用支持

### 主要组件

#### 1. 基础类 (base_llm.py)
```python
from app.llms import BaseLLM, LLMConfig, LLMResponse

# 配置LLM
config = LLMConfig(
    model_name="llama3.2",
    base_url="http://localhost:11434",
    temperature=0.1,
    max_tokens=1000
)
```

#### 2. Ollama实现 (ollama_llm.py)
```python
from app.llms import OllamaLLM, create_ollama_llm

# 创建Ollama LLM
llm = create_ollama_llm(
    model_name="llama3.2",
    temperature=0.1
)

# 同步调用
response = llm("你好，请介绍一下自己")

# 异步调用
response = await llm.ainvoke("请分析这个问题")
```

#### 3. 工厂类 (factory.py)
```python
from app.llms import LLMFactory, LLMType

# 创建LLM实例
llm = LLMFactory.create_llm(
    LLMType.OLLAMA,
    {"model_name": "llama3.2"},
    cache_key="my_llm"
)

# 获取缓存实例
cached_llm = LLMFactory.get_cached_llm("my_llm")
```

#### 4. 便捷函数
```python
from app.llms import get_default_llm

# 获取默认LLM实例
llm = get_default_llm()
```

### 高级特性

#### 链式调用
```python
# 创建普通链
chain = llm.create_chain("请帮我写一个关于{topic}的文章")
result = chain.invoke({"topic": "人工智能"})

# 创建JSON输出链
json_chain = llm.create_json_chain("请以JSON格式返回{city}的信息")
result = json_chain.invoke({"city": "北京"})
```

#### 流式输出
```python
# 启用流式输出
config = LLMConfig(
    model_name="llama3.2",
    stream=True
)

llm = LLMFactory.create_llm(LLMType.OLLAMA, config)

# 流式生成
async for chunk in llm._generate_stream("请写一首诗"):
    print(chunk, end="", flush=True)
```

#### 输出解析
```python
from app.llms import CleanOutputParser, JsonStructOutputParser

# 清理输出解析器
clean_parser = CleanOutputParser()
cleaned_text = clean_parser.parse(raw_output)

# JSON结构解析器
json_parser = JsonStructOutputParser()
json_data = json_parser.parse(json_output)
```

## 数据库连接说明

### 同步数据库设计
项目采用同步数据库连接，以简化代码复杂度：

```python
# 推荐使用方式
from app.database import get_db
from sqlalchemy.orm import Session

def my_api_function(db: Session = Depends(get_db)):
    # 同步数据库操作
    user = db.query(User).first()
    return user
```

### 配置要求
- 确保 `SECRET_KEY` 至少32个字符
- 数据库URL格式：`sqlite:///./app.db` 或 `postgresql://user:pass@host/db`

## 快速开始

### 1. 环境配置
```bash
# 复制环境变量文件
cp env.example .env

# 编辑环境变量，确保SECRET_KEY至少32个字符
vim .env
```

### 2. 本地开发
```bash
# 安装依赖
pip install -r requirements.txt

# 启动应用
python app/main.py

# 或使用uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Docker部署
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看应用日志
docker-compose logs -f api
```

### 4. LLM使用示例
```bash
# 运行LLM使用示例
python -m app.llms.examples
```

## API文档

启动应用后，访问以下地址查看API文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 主要API端点

### 健康检查
- `GET /api/v1/health/` - 系统健康状态
- `GET /api/v1/health/ping` - 简单心跳检测

### 用户管理
- `POST /api/v1/users/` - 创建用户
- `GET /api/v1/users/` - 获取用户列表
- `GET /api/v1/users/{user_id}` - 获取用户详情
- `PUT /api/v1/users/{user_id}` - 更新用户信息
- `DELETE /api/v1/users/{user_id}` - 删除用户
- `GET /api/v1/users/stats/overview` - 用户统计

### AI Agent
- `POST /api/v1/agents/nl2sql` - 自然语言转SQL
- `GET /api/v1/agents/` - 获取Agent列表

### API密钥管理
- `POST /api/v1/api-keys/` - 创建API密钥
- `GET /api/v1/api-keys/` - 获取API密钥列表
- `DELETE /api/v1/api-keys/{key_id}` - 删除API密钥

### 工具管理
- `GET /api/v1/tools/` - 获取工具列表
- `POST /api/v1/tools/{tool_name}/execute` - 执行工具

## 开发规范

### 代码风格
- 使用同步函数：`def` 而不是 `async def`
- 统一使用 `get_db()` 进行数据库访问
- 遵循Pydantic V2语法：`@field_validator` 而不是 `@validator`
- LLM模块遵循LANGGRAPH标准

### LLM开发规范
- 继承 `BaseLLM` 类实现新的LLM
- 使用 `LLMFactory` 进行实例管理
- 支持同步和异步调用
- 实现适当的错误处理和日志记录

### 错误处理
- 使用自定义异常类
- 统一错误响应格式
- 详细的错误日志记录

### 测试要求
- 单元测试覆盖核心业务逻辑
- 使用pytest进行测试
- Mock外部依赖
- LLM模块需要完整的测试覆盖

## 故障排除

### 常见问题
1. **SECRET_KEY错误**: 确保环境变量中的SECRET_KEY至少32个字符
2. **数据库连接失败**: 检查DATABASE_URL配置
3. **OLLAMA连接失败**: 确保OLLAMA服务运行在指定端口
4. **LLM调用失败**: 检查模型是否已下载，服务是否正常运行

### 日志查看
```bash
# 查看应用日志
tail -f logs/app.log

# Docker环境查看日志
docker-compose logs -f api
```

### LLM调试
```bash
# 测试Ollama连接
curl http://localhost:11434/api/tags

# 运行LLM测试
python -m pytest tests/test_llms.py -v
```

## 贡献指南

1. Fork项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

### LLM模块贡献
- 新增LLM实现需继承 `BaseLLM`
- 在 `LLMFactory` 中注册新的LLM类型
- 提供完整的测试用例和使用示例
- 更新相关文档

## 许可证

MIT License 