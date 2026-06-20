import os
import json
import base64
import hashlib
import uuid
import socket
from pathlib import Path
from datetime import datetime

from cryptography.fernet import Fernet, InvalidToken


# ---------------------------------------------------------------------------
# P0-2: 密码加密 — 使用 Fernet (AES-128-CBC + HMAC-SHA256) 替代 Base64
# ---------------------------------------------------------------------------
# 密钥派生: 使用机器指纹 (uuid + hostname) 作为 salt，派生派生密钥
# 配置文件格式: "password": "enc:{base64(fernet_token)}"
# 前缀 "enc:" 用于区分新旧版本，兼容旧版 Base64 编码

def _derive_fernet_key() -> bytes:
    """从机器指纹派生 Fernet 密钥。

    使用 uuid.getnode() + hostname 的 sha256 作为密钥材料，
    确保同一台机器上的配置可被同一程序解密。
    """
    fingerprint = f"{uuid.getnode()}:{socket.gethostname()}"
    digest = hashlib.sha256(fingerprint.encode()).digest()
    return base64.urlsafe_b64encode(digest)


_fernet = Fernet(_derive_fernet_key())


def password_encrypt(password: str) -> str:
    """使用 Fernet 加密密码。

    Args:
        password: 明文密码

    Returns:
        "enc:{base64加密后的token}" 格式的字符串
    """
    token = _fernet.encrypt(password.encode('utf-8'))
    return "enc:" + base64.b64encode(token).decode('utf-8')


def password_decrypt(encoded: str) -> str:
    """解密密码，兼容旧版 Base64 和明文存储。

    支持三种格式:
    - "enc:..."  → Fernet 加密（新格式）
    - 其他字符串 → Base64 解码（旧格式，向后兼容）
    - 异常时     → 返回原文（兼容极旧版明文）

    Args:
        encoded: 加密后的密码字符串

    Returns:
        明文密码
    """
    if not encoded:
        return ""

    # 新格式: Fernet 加密
    if encoded.startswith("enc:"):
        try:
            token = base64.b64decode(encoded[4:].encode('utf-8'))
            return _fernet.decrypt(token).decode('utf-8')
        except InvalidToken:
            # 密钥不匹配（可能是其他机器或密钥已变），尝试回退
            raise ValueError(
                "密码解密失败: 密钥不匹配。请重新输入密码。"
                "可能是配置文件来自其他机器，或系统标识已变更。"
            )
        except Exception:
            raise ValueError("密码解密失败: 加密数据损坏")

    # 旧格式: Base64 编码（向后兼容）
    try:
        return base64.b64decode(encoded.encode('utf-8')).decode('utf-8')
    except Exception:
        # 极旧版: 明文存储
        return encoded


