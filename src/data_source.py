"""数据源抽象层 — P1-5: CSV/JSON 流式导入

支持 Excel (.xlsx/.xls)、CSV、JSON 三种数据源，
提供统一的接口供上层调用。
CSV/JSON 使用流式读取，支持百万级数据。
"""

import csv
import json
import io
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Iterator, Protocol
from abc import ABC, abstractmethod


# ---------------------------------------------------------------------------
# 抽象接口
# ---------------------------------------------------------------------------

class DataSource(ABC):
    """数据源抽象基类"""

    @abstractmethod
    def get_columns(self) -> List[str]:
        """获取列名列表"""
        ...

    @abstractmethod
    def read_rows(self) -> Iterator[Dict[str, Any]]:
        """流式读取数据行"""
        ...

    @abstractmethod
    def get_row_count(self) -> int:
        """获取总行数（尽可能准确，流式源可能返回估算值）"""
        ...

    @abstractmethod
    def get_preview(self, max_rows: int = 50) -> Tuple[List[str], List[Dict[str, Any]]]:
        """获取预览数据"""
        ...

    @property
    @abstractmethod
    def source_type(self) -> str:
        """数据源类型: 'excel' | 'csv' | 'json'"""
        ...


# ---------------------------------------------------------------------------
# Excel 数据源（保持原有逻辑）
# ---------------------------------------------------------------------------

class ExcelDataSource(DataSource):
    """Excel 数据源，支持 .xlsx 和 .xls"""

    def __init__(self, file_path: str, max_rows: int = 100000, max_file_size: int = 10 * 1024 * 1024):
        self.file_path = Path(file_path)
        self.max_rows = max_rows
        self.max_file_size = max_file_size
        self._columns: List[str] = []
        self._raw_data: List[Dict[str, Any]] = []
        self._loaded = False

    @property
    def source_type(self) -> str:
        if self.file_path.suffix.lower() == '.xls':
            return 'excel_xls'
        return 'excel'

    def _load(self):
        """加载 Excel 文件"""
        if self._loaded:
            return

        if not self.file_path.exists():
            raise FileNotFoundError(f"文件不存在: {self.file_path}")

        file_size = self.file_path.stat().st_size
        if file_size > self.max_file_size:
            raise ValueError(
                f"文件大小 {file_size / 1024 / 1024:.1f}MB 超过限制 {self.max_file_size / 1024 / 1024}MB"
            )

        import openpyxl
        wb = openpyxl.load_workbook(self.file_path, read_only=True, data_only=True)
        ws = wb.active

        rows_iter = ws.iter_rows(values_only=True)
        try:
            header_row = next(rows_iter)
        except StopIteration:
            wb.close()
            raise ValueError("Excel 文件为空")

        self._columns = [str(h).strip() if h else "" for h in header_row]
        if not any(self._columns):
            wb.close()
            raise ValueError("Excel 文件没有有效的列名")

        row_count = 0
        for row in rows_iter:
            if row_count >= self.max_rows:
                break
            row_dict = {}
            for i, col_name in enumerate(self._columns):
                if col_name:
                    row_dict[col_name] = row[i] if i < len(row) else None
            self._raw_data.append(row_dict)
            row_count += 1

        wb.close()
        self._loaded = True

    def get_columns(self) -> List[str]:
        self._load()
        return [c for c in self._columns if c]

    def read_rows(self) -> Iterator[Dict[str, Any]]:
        self._load()
        for row in self._raw_data:
            yield row

    def get_row_count(self) -> int:
        self._load()
        return len(self._raw_data)

    def get_preview(self, max_rows: int = 50) -> Tuple[List[str], List[Dict[str, Any]]]:
        self._load()
        return (
            self.get_columns(),
            self._raw_data[:max_rows]
        )


# ---------------------------------------------------------------------------
# CSV 数据源 — 流式读取，支持百万级行
# ---------------------------------------------------------------------------

