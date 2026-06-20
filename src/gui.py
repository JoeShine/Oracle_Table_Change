import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from pathlib import Path
from datetime import datetime
import threading
import os
import sys
import subprocess
import platform
from src.config_manager import ConfigManager
from src.db_connection import DBConnection
from src.excel_handler import ExcelHandler, MAX_FILE_SIZE, MAX_ROWS, MAX_PREVIEW_ROWS
from src.data_updater import DataUpdater
from src.logger import LogManager


class OSCompatibility:
    """操作系统兼容性检测与适配"""
    
    # 操作系统类型常量
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    KYLIN = "kylin"  # 麒麟操作系统
    
    def __init__(self):
        self.os_type = self._detect_os()
        self.os_name = self._get_os_name()
        self.is_server = self._detect_server()
        self.font_family = self._get_font_family()
    
    def _detect_os(self) -> str:
        """检测操作系统类型"""
        if os.name == 'nt':
            return self.WINDOWS
        elif sys.platform == 'darwin':
            return self.MACOS
        else:
            # 检测麒麟操作系统
            try:
                with open('/etc/os-release', 'r') as f:
                    content = f.read().lower()
                    if 'kylin' in content or '麒麟' in content:
                        return self.KYLIN
            except Exception:
                pass
            return self.LINUX
    
    def _get_os_name(self) -> str:
        """获取操作系统完整名称"""
        try:
            if self.os_type == self.WINDOWS:
                return f"Windows {platform.win32_ver()[0]} ({platform.architecture()[0]})"
            elif self.os_type == self.MACOS:
                return f"macOS {platform.mac_ver()[0]}"
            elif self.os_type == self.KYLIN:
                return self._get_kylin_version()
            else:
                return f"Linux {platform.uname().system} {platform.uname().release}"
        except Exception:
            return platform.system()
    
    def _get_kylin_version(self) -> str:
        """获取麒麟操作系统版本"""
        try:
            with open('/etc/os-release', 'r') as f:
                for line in f:
                    if line.startswith('PRETTY_NAME='):
                        return line.split('=')[1].strip().replace('"', '')
                    if line.startswith('VERSION='):
                        return f"麒麟 {line.split('=')[1].strip().replace('"', '')}"
            return "麒麟操作系统"
        except Exception:
            return "麒麟操作系统"
    
    def _detect_server(self) -> bool:
        """检测是否为服务器操作系统"""
        if self.os_type == self.WINDOWS:
            # Windows Server 检测
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                    r"SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion") as key:
                    product_name = winreg.QueryValueEx(key, "ProductName")[0]
                    return "Server" in product_name
            except Exception:
                return False
        elif self.os_type == self.KYLIN:
            # 麒麟服务器版检测
            try:
                with open('/etc/os-release', 'r') as f:
                    content = f.read().lower()
                    return 'server' in content or '服务器' in content
            except Exception:
                return False
        return False
    
    def _get_font_family(self) -> str:
        """根据操作系统获取合适的字体"""
        if self.os_type == self.WINDOWS:
            return "Microsoft YaHei"
        elif self.os_type == self.MACOS:
            return "PingFang SC"
        elif self.os_type == self.KYLIN:
            # 麒麟系统使用 Noto Sans CJK 或文泉驿
            return "Noto Sans CJK SC"
        else:
            return "Noto Sans CJK SC"
    
    def get_info(self) -> dict:
        """获取操作系统信息"""
        return {
            "os_type": self.os_type,
            "os_name": self.os_name,
            "is_server": self.is_server,
            "font_family": self.font_family,
            "python_version": platform.python_version(),
            "architecture": platform.architecture()[0]
        }
    
    @staticmethod
    def get_app_version() -> str:
        """从 VERSION 文件动态获取应用版本号"""
        try:
            # 优先从应用目录下的 VERSION 文件读取
            version_file = Path(__file__).parent.parent / "VERSION"
            if version_file.exists():
                return version_file.read_text(encoding='utf-8').strip()
        except Exception:
            pass
        
        # 备选：从环境变量读取
        env_version = os.environ.get("APP_VERSION", "")
        if env_version:
            return env_version
        
        # 兜底：尝试从包元数据读取
        try:
            from importlib.metadata import version
            return version("Oracle_Table_Change")
        except Exception:
            pass
        
        return "unknown"


class ThemeManager:
    """三套主题系统：Idea蓝色（经典）、深墨琥珀（专业）、清爽浅色（简约）"""

    # 主题 A：Idea 蓝色（经典 IDE 风格）
    IDEA_LIGHT = {
        "name": "Idea 蓝色",
        "name_en": "Idea Blue",
        "bg": "#f5f5f5",
        "fg": "#3c3f41",
        "primary": "#4a86e8",
        "primary_dark": "#3d65a5",
        "secondary": "#909090",
        "success": "#4e9a06",
        "error": "#c75050",
        "warning": "#ca8230",
        "info": "#4a86e8",
        "card_bg": "#ffffff",
        "card_border": "#e5e5e5",
        "text_muted": "#6c757d",
        "text_heading": "#2b2b2b",
        "button_bg": "#4a86e8",
        "button_fg": "#ffffff",
        "button_secondary_bg": "#e8e8e8",
        "button_secondary_fg": "#3c3f41",
        "entry_bg": "#ffffff",
        "entry_border": "#ced4da",
        "tree_bg": "#ffffff",
        "tree_alt": "#f5f5f5",
        "log_bg": "#f7f7f7",
        "scrollbar_bg": "#dcdcdc",
        "status_bg": "#f0f0f0",
        "tab_bg": "#e8e8e8",
        "tab_selected": "#ffffff",
        "tab_border": "#d4d4d4",
        "tab_active_bg": "#ffffff",
        "tab_hover_bg": "#e8e8e8",
        "header_bg": "linear-gradient(135deg, #3d65a5 0%, #4a86e8 100%)",
        "header_fg": "#ffffff",
    }

    IDEA_DARK = {
        "name": "Idea 蓝色",
        "name_en": "Idea Blue",
        "bg": "#2b2b2b",
        "fg": "#a9b7c6",
        "primary": "#4a86e8",
        "primary_dark": "#3d65a5",
        "secondary": "#606366",
        "success": "#4e9a06",
        "error": "#cc6666",
        "warning": "#cc7832",
        "info": "#4a86e8",
        "card_bg": "#3c3f41",
        "card_border": "#555555",
        "text_muted": "#808080",
        "text_heading": "#dcdcdc",
        "button_bg": "#4a86e8",
        "button_fg": "#ffffff",
        "button_secondary_bg": "#35383a",
        "button_secondary_fg": "#a9b7c6",
        "entry_bg": "#3c3f41",
        "entry_border": "#555555",
        "tree_bg": "#3c3f41",
        "tree_alt": "#45494a",
        "log_bg": "#2b2b2b",
        "scrollbar_bg": "#4e4e4e",
        "status_bg": "#3c3f41",
        "tab_bg": "#35383a",
        "tab_selected": "#2b2b2b",
        "tab_border": "#4e4e4e",
        "tab_active_bg": "#3c3f41",
        "tab_hover_bg": "#45494a",
        "header_bg": "linear-gradient(135deg, #1a1a1a 0%, #2b2b2b 100%)",
        "header_fg": "#dcdcdc",
    }

    # 主题 B：深墨琥珀（专业终端风格）
    TERMINAL_LIGHT = {
        "name": "深墨琥珀",
        "name_en": "Amber Terminal",
        "bg": "#F7F5F0",
        "fg": "#2C3E50",
        "primary": "#E8A44C",
        "primary_dark": "#C7862A",
        "secondary": "#5A6B7D",
        "success": "#4ECDC4",
        "error": "#C25B56",
        "warning": "#E8A44C",
        "info": "#4ECDC4",
        "card_bg": "#EFEEE8",
        "card_border": "#E0DDD4",
        "text_muted": "#8E9AA8",
        "text_heading": "#2C3E50",
        "button_bg": "#E8A44C",
        "button_fg": "#0D1B2A",
        "button_secondary_bg": "#EFEEE8",
        "button_secondary_fg": "#2C3E50",
        "entry_bg": "#F7F5F0",
        "entry_border": "#E0DDD4",
        "tree_bg": "#EFEEE8",
        "tree_alt": "#E8E5DC",
        "log_bg": "#0D1B2A",
        "scrollbar_bg": "#D0CCC0",
        "status_bg": "#0D1B2A",
        "tab_bg": "#F7F5F0",
        "tab_selected": "#EFEEE8",
        "tab_border": "#E0DDD4",
        "tab_active_bg": "#EFEEE8",
        "tab_hover_bg": "#E8E5DC",
        "header_bg": "linear-gradient(135deg, #0D1B2A 0%, #1B3A5A 100%)",
        "header_fg": "#ffffff",
    }

    TERMINAL_DARK = {
        "name": "深墨琥珀",
        "name_en": "Amber Terminal",
        "bg": "#0F1E2E",
        "fg": "#E8ECF1",
        "primary": "#E8A44C",
        "primary_dark": "#C7862A",
        "secondary": "#6B7A8C",
        "success": "#4ECDC4",
        "error": "#C25B56",
        "warning": "#E8A44C",
        "info": "#4ECDC4",
        "card_bg": "#152538",
        "card_border": "#253D54",
        "text_muted": "#6B7A8C",
        "text_heading": "#E8ECF1",
        "button_bg": "#E8A44C",
        "button_fg": "#0D1B2A",
        "button_secondary_bg": "#152538",
        "button_secondary_fg": "#A8B5C4",
        "entry_bg": "#0F1E2E",
        "entry_border": "#253D54",
        "tree_bg": "#152538",
        "tree_alt": "#1A2F46",
        "log_bg": "#0D1B2A",
        "scrollbar_bg": "#2C4A6B",
        "status_bg": "#0D1B2A",
        "tab_bg": "#152538",
        "tab_selected": "#0F1E2E",
        "tab_border": "#253D54",
        "tab_active_bg": "#152538",
        "tab_hover_bg": "#1A2F46",
        "header_bg": "linear-gradient(135deg, #0D1B2A 0%, #1B3A5A 100%)",
        "header_fg": "#E8ECF1",
    }

    # 主题 C：清爽浅色（简约现代风格）
    CLEAN_LIGHT = {
        "name": "清爽浅色",
        "name_en": "Clean Light",
        "bg": "#FAFBFC",
        "fg": "#1A202C",
        "primary": "#0066CC",
        "primary_dark": "#004C99",
        "secondary": "#718096",
        "success": "#00A86B",
        "error": "#DC3545",
        "warning": "#FD7E14",
        "info": "#0066CC",
        "card_bg": "#FFFFFF",
        "card_border": "#E8ECF0",
        "text_muted": "#A0AEC0",
        "text_heading": "#1A202C",
        "button_bg": "#0066CC",
        "button_fg": "#ffffff",
        "button_secondary_bg": "#FFFFFF",
        "button_secondary_fg": "#1A202C",
        "entry_bg": "#FFFFFF",
        "entry_border": "#E2E8F0",
        "tree_bg": "#FFFFFF",
        "tree_alt": "#F7FAFC",
        "log_bg": "#F7FAFC",
        "scrollbar_bg": "#CBD5E0",
        "status_bg": "#FFFFFF",
        "tab_bg": "#FAFBFC",
        "tab_selected": "#FFFFFF",
        "tab_border": "#E8ECF0",
        "tab_active_bg": "#FFFFFF",
        "tab_hover_bg": "#F7FAFC",
        "header_bg": "linear-gradient(135deg, #0066CC 0%, #0088FF 100%)",
        "header_fg": "#ffffff",
    }

    CLEAN_DARK = {
        "name": "清爽浅色",
        "name_en": "Clean Light",
        "bg": "#1A1D23",
        "fg": "#E8ECF0",
        "primary": "#0088FF",
        "primary_dark": "#0066CC",
        "secondary": "#9CA3AF",
        "success": "#00D68F",
        "error": "#FF6B6B",
        "warning": "#FFB347",
        "info": "#0088FF",
        "card_bg": "#22262E",
        "card_border": "#2D323C",
        "text_muted": "#6B7280",
        "text_heading": "#E8ECF0",
        "button_bg": "#0088FF",
        "button_fg": "#ffffff",
        "button_secondary_bg": "#22262E",
        "button_secondary_fg": "#E8ECF0",
        "entry_bg": "#1A1D23",
        "entry_border": "#2D323C",
        "tree_bg": "#22262E",
        "tree_alt": "#2A2F38",
        "log_bg": "#1A1D23",
        "scrollbar_bg": "#4A5568",
        "status_bg": "#22262E",
        "tab_bg": "#22262E",
        "tab_selected": "#1A1D23",
        "tab_border": "#2D323C",
        "tab_active_bg": "#22262E",
        "tab_hover_bg": "#2A2F38",
        "header_bg": "linear-gradient(135deg, #1A1D23 0%, #2D323C 100%)",
        "header_fg": "#E8ECF0",
    }

    def __init__(self):
        self.current_style = "terminal"  # 'idea' | 'terminal' | 'clean'
        self.is_dark = False
        self.theme = self.TERMINAL_LIGHT

    def set_style(self, style):
        """设置主题风格（保留深浅色模式）"""
        self.current_style = style
        self._apply_current_theme()

    def toggle_dark_mode(self):
        """切换深浅色模式"""
        self.is_dark = not self.is_dark
        self._apply_current_theme()
        return self.is_dark

    def set_dark_mode(self, is_dark):
        """设置深浅色模式"""
        self.is_dark = is_dark
        self._apply_current_theme()

    def _apply_current_theme(self):
        """根据当前风格和深浅色模式应用主题"""
        if self.current_style == "idea":
            self.theme = self.IDEA_DARK if self.is_dark else self.IDEA_LIGHT
        elif self.current_style == "terminal":
            self.theme = self.TERMINAL_DARK if self.is_dark else self.TERMINAL_LIGHT
        elif self.current_style == "clean":
            self.theme = self.CLEAN_DARK if self.is_dark else self.CLEAN_LIGHT
        else:
            self.theme = self.IDEA_DARK if self.is_dark else self.IDEA_LIGHT

    def get_theme(self):
        return self.current_style, self.is_dark, self.theme

    def toggle_theme(self):
        """切换深浅色模式"""
        self.is_dark = not self.is_dark
        self._apply_current_theme()
        return self.current_style, self.is_dark, self.theme

    def switch_theme_style(self, style_key):
        """切换主题风格（idea / terminal / clean），保留深浅色模式"""
        self.current_style = style_key
        self._apply_current_theme()
        return self.current_style, self.is_dark, self.theme


class OracleBatchUpdaterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DBForge")
        self.root.geometry("1000x800")
        self.root.resizable(True, True)
        self.root.minsize(900, 700)
        
        # 操作系统兼容性检测
        self.os_compat = OSCompatibility()
        self.os_info = self.os_compat.get_info()
        
        self.config = ConfigManager()
        self.log_manager = LogManager()
        self.db_connection = DBConnection()
        self.excel_data = None
        self.is_connected = False
        self.current_connection_info = None
        self.theme_manager = ThemeManager()
        self.progress_window = None
        self.update_column_widgets = []
        self.current_progress_callback = None
        self.theme_buttons = {}  # 存储主题按钮引用
        self.setup_styles()
        self.create_widgets()
        self.load_last_config()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.bind_shortcuts()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.update_styles()

    def update_styles(self):
        _, is_dark, theme = self.theme_manager.get_theme()
        font_family = self.os_info["font_family"]
        self.style.configure("Title.TLabel", font=(font_family, 16, "bold"), foreground=theme["text_heading"])
        self.style.configure("Header.TLabel", font=(font_family, 11, "bold"), foreground=theme["text_heading"])
        self.style.configure("Action.TButton", font=(font_family, 10), padding=6)
        self.style.configure("Primary.TButton", font=(font_family, 11, "bold"), padding=8)
        self.style.map("Primary.TButton",
                       background=[('active', theme["primary_dark"])],
                       foreground=[('active', 'white')])
        self.style.configure("Secondary.TButton", font=(font_family, 10), padding=6)
        self.style.map("Secondary.TButton",
                       background=[('active', theme.get("button_secondary_bg", theme["tab_bg"]))],
                       foreground=[('active', theme.get("button_secondary_fg", theme["fg"]))])
        self.style.configure("Card.TFrame", background=theme["card_bg"], borderwidth=1, relief="solid")
        self.style.configure("Status.TLabel", font=(font_family, 9))

    def bind_shortcuts(self):
        self.root.bind('<Control-s>', lambda e: self.save_config())
        self.root.bind('<Control-S>', lambda e: self.save_config())
        # 键盘导航：上下键切换标签页
        self.root.bind('<Up>', lambda e: self._switch_tab(-1))
        self.root.bind('<Down>', lambda e: self._switch_tab(1))
        # 键盘导航：左右键横向/纵向滚动当前内容区
        self.root.bind('<Left>', lambda e: self._scroll_page(-1))
        self.root.bind('<Right>', lambda e: self._scroll_page(1))

    def _switch_tab(self, direction: int):
        """切换标签页（direction: -1=上一个, 1=下一个）"""
        try:
            total = len(self.tab_frames)
            if total == 0:
                return
            new_index = (self.current_tab_index + direction) % total
            self.switch_tab(new_index)
        except Exception:
            pass

    def _scroll_page(self, direction: int):
        """滚动当前标签页内容（direction: -1=上/左, 1=下/右）"""
        try:
            if not self.tab_frames:
                return
            current_tab = self.tab_frames[self.current_tab_index]
            # 查找当前标签页中的可滚动控件
            for widget in current_tab.winfo_children():
                self._scroll_widget_recursive(widget, direction)
        except Exception:
            pass

    def switch_tab(self, index: int):
        """切换到指定标签页并更新导航按钮样式"""
        if not self.tab_frames or index < 0 or index >= len(self.tab_frames):
            return
        self.current_tab_index = index
        # 隐藏所有标签页
        for tab in self.tab_frames:
            tab.pack_forget()
        # 显示当前标签页
        self.tab_frames[index].pack(fill=tk.BOTH, expand=True)
        self._update_sidebar_buttons()

    def _on_nav_button_enter(self, button, index):
        """导航按钮悬停效果"""
        if index == self.current_tab_index:
            return
        _, _, theme = self.theme_manager.get_theme()
        try:
            button.configure(bg=theme.get("tab_hover_bg", theme["bg"]))
        except Exception:
            pass

    def _on_nav_button_leave(self, button, index):
        """导航按钮离开效果"""
        if index == self.current_tab_index:
            return
        _, _, theme = self.theme_manager.get_theme()
        try:
            button.configure(bg=theme["bg"])
        except Exception:
            pass

    def _update_sidebar_buttons(self):
        """根据当前标签页更新导航按钮样式"""
        if not hasattr(self, 'nav_buttons'):
            return
        _, _, theme = self.theme_manager.get_theme()
        active_bg = theme.get("tab_active_bg", theme["bg"])
        bg = theme["bg"]
        fg = theme["fg"]
        for idx, (btn, indicator) in enumerate(self.nav_buttons):
            try:
                if idx == self.current_tab_index:
                    btn.configure(bg=active_bg, fg=fg, relief="flat")
                    indicator.configure(bg="#ff8c00")
                else:
                    btn.configure(bg=bg, fg=fg, relief="flat")
                    indicator.configure(bg=bg)
            except Exception:
                pass

    def _scroll_widget_recursive(self, widget, direction: int):
        """递归查找并滚动可滚动控件"""
        # ScrolledText 滚动
        if isinstance(widget, scrolledtext.ScrolledText):
            widget.yview_scroll(direction, "units")
            return True
        # Treeview 滚动
        if isinstance(widget, ttk.Treeview):
            widget.yview_scroll(direction, "units")
            return True
        # Canvas 滚动
        if isinstance(widget, tk.Canvas):
            widget.yview_scroll(direction, "units")
            return True
        # 递归子控件
        try:
            for child in widget.winfo_children():
                if self._scroll_widget_recursive(child, direction):
                    return True
        except Exception:
            pass
        return False

    def apply_theme(self):
        style_name, is_dark, theme = self.theme_manager.get_theme()
        self.root.configure(bg=theme["bg"])
        for widget in self.root.winfo_children():
            self.apply_theme_recursive(widget, theme)
        # 重新应用导航栏按钮样式
        self._update_sidebar_buttons()

    def apply_theme_recursive(self, widget, theme):
        try:
            widget.configure(bg=theme["bg"])
        except:
            pass
        try:
            widget.configure(background=theme["bg"])
        except:
            pass
        try:
            widget.configure(foreground=theme["fg"])
        except:
            pass
        try:
            widget.configure(fieldbackground=theme["entry_bg"])
        except:
            pass
        try:
            widget.configure(insertbackground=theme["fg"])
        except:
            pass
        for child in widget.winfo_children():
            self.apply_theme_recursive(child, theme)

    def create_widgets(self):
        _, _, theme = self.theme_manager.get_theme()
        self.main_frame = ttk.Frame(self.root, padding="15")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.create_header()
        
        # 左侧导航栏 + 右侧内容区
        self.content_container = tk.Frame(self.main_frame, bg=theme["bg"])
        self.content_container.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.sidebar_frame = tk.Frame(self.content_container, width=200, bg=theme["bg"])
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar_frame.pack_propagate(False)
        
        self.content_frame = tk.Frame(self.content_container, bg=theme["bg"])
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 导航按钮配置
        nav_items = [
            "📝 批量更新",
            "📜 运行日志",
            "🔌 连接管理",
            "📊 操作历史",
            "📊 统计分析",
            "🔧 系统诊断",
        ]
        self.nav_buttons = []      # (button, indicator) 元组列表
        self.nav_button_refs = []  # button 引用
        for idx, text in enumerate(nav_items):
            btn_container = tk.Frame(self.sidebar_frame, bg=theme["bg"])
            btn_container.pack(fill=tk.X, pady=1)
            
            indicator = tk.Frame(btn_container, bg=theme["bg"], width=2)
            indicator.pack(side=tk.LEFT, fill=tk.Y)
            
            btn = tk.Button(
                btn_container,
                text=text,
                bg=theme["bg"],
                fg=theme["fg"],
                relief="flat",
                anchor="w",
                font=(self.os_info["font_family"], 10),
                padx=10,
                pady=8,
                cursor="hand2",
                command=lambda i=idx: self.switch_tab(i)
            )
            btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # 悬停效果
            btn.bind("<Enter>", lambda e, b=btn, i=idx: self._on_nav_button_enter(b, i))
            btn.bind("<Leave>", lambda e, b=btn, i=idx: self._on_nav_button_leave(b, i))
            
            self.nav_buttons.append((btn, indicator))
            self.nav_button_refs.append(btn)
        
        # 标签页框架
        self.tab_frames = [
            self.create_config_tab(),
            self.create_log_tab(),
            self.create_connection_tab(),
            self.create_history_tab(),
            self.create_stats_tab(),
            self.create_diagnosis_tab(),
        ]
        self.current_tab_index = 0
        self.switch_tab(0)
        
        self.create_status_bar()

    def create_header(self):
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 5))
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(side=tk.LEFT)
        title_label = ttk.Label(title_frame, text="📦 DBForge", style="Title.TLabel")
        title_label.pack()
        subtitle_label = ttk.Label(title_frame, text="Database Forge · 数据库批量更新工具", font=("Microsoft YaHei", 10), foreground="#6c757d")
        subtitle_label.pack(pady=(2, 0))
        control_frame = ttk.Frame(header_frame)
        control_frame.pack(side=tk.RIGHT)

        # 主题风格选择器（三个按钮）
        theme_selector_frame = ttk.Frame(control_frame)
        theme_selector_frame.pack(side=tk.RIGHT, padx=(0, 8))

        # 深浅色切换按钮
        self.theme_btn = ttk.Button(control_frame, text="🌙 深色模式", command=self.toggle_theme, style="Action.TButton")
        self.theme_btn.pack(side=tk.RIGHT)

        # 主题风格标签
        style_label = ttk.Label(control_frame, text="主题:", font=("Microsoft YaHei", 9))
        style_label.pack(side=tk.RIGHT, padx=(0, 4))

        # 三个主题风格按钮
        themes = [
            ("terminal", "深墨🖥"),
            ("idea", "Idea💡"),
            ("clean", "清爽✨"),
        ]
        for i, (style_key, style_label_text) in enumerate(themes):
            btn = tk.Button(
                theme_selector_frame,
                text=style_label_text,
                font=("Microsoft YaHei", 9),
                padx=8,
                pady=3,
                bd=1,
                relief="raised",
                cursor="hand2",
                command=lambda s=style_key: self.switch_theme_style(s)
            )
            btn.pack(side=tk.LEFT, padx=2)
            self.theme_buttons[style_key] = btn

        # 初始化主题按钮状态
        self.root.after(100, self._update_theme_selector_buttons)

        minimize_btn = ttk.Button(control_frame, text="▁", width=3, command=self.root.iconify, style="Action.TButton")
        minimize_btn.pack(side=tk.RIGHT, padx=(5, 0))
        maximize_btn = ttk.Button(control_frame, text="⬜", width=3, command=self.toggle_maximize, style="Action.TButton")
        maximize_btn.pack(side=tk.RIGHT, padx=(5, 5))

    def toggle_maximize(self):
        if self.root.state() == "zoomed":
            self.root.state("normal")
        else:
            self.root.state("zoomed")

    def toggle_theme(self, persist=True):
        """切换深浅色模式"""
        style_name, is_dark, theme = self.theme_manager.toggle_theme()
        self.update_styles()
        self.apply_theme()
        self.update_treeview_style()
        self.update_log_style()
        self.update_history_tree_style()
        self._update_theme_selector_buttons()
        self._update_theme_button_text()
        if persist:
            self._save_theme_config()

    def switch_theme_style(self, style_key, persist=True):
        """切换主题风格（idea / terminal / clean）"""
        self.theme_manager.switch_theme_style(style_key)
        self.apply_theme()
        self.update_styles()
        self.update_treeview_style()
        self.update_log_style()
        self.update_history_tree_style()
        self._update_theme_selector_buttons()
        self._update_theme_button_text()
        if persist:
            self._save_theme_config()

    def _save_theme_config(self):
        """持久化当前主题设置"""
        style_name, is_dark, _ = self.theme_manager.get_theme()
        self.config.set_last_used(
            connection_name=self.connection_var.get(),
            target_table=self.target_table_var.get(),
            key_column=self.key_column_var.get(),
            update_column=self.first_update_entry.get() if hasattr(self, 'first_update_entry') else "",
            schema=self.schema_var.get() if hasattr(self, 'schema_var') else "APPS",
            temp_schema=self.temp_schema_var.get() if hasattr(self, 'temp_schema_var') else "APPS",
            theme_style=style_name,
            theme_dark=is_dark
        )

    def _update_theme_button_text(self):
        """根据当前深浅色模式更新主题按钮文本"""
        style_name, is_dark, _ = self.theme_manager.get_theme()
        icon = "☀️" if is_dark else "🌙"
        mode_text = "浅色" if is_dark else "深色"
        if hasattr(self, 'theme_btn'):
            self.theme_btn.config(text=f"{icon} {mode_text}模式")

    def _update_theme_selector_buttons(self):
        """更新主题选择器按钮状态 - 匹配原型风格"""
        style_name, is_dark, theme = self.theme_manager.get_theme()
        for btn_style, btn in self.theme_buttons.items():
            if btn:
                try:
                    is_active = (btn_style == style_name)
                    if is_active:
                        btn.configure(relief="flat", bg=theme["primary"], fg="white",
                                      bd=1, highlightbackground=theme["primary"])
                    else:
                        bg_color = theme.get("button_secondary_bg", "#e8e8e8")
                        fg_color = theme.get("button_secondary_fg", "#3c3f41")
                        btn.configure(relief="flat", bg=bg_color, fg=fg_color,
                                      bd=1, highlightbackground=theme.get("card_border", "#cccccc"))
                except Exception:
                    pass

    def update_treeview_style(self):
        _, is_dark, theme = self.theme_manager.get_theme()
        self.style.configure("Treeview",
                            background=theme["tree_bg"],
                            foreground=theme["fg"],
                            fieldbackground=theme["tree_bg"])
        self.style.map("Treeview",
                       background=[('selected', theme["primary"])],
                       foreground=[('selected', 'white')])
        if hasattr(self, 'preview_tree'):
            self.preview_tree.update()

    def update_log_style(self):
        _, is_dark, theme = self.theme_manager.get_theme()
        if hasattr(self, 'log_text'):
            self.log_text.configure(bg=theme["log_bg"], fg=theme["fg"])
            self.log_text.tag_config("INFO", foreground=theme["fg"])
            self.log_text.tag_config("SUCCESS", foreground=theme["success"])
            self.log_text.tag_config("ERROR", foreground=theme["error"])
            self.log_text.tag_config("WARNING", foreground=theme["warning"])

    def update_history_tree_style(self):
        _, is_dark, theme = self.theme_manager.get_theme()
        if hasattr(self, 'history_tree'):
            self.style.configure("History.Treeview",
                                background=theme["tree_bg"],
                                foreground=theme["fg"],
                                fieldbackground=theme["tree_bg"])
            self.history_tree.update()

    def create_config_tab(self):
        tab = ttk.Frame(self.content_frame, padding="10")

        # ========== 核心操作逻辑 · 业务场景说明 ==========
        workflow_panel = ttk.Frame(tab)
        workflow_panel.pack(fill=tk.X, pady=(0, 10))

        # 用 Canvas 绘制左侧琥珀色竖条
        wf_canvas = tk.Canvas(workflow_panel, height=2, bg="#d97706", highlightthickness=0)
        # 改用带左边框的 Labelframe 风格
        workflow_label = ttk.Label(workflow_panel,
            text=" 核心操作逻辑 · 5 步完成安全批量更新  |  ① 选场景 → ② 配目标 → ③ 取数据 → ④ 校验预览 → ⑤ 执行（自动备份+批量更新）",
            style="Card.TLabel",
            font=("Microsoft YaHei", 9),
            foreground="#d97706",
            padding=(10, 8),
            background="#f8f9fa",
        )
        workflow_label.pack(fill=tk.X)

        scene_label = ttk.Label(workflow_panel,
            text="  业务场景示例：HR 将 1,200 名员工的部门归属 Excel 载入 DBForge，配置目标表 EMPLOYEE / 主键 EMP_ID / 待更新列 DEPT，"
                 "\n  经重复性校验后一键执行。DBForge 自动：① 备份到 EMPLOYEE_BAK_时间戳 ② 创建临时表分批加载 ③ 按主键匹配 UPDATE ④ 返回统计。"
                 "\n  执行过程可在『运行日志』实时跟踪，历次更新可在『操作历史』追溯。",
            style="Card.TLabel",
            font=("Microsoft YaHei", 8),
            foreground="#6c757d",
            padding=(10, 6),
            wraplength=800,
            justify=tk.LEFT,
        )
        scene_label.pack(fill=tk.X)

        # ========== 场景选择区域 ==========
        template_panel = ttk.LabelFrame(tab, text="📝 配置场景", padding="15", style="Card.TFrame")
        template_panel.pack(fill=tk.X, pady=(0, 10))
        
        template_row1 = ttk.Frame(template_panel)
        template_row1.pack(fill=tk.X, pady=6)
        
        ttk.Label(template_row1, text="选择场景:", width=14, font=(self.os_info["font_family"], 10)).pack(side=tk.LEFT)
        self.template_var = tk.StringVar()
        self.template_combo = ttk.Combobox(template_row1, textvariable=self.template_var, 
                                            state="readonly", font=(self.os_info["font_family"], 10), width=30)
        self.template_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.template_combo.bind("<<ComboboxSelected>>", self.on_template_selected)
        
        # 场景操作按钮
        load_btn = ttk.Button(template_row1, text="📂 加载", command=self.load_template, style="Action.TButton", width=8)
        load_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        save_btn = ttk.Button(template_row1, text="💾 保存为场景", command=self.save_as_template, style="Action.TButton", width=12)
        save_btn.pack(side=tk.LEFT, padx=(3, 0))
        
        delete_btn = ttk.Button(template_row1, text="🗑 删除", command=self.delete_template, style="Action.TButton", width=8)
        delete_btn.pack(side=tk.LEFT, padx=(3, 0))
        
        # 刷新场景列表
        self.refresh_template_list()
        
        # ========== 当前配置区域 ==========
        config_panel = ttk.LabelFrame(tab, text="当前配置", padding="15", style="Card.TFrame")
        config_panel.pack(fill=tk.X, pady=(0, 10))
        
        row0 = ttk.Frame(config_panel)
        row0.pack(fill=tk.X, pady=6)
        ttk.Label(row0, text="目标表模式:", width=14, font=("Microsoft YaHei", 10)).pack(side=tk.LEFT)
        self.schema_var = tk.StringVar(value="APPS")
        self.schema_combo = ttk.Combobox(row0, textvariable=self.schema_var, 
                                     values=self.config.get_schema_values(), font=("Microsoft YaHei", 10))
        self.schema_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        schema_config_btn = ttk.Button(row0, text="⚙", width=3, 
                                       command=lambda: self.configure_schema_values("target"), style="Action.TButton")
        schema_config_btn.pack(side=tk.LEFT, padx=(3, 0))
        
        row0b = ttk.Frame(config_panel)
        row0b.pack(fill=tk.X, pady=6)
        ttk.Label(row0b, text="临时表模式:", width=14, font=("Microsoft YaHei", 10)).pack(side=tk.LEFT)
        self.temp_schema_var = tk.StringVar(value="APPS")
        self.temp_schema_combo = ttk.Combobox(row0b, textvariable=self.temp_schema_var, 
                                     values=self.config.get_schema_values(), font=("Microsoft YaHei", 10))
        self.temp_schema_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(row0b, text="(临时表创建位置)", font=("Microsoft YaHei", 8), foreground="#6c757d").pack(side=tk.LEFT, padx=(5, 0))
        schema_config_btn2 = ttk.Button(row0b, text="⚙", width=3,
                                        command=lambda: self.configure_schema_values("temp"), style="Action.TButton")
        schema_config_btn2.pack(side=tk.LEFT, padx=(3, 0))
        
        row1 = ttk.Frame(config_panel)
        row1.pack(fill=tk.X, pady=6)
        ttk.Label(row1, text="目标表名:", width=14, font=("Microsoft YaHei", 10)).pack(side=tk.LEFT)
        self.target_table_var = tk.StringVar()
        target_table_entry = ttk.Entry(row1, textvariable=self.target_table_var, font=("Microsoft YaHei", 10), width=30)
        target_table_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        row2 = ttk.Frame(config_panel)
        row2.pack(fill=tk.X, pady=6)
        ttk.Label(row2, text="唯一标识列:", width=14, font=("Microsoft YaHei", 10)).pack(side=tk.LEFT)
        self.key_column_var = tk.StringVar()
        key_column_entry = ttk.Entry(row2, textvariable=self.key_column_var, font=("Microsoft YaHei", 10), width=30)
        key_column_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        row3 = ttk.Frame(config_panel)
        row3.pack(fill=tk.X, pady=6)
        ttk.Label(row3, text="快捷键 Ctrl+S 保存", width=14, font=("Microsoft YaHei", 8), foreground="#6c757d").pack(side=tk.LEFT)
        
        row4 = ttk.Frame(config_panel)
        row4.pack(fill=tk.X, pady=6)
        ttk.Label(row4, text="待修改列:", width=14, font=("Microsoft YaHei", 10)).pack(side=tk.LEFT)
        self.update_columns_frame = ttk.Frame(row4)
        self.update_columns_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        first_column_row = ttk.Frame(self.update_columns_frame)
        first_column_row.pack(fill=tk.X, pady=2)
        self.first_update_entry = ttk.Entry(first_column_row, font=("Microsoft YaHei", 10), width=30)
        self.first_update_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        add_col_btn = ttk.Button(first_column_row, text="➕", width=3, command=self.add_update_column, style="Action.TButton")
        add_col_btn.pack(side=tk.LEFT, padx=(5, 0))
        self.update_column_widgets = [self.first_update_entry]
        
        excel_frame = ttk.Frame(config_panel)
        excel_frame.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(excel_frame, text="Excel文件:", width=14, font=("Microsoft YaHei", 10)).pack(side=tk.LEFT)
        self.excel_path_var = tk.StringVar()
        excel_entry = ttk.Entry(excel_frame, textvariable=self.excel_path_var, state="readonly", font=("Microsoft YaHei", 10))
        excel_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        browse_btn = ttk.Button(excel_frame, text="📁 浏览", command=self.browse_excel, style="Action.TButton")
        browse_btn.pack(side=tk.LEFT, padx=(5, 0))
        preview_btn = ttk.Button(excel_frame, text="👁 预览", command=self.preview_excel, style="Action.TButton")
        preview_btn.pack(side=tk.LEFT, padx=(3, 0))
        duplicate_check_btn = ttk.Button(excel_frame, text="🔍 重复性校验", command=self.check_duplicates, style="Action.TButton")
        duplicate_check_btn.pack(side=tk.LEFT, padx=(3, 0))
        consistency_check_btn = ttk.Button(excel_frame, text="✅ 一致性校验", command=self.check_consistency, style="Action.TButton")
        consistency_check_btn.pack(side=tk.LEFT, padx=(3, 0))
        
        hint_label = ttk.Label(config_panel, text=f"支持 .xlsx/.xls 文件，最大10MB，最多10万行", 
                               font=("Microsoft YaHei", 9), foreground="#6c757d")
        hint_label.pack(anchor=tk.W, pady=(5, 0))
        
        config_path_frame = ttk.Frame(config_panel)
        config_path_frame.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(config_path_frame, text="配置文件:", width=14, font=("Microsoft YaHei", 10)).pack(side=tk.LEFT)
        self.config_path_var = tk.StringVar(value=str(self.config.config_file))
        config_path_entry = ttk.Entry(config_path_frame, textvariable=self.config_path_var, 
                                      state="readonly", font=("Microsoft YaHei", 9))
        config_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        open_config_btn = ttk.Button(config_path_frame, text="📁 打开目录", 
                                     command=self.open_config_directory, style="Action.TButton", width=10)
        open_config_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        preview_panel = ttk.LabelFrame(tab, text=f"Excel数据预览（前{MAX_PREVIEW_ROWS}行）", padding="12", style="Card.TFrame")
        preview_panel.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        preview_scroll_x = ttk.Scrollbar(tab, orient=tk.HORIZONTAL)
        preview_scroll_x.pack(fill=tk.X, pady=(0, 5))
        
        self.preview_tree = ttk.Treeview(preview_panel, show="headings", height=8, xscrollcommand=preview_scroll_x.set)
        self.preview_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        preview_scroll_y = ttk.Scrollbar(preview_panel, orient=tk.VERTICAL, command=self.preview_tree.yview)
        preview_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.preview_tree.configure(yscrollcommand=preview_scroll_y.set)
        preview_scroll_x.configure(command=self.preview_tree.xview)
        
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X)
        self.validate_btn = ttk.Button(btn_frame, text="🔍 验证数据", style="Action.TButton", command=self.validate_data)
        self.validate_btn.pack(side=tk.LEFT)
        self.execute_btn = ttk.Button(btn_frame, text="✅ 执行", style="Primary.TButton", command=self.confirm_update, state=tk.DISABLED)
        self.execute_btn.pack(side=tk.LEFT, padx=(10, 0))
        clear_btn = ttk.Button(btn_frame, text="🗑 清空", command=self.clear_form, style="Action.TButton")
        clear_btn.pack(side=tk.LEFT, padx=(10, 0))

        return tab

    def add_update_column(self):
        new_row = ttk.Frame(self.update_columns_frame)
        new_row.pack(fill=tk.X, pady=2)
        entry = ttk.Entry(new_row, font=("Microsoft YaHei", 10), width=30)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        remove_btn = ttk.Button(new_row, text="➖", width=3, command=lambda: self.remove_update_column(new_row), style="Action.TButton")
        remove_btn.pack(side=tk.LEFT, padx=(5, 0))
        self.update_column_widgets.append(entry)

    def remove_update_column(self, row):
        if len(self.update_column_widgets) > 1:
            row.destroy()
            self.update_column_widgets = [w for w in self.update_column_widgets if w.winfo_exists()]

    def get_update_columns(self):
        columns = []
        for entry in self.update_column_widgets:
            value = entry.get().strip()
            if value:
                columns.append(value)
        return columns

    def create_log_tab(self):
        tab = ttk.Frame(self.content_frame, padding="10")
        
        log_panel = ttk.LabelFrame(tab, text="运行日志", padding="12", style="Card.TFrame")
        log_panel.pack(fill=tk.BOTH, expand=True)
        self.log_text = scrolledtext.ScrolledText(log_panel, height=20, wrap=tk.WORD, font=("Consolas", 9), relief="flat")
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.tag_config("INFO", foreground="#333333")
        self.log_text.tag_config("SUCCESS", foreground="#28a745")
        self.log_text.tag_config("ERROR", foreground="#dc3545")
        self.log_text.tag_config("WARNING", foreground="#ffc107")
        self.log_text.tag_config("HEADING", foreground="#4facfe", font=("Consolas", 9, "bold"))
        
        export_frame = ttk.Frame(log_panel)
        export_frame.pack(fill=tk.X, pady=(8, 0))
        export_log_btn = ttk.Button(export_frame, text="📊 导出日志", command=self.export_logs, style="Action.TButton")
        export_log_btn.pack(side=tk.LEFT)
        export_fail_btn = ttk.Button(export_frame, text="❌ 导出失败记录", command=self.export_failed_records, style="Action.TButton")
        export_fail_btn.pack(side=tk.LEFT, padx=(8, 0))
        clear_log_btn = ttk.Button(export_frame, text="🗑 清空日志", command=self.clear_logs, style="Action.TButton")
        clear_log_btn.pack(side=tk.RIGHT)

        return tab

    def create_connection_tab(self):
        tab = ttk.Frame(self.content_frame, padding="10")
        
        panel = ttk.LabelFrame(tab, text="连接配置管理", padding="15", style="Card.TFrame")
        panel.pack(fill=tk.BOTH, expand=True)
        ttk.Label(panel, text="选择连接:", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 8))
        connection_frame = ttk.Frame(panel)
        connection_frame.pack(fill=tk.X, pady=(0, 10))
        self.connection_var = tk.StringVar()
        self.connection_combo = ttk.Combobox(connection_frame, textvariable=self.connection_var, state="readonly", font=("Microsoft YaHei", 10))
        self.connection_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.connection_combo.bind("<<ComboboxSelected>>", self.on_connection_selected)
        test_btn = ttk.Button(connection_frame, text="🔗 测试连接", command=self.test_connection, style="Action.TButton")
        test_btn.pack(side=tk.LEFT, padx=(8, 0))
        btn_frame = ttk.Frame(panel)
        btn_frame.pack(fill=tk.X, pady=(0, 12))
        add_btn = ttk.Button(btn_frame, text="➕ 添加连接", command=self.open_add_connection_dialog, style="Action.TButton")
        add_btn.pack(side=tk.LEFT, expand=True, fill=tk.X)
        delete_btn = ttk.Button(btn_frame, text="➖ 删除连接", command=self.delete_connection, style="Action.TButton")
        delete_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))
        self.connection_status_frame = ttk.Frame(panel)
        self.connection_status_frame.pack(fill=tk.X)
        self.connection_status_label = ttk.Label(self.connection_status_frame, text="🔌 未连接", style="Status.TLabel", foreground="#6c757d")
        self.connection_status_label.pack(anchor=tk.W)
        self.update_connection_list()

        return tab

    def create_history_tab(self):
        tab = ttk.Frame(self.content_frame, padding="10")
        
        panel = ttk.LabelFrame(tab, text="历史操作记录", padding="15", style="Card.TFrame")
        panel.pack(fill=tk.BOTH, expand=True)
        
        btn_frame = ttk.Frame(panel)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        refresh_btn = ttk.Button(btn_frame, text="🔄 刷新", command=self.refresh_history, style="Action.TButton")
        refresh_btn.pack(side=tk.LEFT)
        delete_btn = ttk.Button(btn_frame, text="🗑 批量删除", command=self.delete_selected_history, style="Action.TButton")
        delete_btn.pack(side=tk.LEFT, padx=(8, 0))
        
        tree_frame = ttk.Frame(panel)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("select", "id", "timestamp", "table", "schema", "total", "success", "fail", "status")
        self.history_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15, style="History.Treeview")
        
        self.history_tree.heading("select", text="选择")
        self.history_tree.heading("id", text="序号")
        self.history_tree.heading("timestamp", text="操作时间")
        self.history_tree.heading("table", text="目标表")
        self.history_tree.heading("schema", text="模式")
        self.history_tree.heading("total", text="总行数")
        self.history_tree.heading("success", text="成功")
        self.history_tree.heading("fail", text="失败")
        self.history_tree.heading("status", text="状态")
        
        self.history_tree.column("select", width=50, anchor="center")
        self.history_tree.column("id", width=50, anchor="center")
        self.history_tree.column("timestamp", width=150)
        self.history_tree.column("table", width=120)
        self.history_tree.column("schema", width=80)
        self.history_tree.column("total", width=70, anchor="center")
        self.history_tree.column("success", width=70, anchor="center")
        self.history_tree.column("fail", width=70, anchor="center")
        self.history_tree.column("status", width=80)
        
        history_scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        history_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_tree.configure(yscrollcommand=history_scroll_y.set)
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        return tab

    def create_stats_tab(self):
        tab = ttk.Frame(self.content_frame, padding="10")
        placeholder = ttk.Label(tab, text="📊 统计分析功能即将上线", style="Header.TLabel")
        placeholder.pack(expand=True)
        return tab

    def create_diagnosis_tab(self):
        tab = ttk.Frame(self.content_frame, padding="10")
        placeholder = ttk.Label(tab, text="🔧 系统诊断功能即将上线", style="Header.TLabel")
        placeholder.pack(expand=True)
        return tab

    def create_status_bar(self):
        self.status_bar = ttk.Frame(self.main_frame, padding="8")
        self.status_bar.pack(fill=tk.X, pady=(5, 0))
        
        _, is_dark, theme = self.theme_manager.get_theme()
        self.status_bar.configure(style="StatusBar.TFrame")
        self.style.configure("StatusBar.TFrame", background=theme["status_bg"])
        
        # 连接名称（最左侧）
        self.connection_name_label = ttk.Label(self.status_bar, text="连接: -", style="Status.TLabel", font=("Microsoft YaHei", 9, "bold"))
        self.connection_name_label.pack(side=tk.LEFT)
        
        ttk.Separator(self.status_bar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=15)
        
        # 用户信息
        self.db_user_label = ttk.Label(self.status_bar, text="用户: -", style="Status.TLabel")
        self.db_user_label.pack(side=tk.LEFT)
        
        ttk.Separator(self.status_bar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=15)
        
        # 数据库名称
        self.db_name_label = ttk.Label(self.status_bar, text="数据库: -", style="Status.TLabel")
        self.db_name_label.pack(side=tk.LEFT)
        
        ttk.Separator(self.status_bar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=15)
        
        # 连接状态（带指示器）
        self.conn_indicator = tk.Canvas(self.status_bar, width=10, height=10, bg="#c75050", highlightthickness=0)
        self.conn_indicator.pack(side=tk.LEFT, padx=(0, 5))
        self.indicator_item = self.conn_indicator.create_oval(2, 2, 8, 8, fill="#c75050", outline="")
        
        self.conn_status_label = ttk.Label(self.status_bar, text="未连接", style="Status.TLabel")
        self.conn_status_label.pack(side=tk.LEFT)
        
        ttk.Separator(self.status_bar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=15)
        
        self.operation_status_label = ttk.Label(self.status_bar, text="状态: 就绪", style="Status.TLabel")
        self.operation_status_label.pack(side=tk.LEFT)
        
        # 操作系统版本（右下角，动态从操作系统获取）
        os_version = self.os_info["os_name"]
        if self.os_info["is_server"]:
            os_version += " [服务器版]"
        self.version_label = ttk.Label(self.status_bar, text=f"{os_version}", style="Status.TLabel",
                                       font=("Microsoft YaHei", 9))
        self.version_label.pack(side=tk.RIGHT, padx=(0, 15))

    def update_status_bar(self, connected=False, db_name="-", db_user="-", operation="就绪", conn_name="-"):
        if connected:
            self.conn_indicator.itemconfig(self.indicator_item, fill="#4e9a06")
            self.conn_status_label.config(text="已连接")
        else:
            self.conn_indicator.itemconfig(self.indicator_item, fill="#c75050")
            self.conn_status_label.config(text="未连接")
        
        self.connection_name_label.config(text=f"连接: {conn_name}")
        self.db_name_label.config(text=f"数据库: {db_name}")
        self.db_user_label.config(text=f"用户: {db_user}")
        self.operation_status_label.config(text=f"状态: {operation}")

    def clear_logs(self):
        self.log_text.delete(1.0, tk.END)
        self.log_manager = LogManager()

    def open_config_directory(self):
        """打开配置文件所在目录"""
        config_path = Path(self.config.config_file)
        config_dir = str(config_path.parent)
        try:
            if os.name == 'nt':
                os.startfile(config_dir)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', config_dir])
            else:
                subprocess.Popen(['xdg-open', config_dir])
        except Exception as e:
            messagebox.showinfo("配置路径", f"配置文件路径:\n{config_path}")

    def update_connection_list(self):
        connections = self.config.get_connections()
        self.connection_combo['values'] = [conn['name'] for conn in connections]
        if connections:
            self.connection_combo.current(0)

    def load_last_config(self):
        last_used = self.config.get_last_used()
        if last_used.get('connection_name'):
            self.connection_var.set(last_used['connection_name'])
        if last_used.get('target_table'):
            self.target_table_var.set(last_used['target_table'])
        if last_used.get('key_column'):
            self.key_column_var.set(last_used['key_column'])
        if last_used.get('update_column'):
            self.first_update_entry.insert(0, last_used['update_column'])
        if last_used.get('schema'):
            self.schema_var.set(last_used['schema'])
        if last_used.get('temp_schema'):
            self.temp_schema_var.set(last_used['temp_schema'])
        
        # 恢复主题设置（在UI渲染后应用）
        saved_style = last_used.get('theme_style', 'terminal')
        saved_dark = last_used.get('theme_dark', False)
        if saved_style in ('idea', 'terminal', 'clean'):
            self.root.after(50, lambda: self._restore_theme(saved_style, saved_dark))
        
        # 更新状态栏的连接名称
        conn_name = self.connection_var.get()
        if conn_name:
            self.update_status_bar(conn_name=conn_name)

    def _restore_theme(self, style_key, is_dark):
        """恢复保存的主题设置（启动时调用，不持久化）"""
        self.theme_manager.set_dark_mode(is_dark)
        if style_key != 'terminal':
            self.theme_manager.switch_theme_style(style_key)
        self.update_styles()
        self.apply_theme()
        self.update_treeview_style()
        self.update_log_style()
        self.update_history_tree_style()
        self._update_theme_selector_buttons()
        self._update_theme_button_text()

    def save_config(self):
        style_name, is_dark, _ = self.theme_manager.get_theme()
        self.config.set_last_used(
            connection_name=self.connection_var.get(),
            target_table=self.target_table_var.get(),
            key_column=self.key_column_var.get(),
            update_column=self.first_update_entry.get(),
            schema=self.schema_var.get(),
            temp_schema=self.temp_schema_var.get(),
            theme_style=style_name,
            theme_dark=is_dark
        )
        self.add_log("配置已保存 (Ctrl+S)", "SUCCESS")

    def on_connection_selected(self, event=None):
        conn_name = self.connection_var.get()
        if conn_name:
            self.update_status_bar(conn_name=conn_name)

    def test_connection(self):
        conn_name = self.connection_var.get()
        if not conn_name:
            messagebox.showwarning("提示", "请先选择数据库连接")
            return
        conn_info = self.config.get_connection_by_name(conn_name)
        if not conn_info:
            messagebox.showerror("错误", "未找到连接信息")
            return
        
        self.add_log("正在测试数据库连接...")
        self.update_status_bar(connected=False, conn_name=conn_name, operation="正在连接...")
        
        success, msg = self.db_connection.connect(
            host=conn_info['host'],
            port=conn_info['port'],
            service=conn_info['service'],
            username=conn_info['username'],
            password=conn_info['password']
        )
        
        if success:
            self.is_connected = True
            self.current_connection_info = conn_info
            self.connection_status_label.config(text=f"✅ 已连接: {conn_info['username']}@{conn_info['host']}", foreground="#28a745")
            self.update_status_bar(connected=True, conn_name=conn_name, db_name=conn_info['service'], 
                                   db_user=conn_info['username'], operation="已连接")
            self.log_manager.log_connection(conn_info['host'], conn_info['service'], 
                                           conn_info['username'], True)
            self.add_log(msg, "SUCCESS")
            messagebox.showinfo("成功", msg)
        else:
            self.is_connected = False
            self.connection_status_label.config(text="❌ 连接失败", foreground="#dc3545")
            self.update_status_bar(connected=False, conn_name=conn_name, operation="连接失败")
            self.log_manager.log_connection(conn_info['host'], conn_info['service'], 
                                           conn_info['username'], False, str(msg))
            self.add_log(msg, "ERROR")
            messagebox.showerror("连接失败", msg)

    def open_add_connection_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("添加数据库连接")
        dialog.geometry("420x320")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        _, is_dark, theme = self.theme_manager.get_theme()
        dialog.configure(bg=theme["bg"])
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(main_frame, text="连接名称:", style="Header.TLabel").grid(row=0, column=0, sticky=tk.W, padx=5, pady=8)
        name_var = tk.StringVar()
        name_entry = ttk.Entry(main_frame, textvariable=name_var, width=35, font=("Microsoft YaHei", 10))
        name_entry.grid(row=0, column=1, padx=5, pady=8)
        ttk.Label(main_frame, text="主机地址:", style="Header.TLabel").grid(row=1, column=0, sticky=tk.W, padx=5, pady=8)
        host_var = tk.StringVar()
        host_entry = ttk.Entry(main_frame, textvariable=host_var, width=35, font=("Microsoft YaHei", 10))
        host_entry.grid(row=1, column=1, padx=5, pady=8)
        ttk.Label(main_frame, text="端口:", style="Header.TLabel").grid(row=2, column=0, sticky=tk.W, padx=5, pady=8)
        port_var = tk.IntVar(value=1521)
        port_entry = ttk.Entry(main_frame, textvariable=port_var, width=35, font=("Microsoft YaHei", 10))
        port_entry.grid(row=2, column=1, padx=5, pady=8)
        ttk.Label(main_frame, text="服务名:", style="Header.TLabel").grid(row=3, column=0, sticky=tk.W, padx=5, pady=8)
        service_var = tk.StringVar()
        service_entry = ttk.Entry(main_frame, textvariable=service_var, width=35, font=("Microsoft YaHei", 10))
        service_entry.grid(row=3, column=1, padx=5, pady=8)
        ttk.Label(main_frame, text="用户名:", style="Header.TLabel").grid(row=4, column=0, sticky=tk.W, padx=5, pady=8)
        user_var = tk.StringVar()
        user_entry = ttk.Entry(main_frame, textvariable=user_var, width=35, font=("Microsoft YaHei", 10))
        user_entry.grid(row=4, column=1, padx=5, pady=8)
        ttk.Label(main_frame, text="密码:", style="Header.TLabel").grid(row=5, column=0, sticky=tk.W, padx=5, pady=8)
        pwd_var = tk.StringVar()
        pwd_entry = ttk.Entry(main_frame, textvariable=pwd_var, show="*", width=35, font=("Microsoft YaHei", 10))
        pwd_entry.grid(row=5, column=1, padx=5, pady=8)

        def test_and_save():
            if not all([name_var.get(), host_var.get(), service_var.get(), user_var.get(), pwd_var.get()]):
                messagebox.showwarning("提示", "请填写所有字段")
                return
            temp_conn = DBConnection()
            success, msg = temp_conn.connect(
                host=host_var.get(),
                port=port_var.get(),
                service=service_var.get(),
                username=user_var.get(),
                password=pwd_var.get()
            )
            if success:
                self.config.add_connection({
                    "name": name_var.get(),
                    "host": host_var.get(),
                    "port": port_var.get(),
                    "service": service_var.get(),
                    "username": user_var.get(),
                    "password": pwd_var.get()
                })
                self.update_connection_list()
                messagebox.showinfo("成功", "连接信息已保存")
                dialog.destroy()
            else:
                messagebox.showerror("连接失败", msg)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=15)
        ttk.Button(btn_frame, text="🔗 测试连接", command=test_and_save, style="Primary.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy, style="Action.TButton").pack(side=tk.LEFT, padx=5)

    def delete_connection(self):
        conn_name = self.connection_var.get()
        if not conn_name:
            messagebox.showwarning("提示", "请先选择要删除的连接")
            return
        if messagebox.askyesno("确认", f"确定要删除连接 '{conn_name}' 吗？"):
            self.config.delete_connection(conn_name)
            self.update_connection_list()
            self.connection_status_label.config(text="🔌 未连接", foreground="#6c757d")

    def browse_excel(self):
        file_path = filedialog.askopenfilename(
            title="选择Excel文件",
            filetypes=[("Excel文件", "*.xlsx *.xls"), ("所有文件", "*.*")]
        )
        if file_path:
            file_size = os.path.getsize(file_path)
            if file_size > MAX_FILE_SIZE:
                messagebox.showerror("文件过大", f"文件大小不能超过10MB\n当前文件: {(file_size / 1024 / 1024):.2f}MB")
                return
            self.excel_path_var.set(file_path)
            self.preview_excel()

    def preview_excel(self):
        file_path = self.excel_path_var.get()
        if not file_path:
            return
        
        update_columns = self.get_update_columns()
        
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        
        if update_columns:
            success, msg, data = ExcelHandler.get_multi_column_preview(file_path, update_columns)
        else:
            success, msg, data = ExcelHandler.get_preview_data(file_path)
        
        if success:
            headers = data.get('headers', [])
            self.preview_tree['columns'] = headers
            for header in headers:
                self.preview_tree.heading(header, text=header)
                self.preview_tree.column(header, width=120)
            
            for row in data.get('rows', []):
                self.preview_tree.insert('', tk.END, values=row)
            
            if data.get('has_more'):
                self.preview_tree.insert('', tk.END, values=[f"... 还有 {data.get('total_rows', 0) - MAX_PREVIEW_ROWS} 行数据"] + [''] * (len(headers) - 1))
            
            self.add_log(msg, "SUCCESS")
        else:
            messagebox.showerror("预览失败", msg)
    
    def check_duplicates(self):
        """检查Excel中的唯一标识列是否有重复值"""
        file_path = self.excel_path_var.get()
        if not file_path:
            messagebox.showwarning("提示", "请先选择Excel文件")
            return
        
        self.add_log("正在检查Excel中的重复值...", "INFO")
        self.update_status_bar(connected=self.is_connected, operation="正在检查重复值...")
        
        # 获取Excel中的唯一标识值
        success, msg, key_data = ExcelHandler.get_key_values_with_rows(file_path)
        if not success:
            self.add_log(msg, "ERROR")
            messagebox.showerror("读取失败", msg)
            return
        
        # 检查重复值
        key_dict = {}
        duplicates = []
        for item in key_data:
            key_val = item["key_value"]
            row_num = item["row_num"]
            if key_val in key_dict:
                duplicates.append({
                    "key_value": key_val,
                    "rows": [key_dict[key_val], row_num]
                })
            else:
                key_dict[key_val] = row_num
        
        if duplicates:
            self.add_log(f"发现 {len(duplicates)} 个重复值", "ERROR")
            self.show_duplicate_dialog(duplicates)
        else:
            self.add_log("重复性校验通过，没有发现重复值", "SUCCESS")
            messagebox.showinfo("校验通过", "✅ 重复性校验通过！\nExcel中没有发现重复的唯一标识值。")
        self.update_status_bar(connected=self.is_connected, operation="就绪")
    
    def show_duplicate_dialog(self, duplicates):
        """显示重复值对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("发现重复值")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.resizable(True, True)
        _, is_dark, theme = self.theme_manager.get_theme()
        dialog.configure(bg=theme["bg"])
        
        info_label = tk.Label(dialog, text="⚠️ 发现Excel中存在重复的唯一标识值",
                             font=("Microsoft YaHei", 11, "bold"), fg="#dc3545", bg=theme["bg"])
        info_label.pack(fill=tk.X, padx=15, pady=(15, 5))
        
        tree_frame = ttk.Frame(dialog, padding="15")
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("key_value", "rows")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        tree.heading("key_value", text="唯一标识值", anchor=tk.CENTER)
        tree.heading("rows", text="出现的行号", anchor=tk.CENTER)
        tree.column("key_value", width=200, anchor=tk.CENTER)
        tree.column("rows", width=300, anchor=tk.CENTER)
        
        for dup in duplicates:
            rows_str = ", ".join(map(str, dup["rows"]))
            tree.insert('', tk.END, values=(dup["key_value"], rows_str))
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        btn_frame = ttk.Frame(dialog, padding="15")
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="关闭", command=dialog.destroy, style="Action.TButton").pack(side=tk.RIGHT)
    
    def check_consistency(self):
        """检查Excel中的唯一标识列是否都存在于目标表中"""
        file_path = self.excel_path_var.get()
        if not file_path:
            messagebox.showwarning("提示", "请先选择Excel文件")
            return
        
        if not self.is_connected:
            messagebox.showwarning("提示", "请先连接数据库")
            self.switch_tab(2)
            return
        
        target_table = self.target_table_var.get().strip()
        key_column = self.key_column_var.get().strip()
        schema = self.schema_var.get()
        
        if not target_table or not key_column:
            messagebox.showwarning("提示", "请填写目标表名和唯一标识列")
            return
        
        self.add_log("正在检查数据一致性...", "INFO")
        self.update_status_bar(connected=True, operation="正在检查一致性...")
        
        # 获取Excel中的唯一标识值
        success, msg, excel_keys = ExcelHandler.get_key_values_from_excel(file_path)
        if not success:
            self.add_log(msg, "ERROR")
            messagebox.showerror("读取失败", msg)
            return
        
        self.add_log(f"从Excel中获取了 {len(excel_keys)} 个唯一标识值", "INFO")
        
        # 获取数据库中的唯一标识值
        success, msg, db_keys = self.db_connection.get_key_values_from_table(target_table, key_column, schema)
        if not success:
            self.add_log(msg, "ERROR")
            messagebox.showerror("查询失败", msg)
            return
        
        self.add_log(f"从数据库中获取了 {len(db_keys)} 个唯一标识值", "INFO")
        
        # 检查一致性
        db_key_set = set(db_keys)
        missing_keys = []
        for key in excel_keys:
            if key not in db_key_set:
                missing_keys.append(key)
        
        if missing_keys:
            self.add_log(f"发现 {len(missing_keys)} 个标识在数据库中不存在", "ERROR")
            self.show_consistency_dialog(missing_keys)
        else:
            self.add_log("一致性校验通过，所有标识都存在于数据库中", "SUCCESS")
            messagebox.showinfo("校验通过", "✅ 一致性校验通过！\nExcel中的所有唯一标识值都存在于数据库表中。")
        
        self.update_status_bar(connected=True, operation="就绪")
    
    def show_consistency_dialog(self, missing_keys):
        """显示一致性校验失败对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("发现不一致数据")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.resizable(True, True)
        _, is_dark, theme = self.theme_manager.get_theme()
        dialog.configure(bg=theme["bg"])
        
        info_label = tk.Label(dialog, text="⚠️ 发现Excel中的唯一标识在数据库表中不存在",
                             font=("Microsoft YaHei", 11, "bold"), fg="#dc3545", bg=theme["bg"])
        info_label.pack(fill=tk.X, padx=15, pady=(15, 5))
        
        tree_frame = ttk.Frame(dialog, padding="15")
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("missing_key",)
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        tree.heading("missing_key", text="缺失的唯一标识值", anchor=tk.CENTER)
        tree.column("missing_key", width=400, anchor=tk.CENTER)
        
        for key in missing_keys:
            tree.insert('', tk.END, values=(key,))
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        btn_frame = ttk.Frame(dialog, padding="15")
        btn_frame.pack(fill=tk.X)
        
        def export_missing():
            export_path = filedialog.asksaveasfilename(
                title="导出缺失标识",
                defaultextension=".xlsx",
                filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
            )
            if export_path:
                data = [{"缺失的唯一标识": key} for key in missing_keys]
                success, export_msg = ExcelHandler.export_to_excel(data, export_path, "缺失标识")
                if success:
                    messagebox.showinfo("导出成功", export_msg)
                else:
                    messagebox.showerror("导出失败", export_msg)
        
        ttk.Button(btn_frame, text="📊 导出缺失标识", command=export_missing, style="Action.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="关闭", command=dialog.destroy, style="Action.TButton").pack(side=tk.RIGHT)

    def add_log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if level == "HEADING":
            self.log_text.insert(tk.END, f"{'='*60}\n", "HEADING")
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", "HEADING")
            self.log_text.insert(tk.END, f"{'='*60}\n", "HEADING")
        else:
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", level)
        self.log_text.see(tk.END)

    def show_progress_window(self):
        self.progress_window = tk.Toplevel(self.root)
        self.progress_window.title("正在更新数据")
        self.progress_window.geometry("450x400")
        self.progress_window.transient(self.root)
        self.progress_window.grab_set()
        self.progress_window.resizable(False, False)
        
        _, is_dark, theme = self.theme_manager.get_theme()
        self.progress_window.configure(bg=theme["bg"])
        
        title_frame = ttk.Frame(self.progress_window, padding="15")
        title_frame.pack(fill=tk.X)
        ttk.Label(title_frame, text="⏳ 正在更新数据", font=("Microsoft YaHei", 14, "bold")).pack(side=tk.LEFT)
        close_btn = ttk.Button(title_frame, text="✕", width=3, command=self.close_progress_window, style="Action.TButton")
        close_btn.pack(side=tk.RIGHT)
        
        content_frame = ttk.Frame(self.progress_window, padding="20")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(content_frame, text="请稍候，系统正在处理您的请求...", font=("Microsoft YaHei", 11)).pack(pady=(0, 20))
        
        step_frame = ttk.Frame(content_frame)
        step_frame.pack(fill=tk.X, pady=(0, 20))
        steps = ["备份", "导入", "更新"]
        self.step_labels = []
        for i, step in enumerate(steps):
            step_container = ttk.Frame(step_frame)
            step_container.pack(side=tk.LEFT, expand=True)
            step_num = tk.Label(step_container, text=str(i+1), font=("Microsoft YaHei", 14, "bold"),
                                bg="#e9ecef", fg="#6c757d", width=4, anchor="center")
            step_num.pack()
            step_text = tk.Label(step_container, text=step, font=("Microsoft YaHei", 10), bg=theme["bg"], fg=theme["fg"])
            step_text.pack()
            self.step_labels.append((step_num, step_text))
        
        self.progress_var = tk.DoubleVar(value=0)
        progress_bar = ttk.Progressbar(content_frame, variable=self.progress_var, maximum=100, length=350)
        progress_bar.pack(pady=(10, 10))
        
        self.progress_label = ttk.Label(content_frame, text="处理进度: 0/0 (0%)", font=("Microsoft YaHei", 11))
        self.progress_label.pack()
        
        self.eta_label = ttk.Label(content_frame, text="", font=("Microsoft YaHei", 9), foreground="#6c757d")
        self.eta_label.pack(pady=(5, 0))
        
        self.current_op_label = ttk.Label(content_frame, text="正在连接数据库...", font=("Microsoft YaHei", 9), foreground="#6c757d")
        self.current_op_label.pack(pady=(10, 0))

    def close_progress_window(self):
        if self.progress_window:
            self.progress_window.destroy()
            self.progress_window = None

    def update_progress_gui(self, current, total, percentage, operation, eta_seconds=0):
        if self.progress_window:
            self.progress_var.set(percentage)
            self.progress_label.config(text=f"处理进度: {current}/{total} ({percentage}%)")
            self.current_op_label.config(text=operation)
            if eta_seconds > 0:
                from src.progress import format_eta
                self.eta_label.config(text=f"预计剩余时间: {format_eta(eta_seconds)}")
            else:
                self.eta_label.config(text="")

    def update_step_gui(self, step_index, status):
        if not self.progress_window or step_index >= len(self.step_labels):
            return
        step_num, step_text = self.step_labels[step_index]
        if status == "success":
            step_num.configure(bg="#28a745", fg="white")
        elif status == "active":
            step_num.configure(bg="#4facfe", fg="white")
        elif status == "done":
            step_num.configure(bg="#28a745", fg="white")

    def validate_data(self):
        """验证数据：Excel结构 + 数据库表/列，全部通过后才允许执行"""
        if not self.is_connected:
            messagebox.showwarning("提示", "请先连接数据库")
            self.switch_tab(2)
            return
        
        target_table = self.target_table_var.get().strip()
        key_column = self.key_column_var.get().strip()
        update_columns = self.get_update_columns()
        excel_path = self.excel_path_var.get().strip()
        schema = self.schema_var.get()
        temp_schema = self.temp_schema_var.get()
        
        if not all([target_table, key_column, excel_path]):
            messagebox.showwarning("提示", "请填写所有必填字段")
            return
        
        if not update_columns:
            messagebox.showwarning("提示", "请至少添加一个待修改列")
            return
        
        # 禁用验证按钮，防止重复点击
        self.validate_btn.config(state=tk.DISABLED, text="⏳ 验证中...")
        self.root.update()
        
        validation_errors = []
        
        try:
            # 1. 验证Excel文件
            self.update_status_bar(connected=True, operation="正在验证Excel...")
            valid, msg, _ = ExcelHandler.validate_multi_column_structure(excel_path, update_columns)
            if not valid:
                validation_errors.append(f"Excel验证失败: {msg}")
            else:
                self.add_log(f"Excel验证通过: {msg}", "SUCCESS")
            
            # 2. 验证数据库表/列
            if not validation_errors:
                self.update_status_bar(connected=True, operation="正在验证数据库表/列...")
                updater = DataUpdater(self.db_connection, self.log_manager)
                valid, msg = updater.validate_table_and_columns_multi(schema, target_table, key_column, update_columns)
                if not valid:
                    validation_errors.append(f"数据库验证失败: {msg}")
                else:
                    self.add_log("数据库表和列验证通过", "SUCCESS")
            
            # 3. 验证临时表Schema
            if not validation_errors and temp_schema != schema:
                self.add_log(f"目标表模式: {schema}, 临时表模式: {temp_schema}", "INFO")
        
        except Exception as e:
            validation_errors.append(f"验证过程异常: {str(e)}")
        
        # 恢复按钮状态
        if validation_errors:
            self.validate_btn.config(state=tk.NORMAL, text="🔍 验证数据")
            self.execute_btn.config(state=tk.DISABLED)
            self.update_status_bar(connected=True, operation="验证失败")
            
            error_msg = "\n".join(validation_errors)
            self.add_log(error_msg, "ERROR")
            messagebox.showerror("验证失败", f"数据验证未通过，请修正后重试：\n\n{error_msg}")
        else:
            self.validate_btn.config(state=tk.DISABLED, text="✅ 验证通过")
            self.execute_btn.config(state=tk.NORMAL)
            self.update_status_bar(connected=True, operation="验证通过，可以执行")
            self.add_log("所有验证通过，可以执行更新操作", "SUCCESS")
            messagebox.showinfo("验证通过", "数据验证全部通过！\n\n请点击\"执行\"按钮开始更新数据库。")

    def confirm_update(self):
        if not self.is_connected:
            messagebox.showwarning("提示", "请先连接数据库")
            self.switch_tab(2)
            return
        
        target_table = self.target_table_var.get().strip()
        key_column = self.key_column_var.get().strip()
        update_columns = self.get_update_columns()
        excel_path = self.excel_path_var.get().strip()
        
        if not all([target_table, key_column, excel_path]):
            messagebox.showwarning("提示", "请填写所有必填字段")
            return
        
        if not update_columns:
            messagebox.showwarning("提示", "请至少添加一个待修改列")
            return
        
        schema = self.schema_var.get()
        
        confirm_text = f"""请确认以下配置信息：

数据库模式: {schema}
目标表名: {target_table}
唯一标识列: {key_column}
待修改列: {', '.join(update_columns)}
Excel文件: {excel_path}

⚠️ 警告：系统将自动备份目标表数据。
如果更新失败，将自动回滚到初始状态。"""
        
        if messagebox.askyesno("确认更新", confirm_text):
            self.start_update()

    def start_update(self):
        self.show_progress_window()
        self.switch_tab(1)
        threading.Thread(target=self._run_update, daemon=True).start()

    def _run_update(self):
        try:
            self.save_config()
            self.log_manager.clear_failed_records()
            self.root.after(0, lambda: self.execute_btn.config(state=tk.DISABLED))
            self.root.after(0, lambda: self.update_status_bar(connected=True, operation="正在验证..."))
            
            self.add_log("开始数据更新操作", "HEADING")
            self.add_log(f"目标表: {self.target_table_var.get()}")
            self.add_log(f"唯一标识列: {self.key_column_var.get()}")
            self.add_log(f"待修改列: {', '.join(self.get_update_columns())}")
            
            target_table = self.target_table_var.get().strip()
            key_column = self.key_column_var.get().strip()
            update_columns = self.get_update_columns()
            excel_path = self.excel_path_var.get().strip()
            schema = self.schema_var.get()  # 目标表Schema
            temp_schema = self.temp_schema_var.get()  # 临时表Schema
            
            self.add_log(f"目标表模式: {schema}, 临时表模式: {temp_schema}", "INFO")
            
            self.root.after(0, lambda: self.update_progress_gui(0, 100, 10, "正在验证Excel文件..."))
            self.add_log("正在验证Excel文件...")
            valid, msg, data_rows = ExcelHandler.validate_multi_column_structure(excel_path, update_columns)
            if not valid:
                self.add_log(msg, "ERROR")
                self.root.after(0, lambda: messagebox.showerror("验证失败", msg))
                self.root.after(0, lambda: self.execute_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.close_progress_window())
                self.root.after(0, lambda: self.update_status_bar(connected=True, operation="验证失败"))
                return
            self.add_log(msg, "SUCCESS")
            
            updater = DataUpdater(self.db_connection, self.log_manager)
            
            self.root.after(0, lambda: self.update_progress_gui(10, 100, 15, "正在验证表和列..."))
            self.add_log("正在验证表和列...")
            valid, msg = updater.validate_table_and_columns_multi(schema, target_table, key_column, update_columns)
            if not valid:
                self.add_log(msg, "ERROR")
                self.root.after(0, lambda: messagebox.showerror("验证失败", msg))
                self.root.after(0, lambda: self.execute_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.close_progress_window())
                self.root.after(0, lambda: self.update_status_bar(connected=True, operation="验证失败"))
                return
            self.add_log("表和列验证通过", "SUCCESS")
            
            self.root.after(0, lambda: self.update_step_gui(0, "active"))
            self.root.after(0, lambda: self.update_progress_gui(15, 100, 20, "正在备份数据..."))
            self.add_log("正在创建备份...")
            success, msg = updater.backup_table(schema, target_table)
            if not success:
                self.add_log(f"备份失败: {msg}", "ERROR")
                self.root.after(0, lambda: messagebox.showerror("备份失败", msg))
                self.root.after(0, lambda: self.execute_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.close_progress_window())
                self.root.after(0, lambda: self.update_status_bar(connected=True, operation="备份失败"))
                return
            self.add_log(f"备份表已创建: {updater.backup_table_name}", "SUCCESS")
            self.root.after(0, lambda: self.update_step_gui(0, "done"))
            
            self.root.after(0, lambda: self.update_step_gui(1, "active"))
            self.root.after(0, lambda: self.update_progress_gui(20, 100, 30, "正在创建临时表..."))
            self.add_log("正在创建临时表...")
            success, msg = updater.create_temp_table_multi_column(temp_schema, target_table, key_column, update_columns)
            if not success:
                self.add_log(f"创建临时表失败: {msg}", "ERROR")
                updater.cleanup_on_failure(temp_schema)
                self.root.after(0, lambda: messagebox.showerror("创建临时表失败", msg))
                self.root.after(0, lambda: self.execute_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.close_progress_window())
                self.root.after(0, lambda: self.update_status_bar(connected=True, operation="创建临时表失败"))
                return
            self.add_log(f"临时表: {temp_schema}.{updater.temp_table_name}", "SUCCESS")
            
            def progress_callback(current, total, percentage, operation, eta_seconds=0):
                adjusted_percentage = 30 + int(percentage * 0.2)
                self.root.after(0, lambda: self.update_progress_gui(current, total, adjusted_percentage, operation, eta_seconds))
            
            updater.set_progress_callback(progress_callback)
            
            self.root.after(0, lambda: self.update_progress_gui(30, 100, 35, "正在导入Excel数据..."))
            self.add_log("正在导入Excel数据...")
            success, error, count = updater.import_excel_data_multi_column(temp_schema, key_column, update_columns, data_rows)
            if not success:
                self.add_log(f"导入失败: {error}", "ERROR")
                updater.cleanup_on_failure(temp_schema)
                self.root.after(0, lambda: messagebox.showerror("导入失败", error))
                self.root.after(0, lambda: self.execute_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.close_progress_window())
                self.root.after(0, lambda: self.update_status_bar(connected=True, operation="导入失败"))
                return
            self.add_log(f"成功导入 {count} 条数据", "SUCCESS")
            self.root.after(0, lambda: self.update_step_gui(1, "done"))
            
            self.root.after(0, lambda: self.update_step_gui(2, "active"))
            self.root.after(0, lambda: self.update_progress_gui(50, 100, 55, "正在执行数据更新..."))
            self.add_log("正在执行数据更新...")
            
            def update_progress_callback(current, total, percentage, operation, eta_seconds=0):
                adjusted_percentage = 55 + int(percentage * 0.4)
                self.root.after(0, lambda: self.update_progress_gui(current, total, adjusted_percentage, operation, eta_seconds))
            
            updater.set_progress_callback(update_progress_callback)
            
            success_count, fail_count, failed_records = updater.execute_multi_column_update(
                schema, temp_schema, target_table, key_column, update_columns
            )
            
            self.root.after(0, lambda: self.update_step_gui(2, "done"))
            self.root.after(0, lambda: self.update_progress_gui(100, 100, 95, "正在清理临时表..."))
            
            updater.cleanup_temp_table(temp_schema)
            self.add_log(f"临时表已清理", "SUCCESS")
            
            self.root.after(0, lambda: self.update_progress_gui(100, 100, 100, "更新完成"))
            
            # 统计未匹配记录数
            unmatched_count = len([r for r in failed_records if r.get('reason') == '目标表中不存在此key_value'])
            actual_fail_count = fail_count - unmatched_count
            
            self.add_log(f"更新完成 - 成功: {success_count}, 失败: {actual_fail_count}, 未匹配: {unmatched_count}")
            
            self.log_manager.log_update(
                schema=schema,
                table=target_table,
                key_column=key_column,
                update_columns=update_columns,
                total_count=success_count + actual_fail_count,
                success_count=success_count,
                fail_count=actual_fail_count,
                success=(actual_fail_count == 0),
                backup_table=updater.backup_table_name
            )
            
            if failed_records:
                # 分离失败记录和未匹配记录
                actual_failures = [r for r in failed_records if r.get('reason') != '目标表中不存在此key_value']
                unmatched_records = [r for r in failed_records if r.get('reason') == '目标表中不存在此key_value']
                
                if actual_failures:
                    self.root.after(0, lambda: self.update_status_bar(connected=True, operation=f"部分失败({len(actual_failures)}条)"))
                    self.root.after(0, lambda: self.show_failure_dialog(actual_failures, updater.backup_table_name, unmatched_count))
                elif unmatched_records:
                    self.root.after(0, lambda: self.update_status_bar(connected=True, operation=f"更新成功({unmatched_count}条未匹配)"))
                    self.root.after(0, lambda: self.show_unmatched_dialog(unmatched_records))
                else:
                    self.root.after(0, lambda: self.update_status_bar(connected=True, operation="更新成功"))
                    self.root.after(0, lambda: messagebox.showinfo("完成", f"更新完成！\n成功: {success_count}\n失败: {actual_fail_count}\n未匹配: {unmatched_count}"))
            else:
                self.root.after(0, lambda: self.update_status_bar(connected=True, operation="更新成功"))
                self.root.after(0, lambda: messagebox.showinfo("完成", f"更新完成！\n成功: {success_count}\n失败: {actual_fail_count}\n未匹配: {unmatched_count}"))
            
            self.root.after(0, lambda: self.refresh_history())
            self.root.after(0, lambda: self.execute_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.close_progress_window())
            
        except Exception as e:
            self.add_log(f"执行出错: {str(e)}", "ERROR")
            self.root.after(0, lambda: messagebox.showerror("错误", str(e)))
            self.root.after(0, lambda: self.execute_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.close_progress_window())
            self.root.after(0, lambda: self.update_status_bar(connected=True, operation="执行出错"))

    def show_failure_dialog(self, failed_records, backup_table, unmatched_count=0):
        """显示失败记录对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("更新失败记录")
        dialog.geometry("650x500")
        dialog.transient(self.root)
        dialog.resizable(True, True)
        _, is_dark, theme = self.theme_manager.get_theme()
        dialog.configure(bg=theme["bg"])
        
        # 信息提示
        info_text = "⚠️ 更新完成但存在失败记录。目标表数据未更新，已回滚到初始状态。"
        if unmatched_count > 0:
            info_text += f"\n另外有 {unmatched_count} 条记录未匹配（Excel中存在但目标表中不存在）。"
        info_label = tk.Label(dialog, text=info_text,
                             font=("Microsoft YaHei", 10), fg="#dc3545", bg=theme["card_bg"])
        info_label.pack(fill=tk.X, padx=15, pady=(15, 5))
        
        tree_frame = ttk.Frame(dialog, padding="15")
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("key_value", "reason", "timestamp")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=12)
        tree.heading("key_value", text="唯一标识", anchor=tk.CENTER)
        tree.heading("reason", text="失败原因", anchor=tk.CENTER)
        tree.heading("timestamp", text="时间", anchor=tk.CENTER)
        tree.column("key_value", width=150, anchor=tk.CENTER)
        tree.column("reason", width=300, anchor=tk.CENTER)
        tree.column("timestamp", width=120, anchor=tk.CENTER)
        
        for record in failed_records:
            tree.insert('', tk.END, values=(record["key_value"], record["reason"], record["timestamp"]))
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        btn_frame = ttk.Frame(dialog, padding="15")
        btn_frame.pack(fill=tk.X)

        def export_and_close():
            self.export_failed_records()
            dialog.destroy()
        
        ttk.Button(btn_frame, text="📊 导出失败记录", command=export_and_close, style="Primary.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="确定", command=dialog.destroy, style="Action.TButton").pack(side=tk.LEFT, padx=5)

    def show_unmatched_dialog(self, unmatched_records):
        """显示未匹配记录对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("未匹配记录")
        dialog.geometry("550x400")
        dialog.transient(self.root)
        dialog.resizable(True, True)
        _, is_dark, theme = self.theme_manager.get_theme()
        dialog.configure(bg=theme["bg"])
        
        # 信息提示
        info_label = tk.Label(dialog, 
                             text=f"⚠️ 有 {len(unmatched_records)} 条记录未匹配。\n这些key_value在Excel中存在，但在目标表中不存在。\n目标表数据已正常更新，未匹配记录不影响更新结果。",
                             font=("Microsoft YaHei", 10), fg="#ca8230", bg=theme["card_bg"])
        info_label.pack(fill=tk.X, padx=15, pady=(15, 5))
        
        tree_frame = ttk.Frame(dialog, padding="15")
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("key_value", "reason", "timestamp")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)
        tree.heading("key_value", text="唯一标识", anchor=tk.CENTER)
        tree.heading("reason", text="原因", anchor=tk.CENTER)
        tree.heading("timestamp", text="时间", anchor=tk.CENTER)
        tree.column("key_value", width=150, anchor=tk.CENTER)
        tree.column("reason", width=200, anchor=tk.CENTER)
        tree.column("timestamp", width=120, anchor=tk.CENTER)
        
        for record in unmatched_records:
            tree.insert('', tk.END, values=(record["key_value"], record["reason"], record["timestamp"]))
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        btn_frame = ttk.Frame(dialog, padding="15")
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="确定", command=dialog.destroy, style="Action.TButton").pack(side=tk.LEFT, padx=5)

    def configure_schema_values(self, schema_type="target"):
        """配置模式下拉选项"""
        import tkinter.simpledialog as simpledialog
        
        current_values = self.config.get_schema_values()
        current_str = ", ".join(current_values)
        
        dialog = tk.Toplevel(self.root)
        dialog.title("配置模式选项")
        dialog.geometry("450x280")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="配置模式下拉选项", font=("Microsoft YaHei", 12, "bold")).pack(pady=(15, 5))
        ttk.Label(dialog, text="用逗号分隔，例如: APPS, SYS, SYSTEM, HR, SCOTT", 
                  font=("Microsoft YaHei", 9), foreground="#6c757d").pack(pady=(0, 10))
        
        ttk.Label(dialog, text="模式选项:", font=("Microsoft YaHei", 10)).pack(anchor=tk.W, padx=20)
        entry = ttk.Entry(dialog, font=("Microsoft YaHei", 10), width=50)
        entry.insert(0, current_str)
        entry.pack(padx=20, pady=(5, 15), fill=tk.X)
        entry.select_range(0, tk.END)
        entry.focus_set()
        
        def save_values():
            new_str = entry.get().strip()
            if not new_str:
                messagebox.showwarning("提示", "模式选项不能为空", parent=dialog)
                return
            new_values = [v.strip() for v in new_str.split(",") if v.strip()]
            self.config.set_schema_values(new_values)
            self.refresh_schema_combos()
            dialog.destroy()
            messagebox.showinfo("成功", f"模式选项已更新为 {len(new_values)} 个")
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=(0, 10))
        ttk.Button(btn_frame, text="💾 保存", command=save_values, style="Primary.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy, style="Action.TButton").pack(side=tk.LEFT, padx=5)
    
    def refresh_schema_combos(self):
        """刷新模式下拉框选项"""
        values = self.config.get_schema_values()
        self.schema_combo['values'] = values
        self.temp_schema_combo['values'] = values

    def clear_form(self):
        self.schema_var.set("APPS")
        self.temp_schema_var.set("APPS")
        self.target_table_var.set("")
        self.key_column_var.set("")
        self.first_update_entry.delete(0, tk.END)
        
        for widget in self.update_column_widgets[1:]:
            if widget.winfo_exists():
                widget.destroy()
        self.update_column_widgets = [self.first_update_entry]
        
        self.excel_path_var.set("")
        
        # 重置验证状态
        self.validate_btn.config(state=tk.NORMAL, text="🔍 验证数据")
        self.execute_btn.config(state=tk.DISABLED)
        
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        
        self.excel_data = None
        self.add_log("表单已清空", "INFO")

    def refresh_history(self):
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        records = self.log_manager.get_history_records(100)
        
        if not records:
            self.history_tree.insert('', tk.END, values=('--', '1', '--', '--', '--', '0', '0', '0', '无记录'))
            return
        
        for i, record in enumerate(records, 1):
            status = "成功" if record.get('success', False) else "部分失败"
            status_color = "#28a745" if record.get('success', False) else "#ffc107"
            
            self.history_tree.insert('', tk.END, values=(
                '☐',
                str(i),
                record.get('timestamp', '--'),
                record.get('table', '--'),
                record.get('schema', '--'),
                str(record.get('total_count', 0)),
                str(record.get('success_count', 0)),
                str(record.get('fail_count', 0)),
                status
            ))

    def delete_selected_history(self):
        selected_items = []
        for item in self.history_tree.get_children():
            values = self.history_tree.item(item, 'values')
            if values[0] == '☑':
                selected_items.append(item)
        
        if not selected_items:
            messagebox.showwarning("提示", "请选择要删除的记录")
            return
        
        if messagebox.askyesno("确认", f"确定要删除选中的 {len(selected_items)} 条记录吗？"):
            deleted = 0
            for item in selected_items:
                self.history_tree.delete(item)
                deleted += 1
            
            messagebox.showinfo("完成", f"已删除 {deleted} 条记录")

    def export_logs(self):
        file_path = filedialog.asksaveasfilename(
            title="导出日志",
            defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx")],
            initialfile=f"update_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        if file_path:
            logs = self.log_manager.get_all_logs()
            success, msg = ExcelHandler.export_logs(logs, file_path)
            if success:
                self.log_manager.log_export("日志", file_path, len(logs), True)
                messagebox.showinfo("成功", msg)
            else:
                self.log_manager.log_export("日志", file_path, 0, False, str(msg))
                messagebox.showerror("导出失败", msg)

    def export_failed_records(self):
        file_path = filedialog.asksaveasfilename(
            title="导出失败记录",
            defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx")],
            initialfile=f"failed_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        if file_path:
            failed_records = self.log_manager.get_failed_records()
            if not failed_records:
                failed_records = []
            success, msg = ExcelHandler.export_failed_records(failed_records, file_path)
            if success:
                self.log_manager.log_export("失败记录", file_path, len(failed_records), True)
                messagebox.showinfo("成功", msg)
            else:
                self.log_manager.log_export("失败记录", file_path, 0, False, str(msg))
                messagebox.showerror("导出失败", msg)

    # ==================== 场景管理功能 ====================

    def refresh_template_list(self):
        """刷新场景下拉列表"""
        templates = self.config.get_templates()
        template_names = [t["name"] for t in templates]
        self.template_combo['values'] = template_names
        if template_names:
            self.template_combo.set('')
        self.add_log(f"已加载 {len(templates)} 个配置场景", "INFO")

    def on_template_selected(self, event=None):
        """场景选择事件处理"""
        template_name = self.template_var.get()
        if template_name:
            template = self.config.get_template_by_name(template_name)
            if template:
                self.add_log(f"已选择场景: {template_name}", "INFO")

    def load_template(self):
        """加载选中的场景"""
        template_name = self.template_var.get()
        if not template_name:
            messagebox.showwarning("提示", "请先选择一个场景")
            return
        
        template = self.config.get_template_by_name(template_name)
        if not template:
            messagebox.showerror("错误", f"场景 '{template_name}' 不存在")
            return
        
        # 应用场景配置
        self.schema_var.set(template.get("schema", "APPS"))
        self.temp_schema_var.set(template.get("temp_schema", "APPS"))
        self.target_table_var.set(template.get("target_table", ""))
        self.key_column_var.set(template.get("key_column", ""))
        
        # 设置连接
        if template.get("connection_name"):
            self.connection_var.set(template["connection_name"])
        
        # 设置更新列
        update_columns = template.get("update_columns", [])
        # 清空现有更新列
        for widget in self.update_column_widgets[1:]:
            widget.destroy()
        self.update_column_widgets = [self.first_update_entry]
        
        # 设置第一列
        if update_columns:
            self.first_update_entry.delete(0, tk.END)
            self.first_update_entry.insert(0, update_columns[0])
            # 添加其他列
            for col in update_columns[1:]:
                self.add_update_column_with_value(col)
        
        self.add_log(f"已加载场景: {template_name}", "SUCCESS")
        self.add_log(f"目标表模式: {template.get('schema', 'APPS')}, 临时表模式: {template.get('temp_schema', 'APPS')}", "INFO")
        messagebox.showinfo("成功", f"场景 '{template_name}' 已加载")

    def add_update_column_with_value(self, value):
        """添加更新列并设置值"""
        new_row = ttk.Frame(self.update_columns_frame)
        new_row.pack(fill=tk.X, pady=2)
        entry = ttk.Entry(new_row, font=(self.os_info["font_family"], 10), width=30)
        entry.insert(0, value)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        remove_btn = ttk.Button(new_row, text="➖", width=3, 
                                command=lambda: self.remove_update_column_with_row(new_row, entry), 
                                style="Action.TButton")
        remove_btn.pack(side=tk.LEFT, padx=(5, 0))
        self.update_column_widgets.append(entry)

    def remove_update_column_with_row(self, row, entry):
        """移除指定的更新列"""
        if entry in self.update_column_widgets and entry != self.first_update_entry:
            self.update_column_widgets.remove(entry)
            row.destroy()

    def save_as_template(self):
        """保存当前配置为场景"""
        # 获取当前配置
        connection_name = self.connection_var.get()
        target_table = self.target_table_var.get().strip()
        key_column = self.key_column_var.get().strip()
        schema = self.schema_var.get()
        update_columns = self.get_update_columns()
        
        if not target_table or not key_column:
            messagebox.showwarning("提示", "请先填写目标表名和唯一标识列")
            return
        
        # 弹出对话框输入场景名称
        dialog = tk.Toplevel(self.root)
        dialog.title("保存为场景")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 场景名称
        name_frame = ttk.Frame(dialog, padding="10")
        name_frame.pack(fill=tk.X)
        ttk.Label(name_frame, text="场景名称:", width=12).pack(side=tk.LEFT)
        name_var = tk.StringVar()
        name_entry = ttk.Entry(name_frame, textvariable=name_var, width=30)
        name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 场景描述
        desc_frame = ttk.Frame(dialog, padding="10")
        desc_frame.pack(fill=tk.X)
        ttk.Label(desc_frame, text="场景描述:", width=12).pack(side=tk.LEFT)
        desc_var = tk.StringVar()
        desc_entry = ttk.Entry(desc_frame, textvariable=desc_var, width=30)
        desc_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 按钮
        btn_frame = ttk.Frame(dialog, padding="10")
        btn_frame.pack(fill=tk.X)
        
        def do_save():
            name = name_var.get().strip()
            if not name:
                messagebox.showwarning("提示", "请输入场景名称")
                return
            
            if len(name) > 100:
                messagebox.showwarning("提示", "场景名称不能超过100个字符")
                return
            
            # 检查是否已存在
            existing = self.config.get_template_by_name(name)
            if existing:
                if not messagebox.askyesno("确认", f"场景 '{name}' 已存在，是否覆盖？"):
                    return
            
            # 创建场景
            success, msg = self.config.create_template_from_current(
                name=name,
                description=desc_var.get().strip(),
                connection_name=connection_name,
                target_table=target_table,
                key_column=key_column,
                update_columns=update_columns,
                schema=schema,
                temp_schema=self.temp_schema_var.get()
            )
            
            if success:
                self.refresh_template_list()
                self.template_var.set(name)
                self.add_log(f"已保存场景: {name}", "SUCCESS")
                messagebox.showinfo("成功", msg)
                dialog.destroy()
            else:
                messagebox.showwarning("提示", msg)
        
        save_btn = ttk.Button(btn_frame, text="保存", command=do_save, style="Primary.TButton")
        save_btn.pack(side=tk.LEFT, padx=(10, 0))
        cancel_btn = ttk.Button(btn_frame, text="取消", command=dialog.destroy, style="Action.TButton")
        cancel_btn.pack(side=tk.LEFT, padx=(5, 0))

    def delete_template(self):
        """删除选中的场景"""
        template_name = self.template_var.get()
        if not template_name:
            messagebox.showwarning("提示", "请先选择一个场景")
            return
        
        if messagebox.askyesno("确认", f"确定要删除场景 '{template_name}' 吗？"):
            self.config.delete_template(template_name)
            self.refresh_template_list()
            self.template_var.set('')
            self.add_log(f"已删除场景: {template_name}", "INFO")
            messagebox.showinfo("成功", f"场景 '{template_name}' 已删除")

    def on_closing(self):
        if self.db_connection.is_connected():
            self.db_connection.disconnect()
        self.root.destroy()


def main():
    """GUI 主入口，带错误处理。

    如果 GUI 初始化失败，弹出友好错误对话框而非静默退出。
    """
    import tkinter as tk
    from tkinter import messagebox
    import traceback

    try:
        root = tk.Tk()
        app = OracleBatchUpdaterGUI(root)
        root.mainloop()
    except SystemExit:
        raise
    except KeyboardInterrupt:
        pass
    except Exception as e:
        tb = traceback.format_exc()
        try:
            messagebox.showerror(
                "DBForge - 启动失败",
                f"程序启动时发生错误:\n\n"
                f"{type(e).__name__}: {str(e)}\n\n"
                f"请检查:\n"
                f"  1. Python 版本 >= 3.7\n"
                f"  2. 依赖已安装: pip install -r requirements.txt\n"
                f"  3. config.json 配置文件未损坏\n"
                f"  4. Oracle Instant Client 已正确安装\n\n"
                f"详细错误:\n{'─' * 50}\n{tb[-500:]}"
            )
        except Exception:
            print(f"FATAL: {tb}", file=__import__('sys').stderr)
        raise


if __name__ == "__main__":
    main()
