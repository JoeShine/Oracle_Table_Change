"""ORA 错误码中文映射表 — P1-6

将 Oracle 数据库错误码映射为友好的中文提示，覆盖 30+ 常见 ORA 错误。
供 db_connection.py 和 data_updater.py 统一调用。
"""

from typing import Optional, Dict, Tuple

# ---------------------------------------------------------------------------
# 完整 ORA 错误码 → 中文友好提示映射表 (30+ 错误码)
# ---------------------------------------------------------------------------
ORA_ERROR_MAP: Dict[str, str] = {
    # 连接相关
    "ORA-01017": "用户名或密码无效",
    "ORA-01034": "Oracle 数据库不可用，请检查数据库实例是否已启动",
    "ORA-01031": "权限不足，请检查用户是否有足够权限",
    "ORA-12154": "无法解析服务名，请检查 TNS 配置",
    "ORA-12505": "监听器无法识别连接描述符中的 SID，请检查服务名",
    "ORA-12514": "监听器无法识别服务名，请检查服务名配置",
    "ORA-12541": "无监听程序，请检查主机地址和端口是否正确",
    "ORA-12543": "目标主机不可达，请检查网络连接",
    "ORA-12545": "目标主机不存在，请检查主机名或 IP 地址",
    "ORA-12560": "TNS 协议适配器错误，请检查 Oracle 服务是否启动",
    "ORA-27101": "共享内存域不存在，请检查数据库实例状态",

    # 表/列相关
    "ORA-00942": "表或视图不存在",
    "ORA-00904": "列名无效，请检查列名是否正确",
    "ORA-00955": "名称已被现有对象使用（如表已存在）",
    "ORA-00903": "表名无效",

    # 数据类型
    "ORA-01722": "数据类型不匹配，请检查 Excel 数据与数据库列类型是否一致",
    "ORA-01407": "无法设置为 NULL，目标列不允许空值",
    "ORA-01401": "插入的值对于列来说太大，请检查数据长度",
    "ORA-01438": "值超出列允许的精度范围",
    "ORA-01858": "日期格式不正确，请检查日期格式",
    "ORA-01861": "文字与格式字符串不匹配",

    # 约束
    "ORA-00001": "违反唯一约束，数据重复",
    "ORA-02292": "违反外键约束，存在子记录引用",
    "ORA-02291": "违反外键约束，父键不存在",
    "ORA-01400": "无法插入 NULL，列不允许空值",

    # 表空间/存储
    "ORA-01653": "表空间不足，无法扩展表，请检查表空间容量",
    "ORA-01654": "索引空间不足，无法扩展索引",
    "ORA-01652": "临时表空间不足",

    # 事务/并发
    "ORA-01555": "快照过旧，回滚段数据已被覆盖（建议分批处理或增大 UNDO）",
    "ORA-00060": "检测到死锁，事务被回滚",
    "ORA-00054": "资源正忙，请稍后重试",

    # 权限
    "ORA-01045": "用户缺少 CREATE SESSION 权限",
    "ORA-01031": "权限不足",
    "ORA-01950": "表空间无配额，无法创建对象",
}


def translate_ora_error(error_message: str) -> str:
    """将 Oracle 错误消息翻译为中文友好提示。

    Args:
        error_message: Oracle 原始错误消息（如 "ORA-01017: invalid username/password"）

    Returns:
        中文友好提示，如果未知错误码则返回原始消息
    """
    if not error_message:
        return "未知错误"

    msg_upper = error_message.upper()
    for code, zh_msg in ORA_ERROR_MAP.items():
        if code in msg_upper:
            return f"{zh_msg} ({code})"

    # 未知错误 — 保留原始消息
    return f"数据库错误: {error_message}"


def get_error_hint(error_code: str) -> Optional[str]:
    """获取指定错误码的建议操作。

    Args:
        error_code: ORA 错误码（如 "ORA-01017"）

    Returns:
        建议操作提示，如果无则返回 None
    """
    hints = {
        "ORA-01017": "请检查用户名和密码是否正确，注意大小写。",
        "ORA-12154": "请检查 tnsnames.ora 文件配置，或使用 EZ Connect 格式。",
        "ORA-12541": "请检查主机地址和端口是否正确，防火墙是否开放。",
        "ORA-00942": "请检查表名拼写是否正确，是否存在对应 Schema。",
        "ORA-00904": "请检查列名拼写是否正确，是否区分大小写。",
        "ORA-00001": "请检查数据是否有重复，或使用不同的唯一标识列。",
        "ORA-01722": "请检查 Excel 中该列的数据类型是否与数据库列类型一致。",
        "ORA-01407": "该列不允许空值，请确保 Excel 中有值，或修改数据库列定义。",
        "ORA-01653": "请联系 DBA 扩展表空间，或清理不必要的数据。",
        "ORA-01555": "建议减小批次大小，或联系 DBA 增大 UNDO 表空间。",
        "ORA-00060": "请稍后重试，或减少并发操作。",
        "ORA-01034": "请检查数据库实例是否已启动（STARTUP），监听是否运行。",
        "ORA-01031": "请检查用户是否被授予了必要的权限。",
    }
    return hints.get(error_code)


def extract_ora_code(error_message: str) -> Tuple[str, str]:
    """从错误消息中提取 ORA 错误码和中文翻译。

    Returns:
        Tuple[ora_code, zh_message]: 错误码和中文翻译
    """
    if not error_message:
        return ("", "未知错误")

    msg_upper = error_message.upper()
    for code, zh_msg in ORA_ERROR_MAP.items():
        if code in msg_upper:
            return (code, zh_msg)

    return ("", error_message)