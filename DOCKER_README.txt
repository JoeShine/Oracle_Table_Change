# v2.9.1
# DBForge (Database Forge) - Docker 部署指南
版本: v2.9.0（多数据库支持版：Oracle / MySQL / SQL Server）

## 快速开始

### Easy Connect 连接方式（推荐，支持三种数据库）

本工具使用 **Easy Connect** 方式连接数据库，**无需任何配置文件**。

**Oracle 连接字符串格式：**
```
host:port/service_name
```
示例：
```
192.168.1.100:1521/ORCL
oracle-server:1521/ORCL.localdomain
```

**MySQL 连接字符串格式：**
```
host:port/database
```
示例：
```
192.168.1.100:3306/mydb
mysql-server:3306/mydb
```

**SQL Server 连接字符串格式：**
```
host[:port]/database
```
示例：
```
192.168.1.100:1433/MYDB
sqlserver:1433/MYDB
```

---

## 支持数据库清单（v2.9.0）

| 数据库 | 最低版本 | 驱动 | 是否需要系统客户端 |
|--------|---------|------|-------------------|
| Oracle | 11g | oracledb（纯 Python thin 模式） | 可选（thick 模式需要 Oracle Instant Client） |
| MySQL  | 5.7 | pymysql（纯 Python） | 否 |
| SQL Server | 2008 R2 | pyodbc + Microsoft ODBC Driver 17 for SQL Server | 是（驱动已内置在 Docker 镜像中） |

## 从 Docker 连接三种数据库的说明

### 1. 从 Docker 容器连接 Oracle

**方式 A：使用 oracledb thin 模式（推荐，无需额外依赖）**

oracledb 支持纯 Python thin 模式，无需安装 Oracle Instant Client。
在应用界面中直接输入 Easy Connect 连接字符串即可：
```
host:port/service_name
```

**方式 B：使用 Oracle Instant Client（thick 模式，需要挂载库文件）**

1. 从 Oracle 官网下载 Instant Client Basic（Linux x86-64）：
   https://www.oracle.com/database/technologies/instant-client/downloads.html

2. 解压到宿主机目录，例如：`./instantclient_21_15/`

3. 在 `docker-compose.yml` 中配置挂载（文件中已提供示例）：
```yaml
volumes:
  - ./instantclient_21_15:/opt/oracle/instantclient_21_15:ro
```

4. 构建并启动
```bash
docker-compose build
docker-compose up -d
```

### 2. 从 Docker 容器连接 MySQL（无需额外依赖）

MySQL 使用 pymysql 纯 Python 驱动，不需要系统客户端库。

1. 确保 MySQL 服务器允许远程连接：
   - 确认 bind-address = 0.0.0.0（或容器可达的地址）
   - 确认用户允许从容器 IP 登录（如：'user'@'%' 或 'user'@'172.%'）

2. 在应用界面中选择数据库类型为 "MySQL"，输入：
```
host:port/database
示例：192.168.1.100:3306/mydb
```

3. 如 MySQL 8.0 使用 caching_sha2_password 认证，确保 pymysql 版本 >= 0.9.3（Docker 镜像已内置适配版本）。

### 3. 从 Docker 容器连接 SQL Server（驱动已内置）

SQL Server 需要 Microsoft ODBC Driver 17 for SQL Server，该驱动已在 Docker 镜像中预装。

1. 确保 SQL Server 允许 TCP/IP 远程连接：
   - SQL Server 配置管理器 → SQL Server 网络配置 → 协议 → TCP/IP = 启用
   - 确保端口 1433（或自定义端口）可达

2. SQL Server 认证方式：支持 SQL Server 认证（用户名/密码），不建议使用 Windows 认证（跨平台受限）。

3. 在应用界面中选择数据库类型为 "SQL Server"，输入：
```
host[:port]/database
示例：192.168.1.100:1433/MYDB
```

4. Docker 镜像中已安装：
   - Microsoft ODBC Driver 17 for SQL Server（msodbcsql17）
   - SQL Server 命令行工具（sqlcmd、bcp）位于 /opt/mssql-tools/bin/

### 步骤 4：构建并启动（三种数据库统一流程）

```bash
docker-compose build
docker-compose up -d
```

### 步骤 5：访问应用

浏览器访问：http://localhost:6080

### 步骤 6：在应用中配置连接管理（三种数据库选择）

在应用界面中选择数据库类型（Oracle / MySQL / SQL Server），然后输入 Easy Connect 连接字符串。

---

## Easy Connect 详细说明（通用于三种数据库）

### 什么是 Easy Connect？

Easy Connect 是一种简化连接方式，允许在连接字符串中直接指定所有连接参数，无需依赖 tnsnames.ora、my.cnf、odbc.ini 等配置文件。

### Oracle 连接字符串格式

```
host:port/service_name
```

### MySQL 连接字符串格式

```
host:port/database
```

### SQL Server 连接字符串格式

```
host[:port]/database   # 端口可选，默认 1433
```

### 优势

1. **无需配置文件** - 不需要 tnsnames.ora、my.cnf、odbc.ini 等
2. **简化部署** - 只需挂载需要的驱动库（仅 Oracle thick 模式需要 Instant Client）
3. **易于维护** - 所有连接信息直接在应用中配置
4. **灵活切换** - 可随时切换数据库类型和目标

