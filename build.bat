@echo off
chcp 65001 >nul
echo ========================================
echo Oracle批量更新工具 - 打包脚本
echo ========================================
echo.

echo 正在安装PyInstaller...
pip install pyinstaller -q

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [警告] PyInstaller安装可能失败，尝试继续...
)

echo.
echo 正在打包程序...
echo.

pyinstaller OracleBatchUpdater.spec --clean

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [错误] 打包失败！
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo 打包完成！
echo ========================================
echo.
echo exe文件位置: dist\OracleBatchUpdater.exe
echo.
echo 使用说明:
echo 1. 将dist目录下的所有文件复制到目标电脑
echo 2. 运行OracleBatchUpdater.exe即可使用
echo 3. 无需安装Python环境
echo.
pause
