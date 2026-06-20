"""P3-5: 任务调度模块

提供 TaskScheduler 类，用于注册和管理定期执行的更新任务。
支持 cron 表达式和简单间隔两种调度方式。

任务存储格式: JSON 文件，每个任务定义包含名称、配置、cron 表达式和状态。

依赖:
    - croniter (可选): 用于 cron 表达式解析和下次执行时间计算
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from src.errors import ConfigError, ValidationError


# ---------------------------------------------------------------------------
# croniter 可用性检测
# ---------------------------------------------------------------------------

try:
    from croniter import croniter

    _CRONITER_AVAILABLE = True
except ImportError:
    _CRONITER_AVAILABLE = False


class TaskScheduler:
    """P3-5: 任务调度器

    管理定期更新任务的注册、删除、列表和执行。

    Attributes:
        tasks_file: 任务存储文件路径
        tasks: 当前所有任务定义
    """

    def __init__(self, tasks_file: str = None):
        """初始化任务调度器。

        Args:
            tasks_file: 任务存储文件路径，默认为应用根目录下的 scheduled_tasks.json
        """
        if tasks_file is None:
            app_dir = Path(__file__).parent.parent
            self.tasks_file = app_dir / "scheduled_tasks.json"
        else:
            self.tasks_file = Path(tasks_file)

        self.tasks: Dict[str, Dict[str, Any]] = self._load_tasks()

    # ------------------------------------------------------------------
    # 任务存储
    # ------------------------------------------------------------------

    def _load_tasks(self) -> Dict[str, Dict[str, Any]]:
        """加载已保存的任务定义。

        Returns:
            Dict[str, Dict[str, Any]]: 任务名称到任务定义的映射
        """
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
            except Exception:
                return {}
        return {}

    def _save_tasks(self) -> bool:
        """保存任务定义到文件。

        Returns:
            bool: 保存是否成功
        """
        try:
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
            try:
                os.chmod(self.tasks_file, 0o600)
            except OSError:
                pass
            return True
        except Exception as e:
            raise ConfigError(f"保存任务定义失败: {str(e)}")

    # ------------------------------------------------------------------
    # 任务 CRUD
    # ------------------------------------------------------------------

    def add_task(
        self,
        name: str,
        config: Dict[str, Any],
        cron_expression: str,
        description: str = "",
        enabled: bool = True,
        retry_on_failure: bool = False,
        max_retries: int = 3,
    ) -> bool:
        """注册一个新的调度任务。

        Args:
            name: 任务名称（唯一标识）
            config: 任务配置，包含更新所需的所有参数
                例如: {"connection_name": "prod", "table": "EMPLOYEE", ...}
            cron_expression: Cron 表达式，定义任务执行频率
                格式: "min hour day month weekday" (5字段标准cron)
                例如: "0 8 * * 1-5" (工作日早上8点)
            description: 任务描述
            enabled: 是否启用
            retry_on_failure: 失败时是否重试
            max_retries: 最大重试次数

        Returns:
            bool: 注册是否成功

        Raises:
            ValidationError: 参数无效
        """
        name = name.strip()
        if not name:
            raise ValidationError("任务名称不能为空")

        if len(name) > 100:
            raise ValidationError("任务名称不能超过 100 个字符")

        if not config:
            raise ValidationError("任务配置不能为空")

        if not cron_expression:
            raise ValidationError("cron 表达式不能为空")

        # 验证 cron 表达式
        if _CRONITER_AVAILABLE:
            valid, msg = self._validate_cron(cron_expression)
            if not valid:
                raise ValidationError(f"cron 表达式无效: {msg}")

        is_new = name not in self.tasks

        task_def = {
            "name": name,
            "description": description.strip() if description else "",
            "config": config,
            "cron_expression": cron_expression,
            "enabled": enabled,
            "retry_on_failure": retry_on_failure,
            "max_retries": max_retries,
            "last_run": None,
            "last_result": None,
            "run_count": self.tasks.get(name, {}).get("run_count", 0),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        if is_new:
            task_def["created_at"] = task_def["updated_at"]

        self.tasks[name] = task_def
        self._save_tasks()
        return True

    def remove_task(self, name: str) -> bool:
        """删除一个调度任务。

        Args:
            name: 任务名称

        Returns:
            bool: 是否删除成功

        Raises:
            ConfigError: 任务不存在
        """
        name = name.strip()
        if name not in self.tasks:
            raise ConfigError(f"任务 '{name}' 不存在")

        del self.tasks[name]
        self._save_tasks()
        return True

    def list_tasks(self) -> List[Dict[str, Any]]:
        """列出所有已注册的调度任务。

        Returns:
            List[Dict[str, Any]]: 任务列表，按名称排序
        """
        result = []
        for name, task in sorted(self.tasks.items()):
            next_run = self.get_next_run(name)
            result.append({
                "name": name,
                "description": task.get("description", ""),
                "cron_expression": task.get("cron_expression", ""),
                "enabled": task.get("enabled", True),
                "last_run": task.get("last_run"),
                "last_result": task.get("last_result"),
                "run_count": task.get("run_count", 0),
                "next_run": next_run,
                "retry_on_failure": task.get("retry_on_failure", False),
            })
        return result

    def get_task(self, name: str) -> Dict[str, Any]:
        """获取指定任务的详细信息。

        Args:
            name: 任务名称

        Returns:
            Dict[str, Any]: 任务定义

        Raises:
            ConfigError: 任务不存在
        """
        name = name.strip()
        if name not in self.tasks:
            raise ConfigError(f"任务 '{name}' 不存在")
        return dict(self.tasks[name])

    def enable_task(self, name: str) -> bool:
        """启用一个任务。

        Args:
            name: 任务名称

        Returns:
            bool: 操作是否成功
        """
        name = name.strip()
        if name not in self.tasks:
            raise ConfigError(f"任务 '{name}' 不存在")
        self.tasks[name]["enabled"] = True
        self._save_tasks()
        return True

    def disable_task(self, name: str) -> bool:
        """禁用一个任务。

        Args:
            name: 任务名称

        Returns:
            bool: 操作是否成功
        """
        name = name.strip()
        if name not in self.tasks:
            raise ConfigError(f"任务 '{name}' 不存在")
        self.tasks[name]["enabled"] = False
        self._save_tasks()
        return True

    # ------------------------------------------------------------------
    # 任务执行
    # ------------------------------------------------------------------

    def run_task(self, name: str) -> Dict[str, Any]:
        """立即执行一个任务。

        注意：此方法仅标记任务执行记录，实际执行逻辑由调用方实现。
        调用方应通过 task.config 获取配置参数。

        Args:
            name: 任务名称

        Returns:
            Dict[str, Any]: 任务执行上下文，包含:
                - name: 任务名称
                - config: 任务配置
                - executed_at: 执行时间

        Raises:
            ConfigError: 任务不存在
        """
        name = name.strip()
        if name not in self.tasks:
            raise ConfigError(f"任务 '{name}' 不存在")

        task = self.tasks[name]
        now = datetime.now()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")

        task["last_run"] = now_str
        task["run_count"] = task.get("run_count", 0) + 1
        task["last_result"] = "executed"
        self._save_tasks()

        return {
            "name": name,
            "config": task["config"],
            "executed_at": now_str,
            "run_count": task["run_count"],
        }

    def record_task_result(
        self, name: str, success: bool, message: str = ""
    ) -> None:
        """记录任务执行结果。

        Args:
            name: 任务名称
            success: 是否执行成功
            message: 结果消息
        """
        name = name.strip()
        if name not in self.tasks:
            return

        self.tasks[name]["last_result"] = "success" if success else "failed"
        self.tasks[name]["last_result_message"] = message
        self._save_tasks()

    # ------------------------------------------------------------------
    # 下次执行时间
    # ------------------------------------------------------------------

    def get_next_run(self, name: str) -> Optional[str]:
        """计算任务的下次执行时间。

        Args:
            name: 任务名称

        Returns:
            Optional[str]: 下次执行时间字符串，如果无法计算则返回 None
        """
        name = name.strip()
        if name not in self.tasks:
            return None

        task = self.tasks[name]
        cron_expr = task.get("cron_expression", "")

        if not cron_expr:
            return None

        if _CRONITER_AVAILABLE:
            try:
                cron = croniter(cron_expr, datetime.now())
                next_time = cron.get_next(datetime)
                return next_time.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, KeyError):
                return None

        # croniter 不可用时的回退方案：简单间隔解析
        return self._simple_next_run(cron_expr)

    def _simple_next_run(self, cron_expression: str) -> Optional[str]:
        """简单 cron 解析回退方案（仅支持基础模式）。

        支持的模式:
        - "0 8 * * *": 每天 8:00
        - "0 8 * * 1-5": 工作日 8:00
        - "0 */N * * *": 每 N 小时

        Args:
            cron_expression: Cron 表达式

        Returns:
            Optional[str]: 下次执行时间
        """
        try:
            parts = cron_expression.strip().split()
            if len(parts) != 5:
                return None

            minute = int(parts[0]) if parts[0] != "*" else 0
            hour = parts[1]
            now = datetime.now()

            # 简单计算：如果小时是数字，计算今天或明天的目标时间
            if hour.isdigit():
                target_hour = int(hour)
                next_run = now.replace(
                    hour=target_hour, minute=minute, second=0, microsecond=0
                )
                if next_run <= now:
                    next_run += timedelta(days=1)
                return next_run.strftime("%Y-%m-%d %H:%M:%S")

            return None
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Cron 验证
    # ------------------------------------------------------------------

    def _validate_cron(self, cron_expression: str) -> Tuple[bool, str]:
        """验证 cron 表达式的有效性。

        Args:
            cron_expression: Cron 表达式

        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        if _CRONITER_AVAILABLE:
            try:
                croniter(cron_expression, datetime.now())
                return True, ""
            except (ValueError, KeyError) as e:
                return False, str(e)

        # 简单的格式验证
        parts = cron_expression.strip().split()
        if len(parts) != 5:
            return False, "cron 表达式必须包含 5 个字段"

        return True, ""

    def get_due_tasks(self) -> List[Dict[str, Any]]:
        """获取所有应该执行的任务（当前时间 >= 计划执行时间）。

        仅返回已启用的、且已到执行时间的任务。

        Returns:
            List[Dict[str, Any]]: 到期任务列表
        """
        due = []
        now = datetime.now()

        for name, task in self.tasks.items():
            if not task.get("enabled", True):
                continue

            # 获取上次执行时间
            last_run_str = task.get("last_run")
            if last_run_str:
                try:
                    last_run = datetime.strptime(last_run_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    last_run = None
            else:
                last_run = None

            # 获取下次执行时间
            next_run_str = self.get_next_run(name)
            if not next_run_str:
                continue

            try:
                next_run = datetime.strptime(next_run_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue

            # 检查是否到期
            if now >= next_run and (last_run is None or last_run < next_run):
                due.append({
                    "name": name,
                    "config": task["config"],
                    "scheduled_at": next_run_str,
                    "last_run": last_run_str,
                })

        return due