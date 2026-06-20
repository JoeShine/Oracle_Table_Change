"""P3-1: 数据比较模块

提供 DataCompare 类，用于比较两个数据库表、数据库表与 Excel 数据之间的差异，
并生成格式化的差异报告。

依赖:
    - db_connection: DBConnection 用于数据库查询
    - excel_handler: ExcelHandler 用于读取 Excel 文件
"""

import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from src.errors import ConnectionError, ValidationError, ImportError


class DataCompare:
    """P3-1: 数据比较器

    比较两个数据库表之间的数据差异，或比较数据库表与 Excel 数据之间的差异，
    并生成差异报告。

    Attributes:
        db: DBConnection 实例
        diff_results: 最近一次比较的差异结果
    """

    def __init__(self, db: "DBConnection" = None):
        """初始化 DataCompare 实例。

        Args:
            db: DBConnection 实例，用于数据库查询
        """
        self.db = db
        self.diff_results: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # 表间比较
    # ------------------------------------------------------------------

    def compare_tables(
        self,
        table_a: str,
        table_b: str,
        key_columns: List[str],
        schema_a: str = None,
        schema_b: str = None,
    ) -> Dict[str, Any]:
        """比较两个数据库表之间的数据差异。

        通过 key_columns 指定的主键列匹配两个表中的行，逐行比较所有列值，
        返回新增、删除、修改的行集合。

        Args:
            table_a: 源表名称（基准表）
            table_b: 目标表名称（待比较表）
            key_columns: 主键列名列表，用于行匹配
            schema_a: 源表所在的 schema
            schema_b: 目标表所在的 schema

        Returns:
            Dict[str, Any]: 差异字典，包含以下键:
                - added: 仅在 table_b 中存在的行（相对于 table_a 新增）
                - removed: 仅在 table_a 中存在的行（相对于 table_b 已删除）
                - modified: 在两张表中都存在但值有差异的行
                - unchanged: 完全相同的行数
                - key_columns: 使用的主键列
                - table_a: 源表信息
                - table_b: 目标表信息
                - compared_at: 比较时间

        Raises:
            ConnectionError: 数据库未连接
            ValidationError: 表不存在或列名无效
        """
        if self.db is None or not self.db.is_connected():
            raise ConnectionError("数据库未连接，无法执行表比较")

        if not key_columns:
            raise ValidationError("key_columns 不能为空")

        # 获取两个表的完整数据
        data_a = self._fetch_table_data(table_a, schema_a)
        data_b = self._fetch_table_data(table_b, schema_b)

        if not data_a and not data_b:
            return self._build_diff_result(
                [], [], [], 0, key_columns, table_a, table_b, schema_a, schema_b
            )

        # 构建以主键为索引的字典
        index_a = self._build_key_index(data_a, key_columns)
        index_b = self._build_key_index(data_b, key_columns)

        keys_a = set(index_a.keys())
        keys_b = set(index_b.keys())

        all_columns = self._get_all_columns(data_a, data_b)

        added = []
        removed = []
        modified = []
        unchanged = 0

        # 仅在 table_b 中存在的行 —— 新增
        for key in keys_b - keys_a:
            added.append({"key": key, "row": index_b[key]})

        # 仅在 table_a 中存在的行 —— 删除
        for key in keys_a - keys_b:
            removed.append({"key": key, "row": index_a[key]})

        # 两张表都存在的行 —— 检查是否修改
        for key in keys_a & keys_b:
            row_a = index_a[key]
            row_b = index_b[key]
            diff = self._compute_row_diff(row_a, row_b, all_columns)
            if diff:
                modified.append({"key": key, "changes": diff})
            else:
                unchanged += 1

        self.diff_results = self._build_diff_result(
            added, removed, modified, unchanged,
            key_columns, table_a, table_b, schema_a, schema_b
        )
        return self.diff_results

    # ------------------------------------------------------------------
    # Excel 比较
    # ------------------------------------------------------------------

    def compare_with_excel(
        self,
        table_name: str,
        excel_path: str,
        key_column: str,
        schema: str = None,
        sheet_name: str = None,
    ) -> Dict[str, Any]:
        """比较数据库表与 Excel 数据之间的差异。

        从 Excel 文件读取数据，与数据库表数据逐行比较，返回差异。

        Args:
            table_name: 数据库表名称
            excel_path: Excel 文件路径
            key_column: 主键列名，用于行匹配
            schema: 表所在的 schema
            sheet_name: Excel 工作表名称，默认使用第一个工作表

        Returns:
            Dict[str, Any]: 差异字典，格式同 compare_tables

        Raises:
            ConnectionError: 数据库未连接
            ImportError: Excel 文件读取失败
            ValidationError: 表不存在或列名无效
        """
        if self.db is None or not self.db.is_connected():
            raise ConnectionError("数据库未连接，无法执行比较")

        if not key_column:
            raise ValidationError("key_column 不能为空")

        # 读取 Excel 数据
        try:
            from src.excel_handler import ExcelHandler
            handler = ExcelHandler()
            excel_data = handler.read_excel(excel_path, sheet_name=sheet_name)
        except Exception as e:
            raise ImportError(f"读取 Excel 文件失败: {str(e)}")

        if not excel_data:
            raise ImportError("Excel 文件中没有数据")

        # 获取数据库表数据
        db_data = self._fetch_table_data(table_name, schema)

        # 构建以主键为索引的字典
        idx_db = self._build_key_index(db_data, [key_column])
        idx_excel = self._build_key_index(excel_data, [key_column])

        keys_db = set(idx_db.keys())
        keys_excel = set(idx_excel.keys())

        all_columns = self._get_all_columns(db_data, excel_data)

        added = []
        removed = []
        modified = []
        unchanged = 0

        # Excel 中有但数据库中没有 —— 建议新增
        for key in keys_excel - keys_db:
            added.append({"key": key, "row": idx_excel[key]})

        # 数据库中有但 Excel 中没有 —— 建议删除
        for key in keys_db - keys_excel:
            removed.append({"key": key, "row": idx_db[key]})

        # 两者都存在 —— 检查差异
        for key in keys_db & keys_excel:
            diff = self._compute_row_diff(idx_db[key], idx_excel[key], all_columns)
            if diff:
                modified.append({"key": key, "changes": diff})
            else:
                unchanged += 1

        self.diff_results = self._build_diff_result(
            added, removed, modified, unchanged,
            [key_column], table_name, excel_path, schema, None
        )
        return self.diff_results

    # ------------------------------------------------------------------
    # 差异报告生成
    # ------------------------------------------------------------------

    def generate_diff_report(self, format: str = "text") -> str:
        """生成格式化的差异报告。

        Args:
            format: 报告格式，可选 "text" 或 "html"

        Returns:
            str: 格式化的差异报告字符串

        Raises:
            ValidationError: 尚未执行比较
        """
        if not self.diff_results:
            raise ValidationError("尚未执行比较操作，请先调用 compare_tables 或 compare_with_excel")

        if format == "html":
            return self._generate_html_report()
        return self._generate_text_report()

    def _generate_text_report(self) -> str:
        """生成纯文本格式的差异报告。"""
        diff = self.diff_results
        lines = []
        lines.append("=" * 70)
        lines.append("  数据比较报告")
        lines.append("=" * 70)
        lines.append(f"  比较时间: {diff.get('compared_at', 'N/A')}")
        lines.append(f"  源 (A):   {diff.get('table_a', 'N/A')}")
        lines.append(f"  目标 (B): {diff.get('table_b', 'N/A')}")
        lines.append(f"  主键列:   {', '.join(diff.get('key_columns', []))}")
        lines.append("-" * 70)
        lines.append(f"  新增行:     {len(diff.get('added', []))}")
        lines.append(f"  删除行:     {len(diff.get('removed', []))}")
        lines.append(f"  修改行:     {len(diff.get('modified', []))}")
        lines.append(f"  未变更行:   {diff.get('unchanged', 0)}")
        total = (
            len(diff.get('added', []))
            + len(diff.get('removed', []))
            + len(diff.get('modified', []))
            + diff.get('unchanged', 0)
        )
        lines.append(f"  总行数:     {total}")
        lines.append("=" * 70)

        # 新增行详情
        if diff.get('added'):
            lines.append("\n[新增行]")
            lines.append("-" * 50)
            for item in diff['added']:
                key_str = self._format_key(item['key'])
                lines.append(f"  主键: {key_str}")
                for col, val in item['row'].items():
                    lines.append(f"    {col}: {val}")
                lines.append("")

        # 删除行详情
        if diff.get('removed'):
            lines.append("\n[删除行]")
            lines.append("-" * 50)
            for item in diff['removed']:
                key_str = self._format_key(item['key'])
                lines.append(f"  主键: {key_str}")
                for col, val in item['row'].items():
                    lines.append(f"    {col}: {val}")
                lines.append("")

        # 修改行详情
        if diff.get('modified'):
            lines.append("\n[修改行]")
            lines.append("-" * 50)
            for item in diff['modified']:
                key_str = self._format_key(item['key'])
                lines.append(f"  主键: {key_str}")
                for change in item['changes']:
                    lines.append(
                        f"    {change['column']}: "
                        f"'{change['old_value']}' -> '{change['new_value']}'"
                    )
                lines.append("")

        if not diff.get('added') and not diff.get('removed') and not diff.get('modified'):
            lines.append("\n  两个数据源完全一致，没有差异。")

        lines.append("=" * 70)
        return "\n".join(lines)

    def _generate_html_report(self) -> str:
        """生成 HTML 格式的差异报告。"""
        diff = self.diff_results
        html_parts = []
        html_parts.append("""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>数据比较报告</title>
<style>
  body { font-family: 'Segoe UI', Tahoma, sans-serif; margin: 20px; background: #f5f5f5; }
  .container { max-width: 1200px; margin: 0 auto; background: #fff; padding: 24px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
  h1 { color: #333; border-bottom: 2px solid #007acc; padding-bottom: 10px; }
  .summary { display: flex; gap: 20px; flex-wrap: wrap; margin: 20px 0; }
  .stat { background: #f0f7ff; padding: 12px 20px; border-radius: 6px; text-align: center; min-width: 100px; }
  .stat .num { font-size: 24px; font-weight: bold; color: #007acc; }
  .stat .label { font-size: 12px; color: #666; }
  .stat.added .num { color: #22863a; }
  .stat.removed .num { color: #cb2431; }
  .stat.modified .num { color: #e36209; }
  table { width: 100%; border-collapse: collapse; margin: 16px 0; }
  th { background: #f0f7ff; padding: 10px; text-align: left; border-bottom: 2px solid #007acc; }
  td { padding: 8px 10px; border-bottom: 1px solid #eee; }
  .section-title { background: #f8f9fa; padding: 10px; margin: 20px 0 10px; border-left: 4px solid #007acc; font-weight: bold; }
  .old-val { color: #cb2431; text-decoration: line-through; }
  .new-val { color: #22863a; font-weight: bold; }
  .arrow { color: #666; margin: 0 4px; }
</style>
</head>
<body>
<div class="container">
""")

        html_parts.append(f"<h1>数据比较报告</h1>")
        html_parts.append(f"<p><strong>比较时间:</strong> {diff.get('compared_at', 'N/A')}</p>")
        html_parts.append(f"<p><strong>源 (A):</strong> {diff.get('table_a', 'N/A')}</p>")
        html_parts.append(f"<p><strong>目标 (B):</strong> {diff.get('table_b', 'N/A')}</p>")
        html_parts.append(f"<p><strong>主键列:</strong> {', '.join(diff.get('key_columns', []))}</p>")

        added_count = len(diff.get('added', []))
        removed_count = len(diff.get('removed', []))
        modified_count = len(diff.get('modified', []))
        unchanged_count = diff.get('unchanged', 0)

        html_parts.append(f"""<div class="summary">
  <div class="stat added"><div class="num">{added_count}</div><div class="label">新增</div></div>
  <div class="stat removed"><div class="num">{removed_count}</div><div class="label">删除</div></div>
  <div class="stat modified"><div class="num">{modified_count}</div><div class="label">修改</div></div>
  <div class="stat"><div class="num">{unchanged_count}</div><div class="label">未变更</div></div>
</div>""")

        # 新增行
        if diff.get('added'):
            html_parts.append('<div class="section-title">新增行</div>')
            html_parts.append('<table><tr><th>主键</th><th>数据</th></tr>')
            for item in diff['added']:
                key_str = self._format_key(item['key'])
                row_html = ', '.join(f"{k}={v}" for k, v in item['row'].items())
                html_parts.append(f'<tr><td>{key_str}</td><td>{row_html}</td></tr>')
            html_parts.append('</table>')

        # 删除行
        if diff.get('removed'):
            html_parts.append('<div class="section-title">删除行</div>')
            html_parts.append('<table><tr><th>主键</th><th>数据</th></tr>')
            for item in diff['removed']:
                key_str = self._format_key(item['key'])
                row_html = ', '.join(f"{k}={v}" for k, v in item['row'].items())
                html_parts.append(f'<tr><td>{key_str}</td><td>{row_html}</td></tr>')
            html_parts.append('</table>')

        # 修改行
        if diff.get('modified'):
            html_parts.append('<div class="section-title">修改行</div>')
            html_parts.append('<table><tr><th>主键</th><th>列</th><th>变更</th></tr>')
            for item in diff['modified']:
                key_str = self._format_key(item['key'])
                for i, change in enumerate(item['changes']):
                    col = change['column']
                    old_v = change['old_value']
                    new_v = change['new_value']
                    val_html = (
                        f'<span class="old-val">{old_v}</span>'
                        f'<span class="arrow">-></span>'
                        f'<span class="new-val">{new_v}</span>'
                    )
                    key_display = key_str if i == 0 else ""
                    html_parts.append(
                        f'<tr><td>{key_display}</td><td>{col}</td><td>{val_html}</td></tr>'
                    )
            html_parts.append('</table>')

        if not diff.get('added') and not diff.get('removed') and not diff.get('modified'):
            html_parts.append('<p style="color:#22863a;font-weight:bold;">两个数据源完全一致，没有差异。</p>')

        html_parts.append("</div></body></html>")
        return "\n".join(html_parts)

    # ------------------------------------------------------------------
    # 内部辅助方法
    # ------------------------------------------------------------------

    def _fetch_table_data(
        self, table_name: str, schema: str = None
    ) -> List[Dict[str, Any]]:
        """从数据库获取表的所有数据。

        Args:
            table_name: 表名称
            schema: Schema 名称

        Returns:
            List[Dict[str, Any]]: 表数据列表，每行为一个字典

        Raises:
            ValidationError: 表不存在
        """
        if not self.db.table_exists(table_name, schema):
            src = f"{schema}.{table_name}" if schema else table_name
            raise ValidationError(f"表不存在: {src}")

        full_name = f"{schema}.{table_name}" if schema else table_name
        sql = f"SELECT * FROM {full_name}"
        success, result, error = self.db.execute_sql(sql, commit=False)
        if not success:
            raise ValidationError(f"查询表数据失败: {error}")

        if result is None:
            return []

        # 获取列名
        columns = [col["name"] for col in self.db.get_columns(table_name)]
        return [dict(zip(columns, row)) for row in result]

    @staticmethod
    def _build_key_index(
        data: List[Dict[str, Any]], key_columns: List[str]
    ) -> Dict[Tuple, Dict[str, Any]]:
        """根据主键列构建行索引字典。

        Args:
            data: 数据行列表
            key_columns: 主键列名列表

        Returns:
            Dict[Tuple, Dict[str, Any]]: 主键值元组到行数据的映射
        """
        index = {}
        for row in data:
            key = tuple(row.get(col) for col in key_columns)
            index[key] = row
        return index

    @staticmethod
    def _get_all_columns(
        data_a: List[Dict[str, Any]], data_b: List[Dict[str, Any]]
    ) -> List[str]:
        """获取两个数据源中所有列名的并集。

        Args:
            data_a: 数据源 A
            data_b: 数据源 B

        Returns:
            List[str]: 排好序的列名列表
        """
        columns = set()
        if data_a:
            columns.update(data_a[0].keys())
        if data_b:
            columns.update(data_b[0].keys())
        return sorted(columns)

    @staticmethod
    def _compute_row_diff(
        row_a: Dict[str, Any],
        row_b: Dict[str, Any],
        all_columns: List[str],
    ) -> List[Dict[str, Any]]:
        """逐列比较两行数据，返回差异列表。

        Args:
            row_a: 源行数据
            row_b: 目标行数据
            all_columns: 所有需要比较的列名

        Returns:
            List[Dict[str, Any]]: 差异列表，每个元素包含 column, old_value, new_value
        """
        changes = []
        for col in all_columns:
            val_a = row_a.get(col)
            val_b = row_b.get(col)
            # 统一转换为字符串比较，处理 None 和类型差异
            str_a = str(val_a) if val_a is not None else ""
            str_b = str(val_b) if val_b is not None else ""
            if str_a != str_b:
                changes.append({
                    "column": col,
                    "old_value": str_a,
                    "new_value": str_b,
                })
        return changes

    @staticmethod
    def _format_key(key: Tuple) -> str:
        """格式化主键值用于显示。

        Args:
            key: 主键值元组

        Returns:
            str: 格式化后的主键字符串
        """
        if isinstance(key, tuple) and len(key) == 1:
            return str(key[0])
        return str(key)

    @staticmethod
    def _build_diff_result(
        added: List[Dict],
        removed: List[Dict],
        modified: List[Dict],
        unchanged: int,
        key_columns: List[str],
        table_a: str,
        table_b: str,
        schema_a: str = None,
        schema_b: str = None,
    ) -> Dict[str, Any]:
        """构建统一的差异结果字典。

        Args:
            added: 新增行
            removed: 删除行
            modified: 修改行
            unchanged: 未变更行数
            key_columns: 主键列
            table_a: 源表名
            table_b: 目标表名
            schema_a: 源表 schema
            schema_b: 目标表 schema

        Returns:
            Dict[str, Any]: 差异结果字典
        """
        src_a = f"{schema_a}.{table_a}" if schema_a else table_a
        src_b = f"{schema_b}.{table_b}" if schema_b else table_b

        return {
            "added": added,
            "removed": removed,
            "modified": modified,
            "unchanged": unchanged,
            "key_columns": key_columns,
            "table_a": src_a,
            "table_b": src_b,
            "compared_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }