# CHM 帮助手册 - Windows 安全警告说明

## 为什么打开 CHM 显示空白或" Navigation to the webpage was canceled"？

这是 Windows 安全机制导致的。当文件从互联网下载或通过网络传输时，
Windows 会在文件上附加一个 Zone.Identifier 标记（"来自其他计算机"），
导致 CHM 内容被阻止。

## 解决方案（按推荐顺序）

### 方案一：从 ZIP 包解压（推荐）

1. 解压旁边的 OracleBatchUpdater_UserManual.zip 文件
2. 将解压出的 .chm 文件复制到本地磁盘（如 C:\ 或 D:\）
3. 双击打开

> ZIP 格式不保留 NTFS 的 ADS 安全标记，解压后自动解除锁定。

### 方案二：运行一键修复脚本

- **Windows 10 / 11**：右键 `chm_unblock.ps1` → "使用 PowerShell 运行"
- **Windows 7**：双击 `chm_unblock.bat`

### 方案三：手动解除锁定（适用于所有 Windows 版本）

1. 右键点击 .chm 文件 → 属性
2. 在"常规"选项卡底部，找到"安全："区域
3. 勾选「解除锁定」复选框
4. 点击确定

### 方案四：网络驱动器 + 注册表修复（仅限高级用户）

如果 CHM 必须放在网络共享上，运行以下命令：

```
reg add "HKLM\SOFTWARE\Microsoft\HTMLHelp\1.x\ItssRestrictions" ^
    /v MaxAllowedZone /t REG_DWORD /d 1 /f
```

> 注意：修改注册表可能降低系统安全性，不建议在生产环境使用。

---

生成时间: 2026-06-20 08:51:29
CHM 版本: v2.8.0
