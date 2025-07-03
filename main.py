#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZipMaster - 开源压缩包管理工具 (Python 版本)
作者: ZipMaster Team
版本: 1.0.0
"""

import sys
import os
from pathlib import Path

# 添加 src 目录到 Python 路径
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

def main():
    """主函数"""
    try:
        from gui.main_window import MainWindow
        app = MainWindow()
        app.run()
    except ImportError as e:
        print(f"导入模块失败: {e}")
        print("请确保已安装所有依赖: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"程序启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()