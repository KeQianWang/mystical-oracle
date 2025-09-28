# Mystical Oracle 神秘预言师

<div align="center">

![Mystical Oracle](https://img.shields.io/badge/Mystical%20Oracle-v2.1.0-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-orange)
![LangChain](https://img.shields.io/badge/LangChain-0.3.26-red)

**一个基于 LangChain 的智能算命师聊天机器人，支持八字排盘、解梦、摇卦占卜等功能，并集成了语音合成能力。**

[功能特性](#功能特性) · [快速开始](#快速开始) · [架构设计](#架构设计) · [开发指南](#开发指南) · [部署指南](#部署指南)

</div>

## 功能特性

### 🎯 核心功能
- 🔮 **智能对话系统**：基于 LangChain 框架的自然语言处理，支持多种大语言模型
- 📊 **八字排盘分析**：集成专业八字API，支持传统八字算命分析
- 💭 **智能解梦服务**：基于关键词提取和语义分析的梦境解析
- 🎲 **摇卦占卜功能**：传统易经占卜，自动生成卦象解析
- 🔍 **实时搜索能力**：集成 SerpAPI 获取最新信息
- 📚 **本地知识库**：基于 Qdrant 向量数据库的专业知识存储

### 🎵 增强功能
- 😊 **情绪感知系统**：分析用户情绪，动态调整回复风格
- 🔊 **语音合成服务**：支持 Microsoft Azure TTS 文字转语音
- 💾 **会话记忆管理**：Redis 存储聊天历史，支持多轮对话
- 🌐 **WebSocket 实时通信**：支持流式输出和实时交互

### 🛡️ 企业级特性
- 🔐 **JWT 身份认证**：安全的用户认证和授权机制
- 🗄️ **多数据库支持**：MySQL 主数据库 + Redis 缓存 + Qdrant 向量存储
- 🐳 **容器化部署**：完整的 Docker Compose 部署方案
- 📊 **监控与日志**：完善的日志记录和错误处理机制

## 架构设计

```
mystical-oracle/
├── agent.py                  # 核心 Agent 类 - 主逻辑控制器
├── server.py                 # FastAPI Web 服务器 - 应用入口
├── config/                   # 配置管理模块
│   ├── __init__.py
│   ├── logger.py            # 日志配置
│   └── settings.py         # 统一配置管理
├── prompts/                 # 提示词模板
│   ├── __init__.py
│   ├── mood_prompts.py      # 情绪相关提示词
│   └── system_prompts.py    # 系统提示词
├── services/                # 业务服务层
│   ├── auth.py              # 身份认证服务
│   ├── chat_service.py      # 聊天服务
│   ├── tts_service.py       # 语音合成服务
│   ├── redis_service.py     # Redis 缓存服务
│   └── knowledge_service.py # 知识库服务
├── routers/                 # API 路由层
│   ├── auth.py              # 认证路由
│   ├── chat.py              # 聊天路由
│   ├── websocket.py         # WebSocket 路由
│   └── ...
├── models/                  # 数据模型层
│   ├── user.py              # 用户数据模型
│   └── database.py          # 数据库模型
├── tools/                   # 工具函数层
│   └── tools.py             # LangChain 工具集
├── utils/                   # 工具函数
│   └── helpers.py           # 辅助函数
├── database/                # 数据库相关
│   └── connection.py        # 数据库连接
├── requirements.txt         # Python 依赖包
├── docker-compose.yml       # Docker 编排配置
└── Dockerfile              # Docker 镜像构建
```

### 技术栈
- **后端框架**: FastAPI + Uvicorn
- **AI框架**: LangChain + LangSmith
- **语言模型**: 支持 OpenAI GPT 和 Ollama 本地模型
- **数据库**: MySQL (主数据) + Redis (缓存) + Qdrant (向量存储)
- **认证**: JWT + bcrypt
- **部署**: Docker + Docker Compose + Nginx
- **监控**: 结构化日志 + 健康检查

## 快速开始

### 环境要求
- **Python**: 3.8+
- **Redis**: 用于会话存储和缓存
- **MySQL**: 主数据库存储
- **Qdrant**: 向量数据库
- **Ollama**: 本地大语言模型（可选，也支持 OpenAI）
- **Docker & Docker Compose**: 容器化部署（推荐）

### 安装配置

#### 1. 克隆项目
```bash
git clone <repository-url>
cd mystical-oracle
```

#### 2. 环境配置
```bash
# 复制环境变量模板
cp .env.template .env

# 编辑环境变量
nano .env
```

**环境变量配置示例**:
```env
# === 数据库配置 ===
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=mystical_oracle

# === Redis 配置 ===
REDIS_URL=redis://localhost:6379

# === 向量数据库配置 ===
QDRANT_PATH=./qdrant_data
QDRANT_COLLECTION_NAME=mystical_oracle
BASE_UPLOAD_DIR=./uploads

# === 模型配置（二选一） ===
# OpenAI 配置
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4
OPENAI_EMBEDDINGS=text-embedding-3-small

# Ollama 本地模型配置
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL_NAME=qwen2.5:latest
OLLAMA_EMBEDDINGS=nomic-embed-text

# === API 密钥 ===
SERPAPI_API_KEY=your_serpapi_key
YUANFENJU_API_KEY=your_yuanfenju_key
MICROSOFT_TTS_KEY=your_azure_tts_key

# === JWT 配置 ===
JWT_SECRET_KEY=your_jwt_secret_key
JWT_EXPIRE_MINUTES=720

# === 模型参数 ===
MODEL_TEMPERATURE=0.7
MAX_HISTORY_MESSAGES=20

# === 可选服务 ===
# LangSmith 监控
LANGSMITH_API_KEY=your_langsmith_key_here
```

#### 3. 依赖安装
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

#### 4. 启动外部服务
```bash
# 使用 Docker Compose（推荐）
docker-compose up -d redis mysql qdrant

# 或手动启动服务
redis-server          # Redis
# MySQL 服务启动...
# Qdrant 服务启动...
```

#### 5. 初始化语言模型
```bash
# 如果使用 Ollama 本地模型
ollama serve
ollama pull qwen2.5:latest
ollama pull nomic-embed-text
```

#### 6. 启动应用
```bash
# 开发模式启动
python server.py

# 或使用 Uvicorn 启动
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

服务器将在 `http://localhost:8001` 启动
API 文档: `http://localhost:8001/docs`


## 部署指南

### Docker 部署（推荐）

#### 1. 使用 Docker Compose
```bash
# 生产环境部署
docker-compose up -d

# 单容器部署
docker-compose -f docker-compose.single.yml up -d
```

#### 2. 环境配置
```bash
# 生产环境变量
cp .env.example .env.production
# 编辑生产环境配置...
```

#### 3. 服务访问
- **应用地址**: `http://localhost`
- **API 文档**: `http://localhost/docs`
- **管理后台**: `http://localhost/admin`（如果启用）

### 手动部署

#### 1. 安装系统依赖
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.8 python3-pip redis-server mysql-server

# CentOS/RHEL
sudo yum install python38 python3-pip redis mysql-server
```

#### 2. 数据库初始化
```bash
# MySQL
mysql -u root -p -e "CREATE DATABASE mystical_oracle;"

# Redis
redis-server --daemonize yes
```

#### 3. 启动服务
```bash
# 后台启动
nohup uvicorn server:app --host 0.0.0.0 --port 8001 > server.log 2>&1 &

# 使用进程管理器（如 systemd）
sudo systemctl enable mystical-oracle
sudo systemctl start mystical-oracle
```

### 生产环境配置

#### 1. 反向代理（Nginx）
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

#### 2. 安全配置
- 配置 HTTPS 证书
- 设置防火墙规则
- 定期备份数据库
- 监控日志文件

#### 3. 性能优化
- 配置 Redis 持久化
- 优化 MySQL 参数
- 启用 Gzip 压缩
- 配置负载均衡

## 核心功能详解

### 🔮 八字排盘
基于传统中国八字算命理论，结合现代AI技术：
- **输入要求**: 姓名、出生年月日时、性别、历法类型
- **API集成**: 使用缘分居专业八字API进行排盘分析
- **输出内容**: 八字命盘、五行分析、运势解读、人生建议
- **数据验证**: 完整的输入参数验证，确保数据准确性

### 💭 智能解梦
基于梦境数据库和语义分析技术：
- **关键词提取**: 自动识别梦境中的关键元素
- **语义分析**: 理解梦境情境和情感色彩
- **专业解析**: 结合周公解梦数据库进行解释
- **个性化建议**: 根据用户情况提供针对性建议

### 🎲 摇卦占卜
传统易经占卜与现代AI结合：
- **自动摇卦**: 无需用户手动操作，系统自动生成卦象
- **卦象解析**: 专业的卦辞解读和爻位分析
- **运势指导**: 提供实际的生活和工作建议
- **历史记录**: 保存占卜结果，支持回溯分析

### 😊 情绪感知系统
基于自然语言处理技术：
- **情绪识别**: 分析用户输入的情绪倾向（喜悦、忧虑、愤怒等）
- **动态调整**: 根据情绪自动调整回复风格和语气
- **个性化服务**: 为不同情绪状态提供定制化服务
- **语音适配**: 根据情绪选择不同的语音合成风格

### 🔊 语音合成服务
基于Microsoft Azure TTS技术：
- **多音色支持**: 提供多种语音角色选择
- **情绪适配**: 根据对话内容自动调整语音参数
- **高质量输出**: 支持多种音频格式和采样率
- **流式生成**: 支持实时语音生成和流式传输

## 开发指南

### 项目架构原则
- **SOLID原则**: 遵循单一职责、开放封闭、里氏替换、接口隔离、依赖倒置
- **分层架构**: 清晰的Controller-Service-Model分层
- **模块化设计**: 功能模块独立，便于维护和扩展
- **配置外置**: 所有配置项通过环境变量管理

### 添加新功能

#### 1. 添加新的LangChain工具
在 `tools/tools.py` 中添加：
```python
@tool
def your_new_tool(parameter: str) -> str:
    """工具功能描述"""
    try:
        # 实现工具逻辑
        result = do_something(parameter)
        return result
    except Exception as e:
        logger.error(f"工具执行失败: {e}")
        return "服务暂时不可用，请稍后再试。"
```

在 `agent.py` 中注册工具：
```python
from tools.tools import your_new_tool

# 在Master类中添加工具
self.tools = [bazi_cesuan, search, yaoyigua, jiemeng, get_info_from_knowledge, your_new_tool]
```

#### 2. 扩展API端点
在 `routers/` 目录下创建新的路由文件：
```python
from fastapi import APIRouter, Depends
from services.your_service import YourService

router = APIRouter(tags=["你的功能"])

@router.post("/your-endpoint")
def your_endpoint(data: YourModel):
    return YourService.process(data)
```

在 `server.py` 中注册路由：
```python
from routers import your_router

app.include_router(your_router.router)
```

#### 3. 自定义情绪类型
在 `prompts/mood_prompts.py` 中添加：
```python
class MoodPrompts:
    # 添加新的情绪类型
    NEW_MOOD = "new_mood"

    @classmethod
    def get_mood_role_set(cls, mood: str) -> str:
        role_sets = {
            # 现有情绪...
            cls.NEW_MOOD: "新的角色设定和回复风格"
        }
        return role_sets.get(mood, role_sets[cls.DEFAULT])
```

### 配置管理
所有配置项在 `config/settings.py` 中统一管理：

```python
# 添加新的配置项
class BotConfig:
    NEW_CONFIG_KEY: str = os.getenv("NEW_CONFIG_KEY", "default_value")

    @classmethod
    def get_new_config(cls) -> Dict[str, Any]:
        return {"key": cls.NEW_CONFIG_KEY}
```

### 数据库扩展
如需添加新的数据模型：
1. 在 `models/database.py` 中定义SQLAlchemy模型
2. 在 `database/connection.py` 中创建表
3. 在相应服务中实现CRUD操作

### 测试指南
```bash
# 运行单元测试
pytest tests/

# 运行集成测试
pytest tests/integration/

# 生成覆盖率报告
pytest --cov=mystical_oracle tests/
```

### 代码规范
- **代码风格**: 遵循PEP 8规范
- **类型注解**: 使用Python类型提示
- **文档字符串**: 遵循Google风格
- **错误处理**: 统一异常处理和日志记录

## 监控与维护

### 日志管理
- **结构化日志**: 所有日志采用JSON格式
- **分级记录**: DEBUG、INFO、WARNING、ERROR、CRITICAL
- **日志轮转**: 按日期和大小自动轮转
- **集中存储**: 可配置远程日志收集

### 健康检查
- **服务状态**: 检查所有依赖服务状态
- **数据库连接**: 验证数据库连接状态
- **API响应**: 监控关键API响应时间
- **资源使用**: 监控内存、CPU、磁盘使用情况

### 性能监控
- **响应时间**: API接口响应时间监控
- **并发处理**: WebSocket连接数监控
- **缓存命中率**: Redis缓存效果监控
- **错误率**: 接口错误率统计

## 常见问题

### Q: 如何切换语言模型？
A: 在 `.env` 文件中配置相应的模型参数：
- **OpenAI**: 设置 `OPENAI_API_KEY` 和 `OPENAI_MODEL`
- **Ollama**: 设置 `OLLAMA_BASE_URL` 和 `OLLAMA_MODEL_NAME`

### Q: 语音合成不工作怎么办？
A: 检查以下配置：
1. `MICROSOFT_TTS_KEY` 是否正确配置
2. 网络连接是否正常
3. 音频输出目录权限是否正确

### Q: 如何优化性能？
A: 可以通过以下方式优化：
1. 启用Redis缓存
2. 调整数据库连接池大小
3. 使用CDN加速静态资源
4. 启用Gzip压缩

### Q: 如何备份数据？
A: 建议定期备份：
```bash
# 备份MySQL
mysqldump -u user -p mystical_oracle > backup.sql

# 备份Redis
redis-cli save

# 备份Qdrant
cp -r qdrant_data qdrant_backup
```

## 许可证

本项目基于 MIT 许可证开源。详见 [LICENSE](LICENSE) 文件。

## 贡献指南

欢迎贡献代码！请遵循以下步骤：
1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 联系我们

- **问题反馈**: [GitHub Issues](https://github.com/mystical-oracle/issues)
- **功能建议**: [GitHub Discussions](https://github.com/mystical-oracle/discussions)
- **邮件联系**: 765197310@qq.com

---

<div align="center">

**🔮 愿神秘预言师为您指引人生方向！**

Made with ❤️ by Mystical Oracle Team

</div>