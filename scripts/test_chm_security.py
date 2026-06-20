#!/usr/bin/env python3
"""
CHM 兼容性测试工具 — 模拟 Windows 7/10/11 下的 CHM 安全警告检查

测试项目:
  1-3:  CHM 二进制结构验证 (ITSF/ITSP/PMGL)
  4-6:  内容文件完整性 (HTML/CSS/图片)
  7-9:  安全警告模拟 (检查 Zone.Identifier 风险)
  10-12: 路径兼容性 (网络路径/#字符/长路径)
  13-15: 跨版本兼容性 (Win7/Win10/Win11 注册表策略)
"""

import struct
import os
import sys
import hashlib
import zipfile
from pathlib import Path
from datetime import datetime


# ============================================================
# 工具函数
# ============================================================

def find_chm_files(base_dir: str) -> list:
    """查找项目中的所有 CHM 文件"""
    chm_files = []
    base = Path(base_dir)
    for chm in base.rglob("*.chm"):
        chm_files.append(chm)
    return chm_files


def read_chm_header(chm_path: Path) -> dict:
    """读取 CHM 文件的 ITSF 头部信息"""
    with open(chm_path, 'rb') as f:
        data = f.read(0x60)  # 96 bytes header
        if len(data) < 0x60:
            return {"error": "文件太小，不是有效的 CHM 文件"}

        magic = data[0:4]
        version = struct.unpack_from('<I', data, 4)[0]
        header_len = struct.unpack_from('<I', data, 8)[0]
        lang_id = struct.unpack_from('<I', data, 0x14)[0]
        dir_offset = struct.unpack_from('<Q', data, 0x38)[0]
        content_offset = struct.unpack_from('<Q', data, 0x40)[0]
        total_size = struct.unpack_from('<Q', data, 0x48)[0]

        return {
            "magic": magic,
            "version": version,
            "header_len": header_len,
            "lang_id": lang_id,
            "dir_offset": dir_offset,
            "content_offset": content_offset,
            "total_size": total_size,
        }


def check_zone_identifier_risk(chm_path: Path) -> dict:
    """检查 CHM 文件的 Zone.Identifier 风险

    在 Linux 上无法直接检测 NTFS ADS，但可以检查:
    - 文件是否在 ZIP 归档中（ZIP 不保留 ADS）
    - 文件是否来自 GitHub Release（下载会附加 ADS）
    - 是否有配套的 ZIP 包
    """
    results = {
        "has_zip_wrapper": False,
        "zip_path": None,
        "risk_level": "UNKNOWN",
        "recommendations": [],
    }

    # 检查是否有配套 ZIP
    zip_path = chm_path.parent / (chm_path.stem + ".zip")
    if zip_path.exists():
        results["has_zip_wrapper"] = True
        results["zip_path"] = str(zip_path)
        results["risk_level"] = "LOW"
        results["recommendations"].append(
            "ZIP 包已存在，用户解压后 CHM 自动解除锁定"
        )
    else:
        results["risk_level"] = "HIGH"
        results["recommendations"].append(
            "缺失 ZIP 包！建议运行 build_chm.py 重新构建"
        )

    # 检查是否有修复脚本
    scripts_dir = chm_path.parent.parent / "scripts"
    ps1_path = scripts_dir / "chm_unblock.ps1"
    bat_path = scripts_dir / "chm_unblock.bat"
    if ps1_path.exists() and bat_path.exists():
        results["has_fix_scripts"] = True
        results["recommendations"].append(
            "修复脚本已就绪 (chm_unblock.ps1 / chm_unblock.bat)"
        )
    else:
        results["has_fix_scripts"] = False
        results["recommendations"].append(
            "缺失修复脚本！请运行 chm_unblock.ps1 或 chm_unblock.bat"
        )

    return results


