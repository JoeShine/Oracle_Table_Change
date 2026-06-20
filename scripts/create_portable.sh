#!/bin/bash
# v2.9.1
# DBForge - 便携版打包脚本
# 适用于 Windows 7, Windows Server 2008 R2 及以上系统
# 无需安装，解压即用

echo "========================================"
echo "DBForge - 便携版打包"
echo "========================================"
echo ""

# 设置版本号
VERSION="2.9.0"
APP_NAME="DBForge"
PORTABLE_DIR="${APP_NAME}_Portable_v${VERSION}"

# 创建便携版目录结构
echo "创建便携版目录结构..."
mkdir -p "${PORTABLE_DIR}"
mkdir -p "${PORTABLE_DIR}/App"
mkdir -p "${PORTABLE_DIR}/Data"
mkdir -p "${PORTABLE_DIR}/Data/logs"
mkdir -p "${PORTABLE_DIR}/Data/backups"
mkdir -p "${PORTABLE_DIR}/Data/config"
mkdir -p "${PORTABLE_DIR}/OracleClient"

# 复制应用文件
echo "复制应用文件..."
cp -r dist/* "${PORTABLE_DIR}/App/" 2>/dev/null || echo "警告: dist目录不存在，请先运行 package.bat"
cp -r src/*.py "${PORTABLE_DIR}/App/src/" 2>/dev/null || mkdir -p "${PORTABLE_DIR}/App/src"
cp requirements.txt "${PORTABLE_DIR}/App/" 2>/dev/null
cp *.xlsx "${PORTABLE_DIR}/Data/" 2>/dev/null || echo "无Excel模板文件"

# 创建便携版启动脚本
echo "创建便携版启动脚本..."
cat > "${PORTABLE_DIR}/DBForge_Portable.bat" << 'EOF'
@echo off
REM DBForge - 便携版启动脚本
REM 无需安装，解压即用
REM 适用于 Windows 7, Windows Server 2008 R2 及以上

setlocal

REM 设置应用目录
set APP_DIR=%~dp0App
set DATA_DIR=%~dp0Data
set LOG_DIR=%~dp0Data\logs
set CONFIG_DIR=%~dp0Data\config

REM 设置环境变量
set PYTHONPATH=%APP_DIR%\src
set PATH=%APP_DIR%;%PATH%

REM 方式1: 优先使用 PyInstaller 打包的 exe（无需 Python）
if exist "%APP_DIR%\DBForge.exe" (
    echo 正在启动 DBForge ^(可执行文件模式^)...
    cd /d "%APP_DIR%"
    start DBForge.exe
    goto :end
)

REM 方式2: 使用嵌入式 Python（完整便携版，无需安装）
if exist "%APP_DIR%\python\python.exe" (
    set PYTHON_EXE=%APP_DIR%\python\python.exe
    echo 正在启动 DBForge ^(嵌入式 Python 模式^)...
    cd /d "%APP_DIR%"
    %PYTHON_EXE% main.py
    goto :end
)

REM 方式3: 使用系统 Python（开发/调试模式）
python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_EXE=python
    echo 正在启动 DBForge ^(系统 Python 模式^)...
    cd /d "%APP_DIR%"
    %PYTHON_EXE% main.py
    goto :end
)

REM 全部失败
echo ========================================
echo   错误: 无法启动应用
echo ========================================
echo.
echo 找不到以下任一启动方式:
echo   1. App\DBForge.exe ^(推荐，无需 Python^)
echo   2. App\python\python.exe ^(嵌入式 Python^)
echo   3. 系统 Python ^(需要 Python 3.7+^)
echo.
echo 请确认便携版目录结构完整，或安装 Python 3.7+
echo 下载地址: https://www.python.org/downloads/
echo.
pause
exit /b 1

:end
endlocal
EOF

# 创建配置文件模板
echo "创建配置文件模板..."
cat > "${PORTABLE_DIR}/Data/config/config.json.template" << 'EOF'
{
    "connections": [],
    "templates": [],
    "last_used": {
        "connection_name": "",
        "target_table": "",
        "key_column": "",
        "update_column": "",
        "schema": "APPS",
        "temp_schema": "APPS",
        "theme_style": "terminal",
        "theme_dark": false
    },
    "settings": {
        "log_level": "INFO",
        "backup_enabled": true,
        "max_backup_count": 10
    }
}
EOF

# 创建使用说明
echo "创建使用说明..."
cat > "${PORTABLE_DIR}/README_Portable.txt" << 'EOF'
========================================
DBForge - 便携版
版本: 2.9.0（多数据库支持版）
========================================

【使用说明】

1. 解压即用
   - 无需安装 Python，解压到任意目录即可运行
   - 可放在U盘、网络共享、本地文件夹

2. 启动方式
   - 双击 DBForge_Portable.bat 启动（推荐）
   - 或直接运行 App\DBForge.exe

3. 数据存储
   - 所有数据保存在 Data 目录
   - logs: 运行日志
   - backups: 数据备份
   - config: 配置文件

4. 多数据库支持（v2.9.0）
   DBForge 支持以下三种主流关系型数据库：

   [1] Oracle       11g/12c/19c/21c       - 驱动: oracledb
       - 如需使用 Oracle 客户端，请将 instantclient 目录
         放到 OracleClient 目录中
       - 或使用已安装的 Oracle Instant Client

   [2] MySQL        5.7+/8.0+/MariaDB 10.x - 驱动: pymysql
       - 纯 Python 驱动，无需额外系统依赖
       - 端口默认 3306

   [3] SQL Server   2008 R2/2012+/2019/2022 - 驱动: pyodbc
       - 需要系统已安装 Microsoft ODBC Driver 17 for SQL Server
       - 端口默认 1433

   数据库类型可在「连接管理」页选择，SQL 方言自动适配。

5. 系统要求
   - Windows 7 及以上
   - Windows Server 2008 R2 及以上
   - 不需要安装 Python（便携版包含 .exe 可执行文件）
   - 仅 Oracle Instant Client 与 SQL Server ODBC Driver 需要单独配置

6. 连接数据库
   - Oracle    格式: host:port/service_name  示例: 192.168.1.100:1521/ORCL
   - MySQL     格式: host:port/database       示例: 192.168.1.100:3306/mydb
   - SQL Server 格式: host[:port]/database    示例: 192.168.1.100:1433/MYDB
   - 无需配置 tnsnames.ora 等文件

========================================
EOF

# 创建完整便携版说明（包含Python）
cat > "${PORTABLE_DIR}/README_FullPortable.txt" << 'EOF'
========================================
完整便携版打包说明
========================================

如需创建包含Python环境的完整便携版：

1. 下载 Python Embedded 版本
   https://www.python.org/ftp/python/3.11.x/python-3.11.x-embed-amd64.zip

2. 解压到 App\python 目录

3. 安装依赖
   App\python\python.exe -m pip install -r App\requirements.txt --target App\python\Lib

4. 复制 Oracle Instant Client
   将 instantclient_xx_xx 目录复制到 OracleClient

5. 运行
   双击 DBForge_Portable.bat

========================================
EOF

# 打包为ZIP
echo "打包便携版..."
zip -r "${PORTABLE_DIR}.zip" "${PORTABLE_DIR}"

echo ""
echo "========================================"
echo "便携版打包完成!"
echo "========================================"
echo ""
echo "输出文件: ${PORTABLE_DIR}.zip"
echo "目录结构:"
echo "  ${PORTABLE_DIR}/"
echo "    ├── App/                    应用程序"
echo "    ├── Data/                   数据目录"
echo "    │   ├── logs/               日志"
echo "    │   ├── backups/            备份"
echo "    │   └── config/             配置"
echo "    ├── OracleClient/           Oracle 客户端(可选)"
echo "    ├── DBForge_Portable.bat  启动脚本"
echo "    └── README_Portable.txt     使用说明（含多数据库支持说明）"
echo ""
echo "适用系统:"
echo "  ✓ Windows 7 及以上"
echo "  ✓ Windows Server 2008 R2 及以上"
echo "  ✓ 无需安装，解压即用"
echo ""
echo "多数据库支持（v2.9.0）:"
echo "  ✓ Oracle       11g/12c/19c/21c       - 驱动: oracledb"
echo "  ✓ MySQL        5.7+/8.0+/MariaDB 10.x - 驱动: pymysql"
echo "  ✓ SQL Server   2008 R2/2012+/2019/2022 - 驱动: pyodbc + MS ODBC Driver 17"
echo "========================================"
EOF