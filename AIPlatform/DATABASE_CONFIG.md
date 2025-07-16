# 数据库配置说明

## 问题原因

项目原来的测试代码中硬编码了SQLite连接，导致运行测试时忽略了环境变量配置。

## 解决方案

### 1. 创建.env文件

复制 `env.example` 文件为 `.env`：

```bash
cp env.example .env
```

### 2. 配置PostgreSQL连接

在 `.env` 文件中，确保数据库连接配置为PostgreSQL：

```env
# 数据库配置
DATABASE_URL=postgresql://username:password@localhost:5432/ai_platform
DATABASE_ECHO=false
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
```

请将 `username`, `password`, `localhost`, `5432`, `ai_platform` 替换为您的实际PostgreSQL配置。

### 3. 测试环境配置

在 `test.env` 文件中，已经配置了PostgreSQL连接：

```env
DATABASE_URL=postgresql://username:password@localhost:5432/ai_platform_test
```

### 4. 代码修改

已经修改了以下文件：

- `app/services/user_service.py`: 测试代码现在使用配置文件中的数据库连接
- `app/models/agent.py`: 修改了JSONB字段以兼容不同数据库
- `app/models/api_log.py`: 修改了JSONB字段为数据库兼容格式
- `app/models/api_key.py`: 修改了JSONB字段和测试代码
- `app/models/user.py`: 修改了测试代码使用配置文件
- `app/models/base.py`: 修改了测试代码使用配置文件
- `test.env`: 更新为PostgreSQL连接

### 5. 验证配置

运行测试确保连接正常：

```bash
# 设置环境变量
export $(cat .env | xargs)

# 运行测试
python -m app.services.user_service
```

## 数据库兼容性

现在的Agent模型使用了数据库兼容的JSON字段：

```python
# 配置信息
config: Mapped[Optional[dict]] = mapped_column(
    JSON().with_variant(JSONB(), "postgresql"),
    nullable=True,
    comment="Agent配置信息，JSON格式"
)
```

这样可以：
- 在PostgreSQL中使用JSONB类型（性能更好）
- 在SQLite中使用JSON类型（兼容性测试）
- 在其他数据库中使用标准JSON类型

## 推荐配置

### 开发环境
```env
DATABASE_URL=postgresql://ai_user:ai_password@localhost:5432/ai_platform_dev
```

### 测试环境
```env
DATABASE_URL=postgresql://ai_user:ai_password@localhost:5432/ai_platform_test
```

### 生产环境
```env
DATABASE_URL=postgresql://ai_user:secure_password@db_server:5432/ai_platform_prod
``` 