"""P3-3: 多环境配置管理模块

提供 EnvironmentConfig 类，用于管理 DEV/TEST/UAT/PROD 等多个环境的配置，
支持环境切换、验证和持久化。

配置格式: environments.json
{
    "active_environment": "DEV",
    "environments": {
        "DEV": {
            "description": "开发环境",
            "connection": {
                "host": "dev-db.example.com",
                "port": 1521,
                "service": "ORCLDEV",
                "username": "app_dev",
                "password": "enc:..."
            },
            "settings": {
                "schema": "APPS_DEV",
                "backup_enabled": true,
                "batch_size": 100
            }
        }
    }
}
"""

import json
import os
import copy
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from src.errors import ConfigError, ValidationError


class EnvironmentConfig:
    """P3-3: 多环境配置管理器

    管理多个环境（DEV/TEST/UAT/PROD）的连接管理和设置，
    支持环境切换、验证和持久化。

    Attributes:
        config_file: 环境配置文件路径
        config: 当前配置数据
        active_environment: 当前激活的环境名称
    """

    # 预定义的标准环境名称
    _STANDARD_ENVS = ["DEV", "TEST", "UAT", "PROD", "STAGING", "QA", "DR"]

    def __init__(self, config_file: str = None):
        """初始化多环境配置管理器。

        Args:
            config_file: 环境配置文件路径，默认为应用根目录下的 environments.json
        """
        if config_file is None:
            app_dir = Path(__file__).parent.parent
            self.config_file = app_dir / "environments.json"
        else:
            self.config_file = Path(config_file)

        self.config = self._load_config()
        self.active_environment = self.config.get("active_environment", "")

    # ------------------------------------------------------------------
    # 配置加载与保存
    # ------------------------------------------------------------------

    def _load_config(self) -> Dict[str, Any]:
        """加载环境配置文件。

        Returns:
            Dict[str, Any]: 配置数据，如果文件不存在则返回默认结构
        """
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data
            except json.JSONDecodeError as e:
                raise ConfigError(f"环境配置文件格式错误: {str(e)}")
            except Exception as e:
                raise ConfigError(f"读取环境配置文件失败: {str(e)}")

        return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置结构。

        Returns:
            Dict[str, Any]: 默认配置字典
        """
        return {
            "active_environment": "",
            "environments": {},
        }

    def _save_config(self) -> bool:
        """保存环境配置到文件。

        Returns:
            bool: 保存是否成功
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            try:
                os.chmod(self.config_file, 0o600)
            except OSError:
                pass
            return True
        except Exception as e:
            raise ConfigError(f"保存环境配置文件失败: {str(e)}")

    # ------------------------------------------------------------------
    # 环境加载与切换
    # ------------------------------------------------------------------

    def load_environment(self, env_name: str) -> Dict[str, Any]:
        """加载指定环境的配置。

        Args:
            env_name: 环境名称（如 DEV、TEST、UAT、PROD）

        Returns:
            Dict[str, Any]: 环境配置字典，包含 connection 和 settings

        Raises:
            ConfigError: 环境不存在
        """
        env_name = env_name.upper().strip()
        envs = self.config.get("environments", {})

        if env_name not in envs:
            raise ConfigError(
                f"环境 '{env_name}' 不存在。"
                f"可用环境: {', '.join(sorted(envs.keys())) if envs else '无'}"
            )

        return copy.deepcopy(envs[env_name])

    def switch_environment(self, env_name: str) -> Dict[str, Any]:
        """切换当前激活的环境。

        首先验证环境配置是否有效，然后切换激活环境并保存。

        Args:
            env_name: 目标环境名称

        Returns:
            Dict[str, Any]: 切换后的环境配置

        Raises:
            ConfigError: 环境不存在或配置无效
        """
        env_name = env_name.upper().strip()

        # 验证环境是否存在
        env_config = self.load_environment(env_name)

        # 验证环境配置
        valid, msg = self.validate_environment(env_name)
        if not valid:
            raise ConfigError(f"环境 '{env_name}' 配置无效: {msg}")

        # 切换环境
        self.active_environment = env_name
        self.config["active_environment"] = env_name
        self._save_config()

        return env_config

    def get_current_environment(self) -> Dict[str, Any]:
        """获取当前激活环境的信息。

        Returns:
            Dict[str, Any]: 包含环境名称和配置的字典，如果未激活则返回空信息
        """
        if not self.active_environment:
            return {
                "active": False,
                "name": "",
                "config": None,
                "message": "未设置激活环境",
            }

        try:
            env_config = self.load_environment(self.active_environment)
            return {
                "active": True,
                "name": self.active_environment,
                "config": env_config,
                "message": f"当前环境: {self.active_environment}",
            }
        except ConfigError:
            return {
                "active": False,
                "name": self.active_environment,
                "config": None,
                "message": f"当前环境 '{self.active_environment}' 配置已丢失",
            }

    def list_environments(self) -> List[Dict[str, Any]]:
        """列出所有已配置的环境。

        Returns:
            List[Dict[str, Any]]: 环境列表，每个元素包含 name, description, is_active, connection_summary
        """
        envs = self.config.get("environments", {})
        result = []

        for env_name, env_config in sorted(envs.items()):
            conn = env_config.get("connection", {})
            conn_summary = (
                f"{conn.get('username', '?')}@"
                f"{conn.get('host', '?')}:"
                f"{conn.get('port', '?')}/"
                f"{conn.get('service', '?')}"
            )

            result.append({
                "name": env_name,
                "description": env_config.get("description", ""),
                "is_active": env_name == self.active_environment,
                "connection_summary": conn_summary,
                "schema": env_config.get("settings", {}).get("schema", ""),
            })

        return result

    # ------------------------------------------------------------------
    # 环境验证
    # ------------------------------------------------------------------

    def validate_environment(self, env_name: str) -> Tuple[bool, str]:
        """验证环境配置的完整性和有效性。

        检查项:
        - 必需字段: host, port, service, username
        - 端口号: 必须是1-65535之间的整数
        - 非空检查

        Args:
            env_name: 环境名称

        Returns:
            Tuple[bool, str]: (是否有效, 验证消息)
        """
        env_name = env_name.upper().strip()

        envs = self.config.get("environments", {})
        if env_name not in envs:
            return False, f"环境 '{env_name}' 不存在"

        env_config = envs[env_name]
        conn = env_config.get("connection", {})
        if not conn:
            return False, "缺少 connection 配置"

        # 必需字段检查
        required_fields = ["host", "port", "service", "username"]
        for field in required_fields:
            if field not in conn:
                return False, f"缺少必需字段: connection.{field}"
            if not conn[field] and field != "port":
                return False, f"字段不能为空: connection.{field}"

        # 端口号校验
        try:
            port = int(conn["port"])
            if port < 1 or port > 65535:
                return False, f"端口号超出范围: {port} (应为 1-65535)"
        except (ValueError, TypeError):
            return False, f"端口号无效: {conn.get('port')}"

        # 密码字段（可以为空，但不能缺失）
        if "password" not in conn:
            return False, "缺少必需字段: connection.password"

        return True, "环境配置有效"

    # ------------------------------------------------------------------
    # 环境 CRUD
    # ------------------------------------------------------------------

    def add_environment(
        self,
        env_name: str,
        description: str,
        host: str,
        port: int,
        service: str,
        username: str,
        password: str,
        schema: str = "",
        settings: Dict[str, Any] = None,
    ) -> bool:
        """添加或更新一个环境配置。

        Args:
            env_name: 环境名称
            description: 环境描述
            host: 数据库主机地址
            port: 数据库端口号
            service: 数据库服务名
            username: 数据库用户名
            password: 数据库密码
            schema: 默认 schema
            settings: 其他自定义设置

        Returns:
            bool: 添加是否成功

        Raises:
            ValidationError: 参数无效
        """
        env_name = env_name.upper().strip()
        if not env_name:
            raise ValidationError("环境名称不能为空")

        if len(env_name) > 50:
            raise ValidationError("环境名称不能超过 50 个字符")

        env_config = {
            "description": description.strip() if description else "",
            "connection": {
                "host": host.strip(),
                "port": int(port),
                "service": service.strip(),
                "username": username.strip(),
                "password": password,
            },
            "settings": {
                "schema": schema.strip() if schema else "",
            },
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        # 合并自定义设置
        if settings:
            env_config["settings"].update(settings)

        # 记录创建时间（如果之前不存在）
        if env_name not in self.config.get("environments", {}):
            env_config["created_at"] = env_config["updated_at"]

        if "environments" not in self.config:
            self.config["environments"] = {}

        self.config["environments"][env_name] = env_config
        self._save_config()
        return True

    def remove_environment(self, env_name: str) -> bool:
        """删除一个环境配置。

        Args:
            env_name: 环境名称

        Returns:
            bool: 是否删除成功

        Raises:
            ConfigError: 环境不存在
        """
        env_name = env_name.upper().strip()
        envs = self.config.get("environments", {})

        if env_name not in envs:
            raise ConfigError(f"环境 '{env_name}' 不存在")

        del envs[env_name]

        # 如果删除的是当前激活环境，则清除激活状态
        if self.active_environment == env_name:
            self.active_environment = ""
            self.config["active_environment"] = ""

        self._save_config()
        return True

    def get_connection_for_env(self, env_name: str) -> Dict[str, Any]:
        """获取指定环境的连接管理信息。

        Args:
            env_name: 环境名称

        Returns:
            Dict[str, Any]: 连接参数字典

        Raises:
            ConfigError: 环境不存在或配置无效
        """
        env_config = self.load_environment(env_name)
        conn = env_config.get("connection", {})
        return {
            "host": conn.get("host", ""),
            "port": conn.get("port", 1521),
            "service": conn.get("service", ""),
            "username": conn.get("username", ""),
            "password": conn.get("password", ""),
        }

    def get_settings_for_env(self, env_name: str) -> Dict[str, Any]:
        """获取指定环境的设置信息。

        Args:
            env_name: 环境名称

        Returns:
            Dict[str, Any]: 设置参数字典

        Raises:
            ConfigError: 环境不存在
        """
        env_config = self.load_environment(env_name)
        return copy.deepcopy(env_config.get("settings", {}))