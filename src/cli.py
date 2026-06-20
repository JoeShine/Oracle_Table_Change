"""CLI 命令行接口 — P1-3

支持无 GUI 环境下的自动化调用，可集成到 CI/CD 流水线。
退出码约定: 0=成功, 1=参数错误, 2=连接失败, 3=验证失败, 4=部分失败, 5=全部失败
"""

import sys
import json
import argparse
import time
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到 Python 路径
_project_root = Path(__file__).parent.parent
sys.path.insert(0, str(_project_root))


def connect_db(config: Dict[str, Any]):
    """建立连接管理"""
    from src.db_connection import DBConnection
    db = DBConnection()
    success, msg = db.connect(
        host=config["host"],
        port=config["port"],
        service=config["service"],
        username=config["username"],
        password=config["password"],
    )
    if not success:
        print(f"连接失败: {msg}", file=sys.stderr)
        sys.exit(2)
    return db


def cmd_update(args):
    """执行批量更新"""
    from src.config_manager import ConfigManager
    from src.logger import LogManager
    from src.data_updater import DataUpdater
    from src.data_source import create_data_source

    t_start = time.time()

    # 加载配置
    cm = ConfigManager()
    log = LogManager()

    # 获取连接信息
    conn_info = cm.get_connection_by_name(args.connection)
    if not conn_info:
        print(f"错误: 连接 '{args.connection}' 不存在", file=sys.stderr)
        sys.exit(1)

    # 解析待更新列
    update_columns = [c.strip() for c in args.update_columns.split(",")]
    if not update_columns:
        print("错误: 未指定待更新列", file=sys.stderr)
        sys.exit(1)

    # 加载数据源
    try:
        source = create_data_source(args.file)
        columns = source.get_columns()
        row_count = source.get_row_count()
        print(f"数据源: {args.file}")
        print(f"列: {columns}")
        print(f"行数: {row_count}")
    except Exception as e:
        print(f"错误: 无法加载数据文件 - {e}", file=sys.stderr)
        sys.exit(1)

    if row_count == 0:
        print("错误: 数据文件为空", file=sys.stderr)
        sys.exit(1)

    # Dry-run 模式
    if args.dry_run:
        print(f"\n[Dry-Run] 将更新 {args.schema}.{args.table}")
        print(f"  唯一标识列: {args.key_column}")
        print(f"  待更新列: {', '.join(update_columns)}")
        print(f"  数据行数: {row_count}")
        print(f"  连接: {args.connection} ({conn_info['host']}:{conn_info['port']}/{conn_info['service']})")
        print(f"\n[Dry-Run] 验证通过，未实际执行更新。")
        sys.exit(0)

    # 连接数据库
    db = connect_db(conn_info)

    # 验证列
    updater = DataUpdater(db, log)
    valid, msg = updater.validate_table_and_columns_multi(
        args.schema, args.table, args.key_column, update_columns
    )
    if not valid:
        print(f"验证失败: {msg}", file=sys.stderr)
        db.disconnect()
        sys.exit(3)

    # 执行更新
    print(f"\n开始更新 {args.schema}.{args.table}...")
    print(f"  唯一标识列: {args.key_column}")
    print(f"  待更新列: {', '.join(update_columns)}")
    print(f"  数据行数: {row_count}")

    # 备份
    backup_ok, backup_msg = updater.backup_table(args.schema, args.table)
    if not backup_ok:
        print(f"备份失败: {backup_msg}", file=sys.stderr)
        db.disconnect()
        sys.exit(3)

    print(f"  备份表: {backup_msg}")

    # 创建临时表
    temp_ok, temp_msg = updater.create_temp_table_multi_column(
        args.schema, args.table, args.key_column, update_columns
    )
    if not temp_ok:
        print(f"创建临时表失败: {temp_msg}", file=sys.stderr)
        db.disconnect()
        sys.exit(3)

    # 导入数据
    data_rows = list(source.read_rows())
    import_ok, import_msg, imported = updater.import_excel_data_multi_column(
        args.schema, args.key_column, update_columns, data_rows
    )
    if not import_ok:
        print(f"导入失败: {import_msg}", file=sys.stderr)
        updater.cleanup_on_failure(args.schema)
        db.disconnect()
        sys.exit(3)

    print(f"  导入记录: {imported}")

    # 执行更新
    success_count, fail_count, problem_records = updater.execute_multi_column_update(
        args.schema, args.schema, args.table, args.key_column, update_columns
    )

    elapsed = time.time() - t_start

    # 清理临时表
    updater.cleanup_temp_table(args.schema)

    # 输出结果
    backup_info = updater.get_backup_info()
    print(f"\n{'='*50}")
    print(f"更新完成")
    print(f"  成功: {success_count}")
    print(f"  失败: {fail_count}")
    print(f"  未匹配: {len([r for r in problem_records if '目标表中不存在' in str(r.get('reason', ''))])}")
    print(f"  耗时: {elapsed:.1f}s")
    if backup_info:
        print(f"  备份表: {args.schema}.{backup_info['backup_table_name']}")

    if fail_count > 0:
        print(f"\n失败记录 (前10条):")
        for rec in problem_records[:10]:
            print(f"  key_value={rec['key_value']} -> {rec['reason']}")

    # 审计日志
    log.log_update(
        schema=args.schema,
        table=args.table,
        key_column=args.key_column,
        update_columns=update_columns,
        total_count=row_count,
        success_count=success_count,
        fail_count=fail_count,
        success=(fail_count == 0),
        backup_table=backup_info["backup_table_name"] if backup_info else "",
        sql_summary="CLI 批量更新",
        elapsed_ms=int(elapsed * 1000),
    )

    db.disconnect()

    # 退出码
    if fail_count == 0:
        sys.exit(0)
    elif fail_count < success_count:
        sys.exit(4)
    else:
        sys.exit(5)


