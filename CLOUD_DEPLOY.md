# 云部署配置 - Mystical Oracle 神秘预言师

## 1. 阿里云部署 (Alibaba Cloud)

### ECS + Docker Compose 部署

```bash
# 1. 购买 ECS 实例（推荐配置）
# - CPU: 4核心
# - 内存: 8GB
# - 存储: 40GB SSD
# - 操作系统: Ubuntu 20.04

# 2. 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 3. 部署应用
git clone <your-repo>
cd mystical-oracle
docker-compose up -d
```

### 使用容器服务 ACK

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mystical-oracle
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mystical-oracle
  template:
    metadata:
      labels:
        app: mystical-oracle
    spec:
      containers:
      - name: mystical-oracle
        image: your-registry/mystical-oracle:latest
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        - name: QDRANT_PATH
          value: "/app/qdrant_data"
---
apiVersion: v1
kind: Service
metadata:
  name: mystical-oracle-service
spec:
  selector:
    app: mystical-oracle
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

## 2. 腾讯云部署 (Tencent Cloud)

### 轻量应用服务器部署

```bash
# Lighthouse 实例配置
# - 2核4GB内存
# - 80GB SSD云硬盘
# - Ubuntu 20.04

# 快速部署脚本
#!/bin/bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
git clone <repo-url>
cd mystical-oracle
sudo docker-compose up -d

# 开放端口
sudo ufw allow 8000
sudo ufw enable
```

### 容器服务 TKE 部署

```yaml
# tke-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mystical-oracle-config
data:
  REDIS_URL: "redis://redis:6379"
  OLLAMA_BASE_URL: "http://ollama:11434"
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mystical-oracle
spec:
  serviceName: mystical-oracle
  replicas: 1
  selector:
    matchLabels:
      app: mystical-oracle
  template:
    metadata:
      labels:
        app: mystical-oracle
    spec:
      containers:
      - name: app
        image: mystical-oracle:latest
        envFrom:
        - configMapRef:
            name: mystical-oracle-config
        volumeMounts:
        - name: data
          mountPath: /app/qdrant_data
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
```

## 3. AWS 部署

### ECS Fargate 部署

```yaml
# ecs-task-definition.json
{
  "family": "mystical-oracle",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "mystical-oracle",
      "image": "your-ecr-repo/mystical-oracle:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "REDIS_URL",
          "value": "redis://elasticache-endpoint:6379"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/mystical-oracle",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### 使用 AWS App Runner

```yaml
# apprunner.yaml
version: 1.0
runtime: docker
build:
  commands:
    build:
      - echo "Build started on `date`"
      - docker build -t mystical-oracle .
run:
  runtime-version: latest
  command: python server.py
  network:
    port: 8000
    env: PORT
  env:
    - name: REDIS_URL
      value: "redis://your-elasticache-endpoint:6379"
```

## 4. Google Cloud Platform 部署

### Cloud Run 部署

```bash
# 构建镜像并推送到 GCR
gcloud builds submit --tag gcr.io/PROJECT_ID/mystical-oracle

# 部署到 Cloud Run
gcloud run deploy mystical-oracle \
  --image gcr.io/PROJECT_ID/mystical-oracle \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars REDIS_URL=redis://redis-ip:6379
```

### GKE 部署

```yaml
# gke-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mystical-oracle
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mystical-oracle
  template:
    metadata:
      labels:
        app: mystical-oracle
    spec:
      containers:
      - name: mystical-oracle
        image: gcr.io/PROJECT_ID/mystical-oracle:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: mystical-oracle-service
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
  selector:
    app: mystical-oracle
```

## 5. Microsoft Azure 部署

### Container Instances

```bash
# 创建资源组
az group create --name mystical-oracle-rg --location eastus

# 部署容器实例
az container create \
  --resource-group mystical-oracle-rg \
  --name mystical-oracle \
  --image your-registry/mystical-oracle:latest \
  --cpu 2 \
  --memory 4 \
  --ports 8000 \
  --environment-variables \
    REDIS_URL=redis://redis-cache.redis.cache.windows.net:6380 \
  --dns-name-label mystical-oracle-app
```

### Azure Kubernetes Service (AKS)

```yaml
# aks-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mystical-oracle
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mystical-oracle
  template:
    metadata:
      labels:
        app: mystical-oracle
    spec:
      containers:
      - name: mystical-oracle
        image: mysticaloracle.azurecr.io/mystical-oracle:latest
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: connection-string
```

## 6. 自动化部署

### GitHub Actions CI/CD

```yaml
# .github/workflows/deploy.yml
name: Deploy to Cloud

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Build Docker image
      run: |
        docker build -t mystical-oracle:${{ github.sha }} .
        
    - name: Deploy to production
      run: |
        # 部署逻辑，根据云平台选择相应的部署命令
        echo "Deploying to production..."
```

### Docker Hub 自动构建

```dockerfile
# 在 Dockerfile 添加构建参数
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

LABEL org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="mystical-oracle" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/your-username/mystical-oracle" \
      org.label-schema.version=$VERSION
```

## 7. 监控和日志

### Prometheus + Grafana 监控

```yaml
# monitoring/docker-compose.monitoring.yml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### ELK Stack 日志收集

```yaml
# logging/docker-compose.logging.yml
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.14.0
    environment:
      - discovery.type=single-node
      
  logstash:
    image: docker.elastic.co/logstash/logstash:7.14.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
      
  kibana:
    image: docker.elastic.co/kibana/kibana:7.14.0
    ports:
      - "5601:5601"
```

## 8. 成本优化建议

### 资源配置

| 部署环境 | CPU | 内存 | 存储 | 月成本估算 |
|---------|-----|------|------|------------|
| 开发环境 | 1核 | 2GB | 20GB | $20-40 |
| 测试环境 | 2核 | 4GB | 40GB | $40-80 |
| 生产环境 | 4核 | 8GB | 100GB | $100-200 |

### 成本优化策略

1. **使用 Spot 实例**（AWS/Azure）
2. **自动缩放**配置
3. **预留实例**折扣
4. **存储层次化**（冷热数据分离）
5. **CDN 加速**静态资源

## 9. 安全配置

### 网络安全

```bash
# 防火墙配置
ufw allow ssh
ufw allow 80
ufw allow 443
ufw deny 6379  # Redis 仅内网访问
ufw deny 6333  # Qdrant 仅内网访问
ufw enable
```

### SSL/TLS 配置

```yaml
# nginx-ssl.conf
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 10. 备份策略

### 数据备份

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)

# 备份 Redis 数据
docker exec redis redis-cli BGSAVE
docker cp redis:/data/dump.rdb ./backups/redis_$DATE.rdb

# 备份 Qdrant 数据
docker exec qdrant tar -czf /tmp/qdrant_backup_$DATE.tar.gz /qdrant/storage
docker cp qdrant:/tmp/qdrant_backup_$DATE.tar.gz ./backups/

# 上传到云存储
aws s3 cp ./backups/ s3://your-backup-bucket/ --recursive
```

这个云部署指南涵盖了主要云平台的部署方案，可以根据具体需求选择合适的平台和配置。