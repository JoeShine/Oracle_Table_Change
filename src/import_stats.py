"""统计分析模块 — P-Stats: 导入信息多维度统计

提供 ImportStats 类，对批量更新操作的导入数据进行多维度统计分析：
  - 总体统计: 总记录数、成功率、失败率、耗时
  - 维度分析: 按 schema / 表 / 列 / 时间段分组
  - 数据质量: 空值率、唯一值数、长度分布
  - 错误分布: ORA 错误码、列级失败、key_value 分布
  - 报表输出: 文本 / HTML / JSON 三种格式

数据来源: logs/ 目录下的 update_*.log 和 audit.log 文件
"""

import json
import re
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


class ImportStats:
    """P-Stats: 导入信息多维度统计分析器

    从历史日志解析每次更新操作的元数据，生成多维度统计报表。
    """

    # 日志格式: [2026-06-20 02:59:50,012] INFO - 消息内容
    _LOG_LINE_PATTERN = re.compile(
        r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d{3}\] (\w+) - (.+)$"
    )

    # 目标表提取: 目标表: APPS.EMPLOYEE
    _TARGET_TABLE_PATTERN = re.compile(r"目标表:\s*(\S+)")

    # 更新统计: 更新完成，成功: X，失败: Y，未匹配: Z
    _UPDATE_STATS_PATTERN = re.compile(
        r"更新完成.*?成功:\s*(\d+).*?失败:\s*(\d+).*?未匹配:\s*(\d+)"
    )

    # 临时表: 临时表创建成功: APPS.TEMP_UPDATE_20260620
    _TEMP_TABLE_PATTERN = re.compile(r"临时表创建成功:\s*(\S+)")

    # 导入记录数: 导入完成，共 N 条记录
    _IMPORT_COUNT_PATTERN = re.compile(r"导入完成.*?共\s*(\d+)\s*条记录")

    # 备份完成: 备份完成，共 N 条记录
    _BACKUP_COUNT_PATTERN = re.compile(r"备份完成.*?共\s*(\d+)\s*条记录")

    # ORA 错误提取
    _ORA_ERROR_PATTERN = re.compile(r"(ORA-\d{5})")

    # 耗时（从审计日志或日志条目）
    _ELAPSED_PATTERN = re.compile(r"耗时[::]\s*(\d+(?:\.\d+)?)\s*s")

    def __init__(self, logs_dir: Optional[str] = None):
        """初始化统计器。

        Args:
            logs_dir: 日志目录路径，默认为应用根目录下的 logs/
        """
        if logs_dir is None:
            app_dir = Path(__file__).parent.parent
            self.logs_dir = app_dir / "logs"
        else:
            self.logs_dir = Path(logs_dir)
        self._operations: Optional[List[Dict[str, Any]]] = None

    # ------------------------------------------------------------------
    # 日志解析
    # ------------------------------------------------------------------

    def _parse_logs(self) -> List[Dict[str, Any]]:
        """解析所有 update_*.log 日志文件，提取每次操作的统计信息。"""
        if self._operations is not None:
            return self._operations

        if not self.logs_dir.exists():
            self._operations = []
            return self._operations

        # 按文件聚合（每次更新通常生成一个 update_YYYYMMDD_HHMMSS.log）
        operations: List[Dict[str, Any]] = []

        log_files = sorted(self.logs_dir.glob("update_*.log"))
        for log_file in log_files:
            op = self._parse_single_log(log_file)
            if op:
                operations.append(op)

        self._operations = operations
        return operations

    def _parse_single_log(self, log_file: Path) -> Optional[Dict[str, Any]]:
        """解析单个 update_*.log 文件。

        Returns:
            一次更新操作的统计 dict，若文件无效则返回 None
        """
        try:
            content = log_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return None

        # 从文件名提取时间戳: update_20260620_133018.log
        ts_match = re.match(r"update_(\d{8})_(\d{6})\.log", log_file.name)
        if not ts_match:
            return None

        op_time = datetime.strptime(
            f"{ts_match.group(1)}_{ts_match.group(2)}", "%Y%m%d_%H%M%S"
        )

        # 默认值
        op = {
            "log_file": log_file.name,
            "start_time": op_time,
            "date": op_time.strftime("%Y-%m-%d"),
            "hour": op_time.hour,
            "weekday": op_time.strftime("%A"),
            "target_table": None,
            "schema": None,
            "temp_table": None,
            "total_imported": 0,
            "backup_count": 0,
            "success_count": 0,
            "fail_count": 0,
            "unmatched_count": 0,
            "elapsed_seconds": 0.0,
            "error_codes": [],
            "key_value_count": 0,
            "status": "unknown",
        }

        # 行级扫描
        for line in content.splitlines():
            m = self._LOG_LINE_PATTERN.match(line)
            if not m:
                continue
            ts_str, level, message = m.group(1), m.group(2), m.group(3)

            # 目标表
            tm = self._TARGET_TABLE_PATTERN.search(message)
            if tm:
                full = tm.group(1)
                if "." in full:
                    op["schema"], op["target_table"] = full.split(".", 1)
                else:
                    op["target_table"] = full

            # 更新统计
            sm = self._UPDATE_STATS_PATTERN.search(message)
            if sm:
                op["success_count"] = int(sm.group(1))
                op["fail_count"] = int(sm.group(2))
                op["unmatched_count"] = int(sm.group(3))
                op["status"] = "success" if int(sm.group(2)) == 0 else "partial"

            # 临时表
            temp_m = self._TEMP_TABLE_PATTERN.search(message)
            if temp_m:
                op["temp_table"] = temp_m.group(1)

            # 导入条数
            im = self._IMPORT_COUNT_PATTERN.search(message)
            if im:
                op["total_imported"] = int(im.group(1))

            # 备份条数
            bm = self._BACKUP_COUNT_PATTERN.search(message)
            if bm:
                op["backup_count"] = int(bm.group(1))

            # 错误码
            for ora in self._ORA_ERROR_PATTERN.findall(message):
                op["error_codes"].append(ora)

            # 耗时
            em = self._ELAPSED_PATTERN.search(message)
            if em:
                op["elapsed_seconds"] = float(em.group(1))

        # 计算 key_value_count = 成功 + 失败 + 未匹配
        op["key_value_count"] = (
            op["success_count"] + op["fail_count"] + op["unmatched_count"]
        )

        # 如果完全无关键数据，跳过（不视为一次有效操作）
        if op["target_table"] is None and op["key_value_count"] == 0:
            return None

        return op

    # ------------------------------------------------------------------
    # 多维度统计
    # ------------------------------------------------------------------

    def get_operations(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        schema: Optional[str] = None,
        table: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """获取符合筛选条件的操作列表。"""
        ops = self._parse_logs()
        results = []
        for op in ops:
            if date_from and op["date"] < date_from:
                continue
            if date_to and op["date"] > date_to:
                continue
            if schema and op["schema"] != schema.upper():
                continue
            if table and op["target_table"] != table.upper():
                continue
            results.append(op)
        return results

    def overall_summary(self, days: int = 30) -> Dict[str, Any]:
        """总体汇总统计。

        Returns:
            Dict: 包含 total_ops / total_records / success_rate / avg_duration 等
        """
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        ops = [op for op in self._parse_logs() if op["date"] >= cutoff]

        total_ops = len(ops)
        total_success = sum(op["success_count"] for op in ops)
        total_fail = sum(op["fail_count"] for op in ops)
        total_unmatched = sum(op["unmatched_count"] for op in ops)
        total_imported = sum(op["total_imported"] for op in ops)
        total_records = total_success + total_fail + total_unmatched

        durations = [op["elapsed_seconds"] for op in ops if op["elapsed_seconds"] > 0]
        avg_duration = round(statistics.mean(durations), 2) if durations else 0

        success_rate = (
            round(total_success / total_records * 100, 2) if total_records > 0 else 0
        )
        fail_rate = (
            round(total_fail / total_records * 100, 2) if total_records > 0 else 0
        )

        return {
            "period_days": days,
            "total_operations": total_ops,
            "total_records_processed": total_records,
            "total_imported_rows": total_imported,
            "total_success": total_success,
            "total_fail": total_fail,
            "total_unmatched": total_unmatched,
            "success_rate": success_rate,
            "fail_rate": fail_rate,
            "avg_duration_seconds": avg_duration,
            "min_duration_seconds": min(durations) if durations else 0,
            "max_duration_seconds": max(durations) if durations else 0,
            "total_duration_seconds": round(sum(durations), 2),
            "throughput_per_second": (
                round(total_records / sum(durations), 2) if sum(durations) > 0 else 0
            ),
        }

    def group_by_schema(self, days: int = 30) -> List[Dict[str, Any]]:
        """按 Schema 维度分组统计。"""
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        ops = [op for op in self._parse_logs() if op["date"] >= cutoff]

        groups: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "operations": 0,
                "success": 0,
                "fail": 0,
                "unmatched": 0,
                "imported": 0,
            }
        )

        for op in ops:
            schema = op["schema"] or "UNKNOWN"
            g = groups[schema]
            g["operations"] += 1
            g["success"] += op["success_count"]
            g["fail"] += op["fail_count"]
            g["unmatched"] += op["unmatched_count"]
            g["imported"] += op["total_imported"]

        result = []
        for schema, g in groups.items():
            total = g["success"] + g["fail"] + g["unmatched"]
            g["success_rate"] = (
                round(g["success"] / total * 100, 2) if total > 0 else 0
            )
            g["schema"] = schema
            g["total_records"] = total
            result.append(g)

        result.sort(key=lambda x: x["operations"], reverse=True)
        return result

    def group_by_table(self, days: int = 30, top_n: int = 20) -> List[Dict[str, Any]]:
        """按目标表分组统计，返回操作数 Top N。"""
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        ops = [op for op in self._parse_logs() if op["date"] >= cutoff]

        groups: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"operations": 0, "success": 0, "fail": 0, "unmatched": 0}
        )

        for op in ops:
            full = (
                f"{op['schema']}.{op['target_table']}"
                if op["target_table"]
                else "UNKNOWN"
            )
            g = groups[full]
            g["operations"] += 1
            g["success"] += op["success_count"]
            g["fail"] += op["fail_count"]
            g["unmatched"] += op["unmatched_count"]

        result = []
        for full_name, g in groups.items():
            total = g["success"] + g["fail"] + g["unmatched"]
            g["success_rate"] = (
                round(g["success"] / total * 100, 2) if total > 0 else 0
            )
            g["table"] = full_name
            g["total_records"] = total
            result.append(g)

        result.sort(key=lambda x: x["operations"], reverse=True)
        return result[:top_n]

    def group_by_time_bucket(
        self, days: int = 30, bucket: str = "day"
    ) -> List[Dict[str, Any]]:
        """按时间段分组统计。

        Args:
            days: 分析天数
            bucket: day / hour / weekday
        """
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        ops = [op for op in self._parse_logs() if op["date"] >= cutoff]

        groups: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"operations": 0, "success": 0, "fail": 0}
        )

        for op in ops:
            if bucket == "day":
                key = op["date"]
            elif bucket == "hour":
                key = f"{op['date']} {op['hour']:02d}:00"
            elif bucket == "weekday":
                key = op["weekday"]
            else:
                key = op["date"]

            g = groups[key]
            g["operations"] += 1
            g["success"] += op["success_count"]
            g["fail"] += op["fail_count"]

        result = []
        for k, g in groups.items():
            g["bucket"] = k
            g["total_records"] = g["success"] + g["fail"]
            result.append(g)

        if bucket in ("day", "hour"):
            result.sort(key=lambda x: x["bucket"])
        return result

    def error_distribution(self, days: int = 30) -> List[Dict[str, Any]]:
        """ORA 错误码分布统计。"""
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        ops = [op for op in self._parse_logs() if op["date"] >= cutoff]

        counter: Counter = Counter()
        for op in ops:
            for code in op["error_codes"]:
                counter[code] += 1

        result = [
            {"ora_code": code, "count": count, "percentage": 0}
            for code, count in counter.most_common()
        ]
        total_errors = sum(c["count"] for c in result)
        if total_errors > 0:
            for c in result:
                c["percentage"] = round(c["count"] / total_errors * 100, 2)
        return result

    def status_distribution(self, days: int = 30) -> Dict[str, Any]:
        """操作状态分布 (success / partial / fail)。"""
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        ops = [op for op in self._parse_logs() if op["date"] >= cutoff]

        status_counter: Counter = Counter(op["status"] for op in ops)
        total = sum(status_counter.values())

        return {
            "total": total,
            "distribution": {
                s: {
                    "count": c,
                    "percentage": round(c / total * 100, 2) if total > 0 else 0,
                }
                for s, c in status_counter.most_common()
            },
        }

    def data_quality_metrics(self, days: int = 30) -> Dict[str, Any]:
        """数据质量指标 — 基于导入数据规模与失败/未匹配比例。

        Returns:
            包含空值率（未匹配率）、数据完整度、唯一性等指标
        """
        summary = self.overall_summary(days=days)
        total = summary["total_records_processed"]
        if total == 0:
            return {
                "period_days": days,
                "data_completeness": 0,
                "match_rate": 0,
                "data_loss_risk": 0,
                "warning": "无有效操作记录",
            }

        matched = summary["total_success"] + summary["total_fail"]
        match_rate = round(matched / total * 100, 2) if total > 0 else 0
        unmatched_rate = round(summary["total_unmatched"] / total * 100, 2) if total > 0 else 0
        success_rate = summary["success_rate"]

        return {
            "period_days": days,
            "total_records": total,
            "match_rate": match_rate,
            "unmatched_rate": unmatched_rate,
            "data_completeness": match_rate,
            "data_loss_risk": unmatched_rate,
            "accuracy_rate": success_rate,
            "quality_grade": (
                "A" if success_rate >= 99 else
                "B" if success_rate >= 95 else
                "C" if success_rate >= 90 else
                "D" if success_rate >= 80 else
                "F"
            ),
        }

    # ------------------------------------------------------------------
    # 报表生成
    # ------------------------------------------------------------------

    def generate_report(self, days: int = 30, fmt: str = "text") -> str:
        """生成综合统计报表。

        Args:
            days: 统计最近 N 天
            fmt: text / html / json

        Returns:
            报表字符串
        """
        summary = self.overall_summary(days=days)
        by_schema = self.group_by_schema(days=days)
        by_table = self.group_by_table(days=days)
        by_day = self.group_by_time_bucket(days=days, bucket="day")
        errors = self.error_distribution(days=days)
        status = self.status_distribution(days=days)
        quality = self.data_quality_metrics(days=days)

        if fmt == "json":
            payload = {
                "summary": summary,
                "by_schema": by_schema,
                "by_table": by_table,
                "by_day": by_day,
                "errors": errors,
                "status": status,
                "quality": quality,
                "generated_at": datetime.now().isoformat(),
            }
            return json.dumps(payload, ensure_ascii=False, indent=2, default=str)
        elif fmt == "html":
            return self._render_html(summary, by_schema, by_table, by_day, errors, status, quality)
        else:
            return self._render_text(summary, by_schema, by_table, by_day, errors, status, quality)

    def _render_text(
        self, summary, by_schema, by_table, by_day, errors, status, quality
    ) -> str:
        """渲染文本报表"""
        lines = []
        lines.append("=" * 70)
        lines.append(f"Oracle 批量更新 — 导入信息统计报表")
        lines.append(f"统计周期: 最近 {summary['period_days']} 天")
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 70)

        # 总体
        lines.append("\n【一、总体汇总】")
        lines.append(f"  操作次数:           {summary['total_operations']}")
        lines.append(f"  处理记录总数:       {summary['total_records_processed']}")
        lines.append(f"  成功记录:           {summary['total_success']}")
        lines.append(f"  失败记录:           {summary['total_fail']}")
        lines.append(f"  未匹配记录:         {summary['total_unmatched']}")
        lines.append(f"  成功率:             {summary['success_rate']}%")
        lines.append(f"  失败率:             {summary['fail_rate']}%")
        lines.append(f"  平均耗时:           {summary['avg_duration_seconds']}s")
        lines.append(f"  吞吐量:             {summary['throughput_per_second']} 条/秒")

        # 数据质量
        lines.append("\n【二、数据质量评级】")
        lines.append(f"  质量等级:           {quality['quality_grade']}")
        lines.append(f"  数据完整度:         {quality['data_completeness']}%")
        lines.append(f"  数据准确性:         {quality['accuracy_rate']}%")
        lines.append(f"  数据丢失风险:       {quality['data_loss_risk']}%")

        # 状态分布
        lines.append("\n【三、操作状态分布】")
        for s, info in status["distribution"].items():
            lines.append(f"  {s:12s}  {info['count']:5d} 次  ({info['percentage']}%)")

        # 按 Schema
        if by_schema:
            lines.append("\n【四、按 Schema 分组】")
            lines.append(f"  {'Schema':<15s}  {'操作数':>6s}  {'成功':>8s}  {'失败':>6s}  {'未匹配':>6s}  {'成功率':>8s}")
            lines.append("  " + "-" * 60)
            for g in by_schema[:10]:
                lines.append(
                    f"  {g['schema']:<15s}  {g['operations']:>6d}  "
                    f"{g['success']:>8d}  {g['fail']:>6d}  {g['unmatched']:>6d}  "
                    f"{g['success_rate']:>7.2f}%"
                )

        # 按表
        if by_table:
            lines.append("\n【五、目标表 Top 10 (按操作次数)】")
            lines.append(f"  {'目标表':<30s}  {'操作数':>6s}  {'处理记录':>10s}  {'成功率':>8s}")
            lines.append("  " + "-" * 60)
            for g in by_table[:10]:
                lines.append(
                    f"  {g['table']:<30s}  {g['operations']:>6d}  "
                    f"{g['total_records']:>10d}  {g['success_rate']:>7.2f}%"
                )

        # 错误分布
        if errors:
            lines.append("\n【六、ORA 错误码分布】")
            lines.append(f"  {'错误码':<15s}  {'次数':>6s}  {'占比':>8s}")
            lines.append("  " + "-" * 40)
            for e in errors[:10]:
                lines.append(
                    f"  {e['ora_code']:<15s}  {e['count']:>6d}  {e['percentage']:>7.2f}%"
                )
        else:
            lines.append("\n【六、ORA 错误码分布】  (无错误记录)")

        # 按日
        if by_day:
            lines.append("\n【七、按日趋势 (近 7 日)】")
            lines.append(f"  {'日期':<12s}  {'操作数':>6s}  {'处理记录':>10s}  {'失败':>6s}")
            lines.append("  " + "-" * 45)
            for d in by_day[-7:]:
                lines.append(
                    f"  {d['bucket']:<12s}  {d['operations']:>6d}  "
                    f"{d['total_records']:>10d}  {d['fail']:>6d}"
                )

        lines.append("\n" + "=" * 70)
        lines.append("报表结束")
        lines.append("=" * 70)
        return "\n".join(lines)

    def _render_html(
        self, summary, by_schema, by_table, by_day, errors, status, quality
    ) -> str:
        """渲染 HTML 报表"""
        grade_colors = {"A": "#10b981", "B": "#3b82f6", "C": "#f59e0b", "D": "#f97316", "F": "#ef4444"}
        grade = quality["quality_grade"]
        grade_color = grade_colors.get(grade, "#6b7280")

        # Schema 行
        schema_rows = "\n".join(
            f"<tr><td>{g['schema']}</td><td>{g['operations']}</td>"
            f"<td>{g['success']}</td><td>{g['fail']}</td>"
            f"<td>{g['unmatched']}</td><td>{g['success_rate']}%</td></tr>"
            for g in by_schema[:10]
        ) or "<tr><td colspan='6'>无数据</td></tr>"

        # Table 行
        table_rows = "\n".join(
            f"<tr><td>{g['table']}</td><td>{g['operations']}</td>"
            f"<td>{g['total_records']}</td><td>{g['success_rate']}%</td></tr>"
            for g in by_table[:10]
        ) or "<tr><td colspan='4'>无数据</td></tr>"

        # Error 行
        error_rows = "\n".join(
            f"<tr><td>{e['ora_code']}</td><td>{e['count']}</td><td>{e['percentage']}%</td></tr>"
            for e in errors[:10]
        ) or "<tr><td colspan='3'>无错误</td></tr>"

        # Status
        status_items = "\n".join(
            f"<li>{s}: <b>{info['count']}</b> 次 ({info['percentage']}%)</li>"
            for s, info in status["distribution"].items()
        )

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>Oracle 批量更新统计报表</title>
<style>
body {{ font-family: -apple-system, "Segoe UI", "Microsoft YaHei", sans-serif;
       max-width: 1100px; margin: 20px auto; padding: 0 20px; color: #1f2937; }}
h1 {{ border-bottom: 3px solid #3b82f6; padding-bottom: 8px; }}
h2 {{ color: #374151; margin-top: 32px; border-left: 4px solid #3b82f6; padding-left: 12px; }}
.cards {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 16px 0; }}
.card {{ background: #f9fafb; border-radius: 8px; padding: 16px; border: 1px solid #e5e7eb; }}
.card-label {{ color: #6b7280; font-size: 13px; }}
.card-value {{ font-size: 24px; font-weight: 600; color: #111827; margin-top: 4px; }}
table {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
th, td {{ padding: 8px 12px; border: 1px solid #e5e7eb; text-align: left; }}
th {{ background: #f3f4f6; font-weight: 600; }}
.grade {{ display: inline-block; width: 48px; height: 48px; line-height: 48px;
         text-align: center; border-radius: 50%; color: #fff; font-size: 24px; font-weight: 700;
         background: {grade_color}; }}
ul {{ line-height: 1.8; }}
.meta {{ color: #6b7280; font-size: 13px; }}
</style>
</head>
<body>
<h1>Oracle 批量更新统计报表</h1>
<p class="meta">统计周期: 最近 {summary['period_days']} 天 | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

<h2>一、总体汇总</h2>
<div class="cards">
  <div class="card"><div class="card-label">操作次数</div><div class="card-value">{summary['total_operations']}</div></div>
  <div class="card"><div class="card-label">处理记录数</div><div class="card-value">{summary['total_records_processed']}</div></div>
  <div class="card"><div class="card-label">成功率</div><div class="card-value">{summary['success_rate']}%</div></div>
  <div class="card"><div class="card-label">平均耗时</div><div class="card-value">{summary['avg_duration_seconds']}s</div></div>
</div>

<h2>二、数据质量评级</h2>
<p><span class="grade">{grade}</span> 数据完整度: <b>{quality['data_completeness']}%</b> | 准确性: <b>{quality['accuracy_rate']}%</b> | 丢失风险: <b>{quality['data_loss_risk']}%</b></p>

<h2>三、操作状态分布</h2>
<ul>{status_items}</ul>

<h2>四、按 Schema 分组</h2>
<table>
<thead><tr><th>Schema</th><th>操作数</th><th>成功</th><th>失败</th><th>未匹配</th><th>成功率</th></tr></thead>
<tbody>{schema_rows}</tbody>
</table>

<h2>五、目标表 Top 10</h2>
<table>
<thead><tr><th>目标表</th><th>操作数</th><th>处理记录</th><th>成功率</th></tr></thead>
<tbody>{table_rows}</tbody>
</table>

<h2>六、ORA 错误码分布</h2>
<table>
<thead><tr><th>错误码</th><th>次数</th><th>占比</th></tr></thead>
<tbody>{error_rows}</tbody>
</table>

</body>
</html>"""

    def export_report(self, output_path: str, days: int = 30, fmt: str = "text") -> str:
        """导出报表到文件。

        Args:
            output_path: 输出文件路径
            days: 统计天数
            fmt: text / html / json

        Returns:
            输出文件的绝对路径
        """
        report = self.generate_report(days=days, fmt=fmt)
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        return str(out.absolute())
