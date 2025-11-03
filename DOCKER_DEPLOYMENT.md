# 🐳 Docker部署指南

## 📋 目录

1. [服务器准备](#服务器准备)
2. [快速开始](#快速开始)
3. [详细部署步骤](#详细部署步骤)
4. [配置说明](#配置说明)
5. [数据持久化](#数据持久化)
6. [HTTPS配置](#https配置)
7. [监控和维护](#监控和维护)
8. [常见问题](#常见问题)

---

## 🖥️ 服务器准备

### 最低配置要求

- **CPU**: 2核
- **内存**: 4GB
- **硬盘**: 20GB可用空间
- **操作系统**: Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- **网络**: 稳定的互联网连接

### 推荐配置

- **CPU**: 4核
- **内存**: 8GB
- **硬盘**: 50GB SSD
- **操作系统**: Ubuntu 22.04 LTS

---

## 🚀 快速开始

### 一键安装脚本

在服务器上运行以下命令：

```bash
# 下载安装脚本
curl -O https://raw.githubusercontent.com/your-repo/install-docker.sh
chmod +x install-docker.sh

# 运行安装脚本
./install-docker.sh

# 退出并重新登录以使docker组生效
exit
# 重新SSH登录
```

### 克隆项目并启动

```bash
# 克隆项目
git clone https://github.com/your-username/medical-news-mvp.git
cd medical-news-mvp

# 复制环境变量配置
cp .env.example .env

# 编辑环境变量（设置密码等）
vim .env
# 或者使用nano
nano .env

# 启动所有服务
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f
```

访问服务：
- 后端API: http://你的服务器IP:8000
- 管理后台: http://你的服务器IP:3000
- H5聊天页面: http://你的服务器IP:5173
- MinIO控制台: http://你的服务器IP:9001

---

## 📝 详细部署步骤

### 步骤1: 安装Docker和Docker Compose

#### Ubuntu/Debian

```bash
# 更新系统
sudo apt-get update
sudo apt-get upgrade -y

# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 添加当前用户到docker组
sudo usermod -aG docker $USER

# 安装Docker Compose
sudo apt-get install -y docker-compose-plugin

# 验证安装
docker --version
docker compose version
```

#### CentOS/RHEL

```bash
# 安装Docker
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动Docker
sudo systemctl start docker
sudo systemctl enable docker

# 添加用户到docker组
sudo usermod -aG docker $USER
```

**重要**: 添加到docker组后，必须退出并重新登录才能生效！

### 步骤2: 克隆项目

```bash
# 如果还没有git，先安装
sudo apt-get install -y git

# 克隆项目
git clone https://github.com/your-username/medical-news-mvp.git
cd medical-news-mvp

# 查看项目结构
ls -la
```

### 步骤3: 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑配置文件
vim .env
```

**必须修改的配置项**:

```bash
# 数据库密码（必须修改！）
POSTGRES_PASSWORD=your_strong_password_here

# MinIO密码（必须修改！）
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=your_strong_minio_password_here

# OpenAI API密钥（如果需要RAG功能）
OPENAI_API_KEY=sk-your-real-openai-api-key

# 前端URL（生产环境域名）
FRONTEND_URL=https://your-domain.com
```

### 步骤4: 启动服务

```bash
# 构建并启动所有服务
docker compose up -d

# 这个命令会：
# 1. 构建后端镜像
# 2. 构建管理后台镜像
# 3. 构建H5页面镜像
# 4. 启动PostgreSQL
# 5. 启动Redis
# 6. 启动MinIO
# 7. 启动所有应用

# 首次启动可能需要5-10分钟
# 可以查看实时日志
docker compose logs -f
```

### 步骤5: 验证部署

```bash
# 查看所有容器状态
docker compose ps

# 应该看到所有服务都是 healthy 或 running

# 检查后端API
curl http://localhost:8000/health

# 应该返回 {"status":"healthy"}
```

### 步骤6: 初始化MinIO存储桶

MinIO需要手动创建存储桶：

```bash
# 访问MinIO控制台
http://你的服务器IP:9001

# 使用.env中配置的用户名密码登录

# 点击 "Buckets" -> "Create Bucket"
# 创建以下三个bucket:
# 1. medical-news-raw
# 2. medical-news-clean
# 3. medical-news-attachments

# 将bucket设置为private（默认）
```

或者使用MinIO客户端（mc）：

```bash
# 进入MinIO容器
docker exec -it medical-news-minio sh

# 配置mc
mc alias set local http://localhost:9000 minioadmin your_password

# 创建bucket
mc mb local/medical-news-raw
mc mb local/medical-news-clean
mc mb local/medical-news-attachments

# 退出容器
exit
```

---

## ⚙️ 配置说明

### docker-compose.yml 核心配置

#### 服务端口映射

```yaml
services:
  postgres: 5432:5432    # PostgreSQL数据库
  redis: 6379:6379       # Redis缓存
  minio: 9000:9000       # MinIO API
        9001:9001        # MinIO控制台
  backend: 8000:8000     # 后端API
  admin-frontend: 3000:80     # 管理后台
  h5-frontend: 5173:80        # H5聊天页面
```

#### 数据卷持久化

```yaml
volumes:
  postgres_data:  # PostgreSQL数据
  redis_data:     # Redis数据
  minio_data:     # MinIO对象存储
```

数据存储位置：`/var/lib/docker/volumes/`

### 环境变量详解

| 变量名 | 说明 | 默认值 | 必须修改 |
|--------|------|--------|---------|
| POSTGRES_PASSWORD | 数据库密码 | postgres123 | ✅ 是 |
| MINIO_ROOT_USER | MinIO用户名 | minioadmin | ✅ 是 |
| MINIO_ROOT_PASSWORD | MinIO密码 | minioadmin123 | ✅ 是 |
| OPENAI_API_KEY | OpenAI API密钥 | sk-your-api-key | ⚠️ 可选 |
| FRONTEND_URL | 前端域名 | http://localhost | ⚠️ 建议修改 |

---

## 💾 数据持久化

### 备份数据

```bash
# 创建备份目录
mkdir -p ~/backups

# 备份PostgreSQL数据库
docker exec medical-news-postgres pg_dump -U postgres medical_news > ~/backups/db_backup_$(date +%Y%m%d).sql

# 备份MinIO数据
docker exec medical-news-minio mc mirror local/medical-news-raw ~/backups/minio/raw
docker exec medical-news-minio mc mirror local/medical-news-clean ~/backups/minio/clean

# 或者直接备份Docker数据卷
docker run --rm \
  -v medical-news-mvp_postgres_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/postgres_data_$(date +%Y%m%d).tar.gz /data
```

### 恢复数据

```bash
# 恢复PostgreSQL数据库
cat ~/backups/db_backup_20250101.sql | docker exec -i medical-news-postgres psql -U postgres medical_news

# 恢复MinIO数据
docker exec medical-news-minio mc mirror ~/backups/minio/raw local/medical-news-raw
```

### 定期备份脚本

创建 `backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR=~/backups
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
docker exec medical-news-postgres pg_dump -U postgres medical_news > $BACKUP_DIR/db_$DATE.sql

# 压缩
gzip $BACKUP_DIR/db_$DATE.sql

# 删除7天前的备份
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/db_$DATE.sql.gz"
```

添加到crontab（每天凌晨2点备份）:

```bash
chmod +x backup.sh
crontab -e
# 添加以下行
0 2 * * * /path/to/backup.sh >> /var/log/backup.log 2>&1
```

---

## 🔒 HTTPS配置

### 使用Let's Encrypt免费证书

#### 1. 安装Certbot

```bash
# Ubuntu
sudo apt-get install -y certbot

# 申请证书
sudo certbot certonly --standalone -d your-domain.com

# 证书会保存在
# /etc/letsencrypt/live/your-domain.com/fullchain.pem
# /etc/letsencrypt/live/your-domain.com/privkey.pem
```

#### 2. 复制证书到项目目录

```bash
# 创建SSL目录
mkdir -p nginx/ssl

# 复制证书
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/

# 设置权限
sudo chmod 644 nginx/ssl/fullchain.pem
sudo chmod 600 nginx/ssl/privkey.pem
```

#### 3. 启用Nginx代理

```bash
# 编辑nginx/nginx.conf，取消HTTPS部分的注释

# 启动Nginx服务
docker compose --profile with-nginx up -d

# 现在可以通过以下地址访问
# https://your-domain.com/v1/          - 后端API
# https://your-domain.com/admin/       - 管理后台
# https://your-domain.com/h5/          - H5聊天页面
```

#### 4. 自动续期证书

```bash
# 添加到crontab（每月1号凌晨3点检查续期）
0 3 1 * * certbot renew --quiet && docker compose restart nginx
```

---

## 📊 监控和维护

### 查看服务状态

```bash
# 查看所有容器状态
docker compose ps

# 查看资源使用情况
docker stats

# 查看特定服务日志
docker compose logs backend
docker compose logs -f backend  # 实时跟踪

# 查看最近100行日志
docker compose logs --tail=100 backend
```

### 重启服务

```bash
# 重启所有服务
docker compose restart

# 重启单个服务
docker compose restart backend

# 停止所有服务
docker compose down

# 停止并删除数据卷（危险！）
docker compose down -v
```

### 更新应用

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker compose up -d --build

# 或者分步操作
docker compose build
docker compose up -d
```

### 数据库维护

```bash
# 进入PostgreSQL容器
docker exec -it medical-news-postgres psql -U postgres medical_news

# 查看数据库大小
\l+

# 查看表大小
\dt+

# 清理vacuum
VACUUM ANALYZE;

# 退出
\q
```

### 清理Docker资源

```bash
# 清理未使用的镜像
docker image prune -a

# 清理未使用的卷
docker volume prune

# 清理所有未使用的资源
docker system prune -a
```

---

## 🛠️ 常见问题

### 1. 端口被占用

```bash
# 错误：Bind for 0.0.0.0:8000 failed: port is already allocated

# 查找占用端口的进程
sudo lsof -i :8000
# 或者
sudo netstat -tulpn | grep 8000

# 停止占用端口的进程
sudo kill -9 [PID]

# 或者修改docker-compose.yml中的端口映射
# 例如：将 "8000:8000" 改为 "8080:8000"
```

### 2. 服务无法启动

```bash
# 查看详细错误日志
docker compose logs backend

# 常见原因：
# - 环境变量配置错误
# - 数据库连接失败
# - 依赖服务未启动

# 解决方法：检查.env文件，确保所有依赖服务都healthy
docker compose ps
```

### 3. 数据库连接失败

```bash
# 检查PostgreSQL是否启动
docker compose ps postgres

# 查看PostgreSQL日志
docker compose logs postgres

# 测试数据库连接
docker exec -it medical-news-postgres psql -U postgres -d medical_news

# 如果失败，检查.env中的POSTGRES_PASSWORD是否正确
```

### 4. 前端无法访问后端API

```bash
# 检查后端是否正常运行
curl http://localhost:8000/health

# 检查Nginx配置（如果使用）
docker compose logs admin-frontend

# 确保docker-compose.yml中的网络配置正确
# 所有服务都应该在同一个network中
```

### 5. MinIO无法创建bucket

```bash
# 确保MinIO已启动
docker compose ps minio

# 进入MinIO容器手动创建
docker exec -it medical-news-minio sh
mc alias set local http://localhost:9000 minioadmin your_password
mc mb local/medical-news-raw
```

### 6. 内存不足

```bash
# 检查系统内存
free -h

# 检查Docker容器内存使用
docker stats

# 如果内存不足，可以：
# 1. 增加服务器内存
# 2. 添加swap空间
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 3. 限制容器内存使用（在docker-compose.yml中）
services:
  backend:
    mem_limit: 512m
    mem_reservation: 256m
```

### 7. 磁盘空间不足

```bash
# 检查磁盘使用
df -h

# 清理Docker资源
docker system prune -a

# 清理日志
sudo journalctl --vacuum-time=7d

# 删除旧的备份
find ~/backups -mtime +30 -delete
```

---

## 🔐 安全建议

### 1. 修改默认密码

```bash
# .env文件中必须修改：
POSTGRES_PASSWORD=强密码
MINIO_ROOT_PASSWORD=强密码
```

### 2. 防火墙配置

```bash
# 只开放必要的端口
sudo ufw allow 22      # SSH
sudo ufw allow 80      # HTTP
sudo ufw allow 443     # HTTPS
sudo ufw enable

# 其他端口只允许内网访问
sudo ufw allow from 10.0.0.0/8 to any port 8000
sudo ufw allow from 10.0.0.0/8 to any port 9000
```

### 3. 定期更新

```bash
# 更新系统
sudo apt-get update && sudo apt-get upgrade -y

# 更新Docker镜像
docker compose pull
docker compose up -d
```

### 4. 启用日志监控

使用工具如Prometheus + Grafana监控Docker容器。

---

## 📚 附录

### 完整的一键部署脚本

保存为 `deploy.sh`:

```bash
#!/bin/bash
set -e

echo "=== 医疗资讯MVP项目一键部署脚本 ==="

# 检查是否为root用户
if [[ $EUID -eq 0 ]]; then
   echo "请不要使用root用户运行此脚本"
   exit 1
fi

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "Docker未安装，正在安装..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "Docker安装完成！请退出并重新登录，然后再次运行此脚本"
    exit 0
fi

# 检查Docker Compose是否安装
if ! docker compose version &> /dev/null; then
    echo "Docker Compose未安装，正在安装..."
    sudo apt-get install -y docker-compose-plugin
fi

# 克隆项目（如果还没有）
if [ ! -d "medical-news-mvp" ]; then
    echo "克隆项目..."
    git clone https://github.com/your-username/medical-news-mvp.git
fi

cd medical-news-mvp

# 配置环境变量
if [ ! -f ".env" ]; then
    echo "配置环境变量..."
    cp .env.example .env
    echo "请编辑.env文件设置密码，然后运行: docker compose up -d"
    exit 0
fi

# 启动服务
echo "启动所有服务..."
docker compose up -d

echo "=== 部署完成！==="
echo "后端API: http://$(hostname -I | awk '{print $1}'):8000"
echo "管理后台: http://$(hostname -I | awk '{print $1}'):3000"
echo "H5页面: http://$(hostname -I | awk '{print $1}'):5173"
echo "MinIO控制台: http://$(hostname -I | awk '{print $1}'):9001"
echo ""
echo "请记得创建MinIO的三个存储桶："
echo "  - medical-news-raw"
echo "  - medical-news-clean"
echo "  - medical-news-attachments"
```

使用方法：

```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 📞 技术支持

如有问题，请查看：
1. [GitHub Issues](https://github.com/your-username/medical-news-mvp/issues)
2. [API文档](./API_DOCUMENTATION.md)
3. [项目结构说明](./PROJECT_STRUCTURE.md)

---

**祝部署顺利！** 🎉
