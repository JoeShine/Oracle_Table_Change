@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo Oracle数据批量修改工具 - 完整打包脚本
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 未找到Python，请先安装Python 3.8或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 获取Python版本
for /f "delims=" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo 检测到Python版本: %PYTHON_VERSION%

REM 安装依赖
echo.
echo 步骤1/3: 安装Python依赖...
echo ----------------------------------------
pip install -r requirements.txt -q
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 依赖安装失败！
    echo 请尝试手动运行: pip install -r requirements.txt
    pause
    exit /b 1
)
echo 依赖安装完成

REM 安装PyInstaller
echo.
echo 步骤2/3: 安装PyInstaller...
echo ----------------------------------------
pip install pyinstaller -q
if %ERRORLEVEL% NEQ 0 (
    echo [警告] PyInstaller安装可能有问题，但继续尝试...
)

REM 清理旧的构建文件
echo.
echo 步骤3/3: 打包应用程序...
echo ----------------------------------------
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

REM 执行打包
pyinstaller OracleBatchUpdater.spec --clean --noconfirm

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [错误] 打包失败！
    echo 请查看上面的错误信息
    pause
    exit /b 1
)

REM 复制必要文件
echo.
echo 复制配置文件和目录...
if not exist "dist\logs" mkdir "dist\logs"
if not exist "dist\backups" mkdir "dist\backups"
if not exist "dist\src" mkdir "dist\src"
xcopy /y /q "config.json" "dist\" 2>nul
xcopy /y /q "src\*.py" "dist\src\" 2>nul

echo.
echo ========================================
echo 打包完成！
echo ========================================
echo.
echo exe文件位置: %CD%\dist\OracleBatchUpdater.exe
echo.
echo 部署说明:
echo 1. 将dist目录下的所有文件复制到目标电脑
echo 2. Oracle客户端库(Instant Client)需要单独配置:
echo    - 下载Oracle Instant Client
echo    - 解压到程序目录或系统PATH中
echo 3. 无需安装Python环境
echo.
echo 目录结构:
echo dist\
echo   OracleBatchUpdater.exe  - 主程序
echo   src\                    - 源代码目录
echo   logs\                   - 日志目录
echo   backups\                - 备份目录
echo   config.json             - 配置文件
echo.
echo 是否打开dist目录？(Y/N)
set /p OPEN_DIR=
if /i "!OPEN_DIR!"=="Y" (
    explorer "%CD%\dist"
)

pause