def cmd_connections(args):
    """列出连接配置"""
    from src.config_manager import ConfigManager
    cm = ConfigManager()
    connections = cm.get_connections()
    if not connections:
        print("没有配置任何连接")
        return

    for conn in connections:
        print(f"  {conn['name']}: {conn['host']}:{conn['port']}/{conn['service']} ({conn['username']})")


def cmd_verify_audit(args):
    """验证审计日志完整性"""
    from src.logger import LogManager
    log = LogManager()
    valid, msg = log.verify_audit_integrity()
    if valid:
        print(f"审计日志完整: {msg}")
        sys.exit(0)
    else:
        print(f"审计日志损坏: {msg}", file=sys.stderr)
        sys.exit(1)


def cmd_templates(args):
    """列出场景模板"""
    from src.config_manager import ConfigManager
    cm = ConfigManager()
    templates = cm.get_templates()
    if not templates:
        print("没有配置任何场景模板")
        return

    for tpl in templates:
        print(f"  {tpl['name']}: {tpl.get('description', '')}")
        print(f"    连接: {tpl.get('connection_name', '')} | 表: {tpl.get('target_table', '')}")
        print(f"    列: {tpl.get('update_columns', [])}")


def cmd_version(args):
    """显示版本信息"""
    from src import __version__
    print(f"DBForge v{__version__}")


def main():
    parser = argparse.ArgumentParser(
        description="DBForge CLI - 批量数据更新命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m src.cli update --connection DEV --table EMPLOYEE --excel data.xlsx \\
      --key-column EMP_ID --update-columns NAME,AGE,DEPT --yes

  python -m src.cli update --connection PROD --table EMPLOYEE --excel data.csv \\
      --key-column EMP_ID --update-columns SALARY --dry-run

  python -m src.cli version
  python -m src.cli connections
  python -m src.cli verify-audit
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # update 子命令
    update_parser = subparsers.add_parser("update", help="执行批量数据更新")
    update_parser.add_argument("--connection", "-c", required=True, help="连接配置名称")
    update_parser.add_argument("--table", "-t", required=True, help="目标表名")
    update_parser.add_argument("--schema", "-s", default="APPS", help="目标 Schema (默认: APPS)")
    update_parser.add_argument("--excel", "--file", "-f", dest="file", required=True,
                               help="数据文件路径 (.xlsx / .csv / .json)")
    update_parser.add_argument("--key-column", "-k", required=True, help="唯一标识列")
    update_parser.add_argument("--update-columns", "-u", required=True,
                               help="待更新列，逗号分隔 (如: NAME,AGE,DEPT)")
    update_parser.add_argument("--yes", "-y", action="store_true", help="跳过确认提示")
    update_parser.add_argument("--dry-run", action="store_true", help="仅验证，不实际执行")

    # connections 子命令
    subparsers.add_parser("connections", help="列出所有连接配置")

    # templates 子命令
    subparsers.add_parser("templates", help="列出所有场景模板")

    # verify-audit 子命令
    subparsers.add_parser("verify-audit", help="验证审计日志完整性")

    # version 子命令
    subparsers.add_parser("version", help="显示版本信息")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    commands = {
        "update": cmd_update,
        "connections": cmd_connections,
        "templates": cmd_templates,
        "verify-audit": cmd_verify_audit,
        "version": cmd_version,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()