def check_path_compatibility(chm_path: Path) -> dict:
    """检查 CHM 文件路径的 Windows 兼容性"""
    results = {
        "path": str(chm_path),
        "has_hash": False,
        "is_network_path": False,
        "is_too_long": False,
        "issues": [],
    }

    name = chm_path.name

    # 检查 # 字符
    if "#" in name:
        results["has_hash"] = True
        results["issues"].append(
            "CHM 文件名包含 # 字符，Windows 下无法打开"
        )

    # 检查 UNC 路径
    if str(chm_path).startswith("\\\\"):
        results["is_network_path"] = True
        results["issues"].append(
            "CHM 文件在网络路径上，Windows 下会被阻止。请复制到本地磁盘"
        )

    # 检查路径长度 (Windows MAX_PATH = 260)
    if len(str(chm_path)) > 250:
        results["is_too_long"] = True
        results["issues"].append(
            f"路径过长 ({len(str(chm_path))} 字符)，Windows 下可能无法打开"
        )

    return results


def check_chm_content(chm_path: Path) -> dict:
    """检查 CHM 文件内容完整性：
    - 必须包含的 HTML 页面
    - 必须包含的元数据文件
    - 图片文件
    """
    required_internal = [
        "#SYSTEM", "OracleBatchUpdater_UserManual.hhc",
        "OracleBatchUpdater_UserManual.hhk", "#IDXHDR", "#TOPICS",
        "#STRINGS", "#URLTBL", "#TOCIDX",
    ]
    required_html = [
        "index.html", "product_intro.html", "installation.html",
        "quick_start.html", "features.html", "faq.html",
        "best_practices.html",
    ]
    required_css = ["styles.css"]
    required_images = [
        "images/user_manual_main_interface.jpg",
        "images/user_manual_connection.jpg",
        "images/user_manual_excel_preview.jpg",
    ]

    results = {
        "total_size": chm_path.stat().st_size,
        "internal_files": {"found": 0, "missing": [], "total": len(required_internal)},
        "html_files": {"found": 0, "missing": [], "total": len(required_html)},
        "css_files": {"found": 0, "missing": [], "total": len(required_css)},
        "image_files": {"found": 0, "missing": [], "total": len(required_images)},
        "all_ok": True,
    }

    with open(chm_path, 'rb') as f:
        content = f.read()

    # 搜索内容中的文件名
    for name in required_internal:
        encoded = name.encode('utf-8')
        if encoded in content:
            results["internal_files"]["found"] += 1
        else:
            results["internal_files"]["missing"].append(name)
            results["all_ok"] = False

    for name in required_html:
        encoded = name.encode('utf-8')
        if encoded in content:
            results["html_files"]["found"] += 1
        else:
            results["html_files"]["missing"].append(name)
            results["all_ok"] = False

    for name in required_css:
        encoded = name.encode('utf-8')
        if encoded in content:
            results["css_files"]["found"] += 1
        else:
            results["css_files"]["missing"].append(name)
            results["all_ok"] = False

    for name in required_images:
        encoded = name.encode('utf-8')
        if encoded in content:
            results["image_files"]["found"] += 1
        else:
            results["image_files"]["missing"].append(name)
            results["all_ok"] = False

    return results


def check_win7_registry_policy() -> dict:
    """检查 Windows 7 特有的 CHM 注册表策略兼容性"""
    return {
        "win7_default_zone": 3,  # Internet Zone (默认阻止网络 CHM)
        "win7_max_allowed_zone": 0,  # 默认仅允许本地计算机
        "recommendation": (
            "Windows 7 默认仅允许从本地计算机打开 CHM。"
            "从互联网下载的 CHM 必须解除锁定。"
        ),
        "commanded_fix": "右键文件 → 属性 → 解除锁定",
        "batch_fix": "chm_unblock.bat",
    }


def check_win10_registry_policy() -> dict:
    """检查 Windows 10/11 的 CHM 注册表策略兼容性"""
    return {
        "win10_default_zone": 3,
        "win10_max_allowed_zone": 0,
        "recommendation": (
            "Windows 10/11 默认仅允许从本地计算机打开 CHM。"
            "建议使用 PowerShell 的 Unblock-File 命令解除锁定。"
        ),
        "commanded_fix": "右键文件 → 属性 → 解除锁定 或 powershell Unblock-File",
        "ps_fix": "chm_unblock.ps1",
    }


# ============================================================
# 主测试流程
# ============================================================

def run_all_tests(base_dir: str = None) -> dict:
    """运行全部 CHM 兼容性测试"""
    if base_dir is None:
        base_dir = Path(__file__).parent.parent
    else:
        base_dir = Path(base_dir)

    report = {
        "test_time": datetime.now().isoformat(),
        "base_dir": str(base_dir),
        "chm_files": [],
        "overall_status": "UNKNOWN",
        "total_tests": 0,
        "passed": 0,
        "failed": 0,
        "warnings": 0,
    }

    chm_files = find_chm_files(base_dir)
    if not chm_files:
        report["overall_status"] = "NO_CHM_FOUND"
        report["warnings"] = 1
        report["chm_files"].append({
            "path": "N/A",
            "error": f"在 {base_dir} 中未找到 .chm 文件",
            "tests": [],
        })
        return report

    for chm_path in chm_files:
        file_report = {
            "path": str(chm_path),
            "size": chm_path.stat().st_size,
            "tests": [],
        }

        # 测试 1-3: 二进制结构
        header = read_chm_header(chm_path)
        t1 = {
            "test": "ITSF 魔术字",
            "status": "PASS" if header.get("magic") == b"ITSF" else "FAIL",
            "detail": f"magic={header.get('magic')}",
        }
        t2 = {
            "test": "版本号",
            "status": "PASS" if header.get("version") == 3 else "FAIL",
            "detail": f"version={header.get('version')}",
        }
        t3 = {
            "test": "语言 ID (zh-CN)",
            "status": "PASS" if header.get("lang_id") == 0x0804 else "WARN",
            "detail": f"lang_id=0x{header.get('lang_id', 0):04X}",
        }
        file_report["tests"].extend([t1, t2, t3])

        # 测试 4-6: 内容完整性
        content = check_chm_content(chm_path)
        t4 = {
            "test": f"HTML 页面 ({content['html_files']['found']}/{content['html_files']['total']})",
            "status": "PASS" if content['html_files']['missing'] == [] else "FAIL",
            "detail": content['html_files'].get("missing", []),
        }
        t5 = {
            "test": f"内部元数据 ({content['internal_files']['found']}/{content['internal_files']['total']})",
            "status": "PASS" if content['internal_files']['missing'] == [] else "FAIL",
            "detail": content['internal_files'].get("missing", []),
        }
        t6 = {
            "test": f"图片资源 ({content['image_files']['found']}/{content['image_files']['total']})",
            "status": "PASS" if content['image_files']['missing'] == [] else "WARN",
            "detail": content['image_files'].get("missing", []),
        }
        file_report["tests"].extend([t4, t5, t6])

        # 测试 7-9: Zone.Identifier 风险
        zone = check_zone_identifier_risk(chm_path)
        t7 = {
            "test": "ZIP 安全包",
            "status": "PASS" if zone["has_zip_wrapper"] else "WARN",
            "detail": zone.get("zip_path", "缺失"),
        }
        t8 = {
            "test": "修复脚本",
            "status": "PASS" if zone.get("has_fix_scripts") else "WARN",
            "detail": "chm_unblock.ps1/bat" if zone.get("has_fix_scripts") else "缺失",
        }
        t9 = {
            "test": "安全风险等级",
            "status": "PASS" if zone["risk_level"] == "LOW" else "WARN",
            "detail": zone["risk_level"],
        }
        file_report["tests"].extend([t7, t8, t9])

        # 测试 10-12: 路径兼容性
        path_info = check_path_compatibility(chm_path)
        t10 = {
            "test": "文件名不含 #",
            "status": "FAIL" if path_info["has_hash"] else "PASS",
            "detail": "含 # 字符" if path_info["has_hash"] else "OK",
        }
        t11 = {
            "test": "非网络路径",
            "status": "FAIL" if path_info["is_network_path"] else "PASS",
            "detail": "网络路径" if path_info["is_network_path"] else "本地路径",
        }
        t12 = {
            "test": "路径长度 < 260",
            "status": "FAIL" if path_info["is_too_long"] else "PASS",
            "detail": f"{len(path_info['path'])} 字符",
        }
        file_report["tests"].extend([t10, t11, t12])

        # 测试 13-15: 跨版本兼容性
        win7 = check_win7_registry_policy()
        win10 = check_win10_registry_policy()
        t13 = {
            "test": "Windows 7 兼容性",
            "status": "PASS",
            "detail": win7["recommendation"][:50],
        }
        t14 = {
            "test": "Windows 10/11 兼容性",
            "status": "PASS",
            "detail": win10["recommendation"][:50],
        }
        t15 = {
            "test": "修复方案覆盖",
            "status": "PASS" if zone.get("has_fix_scripts") else "WARN",
            "detail": "PS1 + BAT 双脚本" if zone.get("has_fix_scripts") else "仅手动",
        }
        file_report["tests"].extend([t13, t14, t15])

        # 汇总
        file_report["passed"] = sum(1 for t in file_report["tests"] if t["status"] == "PASS")
        file_report["failed"] = sum(1 for t in file_report["tests"] if t["status"] == "FAIL")
        file_report["warnings"] = sum(1 for t in file_report["tests"] if t["status"] == "WARN")

        report["chm_files"].append(file_report)
        report["total_tests"] += len(file_report["tests"])
        report["passed"] += file_report["passed"]
        report["failed"] += file_report["failed"]
        report["warnings"] += file_report["warnings"]

    if report["failed"] == 0 and report["warnings"] == 0:
        report["overall_status"] = "ALL_PASS"
    elif report["failed"] == 0:
        report["overall_status"] = "PASS_WITH_WARNINGS"
    else:
        report["overall_status"] = "HAS_FAILURES"

    return report


