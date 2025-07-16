# LLM模块API文档

## 文档信息
- **文档名称**: LLM模块API文档
- **编写人**: malou
- **编写日期**: 2025-01-08
- **版本**: v1.0.0
- **适用范围**: AIPlatform项目LLM模块

## 1. 概述

LLM模块提供符合LANGGRAPH标准的大语言模型集成接口，支持多种LLM提供商，包括Ollama、OpenAI、Anthropic等。

## 2. 快速开始

### 2.1 基本导入
```python
from app.llms import (
    BaseLLM,
    LLMConfig,
    LLMResponse,
    OllamaLLM,
    LLMFactory,
    LLMType,
    create_ollama_llm,
    get_default_llm
)
```

### 2.2 创建LLM实例
```python
# 方式1: 使用便捷函数
llm = create_ollama_llm(
    model_name="llama3.2",
    temperature=0.1,
    max_tokens=1000
)

# 方式2: 使用工厂类
llm = LLMFactory.create_ollama_llm(
    model_name="llama3.2",
    base_url="http://localhost:11434"
)

# 方式3: 使用配置对象
config = LLMConfig(
    model_name="llama3.2",
    base_url="http://localhost:11434",
    temperature=0.1,
    max_tokens=1000
)
llm = OllamaLLM(config)
```

### 2.3 基本调用
```python
# 同步调用
response = llm("请介绍一下Python编程语言")

# 异步调用
response = await llm.ainvoke("请分析人工智能的发展趋势")

# 批量调用
responses = llm.batch(["问题1", "问题2", "问题3"])
```

## 3. 核心类API

### 3.1 LLMConfig

#### 3.1.1 类定义
```python
class LLMConfig(BaseModel):
    """LLM配置模型"""
```

#### 3.1.2 字段说明
| 字段名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| model_name | str | 必填 | 模型名称 |
| base_url | str | 必填 | 模型服务地址 |
| temperature | float | 0.1 | 温度参数(0.0-2.0) |
| max_tokens | int | 1000 | 最大令牌数(1-10000) |
| top_p | float | 0.9 | Top-p采样参数(0.0-1.0) |
| frequency_penalty | float | 0.0 | 频率惩罚(-2.0-2.0) |
| presence_penalty | float | 0.0 | 存在惩罚(-2.0-2.0) |
| stream | bool | False | 是否启用流式输出 |
| timeout | int | 30 | 超时时间(秒) |

#### 3.1.3 方法说明
```python
def validate_config(self) -> None:
    """
    验证配置有效性
    
    @throws ValidationException 配置无效时抛出异常
    Note: 验证所有配置参数的有效性
    """
```

#### 3.1.4 使用示例
```python
# 创建配置
config = LLMConfig(
    model_name="llama3.2",
    base_url="http://localhost:11434",
    temperature=0.5,
    max_tokens=2000,
    stream=True
)

# 验证配置
config.validate_config()

# 获取配置字典
config_dict = config.model_dump()
```

### 3.2 LLMResponse

#### 3.2.1 类定义
```python
class LLMResponse(BaseModel):
    """LLM响应模型"""
```

#### 3.2.2 字段说明
| 字段名 | 类型 | 说明 |
|--------|------|------|
| request_id | str | 请求唯一标识 |
| model_name | str | 使用的模型名称 |
| prompt | str | 输入提示词 |
| response | str | 生成的响应 |
| error | Optional[str] | 错误信息 |
| duration | float | 耗时(秒) |
| prompt_tokens | int | 提示词令牌数 |
| completion_tokens | int | 完成令牌数 |
| total_tokens | int | 总令牌数 |

