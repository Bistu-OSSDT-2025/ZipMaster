#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI 主窗口 - 使用 Tkinter
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import logging
from pathlib import Path

from core.archive_manager import ArchiveManager
from utils.helpers import format_size, format_datetime

class MainWindow:
    """主窗口类"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ZipMaster - 压缩包管理工具 v1.0")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # 设置图标（如果存在）
        try:
            icon_path = Path("assets/icons/icon.ico")
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except:
            pass
        
        # 初始化管理器
        self.archive_manager = ArchiveManager()
        self.logger = logging.getLogger(__name__)
        
        # 创建界面
        self._create_widgets()
        self._setup_layout()
        self._setup_events()
        
        # 加载现有数据
        self._load_archives()
    
    def _create_widgets(self):
        """创建界面组件"""
        # 创建菜单栏
        self._create_menu()
        
        # 工具栏
        self.toolbar = ttk.Frame(self.root)
        
        ttk.Button(self.toolbar, text="📁 扫描目录", command=self.scan_directory).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.toolbar, text="📦 解压选中", command=self.extract_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.toolbar, text="🗜️ 创建压缩包", command=self.create_archive).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.toolbar, text="🔍 查看详情", command=self.view_details).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.toolbar, text="🔄 刷新", command=self.refresh_list).pack(side=tk.LEFT, padx=5)
        
        # 分隔符
        ttk.Separator(self.toolbar, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # 搜索框
        ttk.Label(self.toolbar, text="搜索:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.toolbar, textvariable=self.search_var, width=20)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(self.toolbar, text="🔍", command=self.search_archives).pack(side=tk.LEFT)
        
        # 主内容区域
        self.main_frame = ttk.Frame(self.root)
        
        # 文件列表
        columns = ('名称', '路径', '大小', '类型', '文件数', '修改时间')
        self.tree = ttk.Treeview(self.main_frame, columns=columns, show='headings', height=20)
        
        # 设置列标题和宽度
        column_widths = {'名称': 200, '路径': 300, '大小': 100, '类型': 80, '文件数': 80, '修改时间': 150}
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self._sort_column(c))
            self.tree.column(col, width=column_widths.get(col, 100), minwidth=50)
        
        # 滚动条
        v_scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # 状态栏
        self.status_frame = ttk.Frame(self.root)
        self.status_var = tk.StringVar(value="就绪")
        self.status_label = ttk.Label(self.status_frame, textvariable=self.status_var)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.status_frame, variable=self.progress_var, length=200)
        
        # 存储组件引用
        self.v_scrollbar = v_scrollbar
        self.h_scrollbar = h_scrollbar
    
    def _create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="扫描目录...", command=self.scan_directory, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit, accelerator="Ctrl+Q")
        
        # 操作菜单
        action_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="操作", menu=action_menu)
        action_menu.add_command(label="解压选中", command=self.extract_selected, accelerator="Ctrl+E")
        action_menu.add_command(label="创建压缩包", command=self.create_archive, accelerator="Ctrl+N")
        action_menu.add_command(label="查看详情", command=self.view_details, accelerator="Ctrl+I")
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self.show_about)
    
    def _setup_layout(self):
        """设置布局"""
        # 工具栏
        self.toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # 主内容区
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 文件列表和滚动条
        self.tree.grid(row=0, column=0, sticky='nsew')
        self.v_scrollbar.grid(row=0, column=1, sticky='ns')
        self.h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        # 配置网格权重
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # 状态栏
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_label.pack(side=tk.LEFT, padx=5)
        self.progress_bar.pack(side=tk.RIGHT, padx=5, pady=2)
    
    def _setup_events(self):
        """设置事件绑定"""
        # 键盘快捷键
        self.root.bind('<Control-o>', lambda e: self.scan_directory())
        self.root.bind('<Control-e>', lambda e: self.extract_selected())
        self.root.bind('<Control-n>', lambda e: self.create_archive())
        self.root.bind('<Control-i>', lambda e: self.view_details())
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        self.root.bind('<F5>', lambda e: self.refresh_list())
        
        # 搜索框回车
        self.search_entry.bind('<Return>', lambda e: self.search_archives())
        
        # 双击打开详情
        self.tree.bind('<Double-1>', lambda e: self.view_details())
        
        # 右键菜单
        self.tree.bind('<Button-3>', self._show_context_menu)
    
    def _load_archives(self):
        """加载现有压缩包数据"""
        try:
            archives = self.archive_manager.get_all_archives()
            self._populate_tree(archives)
            self.status_var.set(f"加载了 {len(archives)} 个压缩包")
        except Exception as e:
            self.logger.error(f"加载数据失败: {e}")
            messagebox.showerror("错误", f"加载数据失败: {e}")
    
    def _populate_tree(self, archives):
        """填充文件列表"""
        # 清空现有项目
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 添加新项目
        for archive in archives:
            self.tree.insert('', tk.END, values=(
                archive['name'],
                archive['path'],
                format_size(archive['size']),
                archive['type'].upper(),
                archive.get('file_count', 0),
                format_datetime(archive['modified'])
            ))
    
    def scan_directory(self):
        """扫描目录"""
        directory = filedialog.askdirectory(title="选择要扫描的目录")
        if not directory:
            return
        
        # 在后台线程中执行扫描
        def scan_worker():
            try:
                self.status_var.set("正在扫描...")
                self.progress_var.set(0)
                
                def progress_callback(current, total):
                    progress = (current / total) * 100 if total > 0 else 0
                    self.progress_var.set(progress)
                    self.root.update_idletasks()
                
                archives = self.archive_manager.scan_directory(directory, progress_callback)
                
                # 在主线程中更新UI
                self.root.after(0, lambda: self._on_scan_complete(archives))
                
            except Exception as e:
                self.root.after(0, lambda: self._on_scan_error(e))
        
        threading.Thread(target=scan_worker, daemon=True).start()
    
    def _on_scan_complete(self, archives):
        """扫描完成回调"""
        self._populate_tree(archives)
        self.status_var.set(f"扫描完成，找到 {len(archives)} 个压缩包")
        self.progress_var.set(0)
    
    def _on_scan_error(self, error):
        """扫描错误回调"""
        messagebox.showerror("错误", f"扫描失败: {error}")
        self.status_var.set("扫描失败")
        self.progress_var.set(0)
    
    def extract_selected(self):
        """解压选中的文件"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要解压的文件")
            return
        
        output_dir = filedialog.askdirectory(title="选择解压目录")
        if not output_dir:
            return
        
        # 在后台线程中执行解压
        def extract_worker():
            success_count = 0
            total_count = len(selection)
            
            for i, item in enumerate(selection):
                try:
                    values = self.tree.item(item)['values']
                    archive_path = values[1]
                    archive_name = values[0]
                    
                    self.root.after(0, lambda name=archive_name: 
                                  self.status_var.set(f"正在解压 {name}..."))
                    
                    success = self.archive_manager.extract_archive(archive_path, output_dir)
                    if success:
                        success_count += 1
                    
                    progress = ((i + 1) / total_count) * 100
                    self.root.after(0, lambda p=progress: self.progress_var.set(p))
                    
                except Exception as e:
                    self.logger.error(f"解压失败: {e}")
            
            self.root.after(0, lambda: self._on_extract_complete(success_count, total_count))
        
        threading.Thread(target=extract_worker, daemon=True).start()
    
    def _on_extract_complete(self, success_count, total_count):
        """解压完成回调"""
        if success_count == total_count:
            messagebox.showinfo("成功", f"成功解压 {success_count} 个文件")
        else:
            messagebox.showwarning("部分成功", 
                                 f"成功解压 {success_count}/{total_count} 个文件")
        
        self.status_var.set(f"解压完成: {success_count}/{total_count}")
        self.progress_var.set(0)
    
    def create_archive(self):
        """创建压缩包"""
        files = filedialog.askopenfilenames(title="选择要压缩的文件")
        if not files:
            return
        
        # 选择保存位置和格式
        archive_path = filedialog.asksaveasfilename(
            title="保存压缩包",
            defaultextension=".7z",
            filetypes=[("7z 文件", "*.7z"), ("ZIP 文件", "*.zip")]
        )
        
        if not archive_path:
            return
        
        # 确定格式
        format_type = '7z' if archive_path.endswith('.7z') else 'zip'
        
        # 在后台线程中创建压缩包
        def create_worker():
            try:
                self.root.after(0, lambda: self.status_var.set("正在创建压缩包..."))
                success = self.archive_manager.create_archive(list(files), archive_path, format_type)
                self.root.after(0, lambda: self._on_create_complete(success, archive_path))
            except Exception as e:
                self.root.after(0, lambda: self._on_create_error(e))
        
        threading.Thread(target=create_worker, daemon=True).start()
    
    def _on_create_complete(self, success, archive_path):
        """创建完成回调"""
        if success:
            messagebox.showinfo("成功", f"压缩包创建成功: {Path(archive_path).name}")
            self.refresh_list()
        else:
            messagebox.showerror("错误", "创建压缩包失败")
        
        self.status_var.set("就绪")
    
    def _on_create_error(self, error):
        """创建错误回调"""
        messagebox.showerror("错误", f"创建压缩包失败: {error}")
        self.status_var.set("就绪")
    
    def view_details(self):
        """查看压缩包详情"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个压缩包")
            return
        
        item = selection[0]
        values = self.tree.item(item)['values']
        archive_path = values[1]
        
        # 创建详情窗口
        self._show_details_window(archive_path)
    
    def _show_details_window(self, archive_path):
        """显示详情窗口"""
        details_window = tk.Toplevel(self.root)
        details_window.title(f"压缩包详情 - {Path(archive_path).name}")
        details_window.geometry("600x400")
        details_window.transient(self.root)
        
        # 获取详情数据
        try:
            details = self.archive_manager.get_archive_details(archive_path)
            
            # 创建详情界面
            info_frame = ttk.LabelFrame(details_window, text="基本信息", padding=10)
            info_frame.pack(fill=tk.X, padx=10, pady=5)
            
            ttk.Label(info_frame, text=f"文件数量: {details['file_count']}").pack(anchor=tk.W)
            ttk.Label(info_frame, text=f"原始大小: {format_size(details['total_size'])}").pack(anchor=tk.W)
            ttk.Label(info_frame, text=f"压缩大小: {format_size(details['compressed_size'])}").pack(anchor=tk.W)
            
            if details['total_size'] > 0:
                ratio = (1 - details['compressed_size'] / details['total_size']) * 100
                ttk.Label(info_frame, text=f"压缩率: {ratio:.1f}%").pack(anchor=tk.W)
            
            # 文件列表
            files_frame = ttk.LabelFrame(details_window, text="文件列表", padding=10)
            files_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # 创建文件列表
            file_columns = ('文件名', '大小', '压缩大小', '修改时间')
            file_tree = ttk.Treeview(files_frame, columns=file_columns, show='headings')
            
            for col in file_columns:
                file_tree.heading(col, text=col)
                file_tree.column(col, width=120)
            
            # 添加文件数据
            for file_info in details['files'][:100]:  # 限制显示前100个文件
                file_tree.insert('', tk.END, values=(
                    file_info['name'],
                    format_size(file_info['size']),
                    format_size(file_info.get('compressed_size', 0)),
                    format_datetime(file_info.get('modified', ''))
                ))
            
            file_tree.pack(fill=tk.BOTH, expand=True)
            
            if len(details['files']) > 100:
                ttk.Label(files_frame, text=f"... 还有 {len(details['files']) - 100} 个文件未显示").pack()
            
        except Exception as e:
            ttk.Label(details_window, text=f"获取详情失败: {e}").pack(padx=10, pady=10)
    
    def search_archives(self):
        """搜索压缩包"""
        keyword = self.search_var.get().strip()
        if not keyword:
            self._load_archives()
            return
        
        try:
            archives = self.archive_manager.search_archives(keyword)
            self._populate_tree(archives)
            self.status_var.set(f"找到 {len(archives)} 个匹配的压缩包")
        except Exception as e:
            messagebox.showerror("错误", f"搜索失败: {e}")
    
    def refresh_list(self):
        """刷新列表"""
        self._load_archives()
    
    def _sort_column(self, col):
        """排序列"""
        # 简单的排序实现
        items = [(self.tree.set(item, col), item) for item in self.tree.get_children('')]
        items.sort()
        
        for index, (val, item) in enumerate(items):
            self.tree.move(item, '', index)
    
    def _show_context_menu(self, event):
        """显示右键菜单"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            
            context_menu = tk.Menu(self.root, tearoff=0)
            context_menu.add_command(label="解压到...", command=self.extract_selected)
            context_menu.add_command(label="查看详情", command=self.view_details)
            context_menu.add_separator()
            context_menu.add_command(label="在文件管理器中显示", command=self._show_in_explorer)
            
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()
    
    def _show_in_explorer(self):
        """在文件管理器中显示"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.tree.item(item)['values']
        archive_path = values[1]
        
        try:
            import subprocess
            subprocess.run(['explorer', '/select,', archive_path], check=True)
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件管理器: {e}")
    
    def show_about(self):
        """显示关于对话框"""
        about_text = """
ZipMaster v1.0
开源压缩包管理工具

支持格式: 7z, ZIP, RAR, TAR, GZ, BZ2, XZ

开发: ZipMaster Team
许可: MIT License
        """
        messagebox.showinfo("关于 ZipMaster", about_text)
    
    def run(self):
        """运行应用"""
        try:
            # 设置日志
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            self.root.mainloop()
        except Exception as e:
            messagebox.showerror("错误", f"应用运行失败: {e}")
        finally:
            self.archive_manager.close()