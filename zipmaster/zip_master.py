import tkinter as tk
from tkinter import filedialog, messagebox, Listbox, Scrollbar, ttk
import zipfile
import os
from PIL import Image, ImageTk

class ZipMaster:
    def __init__(self, root):
        self.root = root
        self.root.title("ZipMaster")
        # 设置窗口大小和背景颜色
        self.root.geometry("300x300")
        self.root.configure(bg="#f0f0f0")

        # 设置字体样式
        button_font = ('Arial', 10, 'bold')

        # 创建按钮并设置样式
        self.compress_button = tk.Button(
            root,
            text="压缩文件",
            command=self.compress_file,
            font=button_font,
            bg="#4CAF50",
            fg="white",
            activebackground="#45a049"
        )
        self.compress_button.pack(pady=10, padx=50, fill="x")

        self.decompress_button = tk.Button(
            root,
            text="解压文件",
            command=self.decompress_file,
            font=button_font,
            bg="#2196F3",
            fg="white",
            activebackground="#0b7dda"
        )
        self.decompress_button.pack(pady=10, padx=50, fill="x")

        self.view_button = tk.Button(
            root,
            text="查看压缩包文件",
            command=self.view_zip_contents,
            font=button_font,
            bg="#FF9800",
            fg="white",
            activebackground="#e68a00"
        )
        self.view_button.pack(pady=10, padx=50, fill="x")

        # 加载图标
        self.folder_icon = self.load_icon("folder.png")
        self.pdf_icon = self.load_icon("Pdf.png")
        self.excel_icon = self.load_icon("EXCEL.png")
        self.ppt_icon = self.load_icon("PPT.png")
        self.pptx_icon = self.load_icon("PPTX.png")
        self.doc_icon = self.load_icon("doc.png")
        self.picture_icon = self.load_icon("picture-.png")
        # 为不存在的图标使用默认图标
        self.file_icon = self.picture_icon
        self.image_icon = self.picture_icon
        self.code_icon = self.picture_icon

    def load_icon(self, filename):
        """
        加载图标文件，如果文件不存在则返回 None。
        """
        try:
            image = Image.open(filename)
            image = image.resize((32, 32), Image.LANCZOS)
            return ImageTk.PhotoImage(image)
        except FileNotFoundError:
            return None

    def compress_file(self):
        # 选择要压缩的文件或文件夹
        file_path = filedialog.askopenfilename() or filedialog.askdirectory()
        if file_path:
            # 选择保存压缩文件的路径
            save_path = filedialog.asksaveasfilename(defaultextension=".zip")
            if save_path:
                try:
                    with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        if os.path.isfile(file_path):
                            zipf.write(file_path, os.path.basename(file_path))
                        else:
                            for root, dirs, files in os.walk(file_path):
                                for file in files:
                                    file_path_full = os.path.join(root, file)
                                    arcname = os.path.relpath(file_path_full, file_path)
                                    zipf.write(file_path_full, arcname)
                    messagebox.showinfo("成功", "文件压缩成功！")
                except Exception as e:
                    messagebox.showerror("错误", f"文件压缩失败：{e}")

    def decompress_file(self):
        # 选择要解压的压缩文件
        zip_file_path = filedialog.askopenfilename(filetypes=[("Zip Files", "*.zip")])
        if zip_file_path:
            # 选择解压的目标文件夹
            extract_path = filedialog.askdirectory()
            if extract_path:
                try:
                    with zipfile.ZipFile(zip_file_path, 'r') as zipf:
                        zipf.extractall(extract_path)
                    messagebox.showinfo("成功", "文件解压成功！")
                except Exception as e:
                    messagebox.showerror("错误", f"文件解压失败：{e}")

    def view_zip_contents(self):
        """
        查看压缩包内文件列表的方法。
        弹出文件选择对话框让用户选择压缩包，然后显示压缩包内的文件列表。
        """
        zip_file_path = filedialog.askopenfilename(filetypes=[("Zip Files", "*.zip")])
        if zip_file_path:
            try:
                with zipfile.ZipFile(zip_file_path, 'r') as zipf:
                    file_list = zipf.namelist()
                    self.show_file_list(file_list, zip_file_path)
            except Exception as e:
                messagebox.showerror("错误", f"查看压缩包内容失败：{e}")

    def show_file_list(self, file_list, zip_file_path):
        """
        显示文件列表的方法。
        创建一个新窗口，使用图标和列表展示文件信息。
        """
        list_window = tk.Toplevel(self.root)
        list_window.title("压缩包内文件列表 - {}".format(os.path.basename(zip_file_path)))
        list_window.geometry("800x600")
        list_window.configure(bg="#f0f0f0")

        # 创建 Canvas 用于显示图标和文件信息
        canvas = tk.Canvas(list_window, bg="#f0f0f0")
        scrollbar = ttk.Scrollbar(list_window, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        frame = tk.Frame(canvas, bg="#f0f0f0")
        canvas.create_window((0, 0), window=frame, anchor=tk.NW)

        for file in file_list:
            # 判断是文件还是文件夹
            if file.endswith('/'):
                icon = self.folder_icon
            else:
                ext = os.path.splitext(file)[1].lower()
                if ext in ('.jpg', '.jpeg', '.png', '.gif', '.bmp'):
                    icon = self.picture_icon
                elif ext == '.pdf':
                    icon = self.pdf_icon
                elif ext in ('.py', '.js', '.html', '.css'):
                    icon = self.picture_icon  # 用 picture-.png 作为代码文件图标
                elif ext in ('.xls', '.xlsx'):
                    icon = self.excel_icon
                elif ext in ('.ppt',):
                    icon = self.ppt_icon
                elif ext in ('.pptx',):
                    icon = self.pptx_icon
                elif ext in ('.doc', '.docx'):
                    icon = self.doc_icon
                else:
                    icon = self.picture_icon  # 用 picture-.png 作为默认文件图标

            frame_row = tk.Frame(frame, bg="#f0f0f0")
            frame_row.pack(fill=tk.X, padx=5, pady=5)

            if icon:
                icon_label = tk.Label(frame_row, image=icon, bg="#f0f0f0")
                icon_label.image = icon  # 保持引用
                icon_label.pack(side=tk.LEFT)

            name_label = tk.Label(frame_row, text=file, bg="#f0f0f0", anchor=tk.W)
            name_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

if __name__ == "__main__":
    root = tk.Tk()
    app = ZipMaster(root)
    root.mainloop()