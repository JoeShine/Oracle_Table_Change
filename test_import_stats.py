"""Tests for the ImportStats module.

Verifies that:
  - Log parsing correctly extracts operation metadata
  - Multi-dimensional statistics aggregate correctly
  - Report generation in text / html / json works
  - Data quality grading is accurate
"""

import json
import os
import re
import tempfile
from pathlib import Path

import pytest


class TestImportStatsParsing:
    """Verify log file parsing."""

    def test_import_class(self):
        from src.import_stats import ImportStats
        stats = ImportStats()
        assert stats.logs_dir is not None
        assert isinstance(stats.logs_dir, Path)

    def test_parse_real_logs(self):
        from src.import_stats import ImportStats
        stats = ImportStats()
        ops = stats._parse_logs()
        # Real logs/ exists, should parse some operations
        assert isinstance(ops, list)

    def test_parse_single_log_structure(self):
        from src.import_stats import ImportStats
        stats = ImportStats()
        # Find a real log file
        log_files = list(stats.logs_dir.glob("update_*.log"))
        if not log_files:
            pytest.skip("No log files available")
        op = stats._parse_single_log(log_files[0])
        if op is None:
            pytest.skip("Could not parse first log")
        # Check required fields
        assert "log_file" in op
        assert "start_time" in op
        assert "date" in op
        assert "hour" in op
        assert "target_table" in op
        assert "success_count" in op
        assert "fail_count" in op
        assert "unmatched_count" in op

    def test_parse_synthetic_log(self):
        from src.import_stats import ImportStats

        with tempfile.TemporaryDirectory() as d:
            # Create a synthetic log file
            log = Path(d) / "update_20260620_120000.log"
            log.write_text(
                "[2026-06-20 12:00:00,000] INFO - 目标表: APPS.EMPLOYEE\n"
                "[2026-06-20 12:00:01,000] INFO - 临时表创建成功: APPS.TEMP_UPDATE_20260620\n"
                "[2026-06-20 12:00:02,000] INFO - 备份完成，共 100 条记录\n"
                "[2026-06-20 12:00:03,000] INFO - 导入完成，共 50 条记录\n"
                "[2026-06-20 12:00:04,000] SUCCESS - 更新完成，成功: 50，失败: 0，未匹配: 0\n"
                "[2026-06-20 12:00:05,000] INFO - 耗时: 5.0s\n"
            )
            stats = ImportStats(logs_dir=d)
            ops = stats._parse_logs()
            assert len(ops) == 1
            op = ops[0]
            assert op["target_table"] == "EMPLOYEE"
            assert op["schema"] == "APPS"
            assert op["success_count"] == 50
            assert op["fail_count"] == 0
            assert op["unmatched_count"] == 0
            assert op["total_imported"] == 50
            assert op["backup_count"] == 100
            assert op["elapsed_seconds"] == 5.0
            assert op["status"] == "success"
            assert op["key_value_count"] == 50