class ConfigManager:
    def __init__(self):
        self.app_dir = Path(__file__).parent.parent
        self.config_file = self.app_dir / "config.json"
        self.config = self.load_config()

    # ------------------------------------------------------------------
    # 向后兼容的快捷方法（内部调用新的 password_encrypt/decrypt）
    # ------------------------------------------------------------------

    @staticmethod
    def _encode_password(password: str) -> str:
        """P0-2: 使用 Fernet 加密（替代 Base64）"""
        return password_encrypt(password)

    @staticmethod
    def _decode_password(encoded: str) -> str:
        """P0-2: 使用 Fernet 解密（兼容旧版 Base64）"""
        return password_decrypt(encoded)

    def load_config(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return self.get_default_config()
        return self.get_default_config()

    def get_default_config(self):
        return {
            "last_used": {
                "connection_name": "",
                "target_table": "",
                "key_column": "",
                "update_column": "",
                "schema": "APPS",
                "theme_style": "terminal",
                "theme_dark": False
            },
            "connections": [],
            "templates": [],
            "schema_values": ["APPS", "SYS", "SYSTEM"]
        }

    def save_config(self):
        """保存配置，并设置文件权限（P0-2: 仅当前用户可读写）"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            # P0-2: 限制文件权限为 600（仅所有者可读写）
            try:
                os.chmod(self.config_file, 0o600)
            except OSError:
                pass  # Windows 不支持 chmod，忽略
            return True
        except Exception as e:
            print(f"保存配置失败: {str(e)}")
            return False

    def get_last_used(self):
        return self.config.get("last_used", {})

    def set_last_used(self, connection_name="", target_table="", key_column="", update_column="", schema="APPS",
                      temp_schema="APPS", theme_style="terminal", theme_dark=False):
        self.config["last_used"] = {
            "connection_name": connection_name,
            "target_table": target_table,
            "key_column": key_column,
            "update_column": update_column,
            "schema": schema,
            "temp_schema": temp_schema,
            "theme_style": theme_style,
            "theme_dark": theme_dark
        }
        self.save_config()

    def get_connections(self):
        """获取所有数据库连接配置"""
        import copy
        connections = copy.deepcopy(self.config.get("connections", []))
        for conn in connections:
            if "password" in conn:
                conn["password"] = self._decode_password(conn["password"])
        return connections

    def add_connection(self, conn_info):
        """添加或更新连接配置，密码使用 Fernet 加密"""
        conn_info = conn_info.copy()
        conn_info["password"] = self._encode_password(conn_info["password"])

        connections = self.config.get("connections", [])
        for i, conn in enumerate(connections):
            if conn["name"] == conn_info["name"]:
                connections[i] = conn_info
                break
        else:
            connections.append(conn_info)
        self.save_config()

    def _migrate_passwords(self):
        """将旧版 Base64 密码迁移为 Fernet 加密格式。

        迁移策略：
        - 扫描所有连接的密码
        - 检测是否为 "enc:" 前缀（已是新格式则跳过）
        - 对旧格式密码先解密（Base64）再加密（Fernet），然后保存
        """
        connections = self.config.get("connections", [])
        migrated = False
        for conn in connections:
            if "password" in conn:
                pwd = conn["password"]
                if not pwd.startswith("enc:"):
                    try:
                        plain = self._decode_password(pwd)
                        conn["password"] = password_encrypt(plain)
                        migrated = True
                    except Exception:
                        pass  # 解密失败，保持原样
        if migrated:
            self.save_config()

    def delete_connection(self, name):
        """删除连接配置"""
        connections = self.config.get("connections", [])
        connections = [c for c in connections if c["name"] != name]
        self.config["connections"] = connections
        self.save_config()

    def get_connection_by_name(self, name):
        for conn in self.get_connections():
            if conn["name"] == name:
                return conn
        return None

    # ==================== 场景管理功能 ====================

    def get_templates(self):
        return self.config.get("templates", [])

    def get_template_by_name(self, name):
        for template in self.get_templates():
            if template["name"] == name:
                return template
        return None

    def add_template(self, template_info):
        name = template_info.get("name", "")
        if not name or not name.strip():
            return False, "场景名称不能为空"
        name = name.strip()
        if len(name) > 100:
            return False, "场景名称不能超过100个字符"

        template_info["name"] = name

        templates = self.config.get("templates", [])
        for i, template in enumerate(templates):
            if template["name"] == name:
                templates[i] = template_info
                self.config["templates"] = templates
                self.save_config()
                return True, "场景已更新"
        templates.append(template_info)
        self.config["templates"] = templates
        self.save_config()
        return True, "场景已添加"

    def delete_template(self, name):
        templates = self.config.get("templates", [])
        templates = [t for t in templates if t["name"] != name]
        self.config["templates"] = templates
        self.save_config()
        return True

    def create_template_from_current(self, name, description="", connection_name="", target_table="",
                                      key_column="", update_columns=None, schema="APPS", temp_schema="APPS"):
        if not name or not name.strip():
            return False, "场景名称不能为空"
        name = name.strip()
        if len(name) > 100:
            return False, "场景名称不能超过100个字符"

        template = {
            "name": name,
            "description": description,
            "connection_name": connection_name,
            "target_table": target_table,
            "key_column": key_column,
            "update_columns": update_columns or [],
            "schema": schema,
            "temp_schema": temp_schema,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return self.add_template(template)

    def get_schema_values(self):
        return self.config.get("schema_values", ["APPS", "SYS", "SYSTEM"])

    def set_schema_values(self, values):
        self.config["schema_values"] = list(values)
        self.save_config()
        return True