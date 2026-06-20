# ================================================================
# CHM 安全警告修复脚本 (PowerShell)
# 适用: Windows 10 / Windows 11 / Windows Server 2016+
# 功能: 批量解除 CHM 文件的 Zone.Identifier 锁定
# 用法: 右键 → "使用 PowerShell 运行" 或
#        powershell -ExecutionPolicy Bypass -File chm_unblock.ps1
# ================================================================

param(
    [string]$TargetPath = $PSScriptRoot
)

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "CHM 安全警告修复工具"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Oracle 批量更新工具 — CHM 安全修复" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检测操作系统版本
$osVersion = [System.Environment]::OSVersion.Version
$osInfo = Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version
Write-Host "[*] 操作系统: $($osInfo.Caption) ($($osInfo.Version))" -ForegroundColor Gray

# 查找 CHM 文件
$chmFiles = Get-ChildItem -Path $TargetPath -Recurse -Filter "*.chm" -ErrorAction SilentlyContinue
if ($chmFiles.Count -eq 0) {
    Write-Host "[!] 在 $TargetPath 中未找到 .chm 文件" -ForegroundColor Yellow
    Write-Host "    请将脚本放在 CHM 文件所在目录，或使用参数指定路径：" -ForegroundColor Gray
    Write-Host "    powershell -File chm_unblock.ps1 -TargetPath 'C:\path\to\chm'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "按任意键退出..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

Write-Host "[*] 找到 $($chmFiles.Count) 个 CHM 文件" -ForegroundColor Green
Write-Host ""

# 逐个处理
$fixed = 0
$alreadyOk = 0
$failed = 0

foreach ($file in $chmFiles) {
    $shortName = $file.Name
    Write-Host "  → $shortName ... " -NoNewline
    
    # 检查是否在本地驱动器上（非网络路径）
    $fullPath = $file.FullName
    $isLocal = $fullPath -match '^[A-Za-z]:\\'
    
    if (-not $isLocal) {
        Write-Host "跳过 (网络路径)" -ForegroundColor Yellow
        Write-Host "    [!] CHM 文件不能从网络驱动器打开，请先复制到本地磁盘" -ForegroundColor Yellow
        $failed++
        continue
    }
    
    # 检查路径是否包含 #
    if ($fullPath -match '#') {
        Write-Host "跳过 (路径含 #)" -ForegroundColor Yellow
        Write-Host "    [!] CHM 路径不能包含 # 字符，请移动文件" -ForegroundColor Yellow
        $failed++
        continue
    }
    
    try {
        # 尝试解除锁定
        # 检查是否有 Zone.Identifier 流
        $zoneStream = "$fullPath" + ":Zone.Identifier"
        $hadZone = Test-Path $zoneStream -ErrorAction SilentlyContinue
        
        Unblock-File -Path $fullPath -ErrorAction Stop
        
        if ($hadZone) {
            Write-Host "已解除锁定" -ForegroundColor Green
            $fixed++
        } else {
            Write-Host "无需修复 (无锁定标记)" -ForegroundColor Gray
            $alreadyOk++
        }
    } catch {
        # PowerShell 2.0 (Windows 7 默认) 不支持 Unblock-File
        Write-Host "尝试备用方法... " -NoNewline
        try {
            # 备用方法：通过删除 Zone.Identifier 流
            $zoneStream = "$fullPath" + ":Zone.Identifier"
            if (Test-Path $zoneStream) {
                Remove-Item -Path $zoneStream -Force -ErrorAction Stop
                Write-Host "已解除锁定 (备用方法)" -ForegroundColor Green
                $fixed++
            } else {
                Write-Host "无需修复" -ForegroundColor Gray
                $alreadyOk++
            }
        } catch {
            Write-Host "失败" -ForegroundColor Red
            Write-Host "    [!] 请尝试右键文件 → 属性 → 解除锁定" -ForegroundColor Red
            $failed++
        }
    }
}

# 汇总
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  修复完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  已解除锁定: $fixed" -ForegroundColor Green
Write-Host "  无需修复:   $alreadyOk" -ForegroundColor Gray
if ($failed -gt 0) {
    Write-Host "  失败/跳过:  $failed" -ForegroundColor Red
}
Write-Host ""

# 如果是网络路径导致的问题，给出建议
if ($failed -gt 0) {
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "  故障排除建议" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "  1. 将 CHM 文件复制到本地磁盘 (C:\ 或 D:\)" -ForegroundColor White
    Write-Host "  2. 右键文件 → 属性 → 勾选「解除锁定」→ 确定" -ForegroundColor White
    Write-Host "  3. 确保文件路径不含 # 字符" -ForegroundColor White
    Write-Host "  4. 如果从 ZIP 解压，请先解压到本地再打开" -ForegroundColor White
    Write-Host ""
}

Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")