@echo off
REM ================================================================
REM CHM 安全警告修复脚本 (Batch)
REM 适用: Windows 7 / Windows Server 2008 R2
REM 功能: 解除 CHM 文件的 Zone.Identifier 锁定
REM 用法: 双击运行，或放在 CHM 文件所在目录运行
REM ================================================================

title CHM 安全警告修复工具

echo ========================================
echo   Oracle 批量更新工具 - CHM 安全修复
echo ========================================
echo.

REM 检测操作系统版本
ver | find "6.1" >nul && set OSNAME=Windows 7
ver | find "6.0" >nul && set OSNAME=Windows Vista
ver | find "10.0" >nul && set OSNAME=Windows 10/11
if "%OSNAME%"=="" set OSNAME=Windows

echo [*] 操作系统: %OSNAME%
echo [*] 当前目录: %CD%
echo.

REM 查找 CHM 文件
set FIXED=0
set OK=0
set FAILED=0
set FOUND=0

for %%f in (*.chm) do (
    set /a FOUND+=1
    call :FIX_CHM "%%f"
)

if %FOUND%==0 (
    echo [!] 当前目录未找到 .chm 文件
    echo     请将本脚本放在 CHM 文件所在目录运行
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   修复完成
echo ========================================
echo   已解除锁定: %FIXED%
echo   无需修复:   %OK%
if %FAILED% gtr 0 (
    echo   失败/跳过:  %FAILED%
)
echo.

if %FIXED% gtr 0 (
    echo [√] 现在可以正常打开 CHM 帮助手册了
)

if %FAILED% gtr 0 (
    echo ========================================
    echo   故障排除建议
    echo ========================================
    echo   1. 将 CHM 文件复制到本地磁盘 (C: 或 D:)
    echo   2. 右键文件 - 属性 - 勾选"解除锁定"- 确定
    echo   3. 确保文件路径不含 # 字符
    echo   4. 确保文件不在网络驱动器上
    echo.
)

echo 按任意键退出...
pause >nul
exit /b 0

REM ---------------------------------------------------------------
REM 修复单个 CHM 文件
REM ---------------------------------------------------------------
:FIX_CHM
setlocal
set "CHMFILE=%~1"
set "CHMPATH=%~f1"

echo   → %~nx1 ... 

REM 检查是否在本地驱动器
echo %CHMPATH% | find "\\" >nul
if %errorlevel%==0 (
    echo     跳过 ^(网络路径^)
    echo      [!] CHM 文件不能从网络驱动器打开，请先复制到本地磁盘
    set /a FAILED+=1
    goto :EOF
)

REM 检查路径是否包含 #
echo %CHMPATH% | find "#" >nul
if %errorlevel%==0 (
    echo     跳过 ^(路径含 #^)
    echo      [!] CHM 路径不能包含 # 字符，请移动文件
    set /a FAILED+=1
    goto :EOF
)

REM 检查是否有 Zone.Identifier 流
dir /r "%CHMFILE%" 2>nul | find ":Zone.Identifier" >nul
if %errorlevel%==0 (
    REM 有 Zone.Identifier - 需要解除
    REM 方法1: 使用 type 命令读取并丢弃 Zone.Identifier 流
    REM 方法2: 使用 echo 写入空内容覆盖
    (
        echo [ZoneTransfer]
        echo ZoneId=0
    ) > "%CHMPATH%:Zone.Identifier" 2>nul
    
    if %errorlevel%==0 (
        echo     已解除锁定
        set /a FIXED+=1
    ) else (
        REM 备用方法: 使用 more 命令
        type nul > "%CHMPATH%:Zone.Identifier" 2>nul
        if %errorlevel%==0 (
            echo     已解除锁定 ^(备用方法^)
            set /a FIXED+=1
        ) else (
            echo     失败
            echo      [!] 请右键文件 → 属性 → 解除锁定
            set /a FAILED+=1
        )
    )
) else (
    echo     无需修复 ^(无锁定标记^)
    set /a OK+=1
)

goto :EOF