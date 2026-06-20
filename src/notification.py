"""通知模块 — P2-9: Webhook / 钉钉 / 企业微信 / 邮件通知

更新完成后自动推送通知，支持多种通知渠道。
"""

import json
import smtplib
import urllib.request
from email.mime.text import MIMEText
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


class NotificationManager:
    """统一通知管理"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        config_path = Path(__file__).parent.parent / "notification.json"
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {"enabled": False, "channels": {}}

    def _save_config(self):
        config_path = Path(__file__).parent.parent / "notification.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def enable_channel(self, channel: str, settings: Dict[str, str]):
        """启用通知渠道"""
        self.config.setdefault("channels", {})[channel] = settings
        self.config["enabled"] = True
        self._save_config()

    def notify(self, title: str, message: str, level: str = "info") -> Dict[str, bool]:
        """发送通知到所有已启用的渠道。

        Returns:
            Dict[channel_name, success]
        """
        if not self.config.get("enabled"):
            return {}

        results = {}
        channels = self.config.get("channels", {})

        for channel, settings in channels.items():
            try:
                if channel == "dingtalk":
                    results[channel] = self._notify_dingtalk(settings, title, message, level)
                elif channel == "wecom":
                    results[channel] = self._notify_wecom(settings, title, message, level)
                elif channel == "webhook":
                    results[channel] = self._notify_webhook(settings, title, message, level)
                elif channel == "email":
                    results[channel] = self._notify_email(settings, title, message, level)
            except Exception as e:
                results[channel] = False
                print(f"通知发送失败 [{channel}]: {e}")

        return results

    def notify_update_result(self, schema: str, table: str, success_count: int,
                             fail_count: int, unmatched_count: int, elapsed_ms: int,
                             backup_table: str = ""):
        """发送更新结果通知"""
        title = "Oracle 批量更新结果"
        level = "success" if fail_count == 0 else "warning"

        message = (
            f"**目标表:** {schema}.{table}\n"
            f"**成功:** {success_count} 条\n"
            f"**失败:** {fail_count} 条\n"
            f"**未匹配:** {unmatched_count} 条\n"
            f"**耗时:** {elapsed_ms / 1000:.1f}s\n"
            f"**备份表:** {backup_table}\n"
            f"**时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        return self.notify(title, message, level)

    # ------------------------------------------------------------------
    # 钉钉机器人通知
    # ------------------------------------------------------------------

    def _notify_dingtalk(self, settings: Dict, title: str, message: str, level: str) -> bool:
        """发送钉钉机器人通知"""
        webhook_url = settings.get("webhook_url", "")
        if not webhook_url:
            return False

        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": (
                    f"## {title}\n\n"
                    f"{message}\n\n"
                    f"> DBForge v{self._get_version()}"
                ),
            },
        }

        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            return result.get("errcode") == 0

    # ------------------------------------------------------------------
    # 企业微信机器人通知
    # ------------------------------------------------------------------

    def _notify_wecom(self, settings: Dict, title: str, message: str, level: str) -> bool:
        """发送企业微信机器人通知"""
        webhook_url = settings.get("webhook_url", "")
        if not webhook_url:
            return False

        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": (
                    f"## {title}\n"
                    f"{message}\n"
                    f"> DBForge"
                ),
            },
        }

        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            return result.get("errcode") == 0

    # ------------------------------------------------------------------
    # 通用 Webhook 通知
    # ------------------------------------------------------------------

    def _notify_webhook(self, settings: Dict, title: str, message: str, level: str) -> bool:
        """发送通用 Webhook 通知（JSON POST）"""
        webhook_url = settings.get("webhook_url", "")
        if not webhook_url:
            return False

        payload = {
            "title": title,
            "message": message,
            "level": level,
            "timestamp": datetime.now().isoformat(),
            "source": "DBForge",
        }

        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200

    # ------------------------------------------------------------------
    # 邮件通知
    # ------------------------------------------------------------------

    def _notify_email(self, settings: Dict, title: str, message: str, level: str) -> bool:
        """发送邮件通知"""
        smtp_host = settings.get("smtp_host", "")
        smtp_port = int(settings.get("smtp_port", "587"))
        username = settings.get("username", "")
        password = settings.get("password", "")
        to_emails = settings.get("to", "").split(",")

        if not smtp_host or not to_emails:
            return False

        msg = MIMEText(message, "plain", "utf-8")
        msg["Subject"] = f"[DBForge] {title}"
        msg["From"] = username
        msg["To"] = ", ".join(to_emails)

        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.starttls()
            if username and password:
                server.login(username, password)
            server.send_message(msg)

        return True

    @staticmethod
    def _get_version() -> str:
        try:
            from src import __version__
            return __version__
        except Exception:
            return "2.8.0"