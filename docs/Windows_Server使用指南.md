# DBForge - Windows Server 2008 R2 使用指南（v2.9.1 多数据库支持版）

## 适用场景

本工具适用于以下环境：

| 环境 | 说明 |
|-----|------|
| 操作系统 | Windows Server 2008 R2 及以上 |
| Oracle版本 | Oracle 11g 及以上 |
| 客户端 | 已安装Oracle客户端或Instant Client |
| 连接方式 | Easy Connect（无需配置文件） |

---

## 系统兼容性说明

### 发布方式兼容性

| 发布方式 | Windows 7 | Windows Server 2008 R2 | Windows 10+ | Windows Server 2016+ |
|---------|-----------|------------------------|-------------|----------------------|
| exe打包 | ✅ 支持 | ✅ 支持 | ✅ 支持 | ✅ 支持 |
| 便携版 | ✅ 支持 | ✅ 支持 | ✅ 支持 | ✅ 支持 |
| Docker | ❌ 不支持 | ❌ 不支持 | ✅ 支持 | ✅ 支持 |

**推荐：** Windows Server 2008 R2 用户使用 **exe打包** 或 **便携版** 方式。

---

## 快速开始

### 场景描述

您的服务器环境：
- **操作系统**: Windows Server 2008 R2
- **数据库**: Oracle 11g 已安装
- **客户端**: Oracle客户端已安装

**只需配置连接字符串即可使用本工具！**

---

## 安装方式

### 方式一：exe打包（推荐）

直接运行打包好的exe文件：
```
DBForge.exe
```

### 方式二：便携版

解压即用，无需安装：
```
1. 解压 DBForge_Portable_v2.8.0.zip
2. 双击 DBForge_Portable.bat
```

便携版优势：
- 无需管理员权限
- 可放在U盘运行
- 数据完全隔离

---

## 连接配置

### 方式一：使用现有Oracle客户端

如果服务器已安装Oracle客户端，工具会自动使用。

**连接参数填写：**

| 字段 | 填写内容 | 示例 |
|-----|---------|------|
| 连接名称 | 自定义名称 | 生产环境 |
| 主机地址 | Oracle服务器IP或主机名 | 192.168.1.100 |
| 端口 | Oracle监听端口（默认1521） | 1521 |
| 服务名 | Oracle服务名 | ORCL |
| 用户名 | 数据库用户名 | scott |
| 密码 | 数据库密码 | tiger |

### 方式二：使用Easy Connect字符串

**Easy Connect格式：**
```
host:port/service_name
```

**示例：**
```
192.168.1.100:1521/ORCL
localhost:1521/ORCL.localdomain
oracle-server:1521/MYDB
```

**在工具界面中填写：**

| 字段 | Easy Connect分解 | 示例 |
|-----|-----------------|------|
| 主机地址 | host部分 | 192.168.1.100 |
| 端口 | port部分 | 1521 |
| 服务名 | service_name部分 | ORCL |

---

## 安装部署

### 步骤1：获取工具

从GitHub下载：
```
https://github.com/JoeShine/Oracle_Table_Change
```

或下载打包好的exe文件：
```
DBForge.exe
```

### 步骤2：运行工具

**方式A：直接运行exe（推荐）**
```
双击 DBForge.exe
```

**方式B：Python源码运行**
```bash
# 安装依赖
pip install oracledb openpyxl

# 运行
python main.py
```

### 步骤3：配置连接

在工具界面中：

1. 点击 **"添加连接"** 按钮
2. 填写连接信息：
   - 连接名称: `生产环境`
   - 主机地址: `192.168.1.100`
   - 端口: `1521`
   - 服务名: `ORCL`
   - 用户名: `scott`
   - 密码: `tiger`
3. 点击 **"测试连接"**
4. 连接成功后点击 **"保存"**

### 步骤4：开始使用

1. 选择已保存的连接
2. 点击 **"连接"**
3. 选择目标表
4. 选择Excel文件
5. 配置更新列
6. 点击 **"验证数据"** 检查Excel和数据库
7. 验证通过后点击 **"执行"** 开始批量更新

---

## 无需配置文件

### Easy Connect优势

本工具使用 **Easy Connect** 方式，无需任何配置文件：

| 传统方式 | Easy Connect方式 |
|---------|-----------------|
| 需要tnsnames.ora | ❌ 不需要 |
| 需要sqlnet.ora | ❌ 不需要 |
| 需要配置TNS_ADMIN | ❌ 不需要 |
| 需要配置环境变量 | ❌ 不需要 |

### 连接原理

工具内部使用 `oracledb.makedsn()` 构建连接：

```python
# 工具内部实现
dsn = oracledb.makedsn(host, port, service_name=service)
connection = oracledb.connect(user=username, password=password, dsn=dsn)
```

