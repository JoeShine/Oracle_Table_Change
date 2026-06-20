"""History query UI for OracleBatchUpdater.

Provides the HistoryViewer class for reading, searching, filtering,
and exporting past update operations from audit and update log files.
"""

import json
import os
import csv
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional


class HistoryViewer:
    """Reads and queries audit log files and update history from the logs/ directory.

    Data sources (in priority order):
      1. ``history.json`` – structured JSON records produced by ``HistoryManager``.
      2. ``audit.log`` – JSONL audit records produced by ``AuditLogger``.
      3. ``update_*.log`` – plain-text update logs (fallback parsing).

    Usage::

        viewer = HistoryViewer(Path("/path/to/logs"))
        records = viewer.list_history(limit=50)
        results = viewer.search_history(table_name="EMPLOYEE", schema="APPS")
        detail = viewer.get_history_detail("20260620_071719")
        viewer.export_history("export.csv", format="csv")

    """

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def __init__(self, logs_dir: Optional[Path] = None):
        """Create a HistoryViewer for the logs directory.

        Args:
            logs_dir: Path to the ``logs/`` directory. Defaults to ``<project>/logs``.
        """
        if logs_dir is None:
            logs_dir = Path(__file__).parent.parent / "logs"
        self.logs_dir = Path(logs_dir)
        self.audit_file = self.logs_dir / "audit.log"
        self.history_file = self.logs_dir / "history.json"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_history(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Return a list of past update operations, newest first.

        Args:
            limit: Maximum number of records to return.
            offset: Number of records to skip from the beginning.

        Returns:
            List of operation records (dicts).
        """
        records = self._read_all_records()

        # Newest first
        records.sort(key=lambda r: r.get("timestamp", ""), reverse=True)

        return records[offset:offset + limit]

    def search_history(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        table_name: Optional[str] = None,
        schema: Optional[str] = None,
        status: Optional[str] = None,
        action_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Search history records with optional filters.

        Args:
            date_from: Start date in "YYYY-MM-DD" format (inclusive).
            date_to: End date in "YYYY-MM-DD" format (inclusive).
            table_name: Filter by target table name (case-insensitive).
            schema: Filter by schema name (case-insensitive).
            status: Filter by status: "success" or "failure".
            action_type: Filter by action type: "UPDATE", "CONNECTION", etc.
            limit: Maximum number of records to return.

        Returns:
            Filtered list of operation records.
        """
        records = self._read_all_records()

        results = []
        for record in records:
            if not self._match_filters(
                record, date_from, date_to, table_name, schema, status, action_type
            ):
                continue
            results.append(record)
            if len(results) >= limit:
                break

        return results

    def get_history_detail(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get full details of a specific operation.

        The operation_id is the log file timestamp suffix (e.g. "20260620_071719"),
        or the history record id (e.g. "20260620071719000000").

        If the operation is found in the audit log or history, all related
        log entries from the corresponding update log file are also included.

        Args:
            operation_id: Identifier for the operation.

        Returns:
            Full operation detail dict, or None if not found.
        """
        # 1. Try history.json first
        history_records = self._read_history_json()
        for rec in history_records:
            if rec.get("id") == operation_id:
                detail = dict(rec)
                detail["source"] = "history.json"
                detail["log_entries"] = self._read_update_log(rec.get("timestamp", ""))
                return detail

        # 2. Try audit.log
        audit_records = self._read_audit_log()
        for rec in audit_records:
            ts = rec.get("timestamp", "")
            if operation_id in ts.replace(":", "").replace(" ", "").replace("-", ""):
                detail = dict(rec)
                detail["source"] = "audit.log"
                detail["log_entries"] = self._read_update_log(ts)
                return detail

        # 3. Try matching by update log file name
        log_files = sorted(self.logs_dir.glob("update_*.log"), reverse=True)
        for log_file in log_files:
            stem = log_file.stem  # e.g. "update_20260620_071719"
            if operation_id in stem:
                entries = self._parse_log_file(log_file)
                return {
                    "operation_id": stem.replace("update_", ""),
                    "source": f"update log: {log_file.name}",
                    "log_entries": entries,
                    "timestamp": self._extract_timestamp_from_log(entries),
                }

        return None

    def export_history(
        self,
        output_path: str,
        format: str = "csv",
        filters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """Export history records to a CSV or JSON file.

        Args:
            output_path: Destination file path.
            format: "csv" or "json".
            filters: Optional dict of filters (same keys as ``search_history``).

        Returns:
            Tuple of (success, message).
        """
        if filters:
            records = self.search_history(**filters)
        else:
            records = self._read_all_records()

        try:
            if format.lower() == "json":
                self._export_json(output_path, records)
            elif format.lower() == "csv":
                self._export_csv(output_path, records)
            else:
                return False, f"Unsupported format: {format}"
            return True, f"Exported {len(records)} records to {output_path}"
        except Exception as e:
            return False, f"Export failed: {str(e)}"

    # ------------------------------------------------------------------
    # Internal: data loading
    # ------------------------------------------------------------------

    def _read_all_records(self) -> List[Dict[str, Any]]:
        """Read all records from all available sources, deduplicated by id."""
        records = []

        # 1. Structured history (highest priority)
        history = self._read_history_json()
        seen_ids = set()
        for rec in history:
            records.append(rec)
            seen_ids.add(rec.get("id", ""))

        # 2. Audit log records
        for rec in self._read_audit_log():
            rec_id = rec.get("timestamp", "").replace(":", "").replace(" ", "").replace("-", "")
            if rec_id not in seen_ids:
                records.append(self._audit_to_history(rec))
                seen_ids.add(rec_id)

        # 3. Parsed update log files
        for rec in self._read_update_logs_summary():
            rec_id = rec.get("id", "")
            if rec_id not in seen_ids:
                records.append(rec)

        return records

    def _read_history_json(self) -> List[Dict[str, Any]]:
        """Read records from history.json."""
        if not self.history_file.exists():
            return []
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def _read_audit_log(self) -> List[Dict[str, Any]]:
        """Read JSONL audit records from audit.log."""
        if not self.audit_file.exists():
            return []
        records = []
        try:
            with open(self.audit_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except IOError:
            pass
        return records

    def _read_update_logs_summary(self) -> List[Dict[str, Any]]:
        """Parse all update_*.log files and return summary records."""
        summaries = []
        log_files = sorted(self.logs_dir.glob("update_*.log"), reverse=True)
        for log_file in log_files:
            stem = log_file.stem  # "update_20260620_071719"
            op_id = stem.replace("update_", "")
            entries = self._parse_log_file(log_file)
            if not entries:
                continue

            summary = self._build_summary_from_entries(op_id, log_file.name, entries)
            if summary:
                summaries.append(summary)
        return summaries

    def _read_update_log(self, timestamp: str) -> List[str]:
        """Find and read the update log file closest to the given timestamp."""
        if not timestamp:
            return []
        # Try to find matching log file
        date_part = timestamp.replace(":", "").replace(" ", "").replace("-", "")[:8]
        log_files = sorted(self.logs_dir.glob(f"update_{date_part}*.log"))
        for log_file in log_files:
            entries = self._parse_log_file(log_file)
            log_ts = self._extract_timestamp_from_log(entries)
            if log_ts and self._timestamps_close(timestamp, log_ts):
                return entries
        return []

    # ------------------------------------------------------------------
    # Internal: parsing helpers
    # ------------------------------------------------------------------

    _LOG_LINE_RE = re.compile(
        r"^\[(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\]\s+"
        r"(?P<level>\w+)\s+-\s+(?P<message>.*)$"
    )

    def _parse_log_file(self, log_file: Path) -> List[str]:
        """Parse a plain-text update log file into a list of log lines."""
        if not log_file.exists():
            return []
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                return [line.rstrip("\n") for line in f if line.strip()]
        except IOError:
            return []

    def _extract_timestamp_from_log(self, entries: List[str]) -> str:
        """Extract the first timestamp from log entries."""
        for entry in entries:
            m = self._LOG_LINE_RE.match(entry)
            if m:
                return m.group("timestamp")
        return ""

    def _build_summary_from_entries(
        self, op_id: str, filename: str, entries: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Build a summary record from parsed log entries."""
        timestamp = self._extract_timestamp_from_log(entries)
        if not timestamp:
            return None

        # Try to extract operation info
        schema = ""
        table = ""
        key_column = ""
        success_count = 0
        fail_count = 0
        total_count = 0
        backup_table = ""
        success = False
        action_type = "UNKNOWN"

        for entry in entries:
            m = self._LOG_LINE_RE.match(entry)
            if not m:
                continue
            msg = m.group("message")

            # Detect action type
            if "正在备份" in msg or "备份" in msg:
                action_type = "UPDATE"
            if "正在创建临时表" in msg:
                action_type = "UPDATE"
            if "正在执行" in msg and "更新" in msg:
                action_type = "UPDATE"

            # Extract schema/table from "目标表: SCHEMA.TABLE"
            target_match = re.search(r"目标表:\s*(\w+)\.(\w+)", msg)
            if target_match:
                schema = target_match.group(1)
                table = target_match.group(2)

            # Extract backup table name
            backup_match = re.search(r"备份表\s*(\w+)\.(\w+)", msg)
            if backup_match:
                backup_table = f"{backup_match.group(1)}.{backup_match.group(2)}"

            # Extract counts: "成功: N，失败: M"
            counts_match = re.search(
                r"成功:\s*(\d+).*?失败:\s*(\d+)", msg
            )
            if counts_match:
                success_count = int(counts_match.group(1))
                fail_count = int(counts_match.group(2))
                total_count = success_count + fail_count

            # Extract key column from "临时表中共有 N 个key_value"
            key_match = re.search(r"临时表中共有\s+\d+\s+个(\w+)", msg)
            if key_match:
                key_column = key_match.group(1)

            # Determine success
            if "SUCCESS" in m.group("level") or "更新完成" in msg:
                success = True

        return {
            "id": op_id,
            "timestamp": timestamp,
            "action_type": action_type,
            "schema": schema,
            "table": table,
            "key_column": key_column,
            "total_count": total_count,
            "success_count": success_count,
            "fail_count": fail_count,
            "success": success,
            "backup_table": backup_table,
            "source": f"update log: {filename}",
            "log_file": filename,
        }

    @staticmethod
    def _timestamps_close(ts1: str, ts2: str, threshold_seconds: int = 10) -> bool:
        """Check if two timestamps are within the given threshold."""
        try:
            # Normalise: "2026-06-20 07:17:19,095" -> datetime
            for fmt in ("%Y-%m-%d %H:%M:%S,%f", "%Y-%m-%d %H:%M:%S"):
                try:
                    dt1 = datetime.strptime(ts1[: len(fmt.replace("%f", "000"))], fmt)
                    dt2 = datetime.strptime(ts2[: len(fmt.replace("%f", "000"))], fmt)
                    return abs((dt1 - dt2).total_seconds()) <= threshold_seconds
                except ValueError:
                    continue
            return False
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Internal: filtering
    # ------------------------------------------------------------------

    def _match_filters(
        self,
        record: Dict[str, Any],
        date_from: Optional[str],
        date_to: Optional[str],
        table_name: Optional[str],
        schema: Optional[str],
        status: Optional[str],
        action_type: Optional[str],
    ) -> bool:
        """Check whether a record matches all given filters."""
        ts = record.get("timestamp", "")

        # Date range
        if date_from or date_to:
            try:
                record_date_str = ts[:10]  # "YYYY-MM-DD"
                record_date = datetime.strptime(record_date_str, "%Y-%m-%d").date()
                if date_from:
                    from_date = datetime.strptime(date_from, "%Y-%m-%d").date()
                    if record_date < from_date:
                        return False
                if date_to:
                    to_date = datetime.strptime(date_to, "%Y-%m-%d").date()
                    if record_date > to_date:
                        return False
            except (ValueError, IndexError):
                pass

        # Table name (case-insensitive)
        if table_name:
            rec_table = record.get("table", "").lower()
            if table_name.lower() not in rec_table:
                return False

        # Schema (case-insensitive)
        if schema:
            rec_schema = record.get("schema", "").lower()
            if schema.lower() not in rec_schema:
                return False

        # Status
        if status:
            if status.lower() == "success" and not record.get("success", False):
                return False
            if status.lower() == "failure" and record.get("success", False):
                return False

        # Action type
        if action_type:
            rec_type = record.get("action_type", "").upper()
            if action_type.upper() != rec_type:
                return False

        return True

    # ------------------------------------------------------------------
    # Internal: audit-to-history conversion
    # ------------------------------------------------------------------

    def _audit_to_history(self, audit_record: Dict[str, Any]) -> Dict[str, Any]:
        """Convert an audit log record to a history-like record."""
        details = audit_record.get("details", {})
        return {
            "id": audit_record.get("timestamp", "").replace(":", "").replace(" ", "").replace("-", ""),
            "timestamp": audit_record.get("timestamp", ""),
            "action_type": audit_record.get("action_type", ""),
            "schema": details.get("schema", ""),
            "table": details.get("table", ""),
            "key_column": details.get("key_column", ""),
            "update_columns": details.get("update_columns", []),
            "total_count": details.get("total_count", 0),
            "success_count": details.get("success_count", 0),
            "fail_count": details.get("fail_count", 0),
            "success": audit_record.get("success", False),
            "backup_table": details.get("backup_table", ""),
            "source": "audit.log",
        }

    # ------------------------------------------------------------------
    # Internal: export
    # ------------------------------------------------------------------

    _CSV_FIELDS = [
        "id", "timestamp", "action_type", "schema", "table",
        "key_column", "total_count", "success_count", "fail_count",
        "success", "backup_table", "source",
    ]

    def _export_csv(self, output_path: str, records: List[Dict[str, Any]]):
        """Export records to a CSV file."""
        with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=self._CSV_FIELDS, extrasaction="ignore")
            writer.writeheader()
            for record in records:
                # Flatten update_columns for CSV
                row = dict(record)
                if "update_columns" in row and isinstance(row["update_columns"], list):
                    row["update_columns"] = "|".join(row["update_columns"])
                writer.writerow(row)

    def _export_json(self, output_path: str, records: List[Dict[str, Any]]):
        """Export records to a JSON file."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2, default=str)