#### 3.2.3 类方法
```python
@classmethod
def create_success_response(
    cls,
    request_id: str,
    model_name: str,
    prompt: str,
    response: str,
    start_time: float,
    end_time: float,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_tokens: int = 0
) -> "LLMResponse":
    """
    创建成功响应
    
    @param request_id str 请求ID
    @param model_name str 模型名称
    @param prompt str 输入提示
    @param response str 生成响应
    @param start_time float 开始时间
    @param end_time float 结束时间
    @param prompt_tokens int 提示词令牌数
    @param completion_tokens int 完成令牌数
    @param total_tokens int 总令牌数
    @return LLMResponse 响应对象
    Note: 创建成功的LLM响应对象
    """

@classmethod
def create_error_response(
    cls,
    request_id: str,
    model_name: str,
    prompt: str,
    error: str,
    start_time: float,
    end_time: float
) -> "LLMResponse":
    """
    创建错误响应
    
    @param request_id str 请求ID
    @param model_name str 模型名称
    @param prompt str 输入提示
    @param error str 错误信息
    @param start_time float 开始时间
    @param end_time float 结束时间
    @return LLMResponse 响应对象
    Note: 创建错误的LLM响应对象
    """
```

### 3.3 BaseLLM

#### 3.3.1 类定义
```python
class BaseLLM(LLM, ABC):
    """基础LLM类，符合LANGGRAPH标准"""
```

#### 3.3.2 初始化方法
```python
def __init__(self, config: LLMConfig):
    """
    初始化LLM实例
    
    @param config LLMConfig LLM配置对象
    Note: 初始化LLM实例，验证配置和连接
    """
```

#### 3.3.3 抽象方法
```python
@abstractmethod
def _generate_sync(self, prompt: str, **kwargs) -> str:
    """
    同步生成文本
    
    @param prompt str 输入提示词
    @param kwargs Dict 额外参数
    @return str 生成的文本
    Note: 子类必须实现此方法
    """

@abstractmethod
async def _generate_async(self, prompt: str, **kwargs) -> str:
    """
    异步生成文本
    
    @param prompt str 输入提示词
    @param kwargs Dict 额外参数
    @return str 生成的文本
    Note: 子类必须实现此方法
    """
```

#### 3.3.4 公共方法
```python
def validate_connection(self) -> bool:
    """
    验证连接有效性
    
    @return bool 连接是否有效
    Note: 验证与LLM服务的连接状态
    """

def create_chain(self, template: str) -> Chain:
    """
    创建LangChain链
    
    @param template str 提示词模板
    @return Chain LangChain链对象
    Note: 创建普通的LangChain链，使用CleanOutputParser
    """

def create_json_chain(self, template: str) -> Chain:
    """
    创建JSON输出链
    
    @param template str 提示词模板
    @return Chain LangChain链对象
    Note: 创建JSON输出链，使用JsonStructOutputParser
    """

def get_model_info(self) -> Dict[str, Any]:
    """
    获取模型信息
    
    @return Dict[str, Any] 模型信息
    Note: 获取当前模型的详细信息
    """

def get_config(self) -> Dict[str, Any]:
    """
    获取配置信息
    
    @return Dict[str, Any] 配置信息
    Note: 获取当前LLM的配置信息
    """

def update_config(self, updates: Dict[str, Any]) -> None:
    """
    更新配置
    
    @param updates Dict[str, Any] 更新的配置项
    Note: 更新LLM配置，会重新验证连接
    """
```

### 3.4 OllamaLLM

#### 3.4.1 类定义
```python
class OllamaLLM(BaseLLM):
    """Ollama LLM实现"""
```

#### 3.4.2 特有属性
```python
@property
def generate_url(self) -> str:
    """生成API端点URL"""

@property
def models_url(self) -> str:
    """模型列表API端点URL"""
```

#### 3.4.3 特有方法
```python
def get_available_models(self) -> List[str]:
    """
    获取可用模型列表(同步)
    
    @return List[str] 可用模型列表
    Note: 从Ollama服务获取可用模型列表
    """

async def get_available_models_async(self) -> List[str]:
    """
    获取可用模型列表(异步)
    
    @return List[str] 可用模型列表
    Note: 异步获取可用模型列表
    """

async def _generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
    """
    流式生成文本
    
    @param prompt str 输入提示词
    @param kwargs Dict 额外参数
    @return AsyncGenerator[str, None] 文本流
    Note: 生成流式文本输出
    """
```

