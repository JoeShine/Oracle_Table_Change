@echo off
REM Oracle 数据批量修改工具 - 便携版打包脚本
REM 适用于 Windows 7, Windows Server 2008 R2 及以上系统
REM 无需安装，解压即用

setlocal enabledelayedexpansion

echo ========================================
echo Oracle 数据批量修改工具 - 便携版打包
echo ========================================
echo.

REM 设置版本号
set VERSION=2.8.0
set APP_NAME=OracleBatchUpdater
set PORTABLE_DIR=%APP_NAME%_Portable_v%VERSION%

REM 创建便携版目录结构
echo 创建便携版目录结构...
if exist "%PORTABLE_DIR%" rd /s /q "%PORTABLE_DIR%"
mkdir "%PORTABLE_DIR%"
mkdir "%PORTABLE_DIR%\App"
mkdir "%PORTABLE_DIR%\App\src"
mkdir "%PORTABLE_DIR%\Data"
mkdir "%PORTABLE_DIR%\Data\logs"
mkdir "%PORTABLE_DIR%\Data\backups"
mkdir "%PORTABLE_DIR%\Data\config"
mkdir "%PORTABLE_DIR%\OracleClient"

REM 复制应用文件
echo 复制应用文件...
if exist "dist\OracleBatchUpdater.exe" (
    copy "dist\OracleBatchUpdater.exe" "%PORTABLE_DIR%\App\" >nul
    echo   [OK] OracleBatchUpdater.exe
) else (
    echo   [警告] dist\OracleBatchUpdater.exe 不存在，请先运行 package.bat
)

REM 复制源代码（备用）
if exist "src\*.py" (
    copy "src\*.py" "%PORTABLE_DIR%\App\src\" >nul
    echo   [OK] 源代码文件
)

REM 复制依赖文件
if exist "requirements.txt" (
    copy "requirements.txt" "%PORTABLE_DIR%\App\" >nul
    echo   [OK] requirements.txt
)

REM 复制Excel模板
if exist "*.xlsx" (
    copy "*.xlsx" "%PORTABLE_DIR%\Data\" >nul
    echo   [OK] Excel模板文件
)

REM 创建便携版启动脚本
echo 创建便携版启动脚本...
(
echo @echo off
echo REM Oracle 数据批量修改工具 - 便携版启动脚本
echo REM 无需安装，解压即用
echo REM 适用于 Windows 7, Windows Server 2008 R2 及以上
echo.
echo setlocal
echo.
echo REM 设置应用目录
echo set APP_DIR=%%~dp0App
echo set DATA_DIR=%%~dp0Data
echo set LOG_DIR=%%~dp0Data\logs
echo set CONFIG_DIR=%%~dp0Data\config
echo.
echo REM 设置环境变量
echo set PYTHONPATH=%%APP_DIR%%\src
echo set PATH=%%APP_DIR%%;%%PATH%%
echo.
echo REM 检查exe文件
echo if exist "%%APP_DIR%%\OracleBatchUpdater.exe" (
echo     echo 正在启动 Oracle 数据批量修改工具...
echo     cd /d "%%APP_DIR%%"
echo     start OracleBatchUpdater.exe
echo     goto :end
echo )
echo.
echo REM 检查Python环境
echo if exist "%%APP_DIR%%\python\python.exe" (
echo     set PYTHON_EXE=%%APP_DIR%%\python\python.exe
echo ) else (
echo     REM 使用系统Python
echo     python --version ^>nul 2^>^&1
echo     if errorlevel 1 (
echo         echo 错误: 未找到Python环境
echo         echo 请安装Python 3.8+ 或使用完整便携版
echo         pause
echo         exit /b 1
echo     )
echo     set PYTHON_EXE=python
echo )
echo.
echo REM 检查Oracle客户端
echo if exist "%%~dp0OracleClient\instantclient_*" (
echo     set PATH=%%~dp0OracleClient;%%PATH%%
echo )
echo.
echo REM 启动应用
echo echo 正在启动 Oracle 数据批量修改工具...
echo cd /d "%%APP_DIR%%"
echo %%PYTHON_EXE%% main.py
echo.
echo :end
echo endlocal
) > "%PORTABLE_DIR%\OracleBatchUpdater_Portable.bat"
echo   [OK] OracleBatchUpdater_Portable.bat

