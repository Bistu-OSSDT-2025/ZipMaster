#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
密码管理器 - 集成密码爆破、设置和检测功能
"""

import os
import time
import itertools
import string
import zipfile
import rarfile
import py7zr
import threading
import queue
import logging
from typing import Optional, Callable, Dict, List, Tuple
from pathlib import Path

class PasswordManager:
    """密码管理器 - 支持密码检测、设置和爆破"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 字符集定义
        self.char_sets = {
            'digits': string.digits,
            'lower': string.ascii_lowercase,
            'upper': string.ascii_uppercase,
            'letters': string.ascii_letters,
            'alphanumeric': string.ascii_letters + string.digits,
            'all': string.ascii_letters + string.digits + string.punctuation
        }
        
        # 常用密码字典
        self.common_passwords = {
            'password', '123456', '12345678', '123456789', 'admin',
            'qwerty', 'abc123', 'letmein', 'welcome', 'password1',
            '12345', '1234567', '123123', '111111', 'sunshine',
            'iloveyou', 'monkey', 'dragon', 'football', 'baseball',
            '000000', '1qaz2wsx', 'qwertyuiop', 'zxcvbnm', 'asdfgh'
        }
        
        # 多线程控制
        self.stop_attack = False
        self.password_found = None
    
    def check_password_required(self, archive_path: str) -> bool:
        """检测压缩包是否需要密码"""
        try:
            path = Path(archive_path)
            suffix = path.suffix.lower()
            
            if suffix == '.zip':
                return self._check_zip_password(archive_path)
            elif suffix == '.rar':
                return self._check_rar_password(archive_path)
            elif suffix == '.7z':
                return self._check_7z_password(archive_path)
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"检测密码需求失败: {e}")
            return False
    
    def _check_zip_password(self, archive_path: str) -> bool:
        """检查ZIP文件是否需要密码"""
        try:
            with zipfile.ZipFile(archive_path, 'r') as zf:
                # 尝试读取文件列表
                info_list = zf.infolist()
                if not info_list:
                    return False
                
                # 尝试提取第一个文件的少量数据
                first_file = info_list[0]
                if first_file.file_size > 0:
                    try:
                        zf.read(first_file.filename, pwd=None)
                        return False  # 不需要密码
                    except RuntimeError as e:
                        if "Bad password" in str(e) or "password required" in str(e).lower():
                            return True  # 需要密码
                        return False
                return False
        except Exception:
            return False
    
    def _check_rar_password(self, archive_path: str) -> bool:
        """检查RAR文件是否需要密码"""
        try:
            with rarfile.RarFile(archive_path) as rf:
                info_list = rf.infolist()
                if not info_list:
                    return False
                
                # 检查是否有加密文件
                for info in info_list:
                    if hasattr(info, 'needs_password') and info.needs_password():
                        return True
                
                # 尝试提取第一个文件
                first_file = info_list[0]
                if first_file.file_size > 0:
                    try:
                        rf.read(first_file.filename)
                        return False
                    except (rarfile.RarWrongPassword, RuntimeError):
                        return True
                return False
        except Exception:
            return False
    
    def _check_7z_password(self, archive_path: str) -> bool:
        """检查7Z文件是否需要密码"""
        try:
            with py7zr.SevenZipFile(archive_path, mode='r') as szf:
                # 尝试列出文件
                file_list = szf.list()
                if not file_list:
                    return False
                
                # 尝试提取第一个文件
                try:
                    szf.extractall()
                    return False
                except py7zr.PasswordRequired:
                    return True
                except Exception:
                    return False
        except py7zr.PasswordRequired:
            return True
        except Exception:
            return False
    
    def try_password(self, archive_path: str, password: str) -> bool:
        """尝试使用指定密码解压"""
        try:
            path = Path(archive_path)
            suffix = path.suffix.lower()
            
            if suffix == '.zip':
                with zipfile.ZipFile(archive_path, 'r') as zf:
                    # 尝试提取第一个文件
                    info_list = zf.infolist()
                    if info_list:
                        zf.read(info_list[0].filename, pwd=password.encode())
                return True
                
            elif suffix == '.rar':
                with rarfile.RarFile(archive_path) as rf:
                    rf.setpassword(password)
                    info_list = rf.infolist()
                    if info_list:
                        rf.read(info_list[0].filename)
                return True
                
            elif suffix == '.7z':
                with py7zr.SevenZipFile(archive_path, mode='r', password=password) as szf:
                    file_list = szf.list()
                    if file_list:
                        # 尝试提取第一个文件到内存
                        szf.read([file_list[0].filename])
                return True
                
        except Exception:
            return False
        
        return False
    
    def crack_password(self, archive_path: str, method: str = 'dictionary',
                      charset: str = 'alphanumeric', max_length: int = 6,
                      custom_dict: Optional[List[str]] = None,
                      progress_callback: Optional[Callable] = None) -> Optional[str]:
        """破解压缩包密码"""
        self.stop_attack = False
        self.password_found = None
        
        if method == 'dictionary':
            return self._dictionary_attack(archive_path, custom_dict, progress_callback)
        elif method == 'brute_force':
            return self._brute_force_attack(archive_path, charset, max_length, progress_callback)
        elif method == 'hybrid':
            # 先尝试字典攻击，再尝试暴力破解
            result = self._dictionary_attack(archive_path, custom_dict, progress_callback)
            if result:
                return result
            return self._brute_force_attack(archive_path, charset, max_length, progress_callback)
        else:
            raise ValueError(f"不支持的破解方法: {method}")
    
    def _dictionary_attack(self, archive_path: str, custom_dict: Optional[List[str]] = None,
                          progress_callback: Optional[Callable] = None) -> Optional[str]:
        """字典攻击"""
        passwords = list(self.common_passwords)
        if custom_dict:
            passwords.extend(custom_dict)
        
        total = len(passwords)
        
        for i, password in enumerate(passwords):
            if self.stop_attack:
                break
                
            if self.try_password(archive_path, password):
                self.password_found = password
                if progress_callback:
                    progress_callback(i + 1, total, password, True)
                return password
            
            if progress_callback:
                progress_callback(i + 1, total, password, False)
        
        return None
    
    def _brute_force_attack(self, archive_path: str, charset: str = 'alphanumeric',
                           max_length: int = 6, progress_callback: Optional[Callable] = None) -> Optional[str]:
        """暴力破解攻击"""
        if charset not in self.char_sets:
            charset = 'alphanumeric'
        
        chars = self.char_sets[charset]
        
        # 计算总数（估算）
        total_estimate = sum(len(chars) ** length for length in range(1, max_length + 1))
        current = 0
        
        for length in range(1, max_length + 1):
            if self.stop_attack:
                break
                
            for combination in itertools.product(chars, repeat=length):
                if self.stop_attack:
                    break
                    
                password = ''.join(combination)
                current += 1
                
                if self.try_password(archive_path, password):
                    self.password_found = password
                    if progress_callback:
                        progress_callback(current, total_estimate, password, True)
                    return password
                
                if progress_callback and current % 100 == 0:  # 每100次更新一次进度
                    progress_callback(current, total_estimate, password, False)
        
        return None
    
    def stop_crack(self):
        """停止破解"""
        self.stop_attack = True
    
    def create_password_archive(self, files: List[str], archive_path: str,
                               password: str, format_type: str = 'zip') -> bool:
        """创建带密码的压缩包"""
        try:
            if format_type == 'zip':
                return self._create_password_zip(files, archive_path, password)
            elif format_type == '7z':
                return self._create_password_7z(files, archive_path, password)
            else:
                raise ValueError(f"不支持创建带密码的 {format_type} 格式")
        except Exception as e:
            self.logger.error(f"创建带密码压缩包失败: {e}")
            return False
    
    def _create_password_zip(self, files: List[str], archive_path: str, password: str) -> bool:
        """创建带密码的ZIP文件 - 修复版本"""
        try:
            import pyminizip
            
            # 使用pyminizip创建带密码的ZIP
            if len(files) == 1 and Path(files[0]).is_file():
                # 单个文件
                file_path = files[0]
                pyminizip.compress(file_path, None, archive_path, password, 5)
            else:
                # 多个文件或文件夹 - 需要先创建临时文件列表
                temp_files = []
                temp_prefixes = []
                
                for file_path in files:
                    path = Path(file_path)
                    if path.is_file():
                        temp_files.append(str(path))
                        temp_prefixes.append(path.name)
                    elif path.is_dir():
                        for sub_file in path.rglob('*'):
                            if sub_file.is_file():
                                temp_files.append(str(sub_file))
                                rel_path = sub_file.relative_to(path.parent)
                                temp_prefixes.append(str(rel_path))
                            
                            if temp_files:
                                pyminizip.compress_multiple(temp_files, temp_prefixes, archive_path, password, 5)
                        
                        return True
        except ImportError:
                        # 如果pyminizip不可用，回退到标准zipfile（但密码保护可能不完整）
                        self.logger.warning("pyminizip不可用，使用标准zipfile（密码保护可能不完整）")
                        return self._create_password_zip_fallback(files, archive_path, password)
        except Exception as e:
                        self.logger.error(f"创建ZIP失败: {e}")
                        return False
    
    def _create_password_zip_fallback(self, files: List[str], archive_path: str, password: str) -> bool:
        """ZIP密码创建的回退方法"""
        try:
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.setpassword(password.encode())
                
                for file_path in files:
                    path = Path(file_path)
                    if path.is_file():
                        zf.write(path, path.name)
                    elif path.is_dir():
                        for sub_file in path.rglob('*'):
                            if sub_file.is_file():
                                rel_path = sub_file.relative_to(path.parent)
                                zf.write(sub_file, str(rel_path))
            return True
        except Exception as e:
            self.logger.error(f"ZIP回退方法失败: {e}")
            return False
    
    def _create_password_7z(self, files: List[str], archive_path: str, password: str) -> bool:
        """创建带密码的7Z文件"""
        try:
            with py7zr.SevenZipFile(archive_path, 'w', password=password) as szf:
                for file_path in files:
                    path = Path(file_path)
                    if path.is_file():
                        szf.write(path, path.name)
                    elif path.is_dir():
                        for sub_file in path.rglob('*'):
                            if sub_file.is_file():
                                rel_path = sub_file.relative_to(path.parent)
                                szf.write(sub_file, str(rel_path))
            return True
        except Exception as e:
            self.logger.error(f"创建7Z失败: {e}")
            return False
    
    def extract_with_password(self, archive_path: str, output_path: str, password: str) -> bool:
        """使用密码解压文件"""
        try:
            path = Path(archive_path)
            suffix = path.suffix.lower()
            
            output_dir = Path(output_path)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            if suffix == '.zip':
                with zipfile.ZipFile(archive_path, 'r') as zf:
                    zf.extractall(output_path, pwd=password.encode())
                return True
                
            elif suffix == '.rar':
                with rarfile.RarFile(archive_path) as rf:
                    rf.setpassword(password)
                    rf.extractall(output_path)
                return True
                
            elif suffix == '.7z':
                with py7zr.SevenZipFile(archive_path, mode='r', password=password) as szf:
                    szf.extractall(output_path)
                return True
                
        except Exception as e:
            self.logger.error(f"密码解压失败: {e}")
            return False
        
        return False