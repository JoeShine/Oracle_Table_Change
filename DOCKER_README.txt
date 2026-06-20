# Oracle 数据批量修改工具 - Docker 部署指南

## 快速开始

### Easy Connect 连接方式（推荐）

本工具使用 **Easy Connect** 方式连接Oracle数据库，**无需任何配置文件**。

**连接字符串格式：**
```
host:port/service_name
```

**示例：**
```
192.168.1.100:1521/ORCL
oracle-server:1521/ORCL.localdomain
db.example.com:1521/MYDB
```

---

## 部署步骤

### 步骤1：准备 Oracle Instant Client（仅需Basic包）

从Oracle官网下载 Instant Client Basic：
https://www.oracle.com/database/technologies/instant-client/downloads.html

选择 Linux x86-64 版本，推荐 21.15 或更高版本。

**注意：** 只需要 Basic 包，**不需要配置任何文件**（如 tnsnames.ora、sqlnet.ora）。

下载后解压：
```bash
unzip instantclient-basic-linux.x64-21.15.0.0.0dbru.zip
```

### 步骤2：配置 Docker 挂载

编辑 `docker-compose.yml`，取消注释 Oracle 挂载行：
```yaml
volumes:
  - ./instantclient_21_15:/opt/oracle/instantclient_21_15:ro
```

### 步骤3：构建并启动

```bash
docker-compose build
docker-compose up -d
```

### 步骤4：访问应用

浏览器访问：http://localhost:6080

### 步骤5：配置数据库连接

在应用界面中直接输入 Easy Connect 连接字符串：

| 字段 | 输入内容 | 示例 |
|-----|---------|------|
| 主机地址 | host:port/service_name | 192.168.1.100:1521/ORCL |
| 用户名 | 数据库用户名 | scott |
| 密码 | 数据库密码 | tiger |

---

## Easy Connect 详细说明

### 什么是 Easy Connect？

Easy Connect 是 Oracle 提供的简化连接方式，允许在连接字符串中直接指定所有连接参数，无需依赖 tnsnames.ora 等配置文件。

### 连接字符串格式

```
host:port/service_name
```

或更详细的格式：
```
host:port/service_name[:policy][/instance_name]
```

### 支持的格式示例

| 格式 | 示例 | 说明 |
|-----|------|------|
| 基本格式 | 192.168.1.100:1521/ORCL | 最常用 |
| 带域名 | oracle-server:1521/ORCL.localdomain | 服务名带域名 |
| 主机名 | dbserver:1521/MYDB | 使用主机名 |
| IP地址 | 10.0.0.50:1521/PROD | 使用IP地址 |
| 默认端口 | oracle-server/ORCL | 端口默认1521可省略 |

### 优势

1. **无需配置文件** - 不需要 tnsnames.ora、sqlnet.ora
2. **简化部署** - 只需挂载 Instant Client 库文件
3. **易于维护** - 连接信息直接在应用中配置
4. **灵活切换** - 可随时更改连接目标

---

## 端口说明

| 端口 | 用途 | 说明 |
|-----|------|------|
| 6080 | noVNC Web | 浏览器直接访问，无需安装客户端 |
| 5900 | VNC | 使用 VNC Viewer 等客户端连接 |

---

## 数据持久化

以下目录通过 Docker 卷挂载实现持久化：

| 容器路径 | 说明 |
|---------|------|
| /app/config.json | 配置文件（连接信息、模板等） |
| /app/logs | 日志目录 |
| /app/data | 数据目录（Excel文件等） |
| /app/backups | 备份目录 |

---

## 常用命令

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 进入容器
docker-compose exec oracle-batch-updater bash

# 查看容器状态
docker-compose ps

# 查看资源使用
docker stats oracle-batch-updater
```

---

## 资源限制

默认配置：
- CPU 限制：2核
- 内存限制：2GB

可在 docker-compose.yml 中调整：
```yaml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 4G
```

---

## 故障排查

### 问题1：无法连接数据库

**检查步骤：**
```bash
# 1. 检查 Oracle Instant Client 是否挂载
docker-compose exec oracle-batch-updater bash
ls -la /opt/oracle/instantclient_21_15/*.so*

# 2. 检查网络连通性
ping oracle-server
telnet oracle-server 1521

# 3. 检查连接字符串格式
# 确保格式为: host:port/service_name
```

**常见错误：**
| 错误 | 原因 | 解决方案 |
|-----|------|---------|
| ORA-12541: TNS:no listener | 端口错误或服务未启动 | 检查端口和服务状态 |
| ORA-12514: TNS:listener does not know service | service_name错误 | 确认正确的service_name |
| ORA-12154: TNS:could not resolve connect identifier | 连接字符串格式错误 | 使用正确格式 |

### 问题2：浏览器无法访问

```bash
docker-compose exec oracle-batch-updater bash
curl http://localhost:6080
```

### 问题3：中文显示乱码

```bash
docker-compose exec oracle-batch-updater bash
fc-list :lang=zh
```

---

## 安全建议

1. 不要在公网暴露 6080/5900 端口
2. 使用防火墙限制访问
3. 配置 VNC 密码（修改 Dockerfile）
4. 定期备份数据
5. 连接字符串中的密码会被 Base64 编码存储

---

## 升级步骤

1. 备份配置和数据：
```bash
cp config.json config.json.bak
tar -czf logs-backup.tar.gz logs/
```

2. 拉取新版本并重建：
```bash
git pull
docker-compose build
docker-compose up -d
```

---

## 注意事项

1. Oracle Instant Client 需要从 Oracle 官网下载，需要 Oracle 账号
2. **无需配置 tnsnames.ora 等文件**，使用 Easy Connect 方式
3. 生产环境建议配置 VNC 密码和 HTTPS
4. 连接字符串格式：`host:port/service_name`