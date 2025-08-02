# Mystical Oracle 部署指南

## 部署选项

### 1. 单实例部署（开发/测试环境）

使用单个应用实例，适合开发和测试：

```bash
docker-compose -f docker-compose.single.yml up -d
```

应用将在 http://localhost:8000 可用

### 2. 负载均衡部署（生产环境）

使用Nginx负载均衡器和多个应用实例，提供高可用性：

```bash
docker-compose up -d
```

应用将在 http://localhost 可用，nginx自动进行负载均衡

## 目录结构说明

```
mystical-oracle/
├── audio/              # TTS生成的音频文件统一存储目录
├── logs/               # 应用日志文件统一存储目录
├── nginx/              # Nginx配置文件
│   └── nginx.conf     # 负载均衡配置
├── docker-compose.yml          # 生产环境配置（负载均衡）
├── docker-compose.single.yml   # 单实例配置
└── ...
```

## 环境变量配置

在 `.env` 文件中配置以下变量：

```env
# 音频输出目录（Docker内部路径）
AUDIO_OUTPUT_DIR=/app/audio

# 日志配置
LOG_DIR=/app/logs
LOG_RETENTION_DAYS=30

# 其他现有配置...
```

## 负载均衡特性

- **负载均衡策略**: ip_hash，确保同一用户访问同一后端实例
- **健康检查**: 自动检测和移除不健康的实例
- **故障转移**: 主实例故障时自动切换到备份实例
- **静态文件缓存**: 自动缓存CSS、JS、图片等静态资源
- **音频文件缓存**: 音频文件缓存1小时，减少服务器负载

## 监控和日志

- **应用日志**: 自动按日期命名，超过30天自动清理
- **Nginx日志**: 存储在nginx_logs volume中
- **健康检查**: 所有服务都配置了健康检查端点

## 扩展说明

如需增加更多应用实例，修改 `docker-compose.yml`：

1. 复制 `mystical-oracle-2` 服务配置
2. 修改服务名和INSTANCE_ID
3. 在nginx配置中添加新的server