class CsvDataSource(DataSource):
    """CSV 数据源，流式读取，突破 10 万行限制"""

    def __init__(self, file_path: str, encoding: str = 'utf-8', delimiter: str = ',',
                 max_rows: int = 10000000):
        self.file_path = Path(file_path)
        self.encoding = encoding
        self.delimiter = delimiter
        self.max_rows = max_rows
        self._columns: List[str] = []
        self._row_count: Optional[int] = None
        self._preview_cache: Optional[List[Dict[str, Any]]] = None

    @property
    def source_type(self) -> str:
        return 'csv'

    def _get_reader(self) -> csv.DictReader:
        """创建 CSV 读取器"""
        if not self.file_path.exists():
            raise FileNotFoundError(f"文件不存在: {self.file_path}")

        f = open(self.file_path, 'r', encoding=self.encoding, newline='')
        # 尝试自动检测分隔符
        sample = f.read(4096)
        f.seek(0)

        if self.delimiter == ',':
            # 自动检测: 如果逗号比 tab 少，改用 tab
            if sample.count('\t') > sample.count(','):
                self.delimiter = '\t'

        reader = csv.DictReader(f, delimiter=self.delimiter)
        return reader

    def get_columns(self) -> List[str]:
        if not self._columns:
            f = open(self.file_path, 'r', encoding=self.encoding, newline='')
            sample = f.read(4096)
            f.seek(0)
            reader = csv.DictReader(f, delimiter=self.delimiter if self.delimiter != ',' else (
                '\t' if sample.count('\t') > sample.count(',') else ','
            ))
            self._columns = reader.fieldnames or []
            f.close()
        return self._columns

    def read_rows(self) -> Iterator[Dict[str, Any]]:
        f = open(self.file_path, 'r', encoding=self.encoding, newline='')
        sample = f.read(4096)
        f.seek(0)
        actual_delim = '\t' if sample.count('\t') > sample.count(',') else self.delimiter
        reader = csv.DictReader(f, delimiter=actual_delim)

        row_count = 0
        for row in reader:
            if row_count >= self.max_rows:
                break
            row_count += 1
            yield row

        f.close()
        self._row_count = row_count

    def get_row_count(self) -> int:
        if self._row_count is not None:
            return self._row_count

        # 快速计数：读取所有行但不保存数据
        count = 0
        try:
            f = open(self.file_path, 'r', encoding=self.encoding, newline='')
            reader = csv.reader(f, delimiter=self.delimiter)
            next(reader)  # 跳过 header
            for _ in reader:
                count += 1
                if count >= self.max_rows:
                    break
            f.close()
        except Exception:
            pass
        self._row_count = count
        return count

    def get_preview(self, max_rows: int = 50) -> Tuple[List[str], List[Dict[str, Any]]]:
        # 确保列名已填充（read_rows 使用 fieldnames 时会依赖 _columns）
        if not self._columns:
            self.get_columns()

        if self._preview_cache is not None:
            return (self._columns, self._preview_cache[:max_rows])

        self._preview_cache = []
        for i, row in enumerate(self.read_rows()):
            if i >= max_rows:
                break
            self._preview_cache.append(row)
        return (self._columns, self._preview_cache)


# ---------------------------------------------------------------------------
# JSON 数据源 — 流式读取（支持 JSON 数组和 JSON Lines）
# ---------------------------------------------------------------------------

