# AI 卜卦 API 文档

## 项目概述

AI 卜卦（Mystical Oracle）是一个基于 FastAPI 的 AI 算命聊天机器人后端服务，提供智能算命对话、语音合成、用户认证和会话管理等功能。

**Base URL**: `http://localhost:8000` (开发环境)

**技术栈**: FastAPI + SQLAlchemy + JWT Authentication

---

## 认证说明

### JWT Bearer Token 认证

大部分接口需要在请求头中携带 JWT Token：

```
Authorization: Bearer <access_token>
```

### 获取 Token

通过 `/auth/login` 接口登录后获取 `access_token`，在后续请求中使用。

### 公开接口（无需认证）

- `/` - 服务状态
- `/health` - 健康检查
- `/auth/register` - 用户注册
- `/auth/login` - 用户登录
- `/add_knowledge` - 添加知识库
- `/audio/{audio_id}` - 获取音频文件

---

## 1. 系统接口

### 1.1 服务状态

**接口**: `GET /`

**描述**: 获取服务运行状态

**认证**: 无需认证

**响应示例**:
```json
{
  "response": "AI 卜卦服务正在运行",
  "service": "Mystical Oracle"
}
```

---

### 1.2 健康检查

**接口**: `GET /health`

**描述**: 获取服务健康状态，包括配置验证、TTS 可用性、数据库状态等

**认证**: 无需认证

**响应示例**:
```json
{
  "status": "healthy",
  "config_valid": true,
  "tts_available": true,
  "database_status": "connected",
  "version": "1.0.0",
  "timestamp": "2026-01-17T10:30:00Z"
}
```

---

## 2. 用户认证接口

### 2.1 用户注册

**接口**: `POST /auth/register`

**描述**: 注册新用户账号

**认证**: 无需认证

**请求体**:
```json
{
  "username": "string",      // 必填，用户名
  "password": "string",      // 必填，密码
  "phone": "string"          // 必填，手机号
}
```

**响应示例**:
```json
{
  "id": 1,
  "username": "user123",
  "phone": "13800138000",
  "email": null,
  "avatar_url": null,
  "is_active": true,
  "is_admin": false,
  "created_at": "2026-01-17T10:30:00Z",
  "updated_at": "2026-01-17T10:30:00Z",
  "last_login_at": null
}
```

---

### 2.2 用户登录

**接口**: `POST /auth/login`

**描述**: 用户登录获取访问令牌

**认证**: 无需认证

**请求体**:
```json
{
  "username": "string",      // 必填，用户名
  "password": "string"       // 必填，密码
}
```

**响应示例**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

### 2.3 获取当前用户信息

**接口**: `GET /auth/me`

**描述**: 获取当前登录用户的详细信息

**认证**: 需要 Bearer Token

**响应示例**:
```json
{
  "id": 1,
  "username": "user123",
  "phone": "13800138000",
  "email": "user@example.com",
  "avatar_url": "https://example.com/avatar.jpg",
  "is_active": true,
  "is_admin": false,
  "created_at": "2026-01-17T10:30:00Z",
  "updated_at": "2026-01-17T10:30:00Z",
  "last_login_at": "2026-01-17T11:00:00Z"
}
```

---

### 2.4 更新当前用户信息

**接口**: `PUT /auth/update_me`

**描述**: 更新当前登录用户的信息

**认证**: 需要 Bearer Token

**请求体**:
```json
{
  "email": "string",         // 可选，邮箱
  "phone": "string",         // 可选，手机号
  "avatar_url": "string",    // 可选，头像 URL
  "password": "string"       // 可选，新密码
}
```

**响应示例**:
```json
{
  "id": 1,
  "username": "user123",
  "phone": "13800138000",
  "email": "newemail@example.com",
  "avatar_url": "https://example.com/new-avatar.jpg",
  "is_active": true,
  "is_admin": false,
  "created_at": "2026-01-17T10:30:00Z",
  "updated_at": "2026-01-17T12:00:00Z",
  "last_login_at": "2026-01-17T11:00:00Z"
}
```

