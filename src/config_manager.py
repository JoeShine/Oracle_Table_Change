import os
import json
import base64
from pathlib import Path


class ConfigManager:
    def __init__(self):
        self.app_dir = Path(__file__).parent.parent
        self.config_file = self.app_dir / "config.json"
        self.config = self.load_config()

    @staticmethod
    def _encode_password(password: str) -> str:
        """Base64 编码密码"""
        return base64.b64encode(password.encode('utf-8')).decode('utf-8')

    @staticmethod
    def _decode_password(encoded: str) -> str:
        """Base64 解码密码，兼容旧版明文存储"""
        try:
            return base64.b64decode(encoded.encode('utf-8')).decode('utf-8')
        except Exception:
            return encoded  # 兼容旧版明文密码

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
            "connections": []
        }

    def save_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置失败: {str(e)}")
            return False

    def get_last_used(self):
        return self.config.get("last_used", {})

    def set_last_used(self, connection_name="", target_table="", key_column="", update_column="", schema="APPS",
                      theme_style="terminal", theme_dark=False):
        self.config["last_used"] = {
            "connection_name": connection_name,
            "target_table": target_table,
            "key_column": key_column,
            "update_column": update_column,
            "schema": schema,
            "theme_style": theme_style,
            "theme_dark": theme_dark
        }
        self.save_config()

    def get_connections(self):
        connections = self.config.get("connections", [])
        # 解码密码后返回
        for conn in connections:
            if "password" in conn:
                conn["password"] = self._decode_password(conn["password"])
        return connections

    def add_connection(self, conn_info):
        connections = self.get_connections()
        # 编码密码后存储
        conn_info = conn_info.copy()
        conn_info["password"] = self._encode_password(conn_info["password"])
        for i, conn in enumerate(connections):
            if conn["name"] == conn_info["name"]:
                connections[i] = conn_info
                break
        else:
            connections.append(conn_info)
        self.config["connections"] = connections
        self.save_config()

    def delete_connection(self, name):
        connections = self.get_connections()
        connections = [c for c in connections if c["name"] != name]
        self.config["connections"] = connections
        self.save_config()

    def get_connection_by_name(self, name):
        for conn in self.get_connections():
            if conn["name"] == name:
                return conn
        return None