class JsonDataSource(DataSource):
    """JSON 数据源，支持 .json 数组和 .jsonl 行格式"""

    def __init__(self, file_path: str, encoding: str = 'utf-8', max_rows: int = 10000000):
        self.file_path = Path(file_path)
        self.encoding = encoding
        self.max_rows = max_rows
        self._columns: List[str] = []
        self._row_count: Optional[int] = None
        self._jsonl_mode: Optional[bool] = None
        self._preview_cache: Optional[List[Dict[str, Any]]] = None

    @property
    def source_type(self) -> str:
        return 'json'

    def _detect_format(self) -> bool:
        """检测 JSON 格式: True=JSONL 行格式, False=JSON 数组"""
        if self._jsonl_mode is not None:
            return self._jsonl_mode

        if not self.file_path.exists():
            raise FileNotFoundError(f"文件不存在: {self.file_path}")

        # 检测 .jsonl 扩展名
        if self.file_path.suffix.lower() == '.jsonl':
            self._jsonl_mode = True
            return True

        # 检测文件内容格式
        with open(self.file_path, 'r', encoding=self.encoding) as f:
            first_line = f.readline().strip()
            if first_line.startswith('['):
                self._jsonl_mode = False
            elif first_line.startswith('{'):
                self._jsonl_mode = True
            else:
                raise ValueError("无法识别 JSON 格式，请使用 JSON 数组或 JSON Lines 格式")

        return self._jsonl_mode

    def get_columns(self) -> List[str]:
        if self._columns:
            return self._columns

        is_jsonl = self._detect_format()

        if is_jsonl:
            with open(self.file_path, 'r', encoding=self.encoding) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        obj = json.loads(line)
                        self._columns = list(obj.keys())
                        break
        else:
            with open(self.file_path, 'r', encoding=self.encoding) as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    self._columns = list(data[0].keys())

        return self._columns

    def read_rows(self) -> Iterator[Dict[str, Any]]:
        is_jsonl = self._detect_format()

        if is_jsonl:
            with open(self.file_path, 'r', encoding=self.encoding) as f:
                row_count = 0
                for line in f:
                    if row_count >= self.max_rows:
                        break
                    line = line.strip()
                    if line:
                        yield json.loads(line)
                        row_count += 1
                self._row_count = row_count
        else:
            with open(self.file_path, 'r', encoding=self.encoding) as f:
                data = json.load(f)
                if isinstance(data, list):
                    for i, item in enumerate(data):
                        if i >= self.max_rows:
                            break
                        yield item
                    self._row_count = min(len(data), self.max_rows)

    def get_row_count(self) -> int:
        if self._row_count is not None:
            return self._row_count

        is_jsonl = self._detect_format()
        count = 0

        if is_jsonl:
            with open(self.file_path, 'r', encoding=self.encoding) as f:
                for line in f:
                    if line.strip():
                        count += 1
                        if count >= self.max_rows:
                            break
        else:
            with open(self.file_path, 'r', encoding=self.encoding) as f:
                data = json.load(f)
                if isinstance(data, list):
                    count = min(len(data), self.max_rows)

        self._row_count = count
        return count

    def get_preview(self, max_rows: int = 50) -> Tuple[List[str], List[Dict[str, Any]]]:
        # 确保列名已填充
        if not self._columns:
            self.get_columns()

        if self._preview_cache is not None:
            return (self._columns, self._preview_cache[:max_rows])

        self._preview_cache = []
        for i, row in enumerate(self.read_rows()):
            if i >= max_rows:
                break
            self._preview_cache.append(row)
        return (self._columns, self._preview_cache)


# ---------------------------------------------------------------------------
# 工厂函数
# ---------------------------------------------------------------------------

def create_data_source(file_path: str, **kwargs) -> DataSource:
    """根据文件扩展名自动创建数据源。

    Args:
        file_path: 文件路径
        **kwargs: 传递给数据源构造函数的额外参数

    Returns:
        对应的 DataSource 实例

    Raises:
        ValueError: 不支持的文件格式
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix in ('.xlsx', '.xls'):
        return ExcelDataSource(file_path, **kwargs)
    elif suffix == '.csv':
        return CsvDataSource(file_path, **kwargs)
    elif suffix in ('.json', '.jsonl'):
        return JsonDataSource(file_path, **kwargs)
    else:
        raise ValueError(f"不支持的文件格式: {suffix}，支持 .xlsx / .xls / .csv / .json / .jsonl")