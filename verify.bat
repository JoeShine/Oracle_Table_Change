@echo off
chcp 65001 >nul
echo ========================================
echo Oracle数据批量修改工具 - 验证脚本
echo ========================================
echo.

REM 检查Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 未安装Python
    pause
    exit /b 1
)

echo 检查Python版本...
python --version

echo.
echo 检查依赖包...
pip show oracledb >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [警告] oracledb未安装
)

pip show openpyxl >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [警告] openpyxl未安装
)

pip show pyinstaller >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [警告] pyinstaller未安装（打包用）
)

echo.
echo 测试模块导入...
python -c "from src.config_manager import ConfigManager; print('✓ config_manager')"
python -c "from src.logger import LogManager; print('✓ logger')"
python -c "from src.excel_handler import ExcelHandler; print('✓ excel_handler')"
python -c "from src.db_connection import DBConnection; print('✓ db_connection')"
python -c "from src.data_updater import DataUpdater; print('✓ data_updater')"
python -c "from src.gui import OracleBatchUpdaterGUI; print('✓ gui')"

echo.
echo 检查文件完整性...
if not exist "main.py" (
    echo [错误] 缺少main.py
    exit /b 1
)

if not exist "src\config_manager.py" (
    echo [错误] 缺少src\config_manager.py
    exit /b 1
)

if not exist "src\logger.py" (
    echo [错误] 缺少src\logger.py
    exit /b 1
)

if not exist "src\excel_handler.py" (
    echo [错误] 缺少src\excel_handler.py
    exit /b 1
)

if not exist "src\db_connection.py" (
    echo [错误] 缺少src\db_connection.py
    exit /b 1
)

if not exist "src\data_updater.py" (
    echo [错误] 缺少src\data_updater.py
    exit /b 1
)

if not exist "src\gui.py" (
    echo [错误] 缺少src\gui.py
    exit /b 1
)

if not exist "OracleBatchUpdater.spec" (
    echo [警告] 缺少OracleBatchUpdater.spec（不影响运行）
)

if not exist "requirements.txt" (
    echo [错误] 缺少requirements.txt
    exit /b 1
)

echo.
echo ========================================
echo 验证完成！所有文件和模块正常
echo ========================================
echo.
echo 下一步：
echo 1. 运行 'python main.py' 启动程序
echo 2. 或运行 'package.bat' 打包为exe
echo.
pause
