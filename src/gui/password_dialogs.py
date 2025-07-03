#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
密码相关对话框
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import Optional, Callable

class PasswordInputDialog:
    """密码输入对话框"""
    
    def __init__(self, parent, title="输入密码", message="请输入压缩包密码:"):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("300x150")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        # 创建界面
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text=message).pack(pady=(0, 10))
        
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(main_frame, textvariable=self.password_var, show="*", width=30)
        self.password_entry.pack(pady=(0, 20))
        self.password_entry.focus()
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack()
        
        ttk.Button(button_frame, text="确定", command=self.ok_clicked).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="取消", command=self.cancel_clicked).pack(side=tk.LEFT)
        
        # 绑定回车键
        self.password_entry.bind('<Return>', lambda e: self.ok_clicked())
        self.dialog.bind('<Escape>', lambda e: self.cancel_clicked())
    
    def ok_clicked(self):
        self.result = self.password_var.get()
        self.dialog.destroy()
    
    def cancel_clicked(self):
        self.result = None
        self.dialog.destroy()
    
    def show(self) -> Optional[str]:
        self.dialog.wait_window()
        return self.result

class PasswordCrackDialog:
    """密码破解对话框"""
    
    def __init__(self, parent, archive_path: str, crack_callback: Callable):
        self.archive_path = archive_path
        self.crack_callback = crack_callback
        self.cracking = False
        self.result_password = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("密码破解")
        self.dialog.geometry("500x400")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        self._create_widgets()
        
        # 关闭事件
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def _create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 文件信息
        info_frame = ttk.LabelFrame(main_frame, text="文件信息", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(info_frame, text=f"文件: {self.archive_path}").pack(anchor=tk.W)
        
        # 破解选项
        options_frame = ttk.LabelFrame(main_frame, text="破解选项", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 破解方法
        ttk.Label(options_frame, text="破解方法:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.method_var = tk.StringVar(value="dictionary")
        method_combo = ttk.Combobox(options_frame, textvariable=self.method_var, 
                                   values=["dictionary", "brute_force", "hybrid"], state="readonly")
        method_combo.grid(row=0, column=1, sticky=tk.W)
        
        # 字符集（暴力破解用）
        ttk.Label(options_frame, text="字符集:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.charset_var = tk.StringVar(value="alphanumeric")
        charset_combo = ttk.Combobox(options_frame, textvariable=self.charset_var,
                                    values=["digits", "lower", "upper", "letters", "alphanumeric", "all"], 
                                    state="readonly")
        charset_combo.grid(row=1, column=1, sticky=tk.W, pady=(10, 0))
        
        # 最大长度
        ttk.Label(options_frame, text="最大长度:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.max_length_var = tk.IntVar(value=6)
        length_spin = ttk.Spinbox(options_frame, from_=1, to=10, textvariable=self.max_length_var, width=10)
        length_spin.grid(row=2, column=1, sticky=tk.W, pady=(10, 0))
        
        # 进度显示
        progress_frame = ttk.LabelFrame(main_frame, text="破解进度", padding="10")
        progress_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, length=400)
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        self.status_var = tk.StringVar(value="准备就绪")
        self.status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        self.status_label.pack(anchor=tk.W)
        
        # 日志显示
        log_frame = ttk.Frame(progress_frame)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.log_text = tk.Text(log_frame, height=8, width=60)
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        self.start_button = ttk.Button(button_frame, text="开始破解", command=self.start_crack)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="停止", command=self.stop_crack, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="关闭", command=self.on_close).pack(side=tk.RIGHT)
    
    def log_message(self, message: str):
        """添加日志消息"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.dialog.update_idletasks()
    
    def progress_callback(self, current: int, total: int, password: str, found: bool):
        """进度回调"""
        if total > 0:
            progress = (current / total) * 100
            self.progress_var.set(progress)
        
        if found:
            self.status_var.set(f"密码找到: {password}")
            self.log_message(f"✓ 密码破解成功: {password}")
            self.result_password = password
            self.cracking = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            messagebox.showinfo("成功", f"密码破解成功!\n密码: {password}")
        else:
            self.status_var.set(f"正在尝试: {password} ({current}/{total})")
            if current % 100 == 0:  # 每100次记录一次
                self.log_message(f"尝试密码: {password}")
    
    def start_crack(self):
        """开始破解"""
        if self.cracking:
            return
        
        self.cracking = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.progress_var.set(0)
        
        method = self.method_var.get()
        charset = self.charset_var.get()
        max_length = self.max_length_var.get()
        
        self.log_message(f"开始破解: {method}")
        self.log_message(f"字符集: {charset}, 最大长度: {max_length}")
        
        def crack_worker():
            try:
                result = self.crack_callback(
                    self.archive_path, method, charset, max_length, self.progress_callback
                )
                
                if not result and self.cracking:
                    self.dialog.after(0, lambda: self.on_crack_failed())
                    
            except Exception as e:
                self.dialog.after(0, lambda: self.on_crack_error(str(e)))
        
        threading.Thread(target=crack_worker, daemon=True).start()
    
    def stop_crack(self):
        """停止破解"""
        self.cracking = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set("已停止")
        self.log_message("破解已停止")
    
    def on_crack_failed(self):
        """破解失败"""
        self.cracking = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set("破解失败")
        self.log_message("✗ 密码破解失败")
        messagebox.showwarning("失败", "未能破解密码，请尝试其他方法或字典")
    
    def on_crack_error(self, error: str):
        """破解错误"""
        self.cracking = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set("破解出错")
        self.log_message(f"✗ 破解出错: {error}")
        messagebox.showerror("错误", f"破解过程中出现错误:\n{error}")
    
    def on_close(self):
        """关闭对话框"""
        if self.cracking:
            if messagebox.askyesno("确认", "破解正在进行中，确定要关闭吗？"):
                self.stop_crack()
                self.dialog.destroy()
        else:
            self.dialog.destroy()
    
    def show(self) -> Optional[str]:
        """显示对话框并返回破解结果"""
        self.dialog.wait_window()
        return self.result_password

class CreatePasswordArchiveDialog:
    """创建带密码压缩包对话框"""
    
    def __init__(self, parent):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("创建带密码的压缩包")
        self.dialog.geometry("400x200")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        self._create_widgets()
    
    def _create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 密码输入
        ttk.Label(main_frame, text="设置密码:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(main_frame, textvariable=self.password_var, show="*", width=30)
        self.password_entry.grid(row=0, column=1, pady=(0, 5))
        
        # 确认密码
        ttk.Label(main_frame, text="确认密码:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        self.confirm_var = tk.StringVar()
        self.confirm_entry = ttk.Entry(main_frame, textvariable=self.confirm_var, show="*", width=30)
        self.confirm_entry.grid(row=1, column=1, pady=(0, 5))
        
        # 格式选择
        ttk.Label(main_frame, text="压缩格式:").grid(row=2, column=0, sticky=tk.W, pady=(10, 5))
        self.format_var = tk.StringVar(value="zip")
        format_combo = ttk.Combobox(main_frame, textvariable=self.format_var, 
                                   values=["zip", "7z"], state="readonly", width=27)
        format_combo.grid(row=2, column=1, pady=(10, 5))
        
        # 按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(20, 0))
        
        ttk.Button(button_frame, text="确定", command=self.ok_clicked).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="取消", command=self.cancel_clicked).pack(side=tk.LEFT)
        
        # 设置焦点
        self.password_entry.focus()
    
    def ok_clicked(self):
        password = self.password_var.get()
        confirm = self.confirm_var.get()
        
        if not password:
            messagebox.showwarning("警告", "请输入密码")
            return
        
        if password != confirm:
            messagebox.showwarning("警告", "两次输入的密码不一致")
            return
        
        self.result = {
            'password': password,
            'format': self.format_var.get()
        }
        self.dialog.destroy()
    
    def cancel_clicked(self):
        self.result = None
        self.dialog.destroy()
    
    def show(self) -> Optional[dict]:
        self.dialog.wait_window()
        return self.result

class ExtractOptionsDialog:
    """解压选项对话框"""
    
    def __init__(self, parent):
        self.parent = parent
        self.result = None
        
    def show(self):
        """显示对话框并返回选择的选项"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("解压选项")
        dialog.geometry("400x200")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # 居中显示
        dialog.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 50,
            self.parent.winfo_rooty() + 50
        ))
        
        # 选择输出目录
        ttk.Label(dialog, text="选择解压目录:").pack(pady=10)
        
        dir_frame = ttk.Frame(dialog)
        dir_frame.pack(fill=tk.X, padx=20, pady=5)
        
        self.dir_var = tk.StringVar()
        dir_entry = ttk.Entry(dir_frame, textvariable=self.dir_var, state='readonly')
        dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        def browse_dir():
            directory = filedialog.askdirectory(title="选择解压目录")
            if directory:
                self.dir_var.set(directory)
        
        ttk.Button(dir_frame, text="浏览", command=browse_dir).pack(side=tk.RIGHT, padx=(5, 0))
        
        # 创建子文件夹选项
        self.subfolder_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(dialog, text="为每个压缩包创建同名文件夹", 
                       variable=self.subfolder_var).pack(pady=10)
        
        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        def on_ok():
            if not self.dir_var.get():
                messagebox.showwarning("警告", "请选择解压目录")
                return
            
            self.result = {
                'output_dir': self.dir_var.get(),
                'create_subfolder': self.subfolder_var.get()
            }
            dialog.destroy()
        
        def on_cancel():
            self.result = None
            dialog.destroy()
        
        ttk.Button(button_frame, text="确定", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=on_cancel).pack(side=tk.LEFT, padx=5)
        
        # 等待对话框关闭
        dialog.wait_window()
        return self.result