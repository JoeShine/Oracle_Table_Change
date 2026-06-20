@echo off
REM Oracle 数据批量修改工具 - 便携版启动脚本
REM 无需安装，解压即用

setlocal

set APP_DIR=%~dp0App
set DATA_DIR=%~dp0Data
set PATH=%APP_DIR%;%PATH%

REM 检查系统Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python环境
    echo 请安装Python 3.8+ 或使用完整便携版
    pause
    exit /b 1
)

REM 可选Oracle客户端
if exist "%~dp0OracleClient\instantclient_*" (
    set PATH=%~dp0OracleClient;%PATH%
)

REM 启动应用
echo 正在启动 Oracle 数据批量修改工具...
cd /d "%APP_DIR%"
start "" OracleBatchUpdater.exe

endlocal
