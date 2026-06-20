"""P3-6: 趋势分析模块

提供 TrendAnalyzer 类，分析更新历史和日志文件，
识别更新频率模式、错误模式、表活跃度和性能趋势。

数据来源: logs/ 目录下的 update_*.log 文件
"""

import re
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, Any, List, Optional, Tuple


class TrendAnalyzer:
    """P3-6: 趋势分析器

    分析更新历史日志，识别频率模式、错误模式、表活跃度和性能趋势。

    Attributes:
        logs_dir: 日志文件目录
        log_data: 解析后的日志数据缓存
    """

    # 日志格式: [2026-06-20 02:59:50,012] INFO - 消息内容
    _LOG_LINE_PATTERN = re.compile(
        r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d{3}\] (\w+) - (.+)$"
    )

    # 目标表提取: 目标表: APPS.EMPLOYEE
    _TARGET_TABLE_PATTERN = re.compile(r"目标表:\s*(\S+)")

    # 更新统计: 更新完成，成功: (\d+)，失败: (\d+)，未匹配: (\d+)
    _UPDATE_STATS_PATTERN = re.compile(
        r"更新完成.*?成功:\s*(\d+).*?失败:\s*(\d+).*?未匹配:\s*(\d+)"
    )

    # 临时表创建: 临时表创建成功
    _TEMP_TABLE_PATTERN = re.compile(r"临时表创建成功:\s*(\S+)")

    # 导入记录数: 导入完成，共 (\d+) 条记录
    _IMPORT_COUNT_PATTERN = re.compile(r"导入完成.*?共\s*(\d+)\s*条记录")

    def __init__(self, logs_dir: str = None):
        """初始化趋势分析器。

        Args:
            logs_dir: 日志目录路径，默认为应用根目录下的 logs/
        """
        if logs_dir is None:
            app_dir = Path(__file__).parent.parent
            self.logs_dir = app_dir / "logs"
        else:
            self.logs_dir = Path(logs_dir)

        self._parsed_logs: Optional[List[Dict[str, Any]]] = None

    # ------------------------------------------------------------------
    # 日志解析
    # ------------------------------------------------------------------

    def _parse_logs(self) -> List[Dict[str, Any]]:
        """解析所有日志文件，提取结构化信息。

        Returns:
            List[Dict[str, Any]]: 解析后的日志条目列表
        """
        if self._parsed_logs is not None:
            return self._parsed_logs

        if not self.logs_dir.exists():
            self._parsed_logs = []
            return self._parsed_logs

        entries = []

        log_files = sorted(self.logs_dir.glob("update_*.log"))
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue

                        match = self._LOG_LINE_PATTERN.match(line)
                        if not match:
                            continue

                        timestamp_str = match.group(1)
                        level = match.group(2)
                        message = match.group(3)

                        try:
                            timestamp = datetime.strptime(
                                timestamp_str, "%Y-%m-%d %H:%M:%S"
                            )
                        except ValueError:
                            continue

                        entry = {
                            "timestamp": timestamp,
                            "date": timestamp.strftime("%Y-%m-%d"),
                            "hour": timestamp.hour,
                            "weekday": timestamp.strftime("%A"),
                            "level": level,
                            "message": message,
                            "log_file": log_file.name,
                        }

                        # 提取表名
                        table_match = self._TARGET_TABLE_PATTERN.search(message)
                        if table_match:
                            entry["target_table"] = table_match.group(1)

                        # 提取更新统计
                        stats_match = self._UPDATE_STATS_PATTERN.search(message)
                        if stats_match:
                            entry["success_count"] = int(stats_match.group(1))
                            entry["fail_count"] = int(stats_match.group(2))
                            entry["unmatched_count"] = int(stats_match.group(3))

                        # 提取临时表
                        temp_match = self._TEMP_TABLE_PATTERN.search(message)
                        if temp_match:
                            entry["temp_table"] = temp_match.group(1)

                        # 提取导入记录数
                        import_match = self._IMPORT_COUNT_PATTERN.search(message)
                        if import_match:
                            entry["import_count"] = int(import_match.group(1))

                        entries.append(entry)

            except Exception:
                continue

        self._parsed_logs = entries
        return self._parsed_logs

    # ------------------------------------------------------------------
    # 更新频率分析
    # ------------------------------------------------------------------

    def analyze_update_frequency(self, days: int = 30) -> Dict[str, Any]:
        """分析更新操作的频率分布。

        按日、周、小时维度统计更新次数。

        Args:
            days: 分析最近 N 天的数据（默认 30 天）

        Returns:
            Dict[str, Any]: 频率分析结果，包含:
                - daily_counts: 每日更新次数
                - hourly_distribution: 每小时更新次数分布
                - weekly_distribution: 每周各天更新次数分布
                - total_updates: 总更新次数
                - busiest_day: 最繁忙的日期
                - busiest_hour: 最繁忙的小时
                - average_per_day: 日均更新次数
        """
        entries = self._parse_logs()

        # 时间范围过滤
        from datetime import datetime, timedelta
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        update_entries = [
            e for e in entries
            if "success_count" in e and e.get("date", "") >= cutoff_date
        ]

        daily_counts = Counter()
        hourly_counts = Counter()
        weekly_counts = Counter()

        for entry in update_entries:
            daily_counts[entry["date"]] += 1
            hourly_counts[entry["hour"]] += 1
            weekly_counts[entry["weekday"]] += 1

        # 计算汇总指标
        total_updates = len(update_entries)
        unique_days = len(daily_counts)

        busiest_day = daily_counts.most_common(1)
        busiest_hour = hourly_counts.most_common(1)

        # 按日期排序的每日统计
        daily_list = [
            {"date": d, "count": c}
            for d, c in sorted(daily_counts.items())
        ]

        # 按小时排序的每小时统计
        hourly_list = [
            {"hour": h, "count": c}
            for h, c in sorted(hourly_counts.items())
        ]

        # 按周几排序
        weekday_order = [
            "Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday"
        ]
        weekly_list = [
            {"weekday": w, "count": weekly_counts.get(w, 0)}
            for w in weekday_order
        ]

        return {
            "total_updates": total_updates,
            "unique_days": unique_days,
            "days_analyzed": days,
            "average_per_day": round(total_updates / unique_days, 2) if unique_days > 0 else 0,
            "daily_counts": daily_list,
            "hourly_distribution": hourly_list,
            "weekly_distribution": weekly_list,
            "busiest_day": {
                "date": busiest_day[0][0],
                "count": busiest_day[0][1],
            } if busiest_day else None,
            "busiest_hour": {
                "hour": busiest_hour[0][0],
                "count": busiest_hour[0][1],
            } if busiest_hour else None,
        }

    # ------------------------------------------------------------------
    # 错误模式分析
    # ------------------------------------------------------------------

    def analyze_error_patterns(self) -> Dict[str, Any]:
        """从历史日志中识别常见错误模式。

        分析 ERROR 级别日志，提取错误类型和频率。

        Returns:
            Dict[str, Any]: 错误模式分析结果，包含:
                - total_errors: 总错误数
                - error_types: 错误类型分类统计
                - most_common_errors: 最常见的错误
                - error_rate: 错误率 (错误数/总操作数)
                - error_timeline: 错误时间线
        """
        entries = self._parse_logs()

        # 筛选错误日志
        error_entries = [e for e in entries if e["level"] == "ERROR"]
        total_operations = len(entries)

        error_types = Counter()
        error_timeline = defaultdict(int)

        for entry in error_entries:
            msg = entry["message"]

            # 分类错误类型
            if "ORA-" in msg:
                # 提取 ORA 错误码
                ora_match = re.search(r"ORA-(\d{5})", msg)
                if ora_match:
                    error_types[f"ORA-{ora_match.group(1)}"] += 1
                else:
                    error_types["Oracle错误"] += 1
            elif "连接失败" in msg or "连接" in msg:
                error_types["连接错误"] += 1
            elif "超时" in msg or "timeout" in msg.lower():
                error_types["超时错误"] += 1
            elif "权限" in msg or "privilege" in msg.lower():
                error_types["权限错误"] += 1
            elif "不存在" in msg or "not found" in msg.lower():
                error_types["资源不存在"] += 1
            elif "数据类型" in msg or "type" in msg.lower():
                error_types["数据类型错误"] += 1
            elif "约束" in msg or "constraint" in msg.lower():
                error_types["约束违反"] += 1
            elif "测试错误" in msg:
                error_types["测试错误"] += 1
            else:
                error_types["其他错误"] += 1

            # 错误时间线
            error_timeline[entry["date"]] += 1

        # 最常见的错误
        most_common = error_types.most_common(10)

        # 错误率
        error_rate = (
            round(len(error_entries) / total_operations * 100, 2)
            if total_operations > 0 else 0
        )

        # 错误时间线排序
        timeline_sorted = [
            {"date": d, "count": c}
            for d, c in sorted(error_timeline.items())
        ]

        return {
            "total_errors": len(error_entries),
            "total_operations": total_operations,
            "error_rate": error_rate,
            "error_types": [
                {"type": t, "count": c} for t, c in most_common
            ],
            "error_timeline": timeline_sorted,
            "sample_errors": [
                {"timestamp": e["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                 "message": e["message"]}
                for e in error_entries[-10:]
            ],
        }

    # ------------------------------------------------------------------
    # 表活跃度分析
    # ------------------------------------------------------------------

    def analyze_table_activity(self) -> Dict[str, Any]:
        """分析哪些表被更新最频繁。

        Returns:
            Dict[str, Any]: 表活跃度分析结果，包含:
                - table_update_counts: 各表更新次数
                - most_active_table: 最活跃的表
                - table_success_rates: 各表成功率
                - table_avg_records: 各表平均更新记录数
        """
        entries = self._parse_logs()

        update_entries = [e for e in entries if "success_count" in e]

        table_counts = Counter()
        table_successes = defaultdict(int)
        table_failures = defaultdict(int)
        table_records = defaultdict(list)

        for entry in update_entries:
            table = entry.get("target_table", "unknown")
            table_counts[table] += 1
            table_successes[table] += entry.get("success_count", 0)
            table_failures[table] += entry.get("fail_count", 0)
            table_records[table].append(
                entry.get("success_count", 0) + entry.get("fail_count", 0)
            )

        most_active = table_counts.most_common(1)

        # 计算各表成功率
        table_success_rates = {}
        for table in table_counts:
            total = table_successes[table] + table_failures[table]
            if total > 0:
                table_success_rates[table] = round(
                    table_successes[table] / total * 100, 2
                )
            else:
                table_success_rates[table] = 100.0

        # 计算平均记录数
        table_avg_records = {}
        for table, records in table_records.items():
            if records:
                table_avg_records[table] = round(sum(records) / len(records), 2)
            else:
                table_avg_records[table] = 0

        result = [
            {
                "table": table,
                "update_count": count,
                "total_success": table_successes[table],
                "total_fail": table_failures[table],
                "success_rate": table_success_rates.get(table, 100.0),
                "avg_records_per_update": table_avg_records.get(table, 0),
            }
            for table, count in table_counts.most_common()
        ]

        return {
            "table_activity": result,
            "most_active_table": {
                "table": most_active[0][0],
                "count": most_active[0][1],
            } if most_active else None,
            "total_tables": len(table_counts),
        }

    # ------------------------------------------------------------------
    # 性能趋势分析
    # ------------------------------------------------------------------

    def analyze_performance_trends(self) -> Dict[str, Any]:
        """分析更新操作的性能趋势。

        通过分析成功/失败记录数、导入记录数等指标，
        追踪更新操作随时间的变化趋势。

        Returns:
            Dict[str, Any]: 性能趋势分析结果，包含:
                - daily_throughput: 每日处理记录数
                - success_rate_trend: 成功率趋势
                - avg_batch_size_trend: 平均批次大小趋势
                - overall_stats: 总体统计
        """
        entries = self._parse_logs()

        update_entries = [e for e in entries if "success_count" in e]

        daily_throughput = defaultdict(lambda: {"total": 0, "success": 0, "fail": 0, "updates": 0})
        daily_batch_sizes = defaultdict(list)

        for entry in update_entries:
            date = entry["date"]
            total = (
                entry.get("success_count", 0)
                + entry.get("fail_count", 0)
            )
            daily_throughput[date]["total"] += total
            daily_throughput[date]["success"] += entry.get("success_count", 0)
            daily_throughput[date]["fail"] += entry.get("fail_count", 0)
            daily_throughput[date]["updates"] += 1

            if "import_count" in entry:
                daily_batch_sizes[date].append(entry["import_count"])

        # 构建趋势数据
        throughput_trend = []
        success_rate_trend = []
        batch_size_trend = []

        for date in sorted(daily_throughput.keys()):
            stats = daily_throughput[date]
            total = stats["total"]
            success = stats["success"]
            rate = round(success / total * 100, 2) if total > 0 else 100.0

            throughput_trend.append({
                "date": date,
                "total_records": total,
                "success_records": success,
                "fail_records": stats["fail"],
                "updates": stats["updates"],
            })

            success_rate_trend.append({
                "date": date,
                "success_rate": rate,
            })

            sizes = daily_batch_sizes.get(date, [])
            if sizes:
                batch_size_trend.append({
                    "date": date,
                    "avg_batch_size": round(sum(sizes) / len(sizes), 2),
                    "max_batch_size": max(sizes),
                    "min_batch_size": min(sizes),
                })

        # 总体统计
        all_success = sum(e.get("success_count", 0) for e in update_entries)
        all_fail = sum(e.get("fail_count", 0) for e in update_entries)
        all_total = all_success + all_fail
        overall_rate = round(all_success / all_total * 100, 2) if all_total > 0 else 100.0

        return {
            "daily_throughput": throughput_trend,
            "success_rate_trend": success_rate_trend,
            "avg_batch_size_trend": batch_size_trend,
            "overall_stats": {
                "total_records_processed": all_total,
                "total_success": all_success,
                "total_fail": all_fail,
                "overall_success_rate": overall_rate,
                "total_updates": len(update_entries),
                "date_range": {
                    "start": throughput_trend[0]["date"] if throughput_trend else None,
                    "end": throughput_trend[-1]["date"] if throughput_trend else None,
                },
            },
        }

    # ------------------------------------------------------------------
    # 综合趋势报告
    # ------------------------------------------------------------------

    def generate_trend_report(self, format: str = "text") -> str:
        """生成综合趋势分析报告。

        整合频率、错误、活跃度和性能四个维度的分析结果。

        Args:
            format: 报告格式，可选 "text" 或 "html"

        Returns:
            str: 趋势分析报告字符串
        """
        freq = self.analyze_update_frequency()
        errors = self.analyze_error_patterns()
        activity = self.analyze_table_activity()
        perf = self.analyze_performance_trends()

        if format == "html":
            return self._generate_html_report(freq, errors, activity, perf)
        return self._generate_text_report(freq, errors, activity, perf)

    def _generate_text_report(
        self,
        freq: Dict[str, Any],
        errors: Dict[str, Any],
        activity: Dict[str, Any],
        perf: Dict[str, Any],
    ) -> str:
        """生成纯文本趋势报告。"""
        lines = []
        lines.append("=" * 70)
        lines.append("  OracleBatchUpdater 趋势分析报告")
        lines.append("=" * 70)
        lines.append(f"  生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # 1. 更新频率
        lines.append("-" * 70)
        lines.append("  1. 更新频率分析")
        lines.append("-" * 70)
        lines.append(f"  总更新次数:     {freq['total_updates']}")
        lines.append(f"  活动天数:       {freq['unique_days']}")
        lines.append(f"  日均更新:       {freq['average_per_day']}")

        if freq.get("busiest_day"):
            lines.append(
                f"  最繁忙日:       {freq['busiest_day']['date']} "
                f"({freq['busiest_day']['count']} 次)"
            )
        if freq.get("busiest_hour"):
            lines.append(
                f"  最繁忙时段:     {freq['busiest_hour']['hour']}:00 "
                f"({freq['busiest_hour']['count']} 次)"
            )

        # 按周分布
        weekly = freq.get("weekly_distribution", [])
        if weekly:
            lines.append("")
            lines.append("  每周分布:")
            for w in weekly:
                bar = "#" * max(1, w["count"])
                lines.append(f"    {w['weekday']:<10} {bar} ({w['count']})")

        lines.append("")

        # 2. 错误模式
        lines.append("-" * 70)
        lines.append("  2. 错误模式分析")
        lines.append("-" * 70)
        lines.append(f"  总错误数:       {errors['total_errors']}")
        lines.append(f"  总操作数:       {errors['total_operations']}")
        lines.append(f"  错误率:         {errors['error_rate']}%")

        error_types = errors.get("error_types", [])
        if error_types:
            lines.append("")
            lines.append("  错误类型分布:")
            for et in error_types[:10]:
                lines.append(f"    {et['type']:<25} {et['count']} 次")

        lines.append("")

        # 3. 表活跃度
        lines.append("-" * 70)
        lines.append("  3. 表活跃度分析")
        lines.append("-" * 70)
        lines.append(f"  涉及表数:       {activity['total_tables']}")

        if activity.get("most_active_table"):
            lines.append(
                f"  最活跃表:       {activity['most_active_table']['table']} "
                f"({activity['most_active_table']['count']} 次)"
            )

        table_activity = activity.get("table_activity", [])
        if table_activity:
            lines.append("")
            lines.append(f"  {'表名':<30} {'更新次数':>8} {'成功率':>8} {'平均记录':>10}")
            lines.append("  " + "-" * 58)
            for ta in table_activity[:10]:
                lines.append(
                    f"  {ta['table']:<30} {ta['update_count']:>8} "
                    f"{ta['success_rate']:>7.1f}% {ta['avg_records_per_update']:>10.1f}"
                )

        lines.append("")

        # 4. 性能趋势
        lines.append("-" * 70)
        lines.append("  4. 性能趋势分析")
        lines.append("-" * 70)
        overall = perf.get("overall_stats", {})
        lines.append(f"  总处理记录:     {overall.get('total_records_processed', 0)}")
        lines.append(f"  总成功:         {overall.get('total_success', 0)}")
        lines.append(f"  总失败:         {overall.get('total_fail', 0)}")
        lines.append(f"  总体成功率:     {overall.get('overall_success_rate', 0)}%")
        lines.append(f"  总更新操作:     {overall.get('total_updates', 0)}")

        date_range = overall.get("date_range", {})
        if date_range.get("start"):
            lines.append(f"  日期范围:       {date_range['start']} ~ {date_range['end']}")

        # 每日吞吐量
        throughput = perf.get("daily_throughput", [])
        if throughput:
            lines.append("")
            lines.append("  每日吞吐量趋势 (最近 10 天):")
            for t in throughput[-10:]:
                bar_len = max(1, min(50, t["total_records"]))
                bar = "#" * bar_len
                lines.append(
                    f"    {t['date']}  {bar} ({t['total_records']} 条, "
                    f"{t['updates']} 次更新)"
                )

        lines.append("")
        lines.append("=" * 70)
        lines.append("  趋势分析报告结束")
        lines.append("=" * 70)
        return "\n".join(lines)

    def _generate_html_report(
        self,
        freq: Dict[str, Any],
        errors: Dict[str, Any],
        activity: Dict[str, Any],
        perf: Dict[str, Any],
    ) -> str:
        """生成 HTML 趋势报告。"""
        html_parts = []
        html_parts.append("""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>趋势分析报告</title>
<style>
  body { font-family: 'Segoe UI', Tahoma, sans-serif; margin: 20px; background: #f5f5f5; }
  .container { max-width: 1200px; margin: 0 auto; background: #fff; padding: 24px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
  h1 { color: #333; border-bottom: 2px solid #007acc; padding-bottom: 10px; }
  h2 { color: #444; margin-top: 30px; border-left: 4px solid #007acc; padding-left: 12px; }
  .stats { display: flex; gap: 16px; flex-wrap: wrap; margin: 16px 0; }
  .stat { background: #f0f7ff; padding: 12px 20px; border-radius: 6px; text-align: center; min-width: 100px; }
  .stat .num { font-size: 22px; font-weight: bold; color: #007acc; }
  .stat .label { font-size: 12px; color: #666; }
  .stat.warn .num { color: #e36209; }
  .stat.danger .num { color: #cb2431; }
  table { width: 100%; border-collapse: collapse; margin: 16px 0; }
  th { background: #f0f7ff; padding: 10px; text-align: left; border-bottom: 2px solid #007acc; }
  td { padding: 8px 10px; border-bottom: 1px solid #eee; }
  .bar { display: inline-block; background: #007acc; height: 14px; border-radius: 3px; margin-right: 6px; vertical-align: middle; }
  .bar.green { background: #22863a; }
  .bar.red { background: #cb2431; }
  .bar.orange { background: #e36209; }
</style>
</head>
<body>
<div class="container">
""")

        html_parts.append(f"<h1>趋势分析报告</h1>")
        html_parts.append(f"<p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")

        # 1. 更新频率
        html_parts.append("<h2>1. 更新频率分析</h2>")
        html_parts.append(f"""<div class="stats">
  <div class="stat"><div class="num">{freq['total_updates']}</div><div class="label">总更新次数</div></div>
  <div class="stat"><div class="num">{freq['unique_days']}</div><div class="label">活动天数</div></div>
  <div class="stat"><div class="num">{freq['average_per_day']}</div><div class="label">日均更新</div></div>
</div>""")

        if freq.get("weekly_distribution"):
            html_parts.append("<table><tr><th>星期</th><th>更新次数</th><th>分布</th></tr>")
            max_count = max(w["count"] for w in freq["weekly_distribution"]) or 1
            for w in freq["weekly_distribution"]:
                pct = w["count"] / max_count * 100
                html_parts.append(
                    f'<tr><td>{w["weekday"]}</td><td>{w["count"]}</td>'
                    f'<td><span class="bar green" style="width:{pct}%"></span></td></tr>'
                )
            html_parts.append("</table>")

        # 2. 错误模式
        html_parts.append("<h2>2. 错误模式分析</h2>")
        html_parts.append(f"""<div class="stats">
  <div class="stat"><div class="num">{errors['total_errors']}</div><div class="label">总错误数</div></div>
  <div class="stat {'danger' if errors['error_rate'] > 10 else ''}"><div class="num">{errors['error_rate']}%</div><div class="label">错误率</div></div>
</div>""")

        if errors.get("error_types"):
            html_parts.append("<table><tr><th>错误类型</th><th>次数</th></tr>")
            for et in errors["error_types"][:10]:
                html_parts.append(f"<tr><td>{et['type']}</td><td>{et['count']}</td></tr>")
            html_parts.append("</table>")

        # 3. 表活跃度
        html_parts.append("<h2>3. 表活跃度分析</h2>")
        if activity.get("most_active_table"):
            html_parts.append(
                f"<p>最活跃表: <strong>{activity['most_active_table']['table']}</strong> "
                f"({activity['most_active_table']['count']} 次更新)</p>"
            )

        if activity.get("table_activity"):
            html_parts.append("<table><tr><th>表名</th><th>更新次数</th><th>成功率</th><th>平均记录</th></tr>")
            for ta in activity["table_activity"][:10]:
                html_parts.append(
                    f"<tr><td>{ta['table']}</td><td>{ta['update_count']}</td>"
                    f"<td>{ta['success_rate']}%</td><td>{ta['avg_records_per_update']}</td></tr>"
                )
            html_parts.append("</table>")

        # 4. 性能趋势
        html_parts.append("<h2>4. 性能趋势分析</h2>")
        overall = perf.get("overall_stats", {})
        html_parts.append(f"""<div class="stats">
  <div class="stat"><div class="num">{overall.get('total_records_processed', 0)}</div><div class="label">总处理记录</div></div>
  <div class="stat"><div class="num">{overall.get('total_success', 0)}</div><div class="label">总成功</div></div>
  <div class="stat"><div class="num">{overall.get('total_fail', 0)}</div><div class="label">总失败</div></div>
  <div class="stat"><div class="num">{overall.get('overall_success_rate', 0)}%</div><div class="label">总体成功率</div></div>
</div>""")

        throughput = perf.get("daily_throughput", [])
        if throughput:
            html_parts.append("<table><tr><th>日期</th><th>处理记录</th><th>成功</th><th>失败</th><th>更新次数</th></tr>")
            for t in throughput[-14:]:
                html_parts.append(
                    f"<tr><td>{t['date']}</td><td>{t['total_records']}</td>"
                    f"<td>{t['success_records']}</td><td>{t['fail_records']}</td>"
                    f"<td>{t['updates']}</td></tr>"
                )
            html_parts.append("</table>")

        html_parts.append("</div></body></html>")
        return "\n".join(html_parts)