### 3.5 LLMFactory

#### 3.5.1 类定义
```python
class LLMFactory:
    """LLM工厂类，统一管理LLM实例"""
```

#### 3.5.2 核心方法
```python
@staticmethod
def create_llm(
    llm_type: Union[LLMType, str],
    config: Union[Dict[str, Any], LLMConfig],
    cache_key: Optional[str] = None
) -> BaseLLM:
    """
    创建LLM实例
    
    @param llm_type Union[LLMType, str] LLM类型
    @param config Union[Dict, LLMConfig] 配置信息
    @param cache_key Optional[str] 缓存键
    @return BaseLLM LLM实例
    @throws ValidationException 配置无效时抛出异常
    Note: 创建指定类型的LLM实例，支持缓存
    """

@staticmethod
def create_ollama_llm(
    model_name: str,
    base_url: str = "http://localhost:11434",
    cache_key: Optional[str] = None,
    **kwargs
) -> OllamaLLM:
    """
    创建Ollama LLM实例
    
    @param model_name str 模型名称
    @param base_url str 服务地址
    @param cache_key Optional[str] 缓存键
    @param kwargs Dict 额外配置参数
    @return OllamaLLM Ollama LLM实例
    Note: 创建Ollama LLM实例的便捷方法
    """

@staticmethod
def get_cached_llm(cache_key: str) -> Optional[BaseLLM]:
    """
    获取缓存的LLM实例
    
    @param cache_key str 缓存键
    @return Optional[BaseLLM] LLM实例或None
    Note: 从缓存中获取LLM实例
    """

@staticmethod
def clear_cache(cache_key: Optional[str] = None) -> None:
    """
    清除缓存
    
    @param cache_key Optional[str] 缓存键，为None时清除所有缓存
    Note: 清除指定或所有缓存的LLM实例
    """

@staticmethod
def list_cached_llms() -> List[str]:
    """
    列出缓存的LLM实例
    
    @return List[str] 缓存键列表
    Note: 获取所有缓存的LLM实例键
    """

@staticmethod
def get_supported_types() -> List[str]:
    """
    获取支持的LLM类型
    
    @return List[str] 支持的LLM类型列表
    Note: 获取工厂支持的所有LLM类型
    """
```

## 4. 便捷函数API

### 4.1 create_ollama_llm
```python
def create_ollama_llm(
    model_name: str,
    base_url: str = "http://localhost:11434",
    cache_key: Optional[str] = None,
    **kwargs
) -> OllamaLLM:
    """
    创建Ollama LLM实例的便捷函数
    
    @param model_name str 模型名称
    @param base_url str 服务地址
    @param cache_key Optional[str] 缓存键
    @param kwargs Dict 额外配置参数
    @return OllamaLLM Ollama LLM实例
    Note: 快速创建Ollama LLM实例
    """
```

### 4.2 get_default_llm
```python
def get_default_llm() -> BaseLLM:
    """
    获取默认LLM实例
    
    @return BaseLLM 默认LLM实例
    Note: 获取默认配置的LLM实例，自动缓存
    """
```

## 5. 输出解析器API

### 5.1 CleanOutputParser
```python
class CleanOutputParser(StrOutputParser):
    """清理输出解析器"""
    
    def parse(self, text: str) -> str:
        """
        解析并清理输出
        
        @param text str 原始文本
        @return str 清理后的文本
        Note: 移除think标签、HTML标签，清理多余空格
        """
```

### 5.2 JsonStructOutputParser
```python
class JsonStructOutputParser(StrOutputParser):
    """JSON结构输出解析器"""
    
    def parse(self, text: str) -> str:
        """
        解析JSON输出
        
        @param text str 原始文本
        @return str 提取的JSON字符串
        Note: 移除代码块标记，提取JSON内容
        """
```