---

## 端口说明

| 端口 | 用途 | 说明 |
|-----|------|------|
| 6080 | noVNC Web | 浏览器直接访问，无需安装客户端 |
| 5900 | VNC | 使用 VNC Viewer 等客户端连接 |
| 1521 | Oracle 监听 | 仅当本地运行 Oracle 时使用 |
| 3306 | MySQL 监听 | 仅当本地运行 MySQL 时使用 |
| 1433 | SQL Server 监听 | 仅当本地运行 SQL Server 时使用 |

---

## 数据持久化

以下目录通过 Docker 卷挂载实现持久化：

| 容器路径 | 说明 |
|---------|------|
| /app/config.json | 配置文件（连接信息、模板等，包含数据库类型字段） |
| /app/logs | 日志目录 |
| /app/data | 数据目录（Excel 文件等） |
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
docker-compose exec dbforge bash

# 查看容器状态
docker-compose ps

# 查看资源使用
docker stats dbforge

# 验证 MySQL 驱动可用性（容器内）
docker-compose exec dbforge python3 -c "import pymysql; print('pymysql OK', pymysql.__version__)"

# 验证 SQL Server 驱动可用性（容器内）
docker-compose exec dbforge odbcinst -q -d
docker-compose exec dbforge python3 -c "import pyodbc; print('pyodbc OK', pyodbc.version); print([d for d in pyodbc.drivers()])"

# 验证 Oracle 驱动可用性（容器内）
docker-compose exec dbforge python3 -c "import oracledb; print('oracledb OK', oracledb.version)"
```

---

## 资源限制

默认配置：
- CPU 限制：2 核
- 内存限制：2 GB

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

### 问题 1：无法连接数据库（通用于 Oracle / MySQL / SQL Server）

**检查步骤：**
```bash
# 1. 检查相关驱动是否挂载/安装
# Oracle:
docker-compose exec dbforge bash
ls -la /opt/oracle/instantclient_21_15/*.so*

# MySQL:
python3 -c "import pymysql; print('pymysql', pymysql.__version__)"

# SQL Server:
odbcinst -q -d
python3 -c "import pyodbc; print('pyodbc', pyodbc.version); print(pyodbc.drivers())"

# 2. 检查网络连通性
# Oracle:
ping oracle-server
telnet oracle-server 1521

# MySQL:
ping mysql-server
telnet mysql-server 3306

# SQL Server:
ping sqlserver
telnet sqlserver 1433

# 3. 检查连接字符串格式是否正确（见上面的格式说明）
```

**常见错误：**

| 数据库 | 错误 | 原因 | 解决方案 |
|--------|-----|------|---------|
| Oracle | ORA-12541: TNS:no listener | 端口错误或服务未启动 | 检查端口和服务状态 |
| Oracle | ORA-12514: TNS:listener does not know service | service_name错误 | 确认正确的 service_name |
| Oracle | ORA-12154: TNS:could not resolve connect identifier | 连接字符串格式错误 | 使用正确格式 host:port/service_name |
| MySQL | Access denied for user | 用户权限/密码错误 | 检查用户允许远程登录、密码正确性 |
| MySQL | Can't connect to MySQL server on | 网络/服务不通 | 检查 MySQL 是否运行、防火墙 |
| MySQL | caching_sha2_password authentication failed | MySQL 8.0 认证方式 | 升级 pymysql 或修改认证方式 |
| SQL Server | Login timeout expired | 网络/端口不通 | 检查 TCP/IP 是否启用、端口 1433 是否开放 |
| SQL Server | Login failed for user | 登录认证失败 | 检查用户名/密码、是否启用 SQL Server 认证 |
| SQL Server | [unixODBC][Driver Manager]Data source name not found | 缺少 ODBC Driver 17 | Docker 镜像已内置，如缺失需重新构建镜像 |

### 问题 2：浏览器无法访问

```bash
docker-compose exec dbforge bash
curl http://localhost:6080
```

### 问题 3：中文显示乱码

```bash
docker-compose exec dbforge bash
fc-list :lang=zh
```

---

## 安全建议

1. 不要在公网暴露 6080/5900 端口
2. 使用防火墙限制访问
3. 配置 VNC 密码（修改 Dockerfile）
4. 定期备份数据
5. 连接字符串中的密码会被 Base64 编码存储，建议启用 AES-GCM 加密（见源码）

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

1. **Oracle Instant Client 需要从 Oracle 官网下载，需要 Oracle 账号**（仅 thick 模式需要）
2. **无需配置 tnsnames.ora / my.cnf / odbc.ini 等文件**，使用 Easy Connect 方式
3. **MySQL 使用纯 Python 驱动 pymysql，无需系统客户端**
4. **SQL Server 的 Microsoft ODBC Driver 17 for SQL Server 已内置在 Docker 镜像中**
5. **生产环境建议配置 VNC 密码和 HTTPS**
6. **连接管理字符串格式：**
   - Oracle    `host:port/service_name`
   - MySQL     `host:port/database`
   - SQL Server `host[:port]/database`
