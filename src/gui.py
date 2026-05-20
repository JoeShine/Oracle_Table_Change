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


class OracleBatchUpdaterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Oracle数据库批量更新工具")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        self.config = ConfigManager()
        self.log_manager = LogManager()
        self.db_connection = DBConnection()
        self.excel_data = None
        self.is_connected = False
        self.setup_styles()
        self.create_widgets()
        self.load_last_config()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Title.TLabel", font=("Microsoft YaHei", 14, "bold"))
        style.configure("Header.TLabel", font=("Microsoft YaHei", 10, "bold"))
        style.configure("Action.TButton", font=("Microsoft YaHei", 10))
        style.configure("Primary.TButton", font=("Microsoft YaHei", 10, "bold"))

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        title_label = ttk.Label(main_frame, text="Oracle数据库批量更新工具", style="Title.TLabel")
        title_label.pack(pady=(0, 10))
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        left_frame = ttk.LabelFrame(content_frame, text="数据库连接配置", padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5))
        self.create_connection_panel(left_frame)
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.create_update_panel(right_frame)
        log_frame = ttk.LabelFrame(main_frame, text="操作日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        self.create_log_panel(log_frame)

    def create_connection_panel(self, parent):
        ttk.Label(parent, text="选择数据库连接:").pack(anchor=tk.W)
        connection_frame = ttk.Frame(parent)
        connection_frame.pack(fill=tk.X, pady=(0, 5))
        self.connection_var = tk.StringVar()
        self.connection_combo = ttk.Combobox(connection_frame, textvariable=self.connection_var, state="readonly")
        self.connection_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.connection_combo.bind("<<ComboboxSelected>>", self.on_connection_selected)
        test_btn = ttk.Button(connection_frame, text="测试连接", command=self.test_connection)
        test_btn.pack(side=tk.LEFT, padx=(5, 0))
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        add_btn = ttk.Button(btn_frame, text="添加连接", command=self.open_add_connection_dialog)
        add_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))
        delete_btn = ttk.Button(btn_frame, text="删除连接", command=self.delete_connection)
        delete_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2, 0))
        self.connection_status_label = ttk.Label(parent, text="未连接", foreground="gray")
        self.connection_status_label.pack(anchor=tk.W)
        self.update_connection_list()

    def create_update_panel(self, parent):
        config_frame = ttk.LabelFrame(parent, text="更新配置", padding="10")
        config_frame.pack(fill=tk.X, pady=(0, 10))
        row1 = ttk.Frame(config_frame)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="目标表名:").pack(side=tk.LEFT, width=80)
        self.target_table_var = tk.StringVar()
        target_table_entry = ttk.Entry(row1, textvariable=self.target_table_var)
        target_table_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        row2 = ttk.Frame(config_frame)
        row2.pack(fill=tk.X, pady=2)
        ttk.Label(row2, text="唯一标识列:").pack(side=tk.LEFT, width=80)
        self.key_column_var = tk.StringVar()
        key_column_entry = ttk.Entry(row2, textvariable=self.key_column_var)
        key_column_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        row3 = ttk.Frame(config_frame)
        row3.pack(fill=tk.X, pady=2)
        ttk.Label(row3, text="待修改列:").pack(side=tk.LEFT, width=80)
        self.update_column_var = tk.StringVar()
        update_column_entry = ttk.Entry(row3, textvariable=self.update_column_var)
        update_column_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        excel_frame = ttk.Frame(config_frame)
        excel_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Label(excel_frame, text="Excel文件:").pack(side=tk.LEFT, width=80)
        self.excel_path_var = tk.StringVar()
        excel_entry = ttk.Entry(excel_frame, textvariable=self.excel_path_var, state="readonly")
        excel_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        browse_btn = ttk.Button(excel_frame, text="浏览", command=self.browse_excel)
        browse_btn.pack(side=tk.LEFT, padx=(5, 0))
        preview_btn = ttk.Button(excel_frame, text="预览", command=self.preview_excel)
        preview_btn.pack(side=tk.LEFT, padx=(2, 0))
        self.preview_frame = ttk.LabelFrame(parent, text="Excel数据预览", padding="5")
        self.preview_frame.pack(fill=tk.BOTH, expand=True)
        self.preview_tree = ttk.Treeview(self.preview_frame, show="headings", height=6)
        self.preview_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        preview_scroll_y = ttk.Scrollbar(self.preview_frame, orient=tk.VERTICAL, command=self.preview_tree.yview)
        preview_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.preview_tree.configure(yscrollcommand=preview_scroll_y.set)
        preview_scroll_x = ttk.Scrollbar(parent, orient=tk.HORIZONTAL, command=self.preview_tree.xview)
        preview_scroll_x.pack(fill=tk.X)
        self.preview_tree.configure(xscrollcommand=preview_scroll_x.set)
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        self.start_btn = ttk.Button(btn_frame, text="开始更新", style="Primary.TButton", command=self.start_update)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))
        cancel_btn = ttk.Button(btn_frame, text="取消", command=self.cancel_operation)
        cancel_btn.pack(side=tk.LEFT)

    def create_log_panel(self, parent):
        self.log_text = scrolledtext.ScrolledText(parent, height=10, wrap=tk.WORD, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.tag_config("INFO", foreground="black")
        self.log_text.tag_config("SUCCESS", foreground="green")
        self.log_text.tag_config("ERROR", foreground="red")
        self.log_text.tag_config("WARNING", foreground="orange")
        export_frame = ttk.Frame(parent)
        export_frame.pack(fill=tk.X, pady=(5, 0))
        export_log_btn = ttk.Button(export_frame, text="导出日志", command=self.export_logs)
        export_log_btn.pack(side=tk.LEFT, padx=(0, 5))
        export_fail_btn = ttk.Button(export_frame, text="导出失败记录", command=self.export_failed_records)
        export_fail_btn.pack(side=tk.LEFT)

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
            self.connection_status_label.config(text=f"已连接: {conn_info['username']}@{conn_info['host']}", foreground="green")
            messagebox.showinfo("成功", msg)
        else:
            self.add_log(msg, "ERROR")
            self.is_connected = False
            self.connection_status_label.config(text="连接失败", foreground="red")
            messagebox.showerror("连接失败", msg)

    def open_add_connection_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("添加数据库连接")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        ttk.Label(dialog, text="连接名称:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        name_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=name_var, width=30).grid(row=0, column=1, padx=10, pady=5)
        ttk.Label(dialog, text="主机地址:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        host_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=host_var, width=30).grid(row=1, column=1, padx=10, pady=5)
        ttk.Label(dialog, text="端口:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        port_var = tk.IntVar(value=1521)
        ttk.Entry(dialog, textvariable=port_var, width=30).grid(row=2, column=1, padx=10, pady=5)
        ttk.Label(dialog, text="服务名(SID):").grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        service_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=service_var, width=30).grid(row=3, column=1, padx=10, pady=5)
        ttk.Label(dialog, text="用户名:").grid(row=4, column=0, sticky=tk.W, padx=10, pady=5)
        user_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=user_var, width=30).grid(row=4, column=1, padx=10, pady=5)
        ttk.Label(dialog, text="密码:").grid(row=5, column=0, sticky=tk.W, padx=10, pady=5)
        pwd_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=pwd_var, show="*", width=30).grid(row=5, column=1, padx=10, pady=5)

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

        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="测试连接", command=test_and_save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def delete_connection(self):
        conn_name = self.connection_var.get()
        if not conn_name:
            messagebox.showwarning("提示", "请先选择要删除的连接")
            return
        if messagebox.askyesno("确认", f"确定要删除连接 '{conn_name}' 吗？"):
            self.config.delete_connection(conn_name)
            self.update_connection_list()
            self.connection_status_label.config(text="未连接", foreground="gray")

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
            self.preview_tree['columns'] = data['headers']
            for header in data['headers']:
                self.preview_tree.heading(header, text=header)
                self.preview_tree.column(header, width=150)
            for row in data['rows']:
                self.preview_tree.insert('', tk.END, values=row)
        else:
            messagebox.showerror("预览失败", msg)

    def add_log(self, message, level="INFO"):
        self.log_text.insert(tk.END, f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n", level)
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
        self.add_log("=" * 50)
        self.add_log("开始数据更新操作")
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
        dialog.geometry("500x400")
        dialog.transient(self.root)
        tree_frame = ttk.Frame(dialog)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        columns = ("key_value", "update_value", "reason", "timestamp")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        tree.heading("key_value", text="唯一标识")
        tree.heading("update_value", text="待修改数据")
        tree.heading("reason", text="失败原因")
        tree.heading("timestamp", text="时间")
        tree.column("key_value", width=100)
        tree.column("update_value", width=150)
        tree.column("reason", width=150)
        tree.column("timestamp", width=120)
        for record in failed_records:
            tree.insert('', tk.END, values=(record["key_value"], record["update_value"], record["reason"], record["timestamp"]))
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)

        def export_and_close():
            self.export_failed_records()
            dialog.destroy()
        ttk.Button(btn_frame, text="导出失败记录", command=export_and_close).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="确定", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def cancel_operation(self):
        if messagebox.askyesno("确认", "确定要取消操作吗？"):
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