---

## 3. 聊天对话接口

### 3.1 标准聊天

**接口**: `POST /chat`

**描述**: 发送消息给算命师，获取完整响应

**认证**: 需要 Bearer Token

**请求体**:
```json
{
  "query": "string",         // 必填，用户消息
  "session_id": "string",    // 可选，会话 ID（不传则创建新会话）
  "enable_tts": false,       // 可选，是否启用语音合成，默认 false
  "async_mode": false        // 可选，是否异步模式，默认 false
}
```

**响应示例**:
```json
{
  "response": "根据你的生辰八字，我看到...",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "audio_url": null,         // 如果 enable_tts=true，返回音频 URL
  "mood": "神秘",
  "created_at": "2026-01-17T12:00:00Z"
}
```

---

### 3.2 流式聊天（SSE）

**接口**: `POST /chat/stream`

**描述**: 发送消息给算命师，通过 Server-Sent Events 实时流式返回响应

**认证**: 需要 Bearer Token

**请求体**:
```json
{
  "query": "string",         // 必填，用户消息
  "session_id": "string",    // 可选，会话 ID
  "enable_tts": false,       // 可选，是否启用语音合成
  "async_mode": true         // 建议设为 true
}
```

**响应格式**: `text/event-stream`

**SSE 事件流示例**:
```
data: {"type": "content", "content": "與", "session_id": "550e8400-e29b-41d4-a716-446655440000", "mood": "default", "voice_style": "chat"}

data: {"type": "content", "content": "算", "session_id": "550e8400-e29b-41d4-a716-446655440000", "mood": "default", "voice_style": "chat"}

data: {"type": "content", "content": "命", "session_id": "550e8400-e29b-41d4-a716-446655440000", "mood": "default", "voice_style": "chat"}

data: {"type": "complete", "content": "與算命", "session_id": "550e8400-e29b-41d4-a716-446655440000", "mood": "default", "voice_style": "chat", "audio_url": null}
```

**前端使用示例**:
```javascript
const eventSource = new EventSource('/chat/stream', {
  headers: {
    'Authorization': 'Bearer <token>'
  }
});

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'content') {
    // 逐字显示内容
    console.log(data.content);
  } else if (data.type === 'complete') {
    // 响应完成（如果已流式渲染过 content，就不要重复追加完整内容）
    console.log('Session ID:', data.session_id);
    eventSource.close();
  }
};
```

---

## 4. 聊天历史接口

### 4.1 获取聊天历史

**接口**: `GET /chat/history`

**描述**: 获取指定会话的聊天历史记录

**认证**: 需要 Bearer Token

**查询参数**:
- `session_id` (string, 必填): 会话 ID
- `skip` (integer, 可选): 跳过记录数，默认 0
- `limit` (integer, 可选): 返回记录数，默认 50

**请求示例**:
```
GET /chat/history?session_id=550e8400-e29b-41d4-a716-446655440000&skip=0&limit=20
```

**响应示例**:
```json
{
  "total": 45,
  "skip": 0,
  "limit": 20,
  "messages": [
    {
      "id": 1,
      "user_message": "我想算算今年的运势",
      "assistant_message": "根据你的生辰八字...",
      "mood": "神秘",
      "message_type": "fortune",
      "created_at": "2026-01-17T10:00:00Z"
    },
    {
      "id": 2,
      "user_message": "那我的事业呢？",
      "assistant_message": "你的事业运势...",
      "mood": "智慧",
      "message_type": "fortune",
      "created_at": "2026-01-17T10:05:00Z"
    }
  ]
}
```

---

### 4.2 获取聊天统计

**接口**: `GET /chat/stats`

**描述**: 获取当前用户的聊天统计信息

**认证**: 需要 Bearer Token

**响应示例**:
```json
{
  "total_messages": 150,
  "total_sessions": 12,
  "messages_today": 8,
  "most_active_session": "550e8400-e29b-41d4-a716-446655440000",
  "average_messages_per_session": 12.5
}
```