REM 创建配置文件模板
echo 创建配置文件模板...
(
echo {
echo     "connections": [],
echo     "templates": [],
echo     "last_used": {
echo         "connection_name": "",
echo         "target_table": "",
echo         "key_column": "",
echo         "update_column": "",
echo         "schema": "APPS",
echo         "temp_schema": "APPS",
echo         "theme_style": "terminal",
echo         "theme_dark": false
echo     },
echo     "settings": {
echo         "log_level": "INFO",
echo         "backup_enabled": true,
echo         "max_backup_count": 10
echo     }
echo }
) > "%PORTABLE_DIR%\Data\config\config.json.template"
echo   [OK] config.json.template

REM 创建使用说明
echo 创建使用说明...
(
echo ========================================
echo Oracle 数据批量修改工具 - 便携版
echo 版本: 2.7.0
echo ========================================
echo.
echo 【使用说明】
echo.
echo 1. 解压即用
echo    - 无需安装 Python，解压到任意目录即可运行
echo    - 可放在U盘、网络共享、本地文件夹
echo.
echo 2. 启动方式
echo    - 双击 OracleBatchUpdater_Portable.bat 启动（推荐）
echo    - 或直接运行 App\OracleBatchUpdater.exe
echo.
echo 3. 数据存储
echo    - 所有数据保存在 Data 目录
echo    - logs: 操作日志
echo    - backups: 数据备份
echo    - config: 配置文件
echo.
echo 4. Oracle客户端
echo    - 如需使用Oracle客户端，请将instantclient目录
echo      放到 OracleClient 目录中
echo    - 或使用已安装的Oracle客户端
echo.
echo 5. 系统要求
echo    - Windows 7 及以上
echo    - Windows Server 2008 R2 及以上
echo    - 不需要安装 Python（便携版包含 .exe 可执行文件）
echo    - 仅 Oracle Instant Client 需要单独配置
echo.
echo 6. 连接数据库
echo    - 使用 Easy Connect 方式
echo    - 格式: host:port/service_name
echo    - 示例: 192.168.1.100:1521/ORCL
echo    - 无需配置文件
echo.
echo ========================================
) > "%PORTABLE_DIR%\README_Portable.txt"
echo   [OK] README_Portable.txt

REM 创建完整便携版说明
(
echo ========================================
echo 完整便携版打包说明
echo ========================================
echo.
echo 如需创建包含Python环境的完整便携版：
echo.
echo 1. 下载 Python Embedded 版本
echo    https://www.python.org/ftp/python/3.11.x/python-3.11.x-embed-amd64.zip
echo.
echo 2. 解压到 App\python 目录
echo.
echo 3. 安装依赖
echo    App\python\python.exe -m pip install -r App\requirements.txt --target App\python\Lib
echo.
echo 4. 复制 Oracle Instant Client
echo    将 instantclient_xx_xx 目录复制到 OracleClient
echo.
echo 5. 运行
echo    双击 OracleBatchUpdater_Portable.bat
echo.
echo ========================================
) > "%PORTABLE_DIR%\README_FullPortable.txt"
echo   [OK] README_FullPortable.txt

echo.
echo ========================================
echo 便携版打包完成!
echo ========================================
echo.
echo 输出目录: %PORTABLE_DIR%
echo.
echo 目录结构:
echo   %PORTABLE_DIR%\
echo     ├── App\                    应用程序
echo     ├── Data\                   数据目录
echo     │   ├── logs\               日志
echo     │   ├── backups\            备份
echo     │   └── config\             配置
echo     ├── OracleClient\           Oracle客户端(可选)
echo     ├── OracleBatchUpdater_Portable.bat  启动脚本
echo     └── README_Portable.txt     使用说明
echo.
echo 适用系统:
echo   [OK] Windows 7 及以上
echo   [OK] Windows Server 2008 R2 及以上
echo   [OK] 无需安装，解压即用
echo.
echo ========================================
echo.
echo 提示: 如需打包为ZIP文件，请使用以下命令:
echo       powershell Compress-Archive -Path %PORTABLE_DIR% -DestinationPath %PORTABLE_DIR%.zip
echo.

endlocal
pause