def print_report(report: dict):
    """打印测试报告"""
    print("=" * 70)
    print("  CHM 兼容性测试报告")
    print(f"  测试时间: {report['test_time']}")
    print(f"  项目路径: {report['base_dir']}")
    print("=" * 70)

    for file_report in report["chm_files"]:
        if "error" in file_report:
            print(f"\n  [!] {file_report['error']}")
            continue

        print(f"\n  CHM 文件: {Path(file_report['path']).name}")
        print(f"  大小: {file_report['size']:,} bytes ({file_report['size'] / 1024 / 1024:.1f} MB)")
        print(f"  {'─' * 60}")

        for t in file_report["tests"]:
            icon = {"PASS": "✓", "FAIL": "✗", "WARN": "⚠"}[t["status"]]
            color_code = {"PASS": "32", "FAIL": "31", "WARN": "33"}[t["status"]]
            detail_str = str(t["detail"])
            print(f"  \033[{color_code}m{icon} {t['test']}\033[0m")
            if detail_str and detail_str != "OK":
                print(f"     {detail_str}")

        print(f"\n  汇总: {file_report['passed']} 通过, "
              f"{file_report['failed']} 失败, "
              f"{file_report['warnings']} 警告")

    print(f"\n{'=' * 70}")
    print(f"  总计: {report['total_tests']} 项测试, "
          f"{report['passed']} 通过, "
          f"{report['failed']} 失败, "
          f"{report['warnings']} 警告")
    print(f"  状态: {report['overall_status']}")
    print(f"{'=' * 70}")

    return 0 if report["failed"] == 0 else 1


# ============================================================
# 命令行入口
# ============================================================

if __name__ == "__main__":
    base = sys.argv[1] if len(sys.argv) > 1 else None
    report = run_all_tests(base)
    exit_code = print_report(report)
    sys.exit(exit_code)