---

### 4.3 获取最近聊天

**接口**: `GET /chat/recent`

**描述**: 获取最近几天的聊天记录

**认证**: 需要 Bearer Token

**查询参数**:
- `days` (integer, 可选): 最近天数，范围 1-30，默认 7

**请求示例**:
```
GET /chat/recent?days=7
```

**响应示例**:
```json
{
  "days": 7,
  "messages": [
    {
      "id": 150,
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "user_message": "今天运势如何？",
      "assistant_message": "今天你的运势...",
      "mood": "神秘",
      "created_at": "2026-01-17T10:00:00Z"
    }
  ]
}
```

---

## 5. 会话管理接口

### 5.1 创建会话

**接口**: `POST /sessions/creat_sessions`

**描述**: 创建新的聊天会话

**认证**: 需要 Bearer Token

**请求体**:
```json
{
  "title": "string"          // 可选，会话标题
}
```

**响应示例**:
```json
{
  "id": 1,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": 1,
  "title": "2026年运势咨询",
  "created_at": "2026-01-17T10:00:00Z",
  "updated_at": "2026-01-17T10:00:00Z"
}
```

---

### 5.2 获取会话列表

**接口**: `GET /sessions/get_sessions`

**描述**: 获取当前用户的所有会话列表

**认证**: 需要 Bearer Token

**查询参数**:
- `skip` (integer, 可选): 跳过记录数，默认 0
- `limit` (integer, 可选): 返回记录数，默认 50

**请求示例**:
```
GET /sessions/get_sessions?skip=0&limit=20
```

**响应示例**:
```json
{
  "total": 12,
  "skip": 0,
  "limit": 20,
  "sessions": [
    {
      "id": 1,
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "user_id": 1,
      "title": "2026年运势咨询",
      "created_at": "2026-01-17T10:00:00Z",
      "updated_at": "2026-01-17T12:00:00Z"
    },
    {
      "id": 2,
      "session_id": "660e8400-e29b-41d4-a716-446655440001",
      "user_id": 1,
      "title": "事业发展咨询",
      "created_at": "2026-01-16T15:00:00Z",
      "updated_at": "2026-01-16T16:00:00Z"
    }
  ]
}
```

---

### 5.3 更新会话

**接口**: `PUT /sessions/update/{session_id}`

**描述**: 更新指定会话的信息（如标题）

**认证**: 需要 Bearer Token

**路径参数**:
- `session_id` (string, 必填): 会话 ID

**请求体**:
```json
{
  "title": "string"          // 可选，新的会话标题
}
```

**请求示例**:
```
PUT /sessions/update/550e8400-e29b-41d4-a716-446655440000
```

**响应示例**:
```json
{
  "id": 1,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": 1,
  "title": "更新后的标题",
  "created_at": "2026-01-17T10:00:00Z",
  "updated_at": "2026-01-17T13:00:00Z"
}
```

---

### 5.4 删除会话

**接口**: `DELETE /sessions/delete/{session_id}`

**描述**: 删除指定会话及其所有聊天记录

**认证**: 需要 Bearer Token

**路径参数**:
- `session_id` (string, 必填): 会话 ID

**请求示例**:
```
DELETE /sessions/delete/550e8400-e29b-41d4-a716-446655440000
```

**响应示例**:
```json
{
  "message": "会话删除成功",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## 6. 知识库接口

### 6.1 添加知识库内容

**接口**: `POST /add_knowledge`

**描述**: 通过 URL 或文件上传添加内容到知识库

**认证**: 无需认证

**请求格式**: `multipart/form-data`

**表单字段**:
- `url` (string, 可选): 要添加的网页 URL
- `file` (file, 可选): 要上传的文件（支持 `docx`, `pdf`, `xlsx` 格式）
- `session_id` (string, 必填): 关联的会话 ID

**注意**: `url` 和 `file` 至少提供一个

**请求示例（使用 URL）**:
```bash
curl -X POST "http://localhost:8000/add_knowledge" \
  -F "url=https://example.com/article" \
  -F "session_id=550e8400-e29b-41d4-a716-446655440000"
