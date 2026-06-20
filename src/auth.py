"""操作员身份认证 — P1-4

支持本地多用户账户、角色权限、双人审批模式。
"""

import os
import json
import hashlib
import getpass
import socket
import secrets
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# 角色定义
# ---------------------------------------------------------------------------

class Role:
    OPERATOR = "operator"      # 普通操作员 — 可执行更新
    APPROVER = "approver"      # 审批人 — 可审批高风险操作
    AUDITOR = "auditor"        # 审计员 — 只读，可查看审计日志
    ADMIN = "admin"            # 管理员 — 全部权限

    ALL = [OPERATOR, APPROVER, AUDITOR, ADMIN]

    @classmethod
    def can_execute(cls, role: str) -> bool:
        return role in (cls.OPERATOR, cls.ADMIN)

    @classmethod
    def can_approve(cls, role: str) -> bool:
        return role in (cls.APPROVER, cls.ADMIN)

    @classmethod
    def can_audit(cls, role: str) -> bool:
        return role in (cls.AUDITOR, cls.ADMIN)


# ---------------------------------------------------------------------------
# 高风操作判定
# ---------------------------------------------------------------------------

class RiskLevel:
    """风险等级判定"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    # 生产环境关键词
    PROD_KEYWORDS = ["PROD", "PRODUCTION", "LIVE", "PRD", "生产"]

    @classmethod
    def assess(cls, connection_name: str, target_table: str, row_count: int,
               is_production: bool = False) -> Tuple[str, str]:
        """评估操作风险等级。

        Returns:
            Tuple[risk_level, reason]
        """
        # 检查是否生产环境（生产环境判定优先级最高）
        conn_upper = connection_name.upper()
        if is_production or any(kw in conn_upper for kw in cls.PROD_KEYWORDS):
            if row_count > 1000:
                return (cls.HIGH, "生产环境大批量更新（>1000 行）")
            return (cls.MEDIUM, "生产环境更新")

        # 非生产环境：先判定超大风险（>100000），再判定中风险（>1000）
        if row_count > 100000:
            return (cls.HIGH, "超大批量更新（>100000 行）")

        if row_count > 10000:
            return (cls.MEDIUM, "大批量更新（>10000 行）")

        return (cls.LOW, "常规更新")


# ---------------------------------------------------------------------------
# 用户账户管理
# ---------------------------------------------------------------------------

class AuthManager:
    """本地用户账户管理"""

    _users_file = None

    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            config_dir = Path(__file__).parent.parent
        self.config_dir = config_dir
        self._users_file = self.config_dir / "users.json"
        self._sessions_file = self.config_dir / "sessions.json"
        self._users = self._load_users()
        self._ensure_default_admin()

    def _load_users(self) -> Dict:
        if not self._users_file.exists():
            return {}
        try:
            with open(self._users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_users(self):
        with open(self._users_file, 'w', encoding='utf-8') as f:
            json.dump(self._users, f, ensure_ascii=False, indent=2)
        try:
            os.chmod(self._users_file, 0o600)
        except OSError:
            pass

    def _ensure_default_admin(self):
        """确保至少有一个管理员账户"""
        if not self._users:
            self._users = {
                "admin": {
                    "password_hash": self._hash_password("admin"),
                    "role": Role.ADMIN,
                    "display_name": "系统管理员",
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "enabled": True,
                }
            }
            self._save_users()

    @staticmethod
    def _hash_password(password: str) -> str:
        """SHA-256 哈希密码（含随机 salt）"""
        salt = hashlib.sha256(socket.gethostname().encode()).hexdigest()[:16]
        return hashlib.pbkdf2_hmac(
            'sha256', password.encode('utf-8'), salt.encode(), 100000
        ).hex()

    @staticmethod
    def _verify_password(password: str, password_hash: str) -> bool:
        salt = hashlib.sha256(socket.gethostname().encode()).hexdigest()[:16]
        return hashlib.pbkdf2_hmac(
            'sha256', password.encode('utf-8'), salt.encode(), 100000
        ).hex() == password_hash

    def authenticate(self, username: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """认证用户登录。

        Returns:
            Tuple[success, message, user_info]
        """
        if username not in self._users:
            return (False, "用户不存在", None)

        user = self._users[username]
        if not user.get("enabled", True):
            return (False, "用户已被禁用，请联系管理员", None)

        if not self._verify_password(password, user["password_hash"]):
            return (False, "密码错误", None)

        return (True, "认证成功", {
            "username": username,
            "role": user["role"],
            "display_name": user.get("display_name", username),
        })

    def add_user(self, admin_username: str, username: str, password: str,
                 role: str, display_name: str = "") -> Tuple[bool, str]:
        """添加新用户（需管理员权限）"""
        if admin_username not in self._users or self._users[admin_username]["role"] != Role.ADMIN:
            return (False, "只有管理员才能添加用户")

        if username in self._users:
            return (False, f"用户 '{username}' 已存在")

        if role not in Role.ALL:
            return (False, f"无效角色: {role}")

        self._users[username] = {
            "password_hash": self._hash_password(password),
            "role": role,
            "display_name": display_name or username,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "enabled": True,
        }
        self._save_users()
        return (True, f"用户 '{username}' 创建成功")

    def remove_user(self, admin_username: str, username: str) -> Tuple[bool, str]:
        """删除用户"""
        if admin_username not in self._users or self._users[admin_username]["role"] != Role.ADMIN:
            return (False, "只有管理员才能删除用户")

        if username == "admin":
            return (False, "不能删除默认管理员")

        if username not in self._users:
            return (False, f"用户 '{username}' 不存在")

        del self._users[username]
        self._save_users()
        return (True, f"用户 '{username}' 已删除")

    def list_users(self) -> List[Dict]:
        """列出所有用户（不含密码哈希）"""
        return [
            {
                "username": name,
                "role": info["role"],
                "display_name": info.get("display_name", name),
                "enabled": info.get("enabled", True),
                "created_at": info.get("created_at", ""),
            }
            for name, info in self._users.items()
        ]

    def get_user(self, username: str) -> Optional[Dict]:
        """获取用户信息（不含密码哈希）"""
        if username not in self._users:
            return None
        info = self._users[username]
        return {
            "username": username,
            "role": info["role"],
            "display_name": info.get("display_name", username),
            "enabled": info.get("enabled", True),
        }


# ---------------------------------------------------------------------------
# 审批令牌（双人审批模式）
# ---------------------------------------------------------------------------

class ApprovalManager:
    """审批令牌管理 — 高风险操作需要两个操作员确认"""

    _tokens: Dict[str, Dict] = {}
    _token_timeout = timedelta(minutes=30)

    @classmethod
    def generate_token(cls, requester: str, operation: Dict) -> str:
        """生成审批令牌。

        Args:
            requester: 请求审批的用户名
            operation: 操作描述 dict {table, rows, risk_level, ...}

        Returns:
            审批令牌（6 位数字）
        """
        token = secrets.randbelow(1000000)
        token_str = f"{token:06d}"

        cls._cleanup_expired()

        cls._tokens[token_str] = {
            "requester": requester,
            "operation": operation,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + cls._token_timeout,
            "approved_by": None,
            "status": "pending",
        }

        return token_str

    @classmethod
    def approve(cls, token: str, approver: str) -> Tuple[bool, str]:
        """审批令牌。

        Returns:
            Tuple[success, message]
        """
        cls._cleanup_expired()

        if token not in cls._tokens:
            return (False, "审批令牌无效或已过期")

        token_info = cls._tokens[token]
        if token_info["status"] != "pending":
            return (False, f"审批令牌已处理（状态: {token_info['status']}）")

        if token_info["requester"] == approver:
            return (False, "不能审批自己发起的操作")

        token_info["status"] = "approved"
        token_info["approved_by"] = approver
        return (True, "审批通过")

    @classmethod
    def reject(cls, token: str, rejecter: str, reason: str = "") -> Tuple[bool, str]:
        """拒绝审批令牌"""
        cls._cleanup_expired()

        if token not in cls._tokens:
            return (False, "审批令牌无效或已过期")

        token_info = cls._tokens[token]
        token_info["status"] = "rejected"
        token_info["rejected_by"] = rejecter
        token_info["reject_reason"] = reason
        return (True, "审批已拒绝")

    @classmethod
    def is_approved(cls, token: str) -> bool:
        """检查令牌是否已审批"""
        cls._cleanup_expired()
        if token not in cls._tokens:
            return False
        return cls._tokens[token]["status"] == "approved"

    @classmethod
    def _cleanup_expired(cls):
        """清理过期令牌"""
        now = datetime.now()
        expired = [t for t, info in cls._tokens.items() if info["expires_at"] < now]
        for t in expired:
            del cls._tokens[t]