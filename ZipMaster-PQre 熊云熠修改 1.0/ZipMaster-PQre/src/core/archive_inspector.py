#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
此模块用于在不打开压缩包的情况下查看其中的文件列表。
"""

import py7zr
import rarfile
import patoolib
from pathlib import Path


def list_archive_contents(file_path):
    """
    在不打开压缩包的情况下查看其中的文件列表。

    参数:
        file_path (str): 压缩包文件的路径。

    返回:
        list: 压缩包中文件的列表。
        str: 错误信息，如果没有错误则返回空字符串。
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return [], "文件不存在"

    try:
        if file_path.suffix == '.7z':
            with py7zr.SevenZipFile(file_path, 'r') as archive:
                return archive.getnames(), ""
        elif file_path.suffix == '.rar':
            with rarfile.RarFile(file_path) as archive:
                return archive.namelist(), ""
        else:
            # 对于其他格式，使用 patool
            temp_dir = Path('temp_archive')
            temp_dir.mkdir(exist_ok=True)
            try:
                patoolib.extract_archive(str(file_path), outdir=str(temp_dir), interactive=False)
                file_list = [str(f.relative_to(temp_dir)) for f in temp_dir.rglob('*')]
                return file_list, ""
            except Exception as e:
                return [], str(e)
            finally:
                # 清理临时文件
                for f in temp_dir.glob('*'):
                    if f.is_file():
                        f.unlink()
                    elif f.is_dir():
                        import shutil
                        shutil.rmtree(f)
                temp_dir.rmdir()
    except Exception as e:
        return [], str(e)