## 6. 枚举类型API

### 6.1 LLMType
```python
class LLMType(Enum):
    """LLM类型枚举"""
    
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"
```

## 7. 使用示例

### 7.1 基础使用
```python
from app.llms import create_ollama_llm

# 创建LLM实例
llm = create_ollama_llm(
    model_name="llama3.2",
    temperature=0.1,
    max_tokens=1000
)

# 同步调用
response = llm("请介绍一下FastAPI框架")
print(response)

# 异步调用
async def async_example():
    response = await llm.ainvoke("请分析机器学习的应用")
    print(response)
```

### 7.2 工厂模式使用
```python
from app.llms import LLMFactory, LLMType

# 创建高温度LLM(创意)
creative_llm = LLMFactory.create_llm(
    LLMType.OLLAMA,
    {
        "model_name": "llama3.2",
        "temperature": 0.9,
        "max_tokens": 500
    },
    cache_key="creative_llm"
)

# 创建低温度LLM(分析)
analytical_llm = LLMFactory.create_llm(
    LLMType.OLLAMA,
    {
        "model_name": "llama3.2",
        "temperature": 0.1,
        "max_tokens": 1000
    },
    cache_key="analytical_llm"
)

# 使用不同的LLM
creative_response = creative_llm("请创作一个有趣的故事")
analytical_response = analytical_llm("请分析这个数据的趋势")
```

### 7.3 链式调用
```python
# 创建普通链
chain = llm.create_chain("请为{product}写一段产品描述")
result = chain.invoke({"product": "智能手表"})

# 创建JSON链
json_chain = llm.create_json_chain(
    "请以JSON格式返回{topic}的要点，包含title、points、summary字段"
)
result = json_chain.invoke({"topic": "人工智能发展"})
```

### 7.4 流式输出
```python
from app.llms import LLMConfig, LLMFactory, LLMType

# 创建支持流式输出的配置
config = LLMConfig(
    model_name="llama3.2",
    base_url="http://localhost:11434",
    stream=True,
    temperature=0.1
)

llm = LLMFactory.create_llm(LLMType.OLLAMA, config)

# 流式生成
async def stream_example():
    print("流式输出: ", end="")
    async for chunk in llm._generate_stream("请写一首关于秋天的诗"):
        print(chunk, end="", flush=True)
    print()

# 运行示例
import asyncio
asyncio.run(stream_example())
```

### 7.5 批量处理
```python
# 批量同步调用
prompts = [
    "请简述Python的特点",
    "请介绍机器学习的基本概念",
    "请说明API的作用"
]

responses = llm.batch(prompts)
for i, response in enumerate(responses):
    print(f"问题{i+1}: {response}")

# 批量异步调用
async def batch_async_example():
    responses = await llm.abatch(prompts)
    for i, response in enumerate(responses):
        print(f"异步问题{i+1}: {response}")
```

### 7.6 错误处理
```python
from app.core.exceptions import ValidationException

try:
    # 使用无效配置
    config = LLMConfig(
        model_name="",  # 空模型名
        base_url="invalid_url"
    )
    llm = OllamaLLM(config)
except ValidationException as e:
    print(f"配置错误: {e}")

try:
    # 调用不存在的模型
    llm = create_ollama_llm(model_name="non_existent_model")
    response = llm("测试")
except Exception as e:
    print(f"调用错误: {e}")
```

### 7.7 缓存管理
```python
# 创建并缓存LLM实例
llm1 = LLMFactory.create_llm(
    LLMType.OLLAMA,
    {"model_name": "llama3.2"},
    cache_key="my_llm"
)

# 获取缓存实例
llm2 = LLMFactory.get_cached_llm("my_llm")
print(f"实例相同: {llm1 is llm2}")  # True

# 列出缓存实例
cached_keys = LLMFactory.list_cached_llms()
print(f"缓存的LLM: {cached_keys}")

# 清除特定缓存
LLMFactory.clear_cache("my_llm")

# 清除所有缓存
LLMFactory.clear_cache()
```