```

**请求示例（上传文件）**:
```bash
curl -X POST "http://localhost:8000/add_knowledge" \
  -F "file=@document.pdf" \
  -F "session_id=550e8400-e29b-41d4-a716-446655440000"
```

**响应示例**:
```json
{
  "message": "知识库内容添加成功",
  "source": "https://example.com/article",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### 6.2 查询知识库内容

**接口**: `GET /knowledge/{session_id}`

**描述**: 根据 session_id 查询当前知识库内容

**认证**: 无需认证

**路径参数**:
- `session_id` (string, 必填): 会话 ID

**请求示例**:
```bash
curl -X GET "http://localhost:8000/knowledge/550e8400-e29b-41d4-a716-446655440000"
```

**响应示例**:
```json
{
  "sources": [
    "https://example.com/article",
    "document.pdf"
  ]
}
```

---

## 7. 音频接口

### 7.1 获取音频文件

**接口**: `GET /audio/{audio_id}`

**描述**: 获取生成的语音合成音频文件

**认证**: 无需认证

**路径参数**:
- `audio_id` (string, 必填): 音频文件 ID

**请求示例**:
```
GET /audio/abc123def456
```

**响应**: 返回 MP3 音频文件流

**Content-Type**: `audio/mpeg`

---

## 8. WebSocket 实时通信

### 8.1 WebSocket 连接

**接口**: `WS /ws`

**描述**: 建立 WebSocket 连接进行实时双向通信

**认证**: Token 认证（两种方式）

**方式 1: 查询参数传递 Token**
```
ws://localhost:8000/ws?token=<access_token>
```

**方式 2: 首条消息传递 Token**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  // 首条消息发送认证信息
  ws.send(JSON.stringify({
    type: 'auth',
    token: '<access_token>'
  }));
};
```

**发送消息格式**:
```json
{
  "type": "chat",
  "query": "我想算算今年的运势",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "enable_tts": false
}
```

**接收消息格式（流式响应）**:
```json
{
  "type": "content",
  "content": "與",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "mood": "default",
  "voice_style": "chat"
}
```

```json
{
  "type": "complete",
  "content": "哈哈，老夫年歲已高，偶爾言語難免重複，還望見諒。",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "audio_url": null,
  "mood": "default",
  "voice_style": "chat"
}
```

**前端使用示例**:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws?token=' + accessToken);

ws.onopen = () => {
  console.log('WebSocket 连接已建立');

  // 发送聊天消息
  ws.send(JSON.stringify({
    type: 'chat',
    query: '我想算算今年的运势',
    session_id: sessionId,
    enable_tts: false
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'content') {
    // 逐字显示响应内容
    appendToChat(data.content);
  } else if (data.type === 'complete') {
    // 响应完成（如果已流式渲染过 content，就不要重复追加完整内容）
    console.log('会话 ID:', data.session_id);
    if (data.audio_url) {
      playAudio(data.audio_url);
    }
  } else if (data.type === 'error') {
    console.error('错误:', data.message);
  }
};

ws.onerror = (error) => {
  console.error('WebSocket 错误:', error);
};

ws.onclose = () => {
  console.log('WebSocket 连接已关闭');
};
```

---

## 9. 错误响应格式

所有接口在发生错误时返回统一的错误格式：

```json
{
  "detail": "错误描述信息"
}
```

### 常见 HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权（Token 无效或过期） |
| 403 | 禁止访问（权限不足） |
| 404 | 资源不存在 |
| 422 | 请求参数验证失败 |
| 500 | 服务器内部错误 |

### 错误示例

**401 未授权**:
```json
{
  "detail": "未提供有效的认证凭据"
}
```

