"""SQL 注入防御模块 — 标识符白名单校验与 sanitize

攻击面：data_updater.py 和 db_connection.py 中所有 DDL/DML/SELECT
语句的 schema、table_name、column_name 均通过 f-string 拼接。
本模块为这些标识符提供白名单校验，阻断 SQL 注入。

设计原则：
1. 默认拒绝：任何未通过白名单的标识符一律拒绝
2. 最小权限：只允许预定义的安全模式，其余抛出 SecurityError
3. 日志可审计：所有校验失败均记录到日志中
"""

import re
import logging
from typing import Set, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 1. 标识符正则白名单
# ---------------------------------------------------------------------------
# Oracle 标识符规则：
#   - 以字母开头，后可跟字母、数字、$、_、#
#   - 最大长度 30（Oracle 11g）或 128（Oracle 12c+）
#   - 兼容双引号包裹的标识符（大小写敏感）
# 本实现使用 128 作为最大长度，兼容 Oracle 12c+
_IDENTIFIER_PATTERN = re.compile(r'^[A-Za-z][A-Za-z0-9_\$#]{0,127}$')

# 允许双引号包裹的标识符，如 "CaseSensitive"
_QUOTED_IDENTIFIER_PATTERN = re.compile(r'^"[A-Za-z][A-Za-z0-9_\$#\s]{0,126}"$')


def sanitize_identifier(name: str, context: str = "identifier") -> str:
    """校验单个标识符是否符合 Oracle 命名规范。

    Args:
        name: 待校验的标识符（如 table_name, column_name）
        context: 上下文描述，用于错误消息（如 "table_name", "schema"）

    Returns:
        通过校验的原始标识符

    Raises:
        SecurityError: 标识符不符合安全规范
    """
    if not name or not isinstance(name, str):
        raise SecurityError(f"标识符不能为空: context={context}")

    stripped = name.strip()

    # 允许双引号包裹的标识符
    if stripped.startswith('"') and stripped.endswith('"'):
        if _QUOTED_IDENTIFIER_PATTERN.match(stripped):
            return stripped
        raise SecurityError(
            f"非法的双引号标识符: '{name}' (context={context})"
        )

    if _IDENTIFIER_PATTERN.match(stripped):
        return stripped

    raise SecurityError(
        f"非法标识符: '{name}' (context={context})，"
        f"必须以字母开头，仅允许字母/数字/$/_/#，最长128字符"
    )


def sanitize_identifier_list(
    names: list, context: str = "column_list"
) -> list:
    """批量校验标识符列表。

    Args:
        names: 标识符列表
        context: 上下文描述

    Returns:
        通过校验的标识符列表
    """
    if not names:
        return []
    return [sanitize_identifier(n, context) for n in names]


# ---------------------------------------------------------------------------
# 2. Schema 白名单
# ---------------------------------------------------------------------------
# 只允许以下预定义模式，拒绝用户输入任意 schema
_SAFE_SCHEMAS: Set[str] = {
    # 常见业务 Schema
    "APPS", "HR", "SCOTT", "OE", "PM", "SH", "IX",
    # 系统 Schema（仅允许在特定上下文中使用，默认可选）
    "SYS", "SYSTEM", "SYSAUX",
    # 自定义 Schema 占位
}


def get_safe_schemas() -> Set[str]:
    """获取当前安全 Schema 列表"""
    return _SAFE_SCHEMAS.copy()


def register_safe_schema(schema: str) -> None:
    """注册一个新的安全 Schema（由管理员在配置中维护）。

    Args:
        schema: Schema 名称（将自动转为大写）
    """
    sanitize_identifier(schema, "schema_registration")
    _SAFE_SCHEMAS.add(schema.upper())


def validate_schema(schema: str, context: str = "schema") -> str:
    """校验 Schema 是否在安全白名单中。

    Args:
        schema: 待校验的 Schema 名称
        context: 上下文描述

    Returns:
        通过校验的 UPPER Schema 名称

    Raises:
        SecurityError: Schema 不在白名单中
    """
    sanitize_identifier(schema, context)
    upper = schema.upper().strip().strip('"')

    if upper in _SAFE_SCHEMAS:
        return upper

    # 允许以用户自定义前缀开头的 Schema（如 APPS_DEV, HR_TEST）
    # 但必须是已知安全前缀
    for safe in _SAFE_SCHEMAS:
        if upper.startswith(safe + "_") or upper.startswith(safe + "$"):
            return upper

    raise SecurityError(
        f"Schema '{schema}' 不在安全白名单中。"
        f"允许的 Schema: {sorted(_SAFE_SCHEMAS)}"
    )


class SecurityError(Exception):
    """安全相关异常"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
        # 自动记录安全事件
        logger.error(f"[SECURITY] {message}")