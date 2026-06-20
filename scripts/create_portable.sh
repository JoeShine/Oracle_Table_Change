#!/bin/bash
# Oracle 数据批量修改工具 - 便携版打包脚本
# 适用于 Windows 7, Windows Server 2008 R2 及以上系统
# 无需安装，解压即用

echo "========================================"
echo "Oracle 数据批量修改工具 - 便携版打包"
echo "========================================"
echo ""

# 设置版本号
VERSION="2.7.0"
APP_NAME="OracleBatchUpdater"
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
cat > "${PORTABLE_DIR}/OracleBatchUpdater_Portable.bat" << 'EOF'
@echo off
REM Oracle 数据批量修改工具 - 便携版启动脚本
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

REM 检查Python环境
if exist "%APP_DIR%\python\python.exe" (
    set PYTHON_EXE=%APP_DIR%\python\python.exe
) else (
    REM 使用系统Python
    python --version >nul 2>&1
    if errorlevel 1 (
        echo 错误: 未找到Python环境
        echo 请安装Python 3.8+ 或使用完整便携版
        pause
        exit /b 1
    )
    set PYTHON_EXE=python
)

REM 检查Oracle客户端
if exist "%~dp0OracleClient\instantclient_*" (
    set PATH=%~dp0OracleClient;%PATH%
)

REM 启动应用
echo 正在启动 Oracle 数据批量修改工具...
cd /d "%APP_DIR%"
%PYTHON_EXE% main.py

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
Oracle 数据批量修改工具 - 便携版
版本: 2.7.0
========================================

【使用说明】

1. 解压即用
   - 无需安装，解压到任意目录即可运行
   - 可放在U盘、网络共享、本地文件夹

2. 启动方式
   - 双击 OracleBatchUpdater_Portable.bat 启动
   - 或直接运行 App\OracleBatchUpdater.exe

3. 数据存储
   - 所有数据保存在 Data 目录
   - logs: 操作日志
   - backups: 数据备份
   - config: 配置文件

4. Oracle客户端
   - 如需使用Oracle客户端，请将instantclient目录
     放到 OracleClient 目录中
   - 或使用已安装的Oracle客户端

5. 系统要求
   - Windows 7 及以上
   - Windows Server 2008 R2 及以上
   - Python 3.8+（或使用完整便携版）

6. 连接数据库
   - 使用 Easy Connect 方式
   - 格式: host:port/service_name
   - 示例: 192.168.1.100:1521/ORCL
   - 无需配置文件

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
   双击 OracleBatchUpdater_Portable.bat

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
echo "    ├── OracleClient/           Oracle客户端(可选)"
echo "    ├── OracleBatchUpdater_Portable.bat  启动脚本"
echo "    └── README_Portable.txt     使用说明"
echo ""
echo "适用系统:"
echo "  ✓ Windows 7 及以上"
echo "  ✓ Windows Server 2008 R2 及以上"
echo "  ✓ 无需安装，解压即用"
echo "========================================"
EOF