### 7.8 模型管理
```python
# 获取可用模型
models = llm.get_available_models()
print(f"可用模型: {models}")

# 异步获取模型
async def get_models_async():
    models = await llm.get_available_models_async()
    print(f"异步获取模型: {models}")

# 获取模型信息
model_info = llm.get_model_info()
print(f"模型信息: {model_info}")

# 更新配置
llm.update_config({
    "temperature": 0.5,
    "max_tokens": 2000
})
```

## 8. 最佳实践

### 8.1 配置管理
```python
# 推荐: 使用环境变量或配置文件
import os

config = LLMConfig(
    model_name=os.getenv("OLLAMA_MODEL", "llama3.2"),
    base_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
    temperature=float(os.getenv("LLM_TEMPERATURE", "0.1")),
    max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1000"))
)
```

### 8.2 异步使用
```python
# 推荐: 在异步环境中使用异步方法
async def process_requests(prompts: List[str]):
    llm = create_ollama_llm("llama3.2")
    
    # 并发处理
    tasks = [llm.ainvoke(prompt) for prompt in prompts]
    responses = await asyncio.gather(*tasks)
    
    return responses
```

### 8.3 错误处理
```python
# 推荐: 完整的错误处理
async def safe_llm_call(prompt: str) -> str:
    try:
        llm = get_default_llm()
        response = await llm.ainvoke(prompt)
        return response
    except ValidationException as e:
        logger.error(f"配置错误: {e}")
        return "配置错误，请检查LLM设置"
    except Exception as e:
        logger.error(f"LLM调用失败: {e}")
        return "抱歉，服务暂时不可用"
```

### 8.4 性能优化
```python
# 推荐: 使用缓存和连接复用
class LLMService:
    def __init__(self):
        self.llm = LLMFactory.create_llm(
            LLMType.OLLAMA,
            {"model_name": "llama3.2"},
            cache_key="service_llm"
        )
    
    async def process(self, prompt: str) -> str:
        # 复用同一个LLM实例
        return await self.llm.ainvoke(prompt)
```

## 9. 常见问题

### 9.1 连接问题
**问题**: 无法连接到Ollama服务  
**解决**: 检查Ollama服务是否运行，确认URL和端口正确

```bash
# 检查Ollama服务状态
curl http://localhost:11434/api/tags

# 启动Ollama服务
ollama serve
```

### 9.2 模型问题
**问题**: 模型不存在或未下载  
**解决**: 确认模型已下载到本地

```bash
# 列出已下载的模型
ollama list

# 下载模型
ollama pull llama3.2
```

### 9.3 性能问题
**问题**: 响应时间过长  
**解决**: 调整配置参数，使用缓存

```python
# 优化配置
config = LLMConfig(
    model_name="llama3.2",
    max_tokens=500,  # 减少最大令牌数
    temperature=0.1,  # 降低温度提高确定性
    timeout=60  # 增加超时时间
)
```

## 10. 版本更新

### 10.1 当前版本: v1.0.0
- 支持Ollama集成
- 基础LLM接口
- 工厂模式管理
- 输出解析器
- 链式调用支持

### 10.2 计划版本: v1.1.0
- OpenAI集成
- 更多输出解析器
- 性能监控
- 自动重试机制

### 10.3 计划版本: v1.2.0
- Anthropic集成
- 流式输出优化
- 批量处理增强
- 更完善的错误处理

## 11. 联系支持

如有问题或建议，请联系：
- **开发者**: malou
- **邮箱**: malou@example.com
- **项目地址**: https://github.com/your-org/aiplatform

---

*本文档随代码更新而更新，请以最新版本为准。* 