# CHM 帮助手册 - Windows 安全警告说明

## 为什么打开 CHM 显示空白或" Navigation to the webpage was canceled"？

这是 Windows 安全机制导致的。当文件从互联网下载或通过网络传输时，
Windows 会在文件上附加一个 Zone.Identifier 标记（"来自其他计算机"），
导致 CHM 内容被阻止。

## 解决方案（按推荐顺序）

### 方案一：从 ZIP 包解压（推荐）

1. 解压旁边的 DBForge_UserManual.zip 文件
2. 将解压出的 .chm 文件复制到本地磁盘（如 C:\ 或 D:\）
3. 双击打开

> ZIP 格式不保留 NTFS 的 ADS 安全标记，解压后自动解除锁定。

### 方案二：运行一键修复脚本

- **Windows 10 / 11**：右键 `chm_unblock.ps1` → "使用 PowerShell 运行"
- **Windows 7**：双击 `chm_unblock.bat`

### 方案三：手动解除锁定（适用于所有 Windows 版本）

1. 右键点击 .chm 文件 → 属性
2. 在"常规"选项卡底部，找到"安全："区域
3. 勾选「解除锁定」复选框
4. 点击确定

### 方案四：网络驱动器 + 注册表修复（仅限高级用户）

如果 CHM 必须放在网络共享上，运行以下命令：

```
reg add "HKLM\SOFTWARE\Microsoft\HTMLHelp\1.x\ItssRestrictions" ^
    /v MaxAllowedZone /t REG_DWORD /d 1 /f
```

> 注意：修改注册表可能降低系统安全性，不建议在生产环境使用。

## 移动设备 / 掌阅 APP 阅读

CHM 格式依赖 Windows 的 HTML Help 引擎，**安卓版掌阅 APP 不支持直接打开 .chm 文件**。

如需在手机或平板上阅读，请使用同目录下的 EPUB 版本：

- **文件**: `DBForge_UserManual.epub`
- **用途**: 掌阅、微信读书、Kindle 等支持 EPUB 的阅读器
- **生成方式**: `python scripts/build_epub.py`

### 掌阅 APP 导入步骤

1. 将 `DBForge_UserManual.epub` 传输到手机
2. 打开掌阅 APP → 书架 → 右上角 **+** / **导入本地书**
3. 选择 EPUB 文件，导入后即可阅读

---

## 多数据库驱动安装提示（v2.8.0 起支持 MySQL / SQL Server）

当在连接管理中选择 **MySQL** 或 **SQL Server** 时，需要在运行 DBForge 的 Windows 机器上安装对应驱动。

### 1. MySQL 驱动（pymysql）

**安装方式：**
```bash
pip install pymysql
```

**验证：**
```bash
python -c "import pymysql; print(pymysql.__version__)"
```

**常见问题：**
- 若提示找不到模块：请先切换到打包所用的 Python 环境或通过 `pip list` 检查是否已安装。
- 字符集建议：数据库使用 `utf8mb4`，`my.ini` / `my.cnf` 中显式设置 `character-set-server=utf8mb4`。

---

### 2. SQL Server 驱动（ODBC Driver 17 for SQL Server + pyodbc）

**步骤一：安装 ODBC Driver 17 for SQL Server（Windows）**

1. 访问 Microsoft 官方下载页面：`https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server`
2. 下载 **ODBC Driver 17 for SQL Server**（推荐 17.x 版本，兼容 SQL Server 2003 / 2008 R2 / 2012+）。
3. 以管理员身份运行 `msodbcsql.msi` 安装程序，按提示完成安装。
4. 验证是否安装成功：`控制面板 → 管理工具 → ODBC 数据源(64 位) → 驱动程序` 中看到 **ODBC Driver 17 for SQL Server**。

**步骤二：安装 Python pyodbc 包**
```bash
pip install pyodbc
```

**验证：**
```bash
python -c "import pyodbc; print([d for d in pyodbc.drivers() if 'ODBC Driver 17' in d])"
```

**常见问题：**
- 安装 ODBC 驱动时提示"缺少 Windows Installer 4.5"：请先升级 Windows Installer（针对 Windows 7 / Server 2008 环境）。
- 连接错误 `[Microsoft][ODBC Driver 17 for SQL Server]Client unable to establish connection`：
  1. 检查 SQL Server 是否启用 TCP/IP（`SQL Server 配置管理器 → SQL Server 网络配置 → TCP/IP`）。
  2. 检查防火墙 1433 端口是否开放。
  3. 确认 SQL Server Browser 服务是否已启动。
- 中文乱码：数据库排序规则推荐使用 `Chinese_PRC_CI_AS`。

---

生成时间: 2026-06-20 10:45:00
CHM 版本: v2.8.0
EPUB 版本: v2.8.0
