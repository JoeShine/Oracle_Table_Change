"""Oracle 数据批量修改工具 — 主入口

启动流程:
  1. 尝试导入 GUI 模块
  2. 导入失败时显示友好的错误对话框（而非 Windows 系统错误）
  3. 正常启动时显示 GUI 主窗口
"""

import sys
import os
import traceback


def _show_error(title: str, message: str):
    """在不同环境下显示错误信息。

    - GUI 可用时: 使用 tkinter messagebox
    - GUI 不可用时: 输出到 stderr + 尝试 Windows MessageBox
    """
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(title, message)
        root.destroy()
    except Exception:
        # tkinter 不可用，尝试 Windows API
        print(f"\n[ERROR] {title}\n{message}\n", file=sys.stderr)
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.user32.MessageBoxW(
                    0, message, title, 0x10  # MB_ICONERROR
                )
            except Exception:
                pass


def main():
    """应用主入口，带错误处理。

    捕获所有未处理异常，以友好方式展示给用户，
    而非弹出 Windows 系统级错误对话框。
    """
    try:
        from src.gui import main as gui_main
        gui_main()
    except ImportError as e:
        module_name = str(e).split("'")[1] if "'" in str(e) else str(e)
        _show_error(
            "启动失败 - 缺少依赖",
            f"无法加载必要的模块: {module_name}\n\n"
            f"请确认以下依赖已安装:\n"
            f"  - oracledb\n"
            f"  - openpyxl\n"
            f"  - cryptography\n\n"
            f"详细错误:\n{str(e)}"
        )
        sys.exit(1)
    except SystemExit:
        raise
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        tb = traceback.format_exc()
        _show_error(
            "启动失败",
            f"程序启动时发生未预期的错误:\n\n"
            f"{type(e).__name__}: {str(e)}\n\n"
            f"请将以下信息反馈给技术支持:\n"
            f"{'─' * 50}\n"
            f"{tb[-800:]}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()