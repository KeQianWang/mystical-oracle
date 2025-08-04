# Docker 部署指南 - Mystical Oracle 神秘预言师

## 快速开始

### 1. 环境准备

确保已安装以下软件：
- Docker (>= 20.10)
- Docker Compose (>= 2.0)

### 2. 环境变量配置

创建 `.env` 文件（可选，系统已设置默认值）：

```bash
# 模型配置
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=qwen2.5:latest
MODEL_TEMPERATURE=0.7

# 数据库配置  
REDIS_URL=redis://redis:6379
QDRANT_PATH=/app/qdrant_data

# API 密钥（可选）
SERPAPI_API_KEY=your_serpapi_key
YUANFENJU_API_KEY=your_yuanfenju_key
MICROSOFT_TTS_KEY=your_azure_tts_key
```

### 3. 启动服务

```bash
# 构建并启动所有服务
cd /Users/king/Develop/self/mystical-oracle
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f mystical-oracle
```

### 4. 验证部署

- API 服务：http://localhost:8000
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

## 服务架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Mystical      │    │     Redis       │    │    Qdrant      │
│   Oracle        │◄───┤   (缓存/会话)    │    │   (向量数据库)   │
│   (主应用)       │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐
│     Ollama      │
│   (AI 模型)      │
│                 │
└─────────────────┘
```

## 端口说明

| 服务 | 端口 | 说明 |
|------|------|------|
| mystical-oracle | 8000 | 主应用 API 端口 |
| redis | 6379 | Redis 数据库 |
| qdrant | 6333/6334 | Qdrant HTTP/gRPC |
| ollama | 11434 | Ollama API |

## 数据持久化

项目使用 Docker volumes 进行数据持久化：

- `redis_data`: Redis 数据
- `qdrant_data`: 应用数据目录
- `qdrant_storage`: Qdrant 存储
- `ollama_data`: Ollama 模型数据

## 维护命令

```bash
# 重启服务
docker-compose restart

# 更新镜像
docker-compose pull
docker-compose up -d

# 清理数据（谨慎操作）
docker-compose down -v

# 查看资源使用
docker stats

# 进入容器调试
docker-compose exec mystical-oracle bash
```

## 故障排除

### 常见问题

1. **Ollama 模型下载失败**
   ```bash
   # 手动下载模型
docker-compose exec ollama ollama pull qwen2.5:latest
   ```

2. **端口冲突**
   ```bash
   # 修改 docker-compose.yml 中的端口映射
ports:
  - "8001:8000"  # 将宿主机端口改为 8001
   ```

3. **内存不足**
   ```bash
   # 增加 Docker 内存限制或使用更小的模型
# 在 docker-compose.yml 中添加:
deploy:
  resources:
    limits:
      memory: 4G
   ```

### 日志查看

```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs mystical-oracle
docker-compose logs ollama

# 实时跟踪日志
docker-compose logs -f --tail=100 mystical-oracle
```

## 性能优化

### 1. 调整模型参数

在 `.env` 文件中设置：
```bash
MODEL_TEMPERATURE=0.5  # 降低随机性
```

### 2. Redis 优化

```bash
# 在 docker-compose.yml 中配置 Redis
command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

### 3. 资源限制

```yaml
# 在 docker-compose.yml 中添加资源限制
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '1.0'
    reservations:
      memory: 1G
      cpus: '0.5'
```

## 扩展部署

### 单容器部署

如果您需要更简单的部署方式，可以使用单容器部署：

```bash
docker-compose -f docker-compose.single.yml up -d
```

### 多实例部署

```bash
# 启动多个应用实例
docker-compose up -d --scale mystical-oracle=3
```

### 负载均衡

使用 nginx 或 traefik 进行负载均衡：

```yaml
# nginx.conf
upstream mystical_oracle {
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
}

server {
    listen 80;
    location / {
        proxy_pass http://mystical_oracle;
    }
}
```

## 部署注意事项

- 确保防火墙已开放所需端口
- 在生产环境中，建议使用 HTTPS 加密通信
- 定期备份持久化数据卷
- 对于高流量场景，考虑使用 Kubernetes 进行容器编排
- 监控系统资源使用情况，及时调整资源限制

---

使用 Docker 部署可以大大简化环境配置和依赖管理，让您专注于使用和扩展 Mystical Oracle 服务。