@echo off
chcp 65001 >nul
echo ========================================
echo Oracle数据批量修改工具 - 依赖安装脚本
echo ========================================
echo.

echo 正在安装Python依赖...
echo.

pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [错误] 依赖安装失败！
    echo 请确保已安装Python 3.8或更高版本
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo 依赖安装完成！
echo ========================================
echo.
echo 下一步:
echo 1. 运行 'python main.py' 启动程序
echo 2. 或运行 'pyinstaller OracleBatchUpdater.spec' 打包为exe
echo.
pause