**422 参数验证失败**:
```json
{
  "detail": [
    {
      "loc": ["body", "username"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## 10. 数据模型

### User（用户）
```typescript
interface User {
  id: number;
  username: string;
  phone: string;
  email?: string;
  avatar_url?: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
  updated_at: string;
  last_login_at?: string;
}
```

### ChatSession（会话）
```typescript
interface ChatSession {
  id: number;
  session_id: string;
  user_id: number;
  title?: string;
  created_at: string;
  updated_at: string;
}
```

### ChatMessage（聊天消息）
```typescript
interface ChatMessage {
  id: number;
  user_message: string;
  assistant_message: string;
  mood?: string;
  message_type?: string;
  created_at: string;
}
```

### Token（认证令牌）
```typescript
interface Token {
  access_token: string;
  token_type: string;
  expires_in: number;
}
```

---

## 11. 前端开发建议

### 11.1 推荐的页面结构

1. **登录/注册页面**
   - 使用 `/auth/login` 和 `/auth/register`
   - 存储 `access_token` 到 localStorage 或 sessionStorage

2. **主聊天页面**
   - 左侧：会话列表（使用 `/sessions/get_sessions`）
   - 中间：聊天对话区（使用 `/chat/stream` 实现流式显示）
   - 右侧：用户信息和设置

3. **会话历史页面**
   - 显示历史会话（使用 `/chat/history`）
   - 支持搜索和筛选

4. **用户设置页面**
   - 显示和编辑用户信息（使用 `/auth/me` 和 `/auth/update_me`）

### 11.2 推荐的技术选型

- **实时聊天**: 优先使用 WebSocket (`/ws`) 或 SSE (`/chat/stream`)
- **状态管理**: 使用 Redux/Zustand 管理用户状态和会话状态
- **HTTP 客户端**: Axios 或 Fetch API，配置统一的请求拦截器添加 Token
- **UI 组件**: 需要支持流式文本显示、音频播放、文件上传等功能

### 11.3 关键功能实现提示

**1. Token 管理**
```javascript
// 请求拦截器自动添加 Token
axios.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器处理 401 错误
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Token 过期，跳转到登录页
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

**2. 流式聊天显示**
```javascript
// 使用 SSE 实现流式显示
async function streamChat(query, sessionId) {
  const response = await fetch('/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      query,
      session_id: sessionId,
      enable_tts: false,
      async_mode: true
    })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let hasStreamedContent = false;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop();

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        if (data.type === 'content') {
          // 逐字追加到界面
          appendToken(data.content);
          hasStreamedContent = true;
        } else if (data.type === 'complete') {
          // 完成（避免重复追加完整内容）
          if (data.content && !hasStreamedContent) {
            appendToken(data.content);
          }
          onComplete(data.session_id, data.audio_url);
        }
      }
    }
  }
}
```

**3. 会话管理**
```javascript
// 创建新会话
async function createSession(title) {
  const response = await axios.post('/sessions/creat_sessions', { title });
  return response.data.session_id;
}

// 加载会话列表
async function loadSessions() {
  const response = await axios.get('/sessions/get_sessions', {
    params: { skip: 0, limit: 50 }
  });
  return response.data.sessions;
}

// 删除会话
async function deleteSession(sessionId) {
  await axios.delete(`/sessions/delete/${sessionId}`);
}
```

---

## 12. 附录

### 12.1 环境变量配置

项目需要配置以下环境变量（`.env` 文件）：

```env
# 数据库配置
DATABASE_URL=sqlite:///./mystical_oracle.db

# JWT 配置
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# AI 模型配置
OPENAI_API_KEY=your-openai-api-key
MODEL_NAME=gpt-4

# TTS 配置（可选）
TTS_ENABLED=true
TTS_API_KEY=your-tts-api-key
```

### 12.2 开发调试

**启动后端服务**:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**API 文档**:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 12.3 联系方式

如有问题，请联系开发团队或查看项目文档。

---

**文档版本**: v1.0
**最后更新**: 2026-01-17
**维护者**: Mystical Oracle Team
