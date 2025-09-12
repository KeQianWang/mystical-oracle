# 🔮 Mystical Oracle 更新说明

## 📋 更新内容

本次更新为系统添加了完整的用户认证和聊天历史记录功能，使系统更加安全和用户友好。

## 🚀 新增功能

### 1. 用户认证系统
- **用户注册**: `POST /auth/register`
- **用户登录**: `POST /auth/login`
- **获取用户信息**: `GET /auth/me`
- **更新用户信息**: `PUT /auth/me`

### 2. JWT 认证
- 所有API接口都需要先登录后才能使用
- 支持Bearer Token认证
- 令牌过期时间可配置

### 3. 聊天历史记录
- **获取聊天会话列表**: `GET /chat/sessions`
- **获取聊天历史记录**: `GET /chat/history`
- **获取特定会话历史**: `GET /chat/session/{session_id}/history`
- **更新会话标题**: `PUT /chat/session/{session_id}/title`
- **删除会话**: `DELETE /chat/session/{session_id}`
- **获取聊天统计**: `GET /chat/stats`
- **获取最近聊天记录**: `GET /chat/recent`

### 4. 数据存储
- **MySQL 数据库**: 存储用户信息和聊天历史
- **Redis 继续使用**: 存储Agent的实时聊天记忆
- **用户隔离**: 每个用户的聊天记录完全独立

## 📁 新增文件

```
mystical-oracle/
├── models/database.py           # 数据库模型
├── database/connection.py       # 数据库连接
├── services/auth.py             # 认证服务
├── services/user_service.py     # 用户服务
├── services/chat_history_service.py  # 聊天历史服务
├── init_database.py             # 数据库初始化脚本
└── api_test.py                  # API测试脚本
```

## 🔧 配置更新

### 新增环境变量
```bash
# MySQL 数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=mystical_oracle
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=mystical_oracle

# JWT 认证配置
JWT_SECRET_KEY=your_jwt_secret_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=720
```

### 新增依赖
```bash
# 数据库
sqlalchemy==2.0.36
pymysql==1.1.1
alembic==1.14.0

# 认证
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

## 🛠️ 使用步骤

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，设置数据库和JWT配置
```

### 3. 创建MySQL数据库
```sql
CREATE DATABASE mystical_oracle CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. 初始化数据库
```bash
python init_database.py
```

### 5. 启动服务
```bash
python server.py
```

### 6. 测试API
```bash
python api_test.py
```

## 📊 数据库结构

### users 表
- id: 用户ID
- username: 用户名
- email: 邮箱
- password_hash: 密码哈希
- nickname: 昵称
- avatar_url: 头像URL
- is_active: 是否激活
- is_admin: 是否管理员
- created_at: 创建时间
- updated_at: 更新时间
- last_login_at: 最后登录时间

### chat_sessions 表
- id: 会话ID
- user_id: 用户ID
- session_id: 会话唯一标识
- title: 会话标题
- mood: 会话情绪
- is_active: 是否活跃
- created_at: 创建时间
- updated_at: 更新时间

### chat_histories 表
- id: 历史记录ID
- user_id: 用户ID
- session_id: 会话ID
- user_message: 用户消息
- assistant_message: 助手回复
- mood: 对话情绪
- message_type: 消息类型
- metadata: 元数据
- created_at: 创建时间

## 🔐 安全特性

1. **密码加密**: 使用bcrypt加密存储用户密码
2. **JWT认证**: 使用JSON Web Token进行用户认证
3. **用户隔离**: 每个用户只能访问自己的聊天记录
4. **输入验证**: 所有用户输入都经过严格验证
5. **错误处理**: 完善的错误处理和日志记录

## 🎯 API 使用示例

### 用户注册
```bash
curl -X POST "http://localhost:8001/auth/register" \
     -H "Content-Type: application/json" \
     -d '{"username": "testuser", "email": "test@example.com", "password": "password123"}'
```

### 用户登录
```bash
curl -X POST "http://localhost:8001/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "testuser", "password": "password123"}'
```

### 聊天对话
```bash
curl -X POST "http://localhost:8001/chat" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_TOKEN_HERE" \
     -d '{"query": "你好，我想了解一下我的运势"}'
```

### 获取聊天历史
```bash
curl -X GET "http://localhost:8001/chat/history" \
     -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 🔄 向后兼容性

- 现有的Agent功能保持不变
- Redis聊天记忆功能继续使用
- 所有原有的工具和功能都能正常工作
- 新增的功能是可选的，不影响现有功能

## 🐛 已知问题

1. WebSocket接口尚未添加认证支持
2. 需要进一步完善错误处理和日志记录
3. 数据库迁移脚本需要进一步完善

## 📝 下一步计划

1. 为WebSocket添加认证支持
2. 添加用户头像上传功能
3. 实现数据库备份和恢复功能
4. 添加管理员面板
5. 优化数据库查询性能