class TestImportStatsAggregation:
    """Verify multi-dimensional aggregation logic."""

    def _make_synthetic_logs(self, d):
        """Create synthetic log files for aggregation tests."""
        log_data = [
            # Log 1: APPS.EMPLOYEE, 100 success, 0 fail
            (
                "update_20260620_120000.log",
                "目标表: APPS.EMPLOYEE\n"
                "临时表创建成功: APPS.T1\n"
                "导入完成，共 100 条记录\n"
                "更新完成，成功: 100，失败: 0，未匹配: 0\n"
                "耗时: 5.0s\n",
            ),
            # Log 2: APPS.EMPLOYEE, 80 success, 5 fail, 15 unmatched
            (
                "update_20260620_130000.log",
                "目标表: APPS.EMPLOYEE\n"
                "临时表创建成功: APPS.T2\n"
                "导入完成，共 100 条记录\n"
                "更新完成，成功: 80，失败: 5，未匹配: 15\n"
                "ORA-01722: 类型不匹配\n"
                "耗时: 3.0s\n",
            ),
            # Log 3: HR.DEPARTMENT, 50 success
            (
                "update_20260620_140000.log",
                "目标表: HR.DEPARTMENT\n"
                "临时表创建成功: HR.T3\n"
                "导入完成，共 50 条记录\n"
                "更新完成，成功: 50，失败: 0，未匹配: 0\n"
                "耗时: 2.0s\n",
            ),
        ]
        for name, content in log_data:
            (Path(d) / name).write_text(
                f"[2026-06-20 12:00:00,000] INFO - {content.splitlines()[0]}\n"
                + "\n".join(
                    f"[2026-06-20 12:00:0{i},000] INFO - {line}"
                    for i, line in enumerate(content.splitlines()[1:], start=2)
                ),
                encoding="utf-8",
            )

    def test_overall_summary(self):
        from src.import_stats import ImportStats

        with tempfile.TemporaryDirectory() as d:
            self._make_synthetic_logs(d)
            stats = ImportStats(logs_dir=d)
            summary = stats.overall_summary(days=30)
            assert summary["total_operations"] == 3
            assert summary["total_success"] == 230
            assert summary["total_fail"] == 5
            assert summary["total_unmatched"] == 15
            assert summary["total_records_processed"] == 250
            # Success rate = 230/250 = 92.0%
            assert summary["success_rate"] == 92.0
            # Average duration = (5+3+2)/3 = 3.33
            assert abs(summary["avg_duration_seconds"] - 3.33) < 0.01

    def test_group_by_schema(self):
        from src.import_stats import ImportStats

        with tempfile.TemporaryDirectory() as d:
            self._make_synthetic_logs(d)
            stats = ImportStats(logs_dir=d)
            by_schema = stats.group_by_schema(days=30)
            assert len(by_schema) == 2  # APPS and HR
            # APPS should be first (more operations)
            assert by_schema[0]["schema"] == "APPS"
            assert by_schema[0]["operations"] == 2
            assert by_schema[0]["success"] == 180
            assert by_schema[0]["fail"] == 5
            assert by_schema[0]["unmatched"] == 15
            # HR
            assert by_schema[1]["schema"] == "HR"
            assert by_schema[1]["operations"] == 1

    def test_group_by_table(self):
        from src.import_stats import ImportStats

        with tempfile.TemporaryDirectory() as d:
            self._make_synthetic_logs(d)
            stats = ImportStats(logs_dir=d)
            tables = stats.group_by_table(days=30)
            assert len(tables) == 2
            # EMPLOYEE has 2 ops
            emp_table = next(t for t in tables if "EMPLOYEE" in t["table"])
            assert emp_table["operations"] == 2
            assert emp_table["total_records"] == 200

    def test_group_by_time_bucket(self):
        from src.import_stats import ImportStats

        with tempfile.TemporaryDirectory() as d:
            self._make_synthetic_logs(d)
            stats = ImportStats(logs_dir=d)
            daily = stats.group_by_time_bucket(days=30, bucket="day")
            assert len(daily) == 1
            assert daily[0]["operations"] == 3
            assert daily[0]["bucket"] == "2026-06-20"

    def test_error_distribution(self):
        from src.import_stats import ImportStats

        with tempfile.TemporaryDirectory() as d:
            self._make_synthetic_logs(d)
            stats = ImportStats(logs_dir=d)
            errors = stats.error_distribution(days=30)
            assert len(errors) >= 1
            # ORA-01722 should be in the list
            codes = [e["ora_code"] for e in errors]
            assert "ORA-01722" in codes

    def test_status_distribution(self):
        from src.import_stats import ImportStats

        with tempfile.TemporaryDirectory() as d:
            self._make_synthetic_logs(d)
            stats = ImportStats(logs_dir=d)
            status = stats.status_distribution(days=30)
            assert status["total"] == 3
            # All operations: 2 success (no fail), 1 partial
            assert "success" in status["distribution"]
            assert "partial" in status["distribution"]

    def test_data_quality_metrics(self):
        from src.import_stats import ImportStats

        with tempfile.TemporaryDirectory() as d:
            self._make_synthetic_logs(d)
            stats = ImportStats(logs_dir=d)
            quality = stats.data_quality_metrics(days=30)
            assert quality["total_records"] == 250
            # Match rate = (success + fail) / total = 235/250 = 94%
            assert quality["match_rate"] == 94.0
            # Unmatched rate = 15/250 = 6%
            assert quality["unmatched_rate"] == 6.0
            # Quality grade: 92% success → C
            assert quality["quality_grade"] in ("C", "D")
            assert "warning" not in quality


