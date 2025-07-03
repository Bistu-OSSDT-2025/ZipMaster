#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
压缩包管理器 - 核心业务逻辑
"""

import os
import sqlite3
import threading
from pathlib import Path
from typing import List, Dict, Optional, Callable
from datetime import datetime
import logging
from .password_manager import PasswordManager

# 压缩格式处理
import py7zr
import zipfile
import rarfile
import patoolib

class ArchiveManager:
    """压缩包管理器"""
    
    def __init__(self, db_path: str = "archives.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.password_manager = PasswordManager()
        
        # 支持的压缩格式及其处理器
        self.supported_formats = {
            '.7z': self._handle_7z,
            '.zip': self._handle_zip,
            '.rar': self._handle_rar,
            '.tar': self._handle_tar,
            '.gz': self._handle_gz,
            '.bz2': self._handle_bz2,
            '.xz': self._handle_xz
        }
        
        self._init_database()
        self._lock = threading.Lock()
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建压缩包表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS archives (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    path TEXT UNIQUE NOT NULL,
                    size INTEGER,
                    modified DATETIME,
                    type TEXT,
                    file_count INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建文件表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS archive_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    archive_id INTEGER,
                    name TEXT NOT NULL,
                    path TEXT NOT NULL,
                    size INTEGER,
                    compressed_size INTEGER,
                    modified DATETIME,
                    FOREIGN KEY (archive_id) REFERENCES archives (id)
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_archives_path ON archives(path)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_archive ON archive_files(archive_id)')
            
            conn.commit()
            conn.close()
            
            self.logger.info("数据库初始化成功")
            
        except Exception as e:
            self.logger.error(f"数据库初始化失败: {e}")
            raise
    
    def scan_directory(self, directory: str, progress_callback: Optional[Callable] = None) -> List[Dict]:
        """扫描目录中的压缩包"""
        archives = []
        path = Path(directory)
        
        if not path.exists() or not path.is_dir():
            raise ValueError(f"目录不存在或不是有效目录: {directory}")
        
        try:
            # 获取所有文件
            all_files = list(path.rglob('*'))
            total_files = len(all_files)
            processed = 0
            
            for file_path in all_files:
                if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                    try:
                        archive_info = self._get_archive_info(file_path)
                        archives.append(archive_info)
                        self._save_archive(archive_info)
                        
                    except Exception as e:
                        self.logger.warning(f"处理文件失败 {file_path}: {e}")
                
                processed += 1
                if progress_callback:
                    progress_callback(processed, total_files)
            
            self.logger.info(f"扫描完成，找到 {len(archives)} 个压缩包")
            return archives
            
        except Exception as e:
            self.logger.error(f"扫描目录失败: {e}")
            raise
    
    def _get_archive_info(self, file_path: Path) -> Dict:
        """获取压缩包信息"""
        try:
            stat = file_path.stat()
            
            # 尝试获取文件数量
            file_count = 0
            try:
                file_count = self._get_file_count(file_path)
            except:
                pass  # 如果获取失败，保持为0
            
            return {
                'name': file_path.name,
                'path': str(file_path.absolute()),
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'type': file_path.suffix[1:].lower(),
                'file_count': file_count
            }
            
        except Exception as e:
            self.logger.error(f"获取文件信息失败 {file_path}: {e}")
            raise
    
    def _get_file_count(self, file_path: Path) -> int:
        """获取压缩包内文件数量"""
        suffix = file_path.suffix.lower()
        
        try:
            if suffix == '.zip':
                with zipfile.ZipFile(file_path, 'r') as zf:
                    return len(zf.namelist())
            elif suffix == '.7z':
                with py7zr.SevenZipFile(file_path, mode='r') as szf:
                    return len(szf.getnames())
            elif suffix == '.rar':
                with rarfile.RarFile(file_path) as rf:
                    return len(rf.namelist())
            else:
                # 对于其他格式，使用 patoolib
                return 0  # patoolib 不直接提供文件数量
                
        except Exception:
            return 0
    
    def _save_archive(self, archive_info: Dict):
        """保存压缩包信息到数据库"""
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO archives 
                    (name, path, size, modified, type, file_count, updated_at) 
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    archive_info['name'],
                    archive_info['path'],
                    archive_info['size'],
                    archive_info['modified'],
                    archive_info['type'],
                    archive_info.get('file_count', 0)
                ))
                
                conn.commit()
                conn.close()
                
            except Exception as e:
                self.logger.error(f"保存压缩包信息失败: {e}")
                raise
    
    def get_all_archives(self) -> List[Dict]:
        """获取所有压缩包"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM archives ORDER BY modified DESC')
            rows = cursor.fetchall()
            
            archives = [dict(row) for row in rows]
            conn.close()
            
            return archives
            
        except Exception as e:
            self.logger.error(f"获取压缩包列表失败: {e}")
            return []
    
    def search_archives(self, keyword: str) -> List[Dict]:
        """搜索压缩包"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM archives 
                WHERE name LIKE ? OR path LIKE ?
                ORDER BY modified DESC
            ''', (f'%{keyword}%', f'%{keyword}%'))
            
            rows = cursor.fetchall()
            archives = [dict(row) for row in rows]
            conn.close()
            
            return archives
            
        except Exception as e:
            self.logger.error(f"搜索压缩包失败: {e}")
            return []
    
    def extract_archive(self, archive_path: str, output_path: str,
                       selected_files: Optional[List[str]] = None,
                       progress_callback: Optional[Callable] = None,
                       password: Optional[str] = None) -> Dict[str, any]:
        """解压缩文件 - 增强版本，支持密码检测和处理"""
        try:
            path = Path(archive_path)
            if not path.exists():
                raise FileNotFoundError(f"压缩包不存在: {archive_path}")
            
            # 确保输出目录存在
            output_dir = Path(output_path)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            suffix = path.suffix.lower()
            handler = self.supported_formats.get(suffix)
            
            if not handler:
                raise ValueError(f"不支持的格式: {suffix}")
            
            # 首先尝试无密码解压
            if password is None:
                try:
                    success = handler('extract', str(path), str(output_dir), selected_files, progress_callback)
                    if success:
                        return {'success': True, 'password_required': False}
                except Exception:
                    # 检查是否需要密码
                    if self.password_manager.check_password_required(str(path)):
                        return {'success': False, 'password_required': True, 'error': '需要密码'}
                    else:
                        raise
            else:
                # 使用提供的密码解压
                success = self.password_manager.extract_with_password(str(path), str(output_dir), password)
                return {'success': success, 'password_required': True, 'password_correct': success}
            
        except Exception as e:
            self.logger.error(f"解压失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_archive_with_password(self, files: List[str], archive_path: str,
                                   format_type: str = '7z', password: Optional[str] = None,
                                   progress_callback: Optional[Callable] = None) -> bool:
        """创建压缩包（支持密码保护）"""
        try:
            if password:
                return self.password_manager.create_password_archive(files, archive_path, password, format_type)
            else:
                return self.create_archive(files, archive_path, format_type, progress_callback)
        except Exception as e:
            self.logger.error(f"创建压缩包失败: {e}")
            return False
    
    def crack_archive_password(self, archive_path: str, method: str = 'dictionary',
                              progress_callback: Optional[Callable] = None) -> Optional[str]:
        """破解压缩包密码"""
        return self.password_manager.crack_password(archive_path, method, progress_callback=progress_callback)
    
    def create_archive(self, files: List[str], archive_path: str,
                      format_type: str = '7z',
                      progress_callback: Optional[Callable] = None) -> bool:
        """创建压缩包"""
        try:
            if format_type == '7z':
                return self._create_7z(files, archive_path, progress_callback)
            elif format_type == 'zip':
                return self._create_zip(files, archive_path, progress_callback)
            else:
                raise ValueError(f"不支持创建格式: {format_type}")
                
        except Exception as e:
            self.logger.error(f"创建压缩包失败: {e}")
            return False
    
    def _handle_7z(self, operation: str, archive_path: str, 
                   output_path: str, files: Optional[List[str]] = None,
                   progress_callback: Optional[Callable] = None) -> bool:
        """处理 7z 格式"""
        try:
            if operation == 'extract':
                with py7zr.SevenZipFile(archive_path, mode='r') as archive:
                    if files:
                        archive.extract(output_path, targets=files)
                    else:
                        archive.extractall(output_path)
                return True
        except Exception as e:
            self.logger.error(f"7z 操作失败: {e}")
            return False
    
    def _handle_zip(self, operation: str, archive_path: str, 
                    output_path: str, files: Optional[List[str]] = None,
                    progress_callback: Optional[Callable] = None) -> bool:
        """处理 ZIP 格式"""
        try:
            if operation == 'extract':
                with zipfile.ZipFile(archive_path, 'r') as archive:
                    if files:
                        for file in files:
                            archive.extract(file, output_path)
                    else:
                        archive.extractall(output_path)
                return True
        except Exception as e:
            self.logger.error(f"ZIP 操作失败: {e}")
            return False
    
    def _handle_rar(self, operation: str, archive_path: str, 
                    output_path: str, files: Optional[List[str]] = None,
                    progress_callback: Optional[Callable] = None) -> bool:
        """处理 RAR 格式"""
        try:
            if operation == 'extract':
                with rarfile.RarFile(archive_path) as archive:
                    if files:
                        for file in files:
                            archive.extract(file, output_path)
                    else:
                        archive.extractall(output_path)
                return True
        except Exception as e:
            self.logger.error(f"RAR 操作失败: {e}")
            return False
    
    def _handle_tar(self, operation: str, archive_path: str, 
                    output_path: str, files: Optional[List[str]] = None,
                    progress_callback: Optional[Callable] = None) -> bool:
        """处理 TAR 格式"""
        try:
            if operation == 'extract':
                patoolib.extract_archive(archive_path, outdir=output_path)
                return True
        except Exception as e:
            self.logger.error(f"TAR 操作失败: {e}")
            return False
    
    def _handle_gz(self, operation: str, archive_path: str, 
                   output_path: str, files: Optional[List[str]] = None,
                   progress_callback: Optional[Callable] = None) -> bool:
        """处理 GZ 格式"""
        return self._handle_tar(operation, archive_path, output_path, files, progress_callback)
    
    def _handle_bz2(self, operation: str, archive_path: str, 
                    output_path: str, files: Optional[List[str]] = None,
                    progress_callback: Optional[Callable] = None) -> bool:
        """处理 BZ2 格式"""
        return self._handle_tar(operation, archive_path, output_path, files, progress_callback)
    
    def _handle_xz(self, operation: str, archive_path: str, 
                   output_path: str, files: Optional[List[str]] = None,
                   progress_callback: Optional[Callable] = None) -> bool:
        """处理 XZ 格式"""
        return self._handle_tar(operation, archive_path, output_path, files, progress_callback)
    
    def _create_7z(self, files: List[str], archive_path: str,
                   progress_callback: Optional[Callable] = None) -> bool:
        """创建 7z 压缩包"""
        try:
            with py7zr.SevenZipFile(archive_path, 'w') as archive:
                for file_path in files:
                    path = Path(file_path)
                    if path.is_file():
                        archive.write(path, path.name)
                    elif path.is_dir():
                        for sub_file in path.rglob('*'):
                            if sub_file.is_file():
                                rel_path = sub_file.relative_to(path.parent)
                                archive.write(sub_file, str(rel_path))
            return True
        except Exception as e:
            self.logger.error(f"创建 7z 失败: {e}")
            return False
    
    def _create_zip(self, files: List[str], archive_path: str,
                    progress_callback: Optional[Callable] = None) -> bool:
        """创建 ZIP 压缩包"""
        try:
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as archive:
                for file_path in files:
                    path = Path(file_path)
                    if path.is_file():
                        archive.write(path, path.name)
                    elif path.is_dir():
                        for sub_file in path.rglob('*'):
                            if sub_file.is_file():
                                rel_path = sub_file.relative_to(path.parent)
                                archive.write(sub_file, str(rel_path))
            return True
        except Exception as e:
            self.logger.error(f"创建 ZIP 失败: {e}")
            return False
    
    def get_archive_details(self, archive_path: str) -> Dict:
        """获取压缩包详细信息"""
        try:
            path = Path(archive_path)
            if not path.exists():
                raise FileNotFoundError(f"文件不存在: {archive_path}")
            
            suffix = path.suffix.lower()
            files = []
            
            if suffix == '.zip':
                with zipfile.ZipFile(archive_path, 'r') as zf:
                    for info in zf.infolist():
                        files.append({
                            'name': info.filename,
                            'size': info.file_size,
                            'compressed_size': info.compress_size,
                            'modified': datetime(*info.date_time)
                        })
            elif suffix == '.7z':
                with py7zr.SevenZipFile(archive_path, mode='r') as szf:
                    for info in szf.list():
                        files.append({
                            'name': info.filename,
                            'size': info.uncompressed if hasattr(info, 'uncompressed') else 0,
                            'compressed_size': info.compressed if hasattr(info, 'compressed') else 0,
                            'modified': info.creationtime if hasattr(info, 'creationtime') else datetime.now()
                        })
            elif suffix == '.rar':
                with rarfile.RarFile(archive_path) as rf:
                    for info in rf.infolist():
                        files.append({
                            'name': info.filename,
                            'size': info.file_size,
                            'compressed_size': info.compress_size,
                            'modified': datetime(*info.date_time)
                        })
            
            return {
                'files': files,
                'file_count': len(files),
                'total_size': sum(f['size'] for f in files),
                'compressed_size': sum(f.get('compressed_size', 0) for f in files)
            }
            
        except Exception as e:
            self.logger.error(f"获取压缩包详情失败: {e}")
            return {'files': [], 'file_count': 0, 'total_size': 0, 'compressed_size': 0}
    
    def close(self):
        """关闭管理器"""
        self.logger.info("压缩包管理器已关闭")