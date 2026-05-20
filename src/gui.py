import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from pathlib import Path
from datetime import datetime
import threading
import os
from src.config_manager import ConfigManager
from src.db_connection import DBConnection
from src.excel_handler import ExcelHandler, MAX_FILE_SIZE, MAX_ROWS, MAX_PREVIEW_ROWS
from src.data_updater import DataUpdater
from src.logger import LogManager


class ThemeManager:
    LIGHT_THEME = {
        "bg": "#f8f9fa",
        "fg": "#212529",
        "primary": "#4facfe",
        "primary_dark": "#00f2fe",
        "secondary": "#6c757d",
        "success": "#28a745",
        "error": "#dc3545",
        "warning": "#ffc107",
        "info": "#17a2b8",
        "card_bg": "#ffffff",
        "card_border": "#dee2e6",
        "text_muted": "#6c757d",
        "text_heading": "#1a1a1a",
        "button_bg": "#4facfe",
        "button_fg": "#ffffff",
        "entry_bg": "#ffffff",
        "entry_border": "#ced4da",
        "tree_bg": "#ffffff",
        "tree_alt": "#f2f2f2",
        "log_bg": "#ffffff",
        "scrollbar_bg": "#dee2e6",
        "status_bg": "#f0f0f0",
    }

    DARK_THEME = {
        "bg": "#1a1a2e",
        "fg": "#e4e4e7",
        "primary": "#7c3aed",
        "primary_dark": "#5b21b6",
        "secondary": "#71717a",
        "success": "#22c55e",
        "error": "#ef4444",
        "warning": "#f59e0b",
        "info": "#06b6d4",
        "card_bg": "#252542",
        "card_border": "#3f3f68",
        "text_muted": "#a1a1aa",
        "text_heading": "#fafafa",
        "button_bg": "#7c3aed",
        "button_fg": "#ffffff",
        "entry_bg": "#252542",
        "entry_border": "#4f4f7a",
        "tree_bg": "#252542",
        "tree_alt": "#32325a",
        "log_bg": "#1e1e3f",
        "scrollbar_bg": "#4f4f7a",
        "status_bg": "#16213e",
    }

    def __init__(self):
        self.current_theme = "light"
        self.theme = self.LIGHT_THEME

    def toggle_theme(self):
        if self.current_theme == "light":
            self.current_theme = "dark"
            self.theme = self.DARK_THEME
        else:
            self.current_theme = "light"
            self.theme = self.LIGHT_THEME
        return self.current_theme, self.theme

    def get_theme(self):
        return self.current_theme, self.theme


class OracleBatchUpdaterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Oracle数据批量修改工具")
        self.root.geometry("1000x800")
        self.root.resizable(True, True)
        self.root.minsize(900, 700)
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
        _, theme = self.theme_manager.get_theme()
        self.style.configure("Title.TLabel", font=("Microsoft YaHei", 16, "bold"), foreground=theme["text_heading"])
        self.style.configure("Header.TLabel", font=("Microsoft YaHei", 11, "bold"), foreground=theme["text_heading"])
        self.style.configure("Action.TButton", font=("Microsoft YaHei", 10), padding=6)
        self.style.configure("Primary.TButton", font=("Microsoft YaHei", 11, "bold"), padding=8)
        self.style.map("Primary.TButton",
                       background=[('active', theme["primary_dark"])],
                       foreground=[('active', 'white')])
        self.style.configure("Card.TFrame", background=theme["card_bg"], borderwidth=1, relief="solid")
        self.style.configure("Status.TLabel", font=("Microsoft YaHei", 9))
        self.style.configure("TNotebook", background=theme["bg"], borderwidth=0)
        self.style.configure("TNotebook.Tab", padding=[20, 8], font=("Microsoft YaHei", 10))

    def bind_shortcuts(self):
        self.root.bind('<Control-s>', lambda e: self.save_config())
        self.root.bind('<Control-S>', lambda e: self.save_config())

    def apply_theme(self):
        _, theme = self.theme_manager.get_theme()
        self.root.configure(bg=theme["bg"])
        for widget in self.root.winfo_children():
            self.apply_theme_recursive(widget, theme)

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
        self.main_frame = ttk.Frame(self.root, padding="15")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.create_header()
        
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.create_config_tab()
        self.create_log_tab()
        self.create_connection_tab()
        self.create_history_tab()
        
        self.create_status_bar()

    def create_header(self):
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 5))
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(side=tk.LEFT)
        title_label = ttk.Label(title_frame, text="📦 Oracle数据批量修改工具", style="Title.TLabel")
        title_label.pack()
        subtitle_label = ttk.Label(title_frame, text="Oracle Data Batch Modifier", font=("Microsoft YaHei", 10), foreground="#6c757d")
        subtitle_label.pack(pady=(2, 0))
        control_frame = ttk.Frame(header_frame)
        control_frame.pack(side=tk.RIGHT)
        self.theme_btn = ttk.Button(control_frame, text="🌙 深色模式", command=self.toggle_theme, style="Action.TButton")
        self.theme_btn.pack(side=tk.RIGHT)
        minimize_btn = ttk.Button(control_frame, text="▁", width=3, command=self.root.iconify, style="Action.TButton")
        minimize_btn.pack(side=tk.RIGHT, padx=(5, 0))
        maximize_btn = ttk.Button(control_frame, text="⬜", width=3, command=self.toggle_maximize, style="Action.TButton")
        maximize_btn.pack(side=tk.RIGHT, padx=(5, 5))

    def toggle_maximize(self):
        if self.root.state() == "zoomed":
            self.root.state("normal")
        else:
            self.root.state("zoomed")

    def toggle_theme(self):
        theme_name, _ = self.theme_manager.toggle_theme()
        self.update_styles()
        self.apply_theme()
        self.update_treeview_style()
        self.update_log_style()
        self.update_history_tree_style()
        if theme_name == "dark":
            self.theme_btn.config(text="☀️ 浅色模式")
        else:
            self.theme_btn.config(text="🌙 深色模式")

    def update_treeview_style(self):
        _, theme = self.theme_manager.get_theme()
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
        _, theme = self.theme_manager.get_theme()
        if hasattr(self, 'log_text'):
            self.log_text.configure(bg=theme["log_bg"], fg=theme["fg"])
            self.log_text.tag_config("INFO", foreground=theme["fg"])
            self.log_text.tag_config("SUCCESS", foreground=theme["success"])
            self.log_text.tag_config("ERROR", foreground=theme["error"])
            self.log_text.tag_config("WARNING", foreground=theme["warning"])

    def update_history_tree_style(self):
        _, theme = self.theme_manager.get_theme()
        if hasattr(self, 'history_tree'):
            self.style.configure("History.Treeview",
                                background=theme["tree_bg"],
                                foreground=theme["fg"],
                                fieldbackground=theme["tree_bg"])
            self.history_tree.update()

    def create_config_tab(self):
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="📋 当前配置")
        
        config_panel = ttk.LabelFrame(tab, text="当前配置", padding="15", style="Card.TFrame")
        config_panel.pack(fill=tk.X, pady=(0, 10))
        
        row0 = ttk.Frame(config_panel)
        row0.pack(fill=tk.X, pady=6)
        ttk.Label(row0, text="数据库模式:", width=14, font=("Microsoft YaHei", 10)).pack(side=tk.LEFT)
        self.schema_var = tk.StringVar(value="APPS")
        schema_combo = ttk.Combobox(row0, textvariable=self.schema_var, 
                                     values=["APPS", "SYS", "SYSTEM"], state="readonly", font=("Microsoft YaHei", 10))
        schema_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
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
        
        hint_label = ttk.Label(config_panel, text=f"支持 .xlsx/.xls 文件，最大10MB，最多10万行", 
                               font=("Microsoft YaHei", 9), foreground="#6c757d")
        hint_label.pack(anchor=tk.W, pady=(5, 0))
        
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
        self.start_btn = ttk.Button(btn_frame, text="✅ 确认", style="Primary.TButton", command=self.confirm_update)
        self.start_btn.pack(side=tk.LEFT)
        clear_btn = ttk.Button(btn_frame, text="🗑 清空", command=self.clear_form, style="Action.TButton")
        clear_btn.pack(side=tk.LEFT, padx=(10, 0))

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
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="📜 操作日志")
        
        log_panel = ttk.LabelFrame(tab, text="操作日志", padding="12", style="Card.TFrame")
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

    def create_connection_tab(self):
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="🔌 数据库连接")
        
        panel = ttk.LabelFrame(tab, text="数据库连接配置", padding="15", style="Card.TFrame")
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

    def create_history_tab(self):
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="📊 历史记录")
        
        panel = ttk.LabelFrame(tab, text="历史导入记录", padding="15", style="Card.TFrame")
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

    def create_status_bar(self):
        self.status_bar = ttk.Frame(self.main_frame, padding="8")
        self.status_bar.pack(fill=tk.X, pady=(5, 0))
        
        _, theme = self.theme_manager.get_theme()
        self.status_bar.configure(style="StatusBar.TFrame")
        self.style.configure("StatusBar.TFrame", background=theme["status_bg"])
        
        self.conn_indicator = tk.Canvas(self.status_bar, width=10, height=10, bg="#dc3545", highlightthickness=0)
        self.conn_indicator.pack(side=tk.LEFT, padx=(0, 5))
        self.conn_indicator.create_oval(2, 2, 8, 8, fill="#dc3545", outline="")
        
        self.conn_status_label = ttk.Label(self.status_bar, text="未连接", style="Status.TLabel")
        self.conn_status_label.pack(side=tk.LEFT)
        
        ttk.Separator(self.status_bar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=15)
        
        self.db_name_label = ttk.Label(self.status_bar, text="数据库: -", style="Status.TLabel")
        self.db_name_label.pack(side=tk.LEFT)
        
        ttk.Separator(self.status_bar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=15)
        
        self.db_user_label = ttk.Label(self.status_bar, text="用户: -", style="Status.TLabel")
        self.db_user_label.pack(side=tk.LEFT)
        
        ttk.Separator(self.status_bar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=15)
        
        self.operation_status_label = ttk.Label(self.status_bar, text="状态: 就绪", style="Status.TLabel")
        self.operation_status_label.pack(side=tk.LEFT)

    def update_status_bar(self, connected=False, db_name="-", db_user="-", operation="就绪"):
        if connected:
            self.conn_indicator.itemconfig(self.conn_indicator.create_oval(2, 2, 8, 8), fill="#28a745")
            self.conn_status_label.config(text="已连接")
        else:
            self.conn_indicator.itemconfig(self.conn_indicator.create_oval(2, 2, 8, 8), fill="#dc3545")
            self.conn_status_label.config(text="未连接")
        
        self.db_name_label.config(text=f"数据库: {db_name}")
        self.db_user_label.config(text=f"用户: {db_user}")
        self.operation_status_label.config(text=f"状态: {operation}")

    def clear_logs(self):
        self.log_text.delete(1.0, tk.END)
        self.log_manager = LogManager()

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

    def save_config(self):
        self.config.set_last_used(
            connection_name=self.connection_var.get(),
            target_table=self.target_table_var.get(),
            key_column=self.key_column_var.get(),
            update_column=self.first_update_entry.get(),
            schema=self.schema_var.get()
        )
        self.add_log("配置已保存 (Ctrl+S)", "SUCCESS")

    def on_connection_selected(self, event=None):
        pass

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
        self.update_status_bar(connected=False, operation="正在连接...")
        
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
            self.update_status_bar(connected=True, db_name=conn_info['service'], 
                                   db_user=conn_info['username'], operation="已连接")
            self.log_manager.log_connection(conn_info['host'], conn_info['service'], 
                                           conn_info['username'], True)
            self.add_log(msg, "SUCCESS")
            messagebox.showinfo("成功", msg)
        else:
            self.is_connected = False
            self.connection_status_label.config(text="❌ 连接失败", foreground="#dc3545")
            self.update_status_bar(connected=False, operation="连接失败")
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
        _, theme = self.theme_manager.get_theme()
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
        
        _, theme = self.theme_manager.get_theme()
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
        
        self.current_op_label = ttk.Label(content_frame, text="正在连接数据库...", font=("Microsoft YaHei", 9), foreground="#6c757d")
        self.current_op_label.pack(pady=(10, 0))

    def close_progress_window(self):
        if self.progress_window:
            self.progress_window.destroy()
            self.progress_window = None

    def update_progress_gui(self, current, total, percentage, operation):
        if self.progress_window:
            self.progress_var.set(percentage)
            self.progress_label.config(text=f"处理进度: {current}/{total} ({percentage}%)")
            self.current_op_label.config(text=operation)

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

    def confirm_update(self):
        if not self.is_connected:
            messagebox.showwarning("提示", "请先连接数据库")
            self.notebook.select(2)
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
        self.notebook.select(1)
        threading.Thread(target=self._run_update, daemon=True).start()

    def _run_update(self):
        try:
            self.save_config()
            self.log_manager.clear_failed_records()
            self.root.after(0, lambda: self.start_btn.config(state=tk.DISABLED))
            self.root.after(0, lambda: self.update_status_bar(connected=True, operation="正在验证..."))
            
            self.add_log("开始数据更新操作", "HEADING")
            self.add_log(f"目标表: {self.target_table_var.get()}")
            self.add_log(f"唯一标识列: {self.key_column_var.get()}")
            self.add_log(f"待修改列: {', '.join(self.get_update_columns())}")
            
            target_table = self.target_table_var.get().strip()
            key_column = self.key_column_var.get().strip()
            update_columns = self.get_update_columns()
            excel_path = self.excel_path_var.get().strip()
            schema = self.schema_var.get()
            
            self.root.after(0, lambda: self.update_progress_gui(0, 100, 10, "正在验证Excel文件..."))
            self.add_log("正在验证Excel文件...")
            valid, msg, data_rows = ExcelHandler.validate_multi_column_structure(excel_path, update_columns)
            if not valid:
                self.add_log(msg, "ERROR")
                self.root.after(0, lambda: messagebox.showerror("验证失败", msg))
                self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
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
                self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
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
                self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.close_progress_window())
                self.root.after(0, lambda: self.update_status_bar(connected=True, operation="备份失败"))
                return
            self.add_log(f"备份表已创建: {updater.backup_table_name}", "SUCCESS")
            self.root.after(0, lambda: self.update_step_gui(0, "done"))
            
            self.root.after(0, lambda: self.update_step_gui(1, "active"))
            self.root.after(0, lambda: self.update_progress_gui(20, 100, 30, "正在创建临时表..."))
            self.add_log("正在创建临时表...")
            success, msg = updater.create_temp_table_multi_column(schema, target_table, key_column, update_columns)
            if not success:
                self.add_log(f"创建临时表失败: {msg}", "ERROR")
                updater.cleanup_on_failure(schema)
                self.root.after(0, lambda: messagebox.showerror("创建临时表失败", msg))
                self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.close_progress_window())
                self.root.after(0, lambda: self.update_status_bar(connected=True, operation="创建临时表失败"))
                return
            self.add_log(f"临时表: {updater.temp_table_name}", "SUCCESS")
            
            def progress_callback(current, total, percentage, operation):
                adjusted_percentage = 30 + int(percentage * 0.2)
                self.root.after(0, lambda: self.update_progress_gui(current, total, adjusted_percentage, operation))
            
            updater.set_progress_callback(progress_callback)
            
            self.root.after(0, lambda: self.update_progress_gui(30, 100, 35, "正在导入Excel数据..."))
            self.add_log("正在导入Excel数据...")
            success, error, count = updater.import_excel_data_multi_column(schema, key_column, update_columns, data_rows)
            if not success:
                self.add_log(f"导入失败: {error}", "ERROR")
                updater.cleanup_on_failure(schema)
                self.root.after(0, lambda: messagebox.showerror("导入失败", error))
                self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.close_progress_window())
                self.root.after(0, lambda: self.update_status_bar(connected=True, operation="导入失败"))
                return
            self.add_log(f"成功导入 {count} 条数据", "SUCCESS")
            self.root.after(0, lambda: self.update_step_gui(1, "done"))
            
            self.root.after(0, lambda: self.update_step_gui(2, "active"))
            self.root.after(0, lambda: self.update_progress_gui(50, 100, 55, "正在执行数据更新..."))
            self.add_log("正在执行数据更新...")
            
            def update_progress_callback(current, total, percentage, operation):
                adjusted_percentage = 55 + int(percentage * 0.4)
                self.root.after(0, lambda: self.update_progress_gui(current, total, adjusted_percentage, operation))
            
            updater.set_progress_callback(update_progress_callback)
            
            success_count, fail_count, failed_records = updater.execute_multi_column_update(
                schema, target_table, key_column, update_columns
            )
            
            self.root.after(0, lambda: self.update_step_gui(2, "done"))
            self.root.after(0, lambda: self.update_progress_gui(100, 100, 95, "正在清理临时表..."))
            
            updater.cleanup_temp_table(schema)
            self.add_log(f"临时表已清理", "SUCCESS")
            
            self.root.after(0, lambda: self.update_progress_gui(100, 100, 100, "更新完成"))
            self.add_log(f"更新完成 - 成功: {success_count}, 失败: {fail_count}")
            
            self.log_manager.log_update(
                schema=schema,
                table=target_table,
                key_column=key_column,
                update_columns=update_columns,
                total_count=success_count + fail_count,
                success_count=success_count,
                fail_count=fail_count,
                success=(fail_count == 0),
                backup_table=updater.backup_table_name
            )
            
            if failed_records:
                self.root.after(0, lambda: self.update_status_bar(connected=True, operation=f"部分失败({fail_count}条)"))
                self.root.after(0, lambda: self.show_failure_dialog(failed_records, updater.backup_table_name))
            else:
                self.root.after(0, lambda: self.update_status_bar(connected=True, operation="更新成功"))
                self.root.after(0, lambda: messagebox.showinfo("完成", f"更新完成！\n成功: {success_count}\n失败: {fail_count}"))
            
            self.root.after(0, lambda: self.refresh_history())
            self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.close_progress_window())
            
        except Exception as e:
            self.add_log(f"执行出错: {str(e)}", "ERROR")
            self.root.after(0, lambda: messagebox.showerror("错误", str(e)))
            self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.close_progress_window())
            self.root.after(0, lambda: self.update_status_bar(connected=True, operation="执行出错"))

    def show_failure_dialog(self, failed_records, backup_table):
        dialog = tk.Toplevel(self.root)
        dialog.title("更新失败记录")
        dialog.geometry("650x500")
        dialog.transient(self.root)
        dialog.resizable(True, True)
        _, theme = self.theme_manager.get_theme()
        dialog.configure(bg=theme["bg"])
        
        info_label = tk.Label(dialog, text="⚠️ 更新完成但存在失败记录。目标表数据未更新，已回滚到初始状态。",
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

    def clear_form(self):
        self.schema_var.set("APPS")
        self.target_table_var.set("")
        self.key_column_var.set("")
        self.first_update_entry.delete(0, tk.END)
        
        for widget in self.update_column_widgets[1:]:
            if widget.winfo_exists():
                widget.destroy()
        self.update_column_widgets = [self.first_update_entry]
        
        self.excel_path_var.set("")
        
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

    def on_closing(self):
        if self.db_connection.is_connected():
            self.db_connection.disconnect()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = OracleBatchUpdaterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