等效于Easy Connect字符串：
```
host:port/service_name
```

---

## Windows Server 2008 R2 特殊说明

### 系统要求

| 项目 | 要求 |
|-----|------|
| 操作系统 | Windows Server 2008 R2 SP1 或更高 |
| Oracle客户端 | 11g或更高版本 |
| Python | 3.7+（源码运行需要） |

### Oracle客户端兼容性

| Oracle版本 | 客户端要求 | 工具支持 |
|-----------|-----------|---------|
| Oracle 11g | Instant Client 11g+ | ✓ 支持 |
| Oracle 12c | Instant Client 12c+ | ✓ 支持 |
| Oracle 19c | Instant Client 19c+ | ✓ 支持 |

### 已安装Oracle 11g的场景

如果服务器已安装Oracle 11g数据库和客户端：

1. **无需额外安装Instant Client**
2. 工具会自动使用已安装的客户端库
3. 直接配置连接字符串即可

**验证Oracle客户端：**
```cmd
# 检查Oracle客户端版本
sqlplus -v

# 检查环境变量
echo %ORACLE_HOME%
echo %PATH%
```

---

## 使用示例

### 示例1：更新员工表

**场景：** 批量更新员工薪资

**步骤：**

1. 准备Excel文件 `员工薪资更新.xlsx`：
   | EMP_ID | SALARY |
   |--------|--------|
   | 1001 | 8000 |
   | 1002 | 9000 |
   | 1003 | 7500 |

2. 配置工具：
   - 连接: `192.168.1.100:1521/ORCL`
   - 目标表: `EMP`
   - 唯一标识列: `EMP_ID`
   - 更新列: `SALARY`

3. 执行更新

### 示例2：更新产品库存

**场景：** 批量更新产品库存数量

**步骤：**

1. 准备Excel文件 `库存更新.xlsx`：
   | PRODUCT_ID | STOCK_QTY |
   |------------|-----------|
   | P001 | 100 |
   | P002 | 200 |
   | P003 | 150 |

2. 配置工具：
   - 连接: `oracle-server:1521/PRODDB`
   - 目标表: `PRODUCTS`
   - 唯一标识列: `PRODUCT_ID`
   - 更新列: `STOCK_QTY`

3. 执行更新

---

## 常见问题

### Q1: 连接失败怎么办？

**检查清单：**

1. 检查Oracle服务是否启动
   ```cmd
   # 检查Oracle服务状态
   sc query OracleServiceORCL
   ```

2. 检查监听程序是否运行
   ```cmd
   # 检查监听状态
   lsnrctl status
   ```

3. 检查网络连通性
   ```cmd
   ping oracle-server
   telnet oracle-server 1521
   ```

4. 检查服务名是否正确
   ```sql
   -- 在数据库中查询服务名
   SELECT name FROM v$database;
   SELECT global_name FROM global_name;
   ```

### Q2: 需要配置tnsnames.ora吗？

**不需要！**

本工具使用Easy Connect方式，直接在界面中输入：
- 主机地址
- 端口
- 服务名

无需任何配置文件。

### Q3: Oracle 11g兼容性？

**完全兼容。**

工具使用 `oracledb` Python库，支持Oracle 11g及以上版本。

### Q4: 如何获取正确的服务名？

**方法一：查询数据库**
```sql
SELECT value FROM v$parameter WHERE name = 'service_names';
```

**方法二：查看监听状态**
```cmd
lsnrctl status
```

输出中会显示服务名：
```
Services Summary...
Service "ORCL" has 1 instance(s).
```

### Q5: 端口不是1521怎么办？

在工具界面中修改端口值即可。

常见Oracle端口：
| 端口 | 用途 |
|-----|------|
| 1521 | 默认监听端口 |
| 1522 | 第二监听端口 |
| 1526 | 非默认端口 |

---

## 安全建议

1. **密码安全**
   - 工具使用Base64编码存储密码
   - 建议定期更换数据库密码

2. **权限控制**
   - 使用专用数据库账号
   - 仅授予必要权限（SELECT, UPDATE）

3. **操作审计**
   - 工具自动记录运行日志
   - 日志位置: `logs/update_*.log`

4. **数据备份**
   - 更新前建议备份数据
   - 工具支持创建备份表

---

## 总结

**Windows Server 2008 R2 + Oracle 11g 使用流程：**

```
1. 运行 DBForge.exe
   ↓
2. 点击 "添加连接"
   ↓
3. 填写连接信息（无需配置文件）
   - 主机地址: 192.168.1.100
   - 端口: 1521
   - 服务名: ORCL
   - 用户名: scott
   - 密码: tiger
   ↓
4. 测试连接 → 保存
   ↓
5. 选择连接 → 连接数据库
   ↓
6. 选择表 → 选择Excel → 执行更新
```

**无需配置任何Oracle配置文件！**