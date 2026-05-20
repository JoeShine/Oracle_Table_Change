import logging
import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


class AuditLogger:
    def __init__(self, app_dir: Path):
        self.audit_file = app_dir / "logs" / "audit.log"
        self.app_dir = app_dir
        self.app_dir.mkdir(exist_ok=True)
        
    def log_action(self, action_type: str, details: Dict[str, Any], user: str = "system", success: bool = True, error_msg: str = ""):
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action_type": action_type,
            "user": user,
            "success": success,
            "error_msg": error_msg,
            "details": details
        }
        
        try:
            with open(self.audit_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"写入审计日志失败: {e}")
    
    def get_audit_logs(self, limit: int = 100, action_type: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.audit_file.exists():
            return []
        
        logs = []
        try:
            with open(self.audit_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if action_type is None or entry.get('action_type') == action_type:
                            logs.append(entry)
                    except:
                        continue
            
            logs.reverse()
            return logs[:limit]
        except Exception as e:
            print(f"读取审计日志失败: {e}")
            return []
    
    def delete_audit_logs(self, before_date: str) -> int:
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
                    except:
                        continue
            
            with open(self.audit_file, 'w', encoding='utf-8') as f:
                f.writelines(remaining_logs)
            
            return deleted_count
        except Exception as e:
            print(f"删除审计日志失败: {e}")
            return 0


class HistoryManager:
    def __init__(self, app_dir: Path):
        self.history_file = app_dir / "logs" / "history.json"
        self.app_dir = app_dir
        self.app_dir.mkdir(exist_ok=True)
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
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.logs_dir / f"update_{timestamp}.log"
        self.logger = logging.getLogger('OracleUpdater')
        self.logger.setLevel(logging.INFO)
        if self.logger.handlers:
            self.logger.handlers.clear()
        fh = logging.FileHandler(self.log_file, encoding='utf-8')
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
    
    def log_connection(self, host: str, service: str, username: str, success: bool, error_msg: str = ""):
        self.audit_logger.log_action(
            action_type="CONNECTION",
            details={"host": host, "service": service, "username": username},
            success=success,
            error_msg=error_msg
        )
    
    def log_update(self, schema: str, table: str, key_column: str, update_columns: List[str], 
                   total_count: int, success_count: int, fail_count: int, success: bool, 
                   backup_table: str = "", error_msg: str = ""):
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
                "backup_table": backup_table
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
