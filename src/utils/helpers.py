#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
辅助工具函数
"""

from datetime import datetime
from typing import Union

def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"

def format_datetime(dt: Union[datetime, str]) -> str:
    """格式化日期时间"""
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except:
            return dt
    
    if isinstance(dt, datetime):
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    
    return str(dt)

def validate_archive_path(path: str) -> bool:
    """验证压缩包路径"""
    from pathlib import Path
    
    try:
        p = Path(path)
        return p.exists() and p.is_file()
    except:
        return False

def get_archive_type(path: str) -> str:
    """获取压缩包类型"""
    from pathlib import Path
    
    try:
        return Path(path).suffix[1:].lower()
    except:
        return "unknown"