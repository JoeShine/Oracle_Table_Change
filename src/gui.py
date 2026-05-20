import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from pathlib import Path
from datetime import datetime
import threading
import os
from src.config_manager import ConfigManager
from src.db_connection import DBConnection
from src.excel_handler import ExcelHandler
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
        self.root.title("Oracle数据库批量更新工具")
        self.root.geometry("1000x750")
        self.root.resizable(True, True)
        self.root.minsize(800, 600)
        self.config = ConfigManager()
        self.log_manager = LogManager()
        self.db_connection = DBConnection()
        self.excel_data = None
        self.is_connected = False
        self.theme_manager = ThemeManager()
        self.setup_styles()
        self.create_widgets()
        self.load_last_config()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

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
        self.style.configure("Status.TLabel", font=("Microsoft YaHei", 10))

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
        content_frame = ttk.Frame(self.main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10), width=350)
        self.create_connection_panel(left_frame)
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.create_update_panel(right_frame)
        self.create_log_panel(self.main_frame)

    def create_header(self):
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 5))
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(side=tk.LEFT)
        title_label = ttk.Label(title_frame, text="📦 Oracle批量更新工具", style="Title.TLabel")
        title_label.pack()
        subtitle_label = ttk.Label(title_frame, text="Oracle Database Batch Updater", font=("Microsoft YaHei", 10), foreground="#6c757d")
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

    def create_connection_panel(self, parent):
        panel = ttk.LabelFrame(parent, text="数据库连接", padding="15", style="Card.TFrame")
        panel.pack(fill=tk.BOTH, expand=True)
        ttk.Label(panel, text="选择连接:", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 8))
        connection_frame = ttk.Frame(panel)
        connection_frame.pack(fill=tk.X, pady=(0, 10))
        self.connection_var = tk.StringVar()
        self.connection_combo = ttk.Combobox(connection_frame, textvariable=self.connection_var, state="readonly", font=("Microsoft YaHei", 10))
        self.connection_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.connection_combo.bind("<<ComboboxSelected>>", self.on_connection_selected)
        test_btn = ttk.Button(connection_frame, text="测试连接", command=self.test_connection, style="Action.TButton")
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

    def create_update_panel(self, parent):
        config_panel = ttk.LabelFrame(parent, text="更新配置", padding="15", style="Card.TFrame")
        config_panel.pack(fill=tk.X, pady=(0, 10))
        row1 = ttk.Frame(config_panel)
        row1.pack(fill=tk.X, pady=6)
        ttk.Label(row1, text="目标表名:", width=12, font=("Microsoft YaHei", 10)).pack(side=tk.LEFT)
        self.target_table_var = tk.StringVar()
        target_table_entry = ttk.Entry(row1, textvariable=self.target_table_var, font=("Microsoft YaHei", 10), width=30)
        target_table_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        row2 = ttk.Frame(config_panel)
        row2.pack(fill=tk.X, pady=6)
        ttk.Label(row2, text="唯一标识列:", width=12, font=("Microsoft YaHei", 10)).pack(side=tk.LEFT)
        self.key_column_var = tk.StringVar()
        key_column_entry = ttk.Entry(row2, textvariable=self.key_column_var, font=("Microsoft YaHei", 10), width=30)
        key_column_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        row3 = ttk.Frame(config_panel)
        row3.pack(fill=tk.X, pady=6)
        ttk.Label(row3, text="待修改列:", width=12, font=("Microsoft YaHei", 10)).pack(side=tk.LEFT)
        self.update_column_var = tk.StringVar()
        update_column_entry = ttk.Entry(row3, textvariable=self.update_column_var, font=("Microsoft YaHei", 10), width=30)
        update_column_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        excel_frame = ttk.Frame(config_panel)
        excel_frame.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(excel_frame, text="Excel文件:", width=12, font=("Microsoft YaHei", 10)).pack(side=tk.LEFT)
        self.excel_path_var = tk.StringVar()
        excel_entry = ttk.Entry(excel_frame, textvariable=self.excel_path_var, state="readonly", font=("Microsoft YaHei", 10))
        excel_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        browse_btn = ttk.Button(excel_frame, text="📁 浏览", command=self.browse_excel, style="Action.TButton")
        browse_btn.pack(side=tk.LEFT, padx=(5, 0))
        preview_btn = ttk.Button(excel_frame, text="👁 预览", command=self.preview_excel, style="Action.TButton")
        preview_btn.pack(side=tk.LEFT, padx=(3, 0))
        preview_panel = ttk.LabelFrame(parent, text="Excel数据预览", padding="12", style="Card.TFrame")
        preview_panel.pack(fill=tk.BOTH, expand=True)
        self.preview_tree = ttk.Treeview(preview_panel, show="headings", height=7)
        self.preview_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        preview_scroll_y = ttk.Scrollbar(preview_panel, orient=tk.VERTICAL, command=self.preview_tree.yview)
        preview_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.preview_tree.configure(yscrollcommand=preview_scroll_y.set)
        preview_scroll_x = ttk.Scrollbar(parent, orient=tk.HORIZONTAL, command=self.preview_tree.xview)
        preview_scroll_x.pack(fill=tk.X)
        self.preview_tree.configure(xscrollcommand=preview_scroll_x.set)
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        self.start_btn = ttk.Button(btn_frame, text="🚀 开始更新", style="Primary.TButton", command=self.start_update)
        self.start_btn.pack(side=tk.LEFT)
        cancel_btn = ttk.Button(btn_frame, text="✖️ 取消", command=self.cancel_operation, style="Action.TButton")
        cancel_btn.pack(side=tk.LEFT, padx=(10, 0))

    def create_log_panel(self, parent):
        log_panel = ttk.LabelFrame(parent, text="📜 操作日志", padding="12", style="Card.TFrame")
        log_panel.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        self.log_text = scrolledtext.ScrolledText(log_panel, height=12, wrap=tk.WORD, font=("Consolas", 9), relief="flat")
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
            self.update_column_var.set(last_used['update_column'])

    def save_current_config(self):
        self.config.set_last_used(
            connection_name=self.connection_var.get(),
            target_table=self.target_table_var.get(),
            key_column=self.key_column_var.get(),
            update_column=self.update_column_var.get()
        )

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
        self.add_log("正在测试连接...")
        success, msg = self.db_connection.connect(
            host=conn_info['host'],
            port=conn_info['port'],
            service=conn_info['service'],
            username=conn_info['username'],
            password=conn_info['password']
        )
        if success:
            self.add_log(msg, "SUCCESS")
            self.is_connected = True
            self.connection_status_label.config(text=f"✅ 已连接: {conn_info['username']}@{conn_info['host']}", foreground="#28a745")
            messagebox.showinfo("成功", msg)
        else:
            self.add_log(msg, "ERROR")
            self.is_connected = False
            self.connection_status_label.config(text="❌ 连接失败", foreground="#dc3545")
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
            self.excel_path_var.set(file_path)
            self.preview_excel()

    def preview_excel(self):
        file_path = self.excel_path_var.get()
        if not file_path:
            return
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        success, msg, data = ExcelHandler.get_preview_data(file_path)
        if success:
            self.preview_tree['columns'] = data['headers'][:2]
            for header in data['headers'][:2]:
                self.preview_tree.heading(header, text=header)
                self.preview_tree.column(header, width=200)
            for row in data['rows']:
                self.preview_tree.insert('', tk.END, values=row[:2])
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

    def start_update(self):
        if not self.is_connected:
            messagebox.showwarning("提示", "请先连接数据库")
            return
        target_table = self.target_table_var.get().strip()
        key_column = self.key_column_var.get().strip()
        update_column = self.update_column_var.get().strip()
        excel_path = self.excel_path_var.get().strip()
        if not all([target_table, key_column, update_column, excel_path]):
            messagebox.showwarning("提示", "请填写所有必填字段")
            return
        self.add_log("开始数据更新操作", "HEADING")
        threading.Thread(target=self._run_update, args=(target_table, key_column, update_column, excel_path), daemon=True).start()

    def _run_update(self, target_table, key_column, update_column, excel_path):
        try:
            self.save_current_config()
            self.log_manager.clear_failed_records()
            self.start_btn.config(state=tk.DISABLED)
            self.add_log(f"目标表: {target_table}")
            self.add_log(f"唯一标识列: {key_column}")
            self.add_log(f"待修改列: {update_column}")
            self.add_log("正在验证Excel文件...")
            valid, msg, data_rows = ExcelHandler.validate_excel_structure(excel_path)
            if not valid:
                self.add_log(msg, "ERROR")
                messagebox.showerror("验证失败", msg)
                self.start_btn.config(state=tk.NORMAL)
                return
            self.add_log(msg, "SUCCESS")
            dup_valid, duplicates = ExcelHandler.check_duplicate_keys(data_rows)
            if not dup_valid:
                error_msg = f"Excel中唯一标识列存在重复值: {duplicates[:5]}"
                self.add_log(error_msg, "ERROR")
                messagebox.showerror("数据错误", error_msg)
                self.start_btn.config(state=tk.NORMAL)
                return
            updater = DataUpdater(self.db_connection, self.log_manager)
            schema = "APPS"
            self.add_log("正在验证表和列...")
            valid, msg = updater.validate_table_and_columns(schema, target_table, key_column, update_column)
            if not valid:
                self.add_log(msg, "ERROR")
                messagebox.showerror("验证失败", msg)
                self.start_btn.config(state=tk.NORMAL)
                return
            self.add_log("表和列验证通过", "SUCCESS")
            self.add_log("正在创建备份...")
            success, msg = updater.backup_table(schema, target_table)
            if not success:
                self.add_log(f"备份失败: {msg}", "ERROR")
                messagebox.showerror("备份失败", msg)
                self.start_btn.config(state=tk.NORMAL)
                return
            self.add_log(f"备份表已创建: {updater.backup_table_name}", "SUCCESS")
            self.add_log("正在创建临时表...")
            success, msg = updater.create_temp_table(schema, target_table, key_column, update_column)
            if not success:
                self.add_log(f"创建临时表失败: {msg}", "ERROR")
                messagebox.showerror("创建临时表失败", msg)
                self.start_btn.config(state=tk.NORMAL)
                return
            self.add_log(f"临时表: {updater.temp_table_name}", "SUCCESS")
            self.add_log("正在导入Excel数据...")
            success, error, count = updater.import_excel_data(schema, key_column, update_column, data_rows)
            if not success:
                self.add_log(f"导入失败: {error}", "ERROR")
                messagebox.showerror("导入失败", error)
                self.start_btn.config(state=tk.NORMAL)
                return
            self.add_log(f"成功导入 {count} 条数据", "SUCCESS")
            self.add_log("正在执行数据更新...")
            success_count, fail_count, failed_records = updater.execute_update(
                schema, target_table, key_column, update_column
            )
            self.add_log(f"更新完成 - 成功: {success_count}, 失败: {fail_count}")
            updater.cleanup_temp_table(schema)
            if failed_records:
                self.show_failure_dialog(failed_records)
            else:
                messagebox.showinfo("完成", f"更新完成！\n成功: {success_count}\n失败: {fail_count}")
            self.start_btn.config(state=tk.NORMAL)
        except Exception as e:
            self.add_log(f"执行出错: {str(e)}", "ERROR")
            messagebox.showerror("错误", str(e))
            self.start_btn.config(state=tk.NORMAL)

    def show_failure_dialog(self, failed_records):
        dialog = tk.Toplevel(self.root)
        dialog.title("更新失败记录")
        dialog.geometry("600x450")
        dialog.transient(self.root)
        dialog.resizable(True, True)
        _, theme = self.theme_manager.get_theme()
        dialog.configure(bg=theme["bg"])
        tree_frame = ttk.Frame(dialog, padding="15")
        tree_frame.pack(fill=tk.BOTH, expand=True)
        columns = ("key_value", "update_value", "reason", "timestamp")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=12)
        tree.heading("key_value", text="唯一标识", anchor=tk.CENTER)
        tree.heading("update_value", text="待修改数据", anchor=tk.CENTER)
        tree.heading("reason", text="失败原因", anchor=tk.CENTER)
        tree.heading("timestamp", text="时间", anchor=tk.CENTER)
        tree.column("key_value", width=120, anchor=tk.CENTER)
        tree.column("update_value", width=180, anchor=tk.CENTER)
        tree.column("reason", width=200, anchor=tk.CENTER)
        tree.column("timestamp", width=120, anchor=tk.CENTER)
        for record in failed_records:
            tree.insert('', tk.END, values=(record["key_value"], record["update_value"], record["reason"], record["timestamp"]))
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

    def cancel_operation(self):
        if messagebox.askyesno("确认", "确定要退出吗？"):
            self.root.destroy()

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
                messagebox.showinfo("成功", msg)
            else:
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
                messagebox.showinfo("成功", msg)
            else:
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
