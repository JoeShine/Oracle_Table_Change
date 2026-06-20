import logging
import logging.handlers
import os
import json
import hmac
import hashlib
import getpass
import socket
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


# ---------------------------------------------------------------------------
# P0-3: 审计日志防篡改 — HMAC 链式签名 + RotatingFileHandler + 扩展字段
# ---------------------------------------------------------------------------
# 每条审计日志包含:
#   - prev_hash: 上一条日志的 HMAC 签名（链式防篡改）
#   - current_hash: 当前日志的 HMAC 签名
#   - 扩展字段: os_username, hostname, install_fingerprint
# 日志轮转: RotatingFileHandler (10MB × 10 个备份)

def _get_machine_fingerprint() -> str:
    """获取机器指纹作为 HMAC 密钥"""
    return hashlib.sha256(
        f"{uuid.getnode()}:{socket.gethostname()}".encode()
    ).hexdigest()


def _compute_hmac(data: str, key: str) -> str:
    """计算 HMAC-SHA256 签名"""
    return hmac.new(key.encode(), data.encode(), hashlib.sha256).hexdigest()


class AuditLogger:
    """P0-3: 防篡改审计日志记录器"""

    _hmac_key = _get_machine_fingerprint()
    _os_username = getpass.getuser()
    _hostname = socket.gethostname()
    _install_fingerprint = _hmac_key[:16]  # 安装指纹的短标识

    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.audit_file = self.log_dir / "audit.log"
        self._last_hash = self._read_last_hash()

    def _read_last_hash(self) -> str:
        """读取最后一条审计日志的 current_hash，用于链式签名"""
        if not self.audit_file.exists():
            return "GENESIS"
        try:
            with open(self.audit_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    last_entry = json.loads(lines[-1].strip())
                    return last_entry.get("current_hash", "GENESIS")
        except Exception:
            pass
        return "GENESIS"

    def log_action(self, action_type: str, details: Dict[str, Any],
                   user: str = None, success: bool = True, error_msg: str = ""):
        """记录一条审计日志（P0-3: 含 HMAC 链式签名）"""
        user = user or self._os_username
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        entry = {
            "timestamp": timestamp,
            "action_type": action_type,
            "user": user,
            "success": success,
            "error_msg": error_msg,
            "details": details,
            # P0-3: 扩展审计字段
            "os_username": self._os_username,
            "hostname": self._hostname,
            "install_fingerprint": self._install_fingerprint,
            "prev_hash": self._last_hash,
        }

        # 计算当前条目的 HMAC
        payload = json.dumps(entry, ensure_ascii=False, sort_keys=True)
        entry["current_hash"] = _compute_hmac(payload, self._hmac_key)

        try:
            with open(self.audit_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            self._last_hash = entry["current_hash"]
        except Exception as e:
            print(f"写入审计日志失败: {e}")

    def verify_integrity(self) -> Tuple[bool, str]:
        """验证审计日志完整性（从第一条开始校验链式签名）

        Returns:
            Tuple[bool, str]: (是否完整, 错误描述)
        """
        if not self.audit_file.exists():
            return True, "审计日志文件不存在"

        prev_hash = "GENESIS"
        line_no = 0

        try:
            with open(self.audit_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line_no += 1
                    try:
                        entry = json.loads(line.strip())
                    except json.JSONDecodeError:
                        return False, f"第 {line_no} 行: JSON 解析失败"

                    # 保存 current_hash，然后从 entry 中移除
                    # 注意: prev_hash 保留在 entry 中，因为 log_action 计算 HMAC 时包含 prev_hash
                    current_hash = entry.pop("current_hash", None)
                    if not current_hash:
                        return False, f"第 {line_no} 行: 缺少 current_hash 字段"

                    stored_prev = entry.get("prev_hash", "GENESIS")
                    if stored_prev != prev_hash:
                        return False, (
                            f"第 {line_no} 行: prev_hash 不匹配 "
                            f"(期望 {prev_hash[:16]}..., 实际 {stored_prev[:16]}...)"
                        )

                    payload = json.dumps(entry, ensure_ascii=False, sort_keys=True)
                    computed = _compute_hmac(payload, self._hmac_key)
                    if computed != current_hash:
                        return False, f"第 {line_no} 行: HMAC 签名不匹配（日志可能被篡改）"

                    prev_hash = current_hash

            return True, f"验证通过，共 {line_no} 条日志"
        except Exception as e:
            return False, f"验证过程出错: {str(e)}"

    def get_audit_logs(self, limit: int = 100, action_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """读取审计日志（返回时可移除 HMAC 字段以减少输出）"""
        if not self.audit_file.exists():
            return []

        logs = []
        try:
            with open(self.audit_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if action_type is None or entry.get('action_type') == action_type:
                            # 移除 HMAC 内部字段，减少输出噪音
                            entry.pop("prev_hash", None)
                            entry.pop("current_hash", None)
                            logs.append(entry)
                    except json.JSONDecodeError:
                        continue

            logs.reverse()
            return logs[:limit]
        except Exception as e:
            print(f"读取审计日志失败: {e}")
            return []

    def delete_audit_logs(self, before_date: str) -> int:
        """删除指定日期之前的审计日志"""
        if not self.audit_file.exists():
            return 0

        deleted_count = 0
        remaining_logs = []

        try:
            with open(self.audit_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if entry.get('timestamp', '') < before_date:
                            deleted_count += 1
                        else:
                            remaining_logs.append(line)
                    except json.JSONDecodeError:
                        continue

            with open(self.audit_file, 'w', encoding='utf-8') as f:
                f.writelines(remaining_logs)

            # 删除后重新计算 last_hash
            self._last_hash = self._read_last_hash()

            return deleted_count
        except Exception as e:
            print(f"删除审计日志失败: {e}")
            return 0


class HistoryManager:
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.log_dir / "history.json"
        self.history = self._load_history()

    def _load_history(self) -> List[Dict[str, Any]]:
        if not self.history_file.exists():
            return []
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"读取历史记录失败: {e}")
            return []

    def _save_history(self):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史记录失败: {e}")

    def add_record(self, record: Dict[str, Any]):
        record['id'] = datetime.now().strftime("%Y%m%d%H%M%S%f")
        record['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.history.append(record)
        self._save_history()

    def get_records(self, limit: int = 100) -> List[Dict[str, Any]]:
        records = self.history.copy()
        records.reverse()
        return records[:limit]

    def delete_records(self, record_ids: List[str]) -> int:
        original_count = len(self.history)
        self.history = [r for r in self.history if r.get('id') not in record_ids]
        self._save_history()
        return original_count - len(self.history)

    def clear_all(self):
        self.history = []
        self._save_history()


class LogManager:
    # P0-3: 日志轮转配置
    _MAX_LOG_BYTES = 10 * 1024 * 1024  # 10MB
    _BACKUP_COUNT = 10

    def __init__(self):
        self.app_dir = Path(__file__).parent.parent
        self.logs_dir = self.app_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        self.log_file = None
        self.logger = None
        self.failed_records = []
        self.audit_logger = AuditLogger(self.logs_dir)
        self.history_manager = HistoryManager(self.logs_dir)
        self.init_logger()

    def init_logger(self):
        """P0-3: 使用 RotatingFileHandler 自动轮转日志"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.logs_dir / f"update_{timestamp}.log"
        self.logger = logging.getLogger('OracleUpdater')
        self.logger.setLevel(logging.INFO)
        if self.logger.handlers:
            self.logger.handlers.clear()

        # P0-3: RotatingFileHandler — 自动轮转，防止磁盘占满
        fh = logging.handlers.RotatingFileHandler(
            self.log_file,
            maxBytes=self._MAX_LOG_BYTES,
            backupCount=self._BACKUP_COUNT,
            encoding='utf-8'
        )
        fh.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

    def info(self, message):
        self.logger.info(message)

    def success(self, message):
        self.logger.info(f"SUCCESS - {message}")

    def error(self, message):
        self.logger.error(f"ERROR - {message}")

    def warning(self, message):
        self.logger.warning(f"WARNING - {message}")

    def add_failed_record(self, key_value, update_value, reason):
        self.failed_records.append({
            "key_value": key_value,
            "update_value": update_value,
            "reason": reason,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    def get_failed_records(self):
        return self.failed_records

    def clear_failed_records(self):
        self.failed_records = []

    def get_log_file_path(self):
        return str(self.log_file)

    def get_all_logs(self):
        if self.log_file and self.log_file.exists():
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    return f.readlines()
            except Exception:
                return []
        return []

    # ------------------------------------------------------------------
    # P0-3: 审计日志扩展字段
    # ------------------------------------------------------------------

    def log_connection(self, host: str, service: str, username: str, success: bool, error_msg: str = ""):
        self.audit_logger.log_action(
            action_type="CONNECTION",
            details={
                "host": host,
                "service": service,
                "username": username
            },
            success=success,
            error_msg=error_msg
        )

    def log_update(self, schema: str, table: str, key_column: str, update_columns: List[str],
                   total_count: int, success_count: int, fail_count: int, success: bool,
                   backup_table: str = "", error_msg: str = "",
                   sql_summary: str = "", elapsed_ms: int = 0):
        """P0-3: 扩展审计字段"""
        self.audit_logger.log_action(
            action_type="UPDATE",
            details={
                "schema": schema,
                "table": table,
                "key_column": key_column,
                "update_columns": update_columns,
                "total_count": total_count,
                "success_count": success_count,
                "fail_count": fail_count,
                "backup_table": backup_table,
                "sql_summary": sql_summary,
                "elapsed_ms": elapsed_ms,
            },
            success=success,
            error_msg=error_msg
        )

        self.history_manager.add_record({
            "schema": schema,
            "table": table,
            "key_column": key_column,
            "update_columns": update_columns,
            "total_count": total_count,
            "success_count": success_count,
            "fail_count": fail_count,
            "success": success,
            "backup_table": backup_table
        })

    def log_export(self, export_type: str, file_path: str, record_count: int, success: bool, error_msg: str = ""):
        self.audit_logger.log_action(
            action_type="EXPORT",
            details={"export_type": export_type, "file_path": file_path, "record_count": record_count},
            success=success,
            error_msg=error_msg
        )

    def log_rollback(self, schema: str, table: str, backup_table: str, success: bool, error_msg: str = ""):
        self.audit_logger.log_action(
            action_type="ROLLBACK",
            details={"schema": schema, "table": table, "backup_table": backup_table},
            success=success,
            error_msg=error_msg
        )

    def get_audit_logs(self, limit: int = 100, action_type: str = None) -> List[Dict[str, Any]]:
        return self.audit_logger.get_audit_logs(limit, action_type)

    def get_history_records(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self.history_manager.get_records(limit)

    def delete_history_records(self, record_ids: List[str]) -> int:
        return self.history_manager.delete_records(record_ids)

    def clear_history(self):
        self.history_manager.clear_all()

    def verify_audit_integrity(self) -> Tuple[bool, str]:
        """P0-3: 验证审计日志完整性"""
        return self.audit_logger.verify_integrity()