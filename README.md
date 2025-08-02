# Mystical Oracle 神秘预言师

一个基于 LangChain 的智能算命师聊天机器人，支持八字排盘、解梦、摇卦占卜等功能，并集成了语音合成能力。

## 功能特点

- 🔮 **智能对话**：基于 LangChain 框架的自然语言处理
- 📊 **八字排盘**：支持传统八字算命分析
- 💭 **解梦服务**：智能解析梦境内容
- 🎲 **摇卦占卜**：传统易经占卜功能
- 🔍 **实时搜索**：集成搜索引擎获取最新信息
- 📚 **知识库**：本地向量数据库存储运势、星座信息
- 🎵 **语音合成**：支持 Microsoft Azure TTS 文字转语音
- 😊 **情绪感知**：根据用户情绪调整回复风格
- 💾 **会话记忆**：Redis 存储聊天历史

## 项目结构

```
mystical-oracle/
├── agent.py              # 核心 Agent 类
├── server.py             # FastAPI Web 服务器
├── config/               # 配置管理
│   ├── settings.py       # 系统配置
│   └── keys.py          # API 密钥管理
├── prompts/             # 提示词模板
│   ├── system_prompts.py # 系统提示词
│   └── mood_prompts.py  # 情绪相关提示词
├── services/            # 业务服务
│   ├── tools.py         # 工具函数集合
│   └── tts_service.py   # 语音合成服务
├── models/              # 数据模型
│   └── user.py          # 用户数据模型
├── utils/               # 工具函数
│   └── helpers.py       # 辅助函数
├── requirements.txt     # 依赖包列表
└── README.md           # 项目说明文档
```

## 环境要求

- Python 3.8+
- Redis (用于会话存储)
- Qdrant (向量数据库)
- Ollama (本地大语言模型)

## 安装配置

1. **克隆项目**
   ```bash
   cd /Users/king/Develop/self/mystical-oracle
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境变量**
   创建 `.env` 文件并配置以下环境变量：
   ```env
   # API 密钥
   SERPAPI_API_KEY=your_serpapi_key
   YUANFENJU_API_KEY=your_yuanfenju_key
   MICROSOFT_TTS_KEY=your_azure_tts_key
   
   # 数据库配置
   REDIS_URL=redis://localhost:6379
   QDRANT_PATH=./qdrant_data
   
   # 模型配置
   OLLAMA_MODEL=qwen2.5:latest
   OLLAMA_BASE_URL=http://localhost:11434
   ```

4. **启动外部服务**
   ```bash
   # 启动 Redis
   redis-server
   
   # 启动 Ollama
   ollama serve
   
   # 下载模型
   ollama pull qwen2.5:latest
   ```

## 使用方法

### 启动服务器

```bash
python server.py
```

服务器将在 `http://localhost:8000` 启动

### API 端点

- **POST /chat** - 智能对话
  ```json
  {
    "query": "帮我算一下今天的运势"
  }
  ```

- **GET /audio/{audio_id}** - 获取语音文件
- **POST /add_urls** - 添加网页到知识库
- **GET /health** - 健康检查
- **WebSocket /ws** - 实时对话

### API 文档

启动服务后访问 `http://localhost:8000/docs` 查看完整 API 文档

## 核心功能

### 八字排盘
输入用户姓名和出生年月日时，系统会调用专业八字 API 进行排盘分析。

### 解梦服务
用户描述梦境内容，系统会提取关键词并返回专业解梦结果。

### 摇卦占卜
无需用户输入，系统自动摇卦并返回卦象解析。

### 情绪感知
系统会分析用户输入的情绪倾向，动态调整回复风格和语音合成参数。

### 语音合成
支持将文字回复转换为语音，根据不同情绪使用不同的语音风格。

## 配置说明

### 模型配置
在 `config/settings.py` 中可以调整：
- 使用的 LLM 模型
- 温度、max_tokens 等参数
- 系统提示词设置

### API 密钥管理
在 `config/keys.py` 中集中管理所有 API 密钥，支持环境变量和默认值。

### 提示词模板
在 `prompts/` 目录下管理所有提示词模板，便于维护和调整。

## 开发指南

### 添加新工具
1. 在 `services/tools.py` 中定义新的工具函数
2. 使用 `@tool` 装饰器标注
3. 在 `agent.py` 中将工具添加到工具列表

### 自定义情绪
1. 在 `prompts/mood_prompts.py` 中添加新的情绪类型
2. 定义对应的角色设定和语音风格
3. 更新情绪分析提示词

### 扩展 API
1. 在 `server.py` 中添加新的路由
2. 实现对应的业务逻辑
3. 更新 API 文档

## 注意事项

- 确保 Redis 和 Ollama 服务正常运行
- API 密钥需要有效才能使用相应功能
- 语音合成需要 Microsoft Azure TTS 服务
- 建议在生产环境中使用更强的密钥管理方案

## 许可证

本项目仅供学习和研究使用。

## 更新日志

### v2.1.0
- 重构项目结构，提高可维护性
- 集成语音合成功能
- 添加情绪感知和动态回复
- 优化配置管理
- 完善错误处理

---

🔮 愿神秘预言师为您指引人生方向！