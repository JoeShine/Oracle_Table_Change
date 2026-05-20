import os
import json
from pathlib import Path


class ConfigManager:
    def __init__(self):
        self.app_dir = Path(__file__).parent.parent
        self.config_file = self.app_dir / "config.json"
        self.config = self.load_config()

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
                "schema": "APPS"
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

    def set_last_used(self, connection_name="", target_table="", key_column="", update_column="", schema="APPS"):
        self.config["last_used"] = {
            "connection_name": connection_name,
            "target_table": target_table,
            "key_column": key_column,
            "update_column": update_column,
            "schema": schema
        }
        self.save_config()

    def get_connections(self):
        return self.config.get("connections", [])

    def add_connection(self, conn_info):
        connections = self.get_connections()
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