class TestImportStatsReport:
    """Verify report generation in different formats."""

    def _make_synthetic_logs(self, d):
        Path(d).mkdir(parents=True, exist_ok=True)
        (Path(d) / "update_20260620_120000.log").write_text(
            "[2026-06-20 12:00:00,000] INFO - 目标表: APPS.EMPLOYEE\n"
            "[2026-06-20 12:00:01,000] INFO - 临时表创建成功: APPS.T1\n"
            "[2026-06-20 12:00:02,000] INFO - 导入完成，共 100 条记录\n"
            "[2026-06-20 12:00:03,000] SUCCESS - 更新完成，成功: 100，失败: 0，未匹配: 0\n"
            "[2026-06-20 12:00:04,000] INFO - 耗时: 5.0s\n",
            encoding="utf-8",
        )

    def test_generate_text_report(self):
        from src.import_stats import ImportStats

        with tempfile.TemporaryDirectory() as d:
            self._make_synthetic_logs(d)
            stats = ImportStats(logs_dir=d)
            report = stats.generate_report(days=30, fmt="text")
            assert "总体汇总" in report
            assert "数据质量评级" in report
            assert "Schema" in report
            assert "EMPLOYEE" in report

    def test_generate_html_report(self):
        from src.import_stats import ImportStats

        with tempfile.TemporaryDirectory() as d:
            self._make_synthetic_logs(d)
            stats = ImportStats(logs_dir=d)
            report = stats.generate_report(days=30, fmt="html")
            assert "<!DOCTYPE html>" in report
            assert "Oracle 批量更新统计报表" in report
            assert "<table>" in report

    def test_generate_json_report(self):
        from src.import_stats import ImportStats

        with tempfile.TemporaryDirectory() as d:
            self._make_synthetic_logs(d)
            stats = ImportStats(logs_dir=d)
            report = stats.generate_report(days=30, fmt="json")
            data = json.loads(report)
            assert "summary" in data
            assert "by_schema" in data
            assert "by_table" in data
            assert "by_day" in data
            assert "errors" in data
            assert "status" in data
            assert "quality" in data

    def test_export_report(self):
        from src.import_stats import ImportStats

        with tempfile.TemporaryDirectory() as d:
            self._make_synthetic_logs(d)
            stats = ImportStats(logs_dir=d)

            # HTML
            html_path = stats.export_report(
                os.path.join(d, "report.html"), days=30, fmt="html"
            )
            assert os.path.exists(html_path)
            assert os.path.getsize(html_path) > 1000

            # JSON
            json_path = stats.export_report(
                os.path.join(d, "report.json"), days=30, fmt="json"
            )
            assert os.path.exists(json_path)
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert "summary" in data


class TestImportStatsFiltering:
    """Verify filtering operations."""

    def test_filter_by_date(self):
        from src.import_stats import ImportStats

        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "update_20260101_120000.log").write_text(
                "[2026-01-01 12:00:00,000] INFO - 目标表: APPS.OLD\n"
                "[2026-01-01 12:00:01,000] INFO - 更新完成，成功: 1，失败: 0，未匹配: 0\n",
                encoding="utf-8",
            )
            (Path(d) / "update_20260620_120000.log").write_text(
                "[2026-06-20 12:00:00,000] INFO - 目标表: APPS.NEW\n"
                "[2026-06-20 12:00:01,000] INFO - 更新完成，成功: 1，失败: 0，未匹配: 0\n",
                encoding="utf-8",
            )

            stats = ImportStats(logs_dir=d)
            recent = stats.get_operations(date_from="2026-06-01")
            assert all(op["target_table"] != "OLD" for op in recent)
            assert any(op["target_table"] == "NEW" for op in recent)

    def test_filter_by_schema(self):
        from src.import_stats import ImportStats

        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "update_20260620_120000.log").write_text(
                "[2026-06-20 12:00:00,000] INFO - 目标表: APPS.T1\n"
                "[2026-06-20 12:00:01,000] INFO - 更新完成，成功: 1，失败: 0，未匹配: 0\n",
                encoding="utf-8",
            )
            (Path(d) / "update_20260620_130000.log").write_text(
                "[2026-06-20 13:00:00,000] INFO - 目标表: HR.T2\n"
                "[2026-06-20 13:00:01,000] INFO - 更新完成，成功: 1，失败: 0，未匹配: 0\n",
                encoding="utf-8",
            )

            stats = ImportStats(logs_dir=d)
            apps = stats.get_operations(schema="APPS")
            assert all(op["schema"] == "APPS" for op in apps)
            assert len(apps) == 1
