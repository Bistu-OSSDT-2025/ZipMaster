import os
import time
import itertools
import string
import zipfile
import rarfile
import py7zr
import threading
import queue
import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import datetime

class ArchivePasswordCracker:
    """
    压缩包密码爆破教学模块 - 仅供网络安全教学使用
    
    功能：
    - 支持多种压缩格式：ZIP, RAR, 7z
    - 暴力破解（Brute-force）
    - 字典攻击（Dictionary attack）
    - 混合攻击（Hybrid attack）
    - 多线程加速
    - 密码强度评估
    - 破解过程可视化
    - 防御机制模拟
    """
    
    def __init__(self, max_length=8):
        # 初始化字符集
        self.char_sets = {
            'lower': string.ascii_lowercase,
            'upper': string.ascii_uppercase,
            'digits': string.digits,
            'symbols': string.punctuation,
            'alphanumeric': string.ascii_letters + string.digits,
            'all': string.ascii_letters + string.digits + string.punctuation
        }
        
        # 攻击历史记录
        self.attack_history = []
        self.max_length = max_length
        
        # 加载常用密码字典
        self.common_passwords = self.load_common_passwords()
        
        # 多线程相关
        self.found = False
        self.password_queue = queue.Queue()
        self.result_queue = queue.Queue()
    
    def load_common_passwords(self):
        """加载常用密码字典"""
        common_passwords = [
            'password', '123456', '12345678', '123456789', 'admin', 
            'qwerty', 'abc123', 'letmein', 'welcome', 'password1',
            '12345', '1234567', '123123', '111111', 'sunshine', 
            'iloveyou', 'monkey', 'dragon', 'football', 'baseball'
        ]
        return set(common_passwords)
    
    def try_password(self, archive_path, password, file_type):
        """尝试使用密码解压文件"""
        try:
            if file_type == 'zip':
                with zipfile.ZipFile(archive_path) as zf:
                    zf.extractall(pwd=password.encode())
                return True
            elif file_type == 'rar':
                with rarfile.RarFile(archive_path) as rf:
                    rf.extractall(pwd=password)
                return True
            elif file_type == '7z':
                with py7zr.SevenZipFile(archive_path, password=password) as zf:
                    zf.extractall()
                return True
        except (RuntimeError, zipfile.BadZipFile, rarfile.BadRarFile, 
                rarfile.RarWrongPassword, py7zr.Bad7zFile, py7zr.PasswordRequired):
            return False
        return False
    
    def worker(self, archive_path, file_type, attack_id):
        """工作线程，尝试密码队列中的密码"""
        while not self.found and not self.password_queue.empty():
            try:
                password = self.password_queue.get(timeout=0.1)
                start_time = time.time()
                
                # 尝试密码
                success = self.try_password(archive_path, password, file_type)
                
                # 记录尝试
                self.result_queue.put({
                    'attack_id': attack_id,
                    'password': password,
                    'success': success,
                    'time_taken': time.time() - start_time
                })
                
                if success:
                    self.found = True
                    return
                    
            except queue.Empty:
                pass
    
    def brute_force_attack(self, archive_path, file_type, charset='alphanumeric', 
                           min_length=1, max_length=8, num_threads=4):
        """
        暴力破解攻击
        :param archive_path: 压缩包路径
        :param file_type: 文件类型 (zip, rar, 7z)
        :param charset: 使用的字符集
        :param min_length: 最小密码长度
        :param max_length: 最大密码长度
        :param num_threads: 线程数
        :return: (是否成功, 密码, 尝试次数, 耗时)
        """
        if charset not in self.char_sets:
            raise ValueError(f"无效字符集: {charset}")
        
        chars = self.char_sets[charset]
        start_time = time.time()
        attempts = 0
        
        # 清空队列
        self.found = False
        while not self.password_queue.empty():
            self.password_queue.get()
        while not self.result_queue.empty():
            self.result_queue.get()
        
        # 生成密码并加入队列
        for length in range(min_length, max_length + 1):
            for combination in itertools.product(chars, repeat=length):
                self.password_queue.put(''.join(combination))
        
        total_passwords = self.password_queue.qsize()
        
        # 记录攻击开始
        attack_id = len(self.attack_history) + 1
        self.attack_history.append({
            'id': attack_id,
            'type': 'brute_force',
            'archive': os.path.basename(archive_path),
            'charset': charset,
            'min_length': min_length,
            'max_length': max_length,
            'start_time': datetime.now(),
            'status': 'running',
            'attempts': 0,
            'passwords_per_sec': 0,
            'password_found': None,
            'total_passwords': total_passwords
        })
        
        # 创建并启动工作线程
        threads = []
        for _ in range(num_threads):
            t = threading.Thread(target=self.worker, args=(archive_path, file_type, attack_id))
            t.daemon = True
            t.start()
            threads.append(t)
        
        # 监控进度
        last_update = time.time()
        update_interval = 1.0  # 每秒更新一次
        
        while any(t.is_alive() for t in threads) and not self.found:
            time.sleep(0.1)
            
            # 更新进度
            current_time = time.time()
            if current_time - last_update >= update_interval:
                # 处理结果队列
                results = []
                while not self.result_queue.empty():
                    results.append(self.result_queue.get())
                
                attempts += len(results)
                
                # 更新攻击记录
                if results:
                    self.attack_history[-1]['attempts'] = attempts
                    self.attack_history[-1]['passwords_per_sec'] = len(results) / (current_time - last_update)
                
                last_update = current_time
        
        # 处理剩余结果
        results = []
        while not self.result_queue.empty():
            results.append(self.result_queue.get())
        
        attempts += len(results)
        
        # 检查是否找到密码
        found_password = None
        for result in results:
            if result['success']:
                found_password = result['password']
                break
        
        end_time = time.time()
        time_taken = end_time - start_time
        
        # 更新攻击记录
        if found_password:
            self.attack_history[-1].update({
                'end_time': datetime.now(),
                'status': 'success',
                'attempts': attempts,
                'password_found': found_password,
                'time_taken': time_taken,
                'passwords_per_sec': attempts / time_taken
            })
            return True, found_password, attempts, time_taken
        else:
            self.attack_history[-1].update({
                'end_time': datetime.now(),
                'status': 'failed',
                'attempts': attempts,
                'time_taken': time_taken,
                'passwords_per_sec': attempts / time_taken
            })
            return False, None, attempts, time_taken
    
    def dictionary_attack(self, archive_path, file_type, dictionary=None, num_threads=4):
        """
        字典攻击
        :param archive_path: 压缩包路径
        :param file_type: 文件类型 (zip, rar, 7z)
        :param dictionary: 自定义字典
        :param num_threads: 线程数
        :return: (是否成功, 密码, 尝试次数, 耗时)
        """
        if dictionary is None:
            dictionary = self.common_passwords
        
        start_time = time.time()
        
        # 清空队列
        self.found = False
        while not self.password_queue.empty():
            self.password_queue.get()
        while not self.result_queue.empty():
            self.result_queue.get()
        
        # 添加字典密码到队列
        for password in dictionary:
            self.password_queue.put(password)
        
        total_passwords = len(dictionary)
        
        # 记录攻击开始
        attack_id = len(self.attack_history) + 1
        self.attack_history.append({
            'id': attack_id,
            'type': 'dictionary',
            'archive': os.path.basename(archive_path),
            'dictionary_size': len(dictionary),
            'start_time': datetime.now(),
            'status': 'running',
            'attempts': 0,
            'passwords_per_sec': 0,
            'password_found': None,
            'total_passwords': total_passwords
        })
        
        # 创建并启动工作线程
        threads = []
        for _ in range(num_threads):
            t = threading.Thread(target=self.worker, args=(archive_path, file_type, attack_id))
            t.daemon = True
            t.start()
            threads.append(t)
        
        # 监控进度
        last_update = time.time()
        update_interval = 1.0  # 每秒更新一次
        attempts = 0
        
        while any(t.is_alive() for t in threads) and not self.found:
            time.sleep(0.1)
            
            # 更新进度
            current_time = time.time()
            if current_time - last_update >= update_interval:
                # 处理结果队列
                results = []
                while not self.result_queue.empty():
                    results.append(self.result_queue.get())
                
                attempts += len(results)
                
                # 更新攻击记录
                if results:
                    self.attack_history[-1]['attempts'] = attempts
                    self.attack_history[-1]['passwords_per_sec'] = len(results) / (current_time - last_update)
                
                last_update = current_time
        
        # 处理剩余结果
        results = []
        while not self.result_queue.empty():
            results.append(self.result_queue.get())
        
        attempts += len(results)
        
        # 检查是否找到密码
        found_password = None
        for result in results:
            if result['success']:
                found_password = result['password']
                break
        
        end_time = time.time()
        time_taken = end_time - start_time
        
        # 更新攻击记录
        if found_password:
            self.attack_history[-1].update({
                'end_time': datetime.now(),
                'status': 'success',
                'attempts': attempts,
                'password_found': found_password,
                'time_taken': time_taken,
                'passwords_per_sec': attempts / time_taken
            })
            return True, found_password, attempts, time_taken
        else:
            self.attack_history[-1].update({
                'end_time': datetime.now(),
                'status': 'failed',
                'attempts': attempts,
                'time_taken': time_taken,
                'passwords_per_sec': attempts / time_taken
            })
            return False, None, attempts, time_taken
    
    def hybrid_attack(self, archive_path, file_type, dictionary=None, 
                      charset='alphanumeric', suffix_length=2, num_threads=4):
        """
        混合攻击（字典+暴力破解）
        :param archive_path: 压缩包路径
        :param file_type: 文件类型 (zip, rar, 7z)
        :param dictionary: 自定义字典
        :param charset: 使用的字符集
        :param suffix_length: 后缀长度
        :param num_threads: 线程数
        :return: (是否成功, 密码, 尝试次数, 耗时)
        """
        if dictionary is None:
            dictionary = self.common_passwords
        
        if charset not in self.char_sets:
            raise ValueError(f"无效字符集: {charset}")
        
        chars = self.char_sets[charset]
        start_time = time.time()
        
        # 清空队列
        self.found = False
        while not self.password_queue.empty():
            self.password_queue.get()
        while not self.result_queue.empty():
            self.result_queue.get()
        
        # 生成混合密码并加入队列
        suffixes = [''.join(p) for p in itertools.product(chars, repeat=suffix_length)]
        for base in dictionary:
            for suffix in suffixes:
                self.password_queue.put(base + suffix)
        
        total_passwords = len(dictionary) * (len(chars) ** suffix_length)
        
        # 记录攻击开始
        attack_id = len(self.attack_history) + 1
        self.attack_history.append({
            'id': attack_id,
            'type': 'hybrid',
            'archive': os.path.basename(archive_path),
            'dictionary_size': len(dictionary),
            'charset': charset,
            'suffix_length': suffix_length,
            'start_time': datetime.now(),
            'status': 'running',
            'attempts': 0,
            'passwords_per_sec': 0,
            'password_found': None,
            'total_passwords': total_passwords
        })
        
        # 创建并启动工作线程
        threads = []
        for _ in range(num_threads):
            t = threading.Thread(target=self.worker, args=(archive_path, file_type, attack_id))
            t.daemon = True
            t.start()
            threads.append(t)
        
        # 监控进度
        last_update = time.time()
        update_interval = 1.0  # 每秒更新一次
        attempts = 0
        
        while any(t.is_alive() for t in threads) and not self.found:
            time.sleep(0.1)
            
            # 更新进度
            current_time = time.time()
            if current_time - last_update >= update_interval:
                # 处理结果队列
                results = []
                while not self.result_queue.empty():
                    results.append(self.result_queue.get())
                
                attempts += len(results)
                
                # 更新攻击记录
                if results:
                    self.attack_history[-1]['attempts'] = attempts
                    self.attack_history[-1]['passwords_per_sec'] = len(results) / (current_time - last_update)
                
                last_update = current_time
        
        # 处理剩余结果
        results = []
        while not self.result_queue.empty():
            results.append(self.result_queue.get())
        
        attempts += len(results)
        
        # 检查是否找到密码
        found_password = None
        for result in results:
            if result['success']:
                found_password = result['password']
                break
        
        end_time = time.time()
        time_taken = end_time - start_time
        
        # 更新攻击记录
        if found_password:
            self.attack_history[-1].update({
                'end_time': datetime.now(),
                'status': 'success',
                'attempts': attempts,
                'password_found': found_password,
                'time_taken': time_taken,
                'passwords_per_sec': attempts / time_taken
            })
            return True, found_password, attempts, time_taken
        else:
            self.attack_history[-1].update({
                'end_time': datetime.now(),
                'status': 'failed',
                'attempts': attempts,
                'time_taken': time_taken,
                'passwords_per_sec': attempts / time_taken
            })
            return False, None, attempts, time_taken
    
    def evaluate_password_strength(self, password):
        """
        评估密码强度
        :param password: 要评估的密码
        :return: 强度评分 (0-100)
        """
        length = len(password)
        score = min(length * 4, 40)  # 长度最多占40分
        
        # 字符种类加分
        has_upper = any(c in string.ascii_uppercase for c in password)
        has_lower = any(c in string.ascii_lowercase for c in password)
        has_digit = any(c in string.digits for c in password)
        has_symbol = any(c in string.punctuation for c in password)
        
        char_types = sum([has_upper, has_lower, has_digit, has_symbol])
        score += (char_types - 1) * 15  # 每多一种字符类型加15分
        
        # 常见密码检查
        if password.lower() in self.common_passwords:
            score = max(0, score - 30)
        
        return min(max(score, 0), 100)
    
    def get_attack_history(self):
        """获取攻击历史"""
        return self.attack_history
    
    def reset_history(self):
        """重置攻击历史"""
        self.attack_history = []
    
    def visualize_attack_comparison(self):
        """可视化不同攻击类型的性能比较"""
        if not self.attack_history:
            print("没有攻击历史可供可视化")
            return
        
        attack_types = defaultdict(list)
        for attack in self.attack_history:
            if attack['status'] == 'success':
                attack_types[attack['type']].append({
                    'attempts': attack['attempts'],
                    'time': attack['time_taken'],
                    'speed': attack['passwords_per_sec']
                })
        
        if not attack_types:
            print("没有成功的攻击可供比较")
            return
        
        # 准备数据
        types = []
        avg_attempts = []
        avg_times = []
        avg_speeds = []
        
        for attack_type, results in attack_types.items():
            types.append(attack_type)
            avg_attempts.append(sum(r['attempts'] for r in results) / len(results))
            avg_times.append(sum(r['time'] for r in results) / len(results))
            avg_speeds.append(sum(r['speed'] for r in results) / len(results))
        
        # 创建图表
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12))
        
        # 平均尝试次数
        ax1.bar(types, avg_attempts, color='skyblue')
        ax1.set_title('不同攻击方法的平均尝试次数')
        ax1.set_ylabel('尝试次数')
        ax1.grid(axis='y', linestyle='--', alpha=0.7)
        
        # 平均耗时
        ax2.bar(types, avg_times, color='lightcoral')
        ax2.set_title('不同攻击方法的平均耗时 (秒)')
        ax2.set_ylabel('时间 (秒)')
        ax2.grid(axis='y', linestyle='--', alpha=0.7)
        
        # 平均速度
        ax3.bar(types, avg_speeds, color='lightgreen')
        ax3.set_title('不同攻击方法的平均速度 (密码/秒)')
        ax3.set_ylabel('速度 (密码/秒)')
        ax3.grid(axis='y', linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        plt.show()
    
    def visualize_password_strength(self, passwords):
        """可视化密码强度分布"""
        strengths = [self.evaluate_password_strength(pwd) for pwd in passwords]
        
        plt.figure(figsize=(10, 6))
        plt.hist(strengths, bins=20, color='skyblue', edgecolor='black')
        plt.title('密码强度分布')
        plt.xlabel('强度分数 (0-100)')
        plt.ylabel('密码数量')
        plt.grid(axis='y', alpha=0.75)
        plt.show()


# 教学演示
if __name__ == "__main__":
    print("=" * 60)
    print("压缩包密码爆破教学模块 - 仅供网络安全教学使用")
    print("=" * 60)
    print("本模块用于演示常见密码攻击技术，帮助学生理解密码安全的重要性")
    print("请勿将此模块用于任何非法目的\n")
    
    # 创建测试压缩包
    TEST_DIR = "test_archives"
    os.makedirs(TEST_DIR, exist_ok=True)
    
    # 创建带密码的测试文件
    def create_test_archive(archive_type, password, filename):
        test_file = os.path.join(TEST_DIR, "test.txt")
        with open(test_file, "w") as f:
            f.write("This is a test file for password cracking demonstration.")
        
        archive_path = os.path.join(TEST_DIR, filename)
        
        if archive_type == "zip":
            with zipfile.ZipFile(archive_path, 'w') as zf:
                zf.write(test_file, os.path.basename(test_file))
                zf.setpassword(password.encode())
        elif archive_type == "rar":
            with rarfile.RarFile(archive_path, 'w') as rf:
                rf.write(test_file, os.path.basename(test_file))
                # RAR 创建时需要设置密码，但标准库不支持，这里仅演示
                print(f"注意: Python rarfile 库不支持创建加密 RAR 文件。请手动创建或使用其他工具。")
        elif archive_type == "7z":
            with py7zr.SevenZipFile(archive_path, 'w', password=password) as zf:
                zf.write(test_file, os.path.basename(test_file))
        
        os.remove(test_file)
        return archive_path
    
    # 创建测试压缩包
    weak_password = "12345"
    strong_password = "Secur3P@ss!"
    
    zip_weak = create_test_archive("zip", weak_password, "weak_password.zip")
    zip_strong = create_test_archive("zip", strong_password, "strong_password.zip")
    # 7z_weak = create_test_archive("7z", weak_password, "weak_password.7z")
    # 7z_strong = create_test_archive("7z", strong_password, "strong_password.7z")
    
    cracker = ArchivePasswordCracker(max_length=8)
    
    # 评估密码强度
    weak_strength = cracker.evaluate_password_strength(weak_password)
    strong_strength = cracker.evaluate_password_strength(strong_password)
    print(f"弱密码 '{weak_password}' 强度: {weak_strength}/100")
    print(f"强密码 '{strong_password}' 强度: {strong_strength}/100\n")
    
    # 演示不同攻击方法
    print("=" * 60)
    print("开始演示密码攻击技术...\n")
    
    # 对弱密码ZIP进行字典攻击
    print("[字典攻击 - 弱密码ZIP]")
    success, password, attempts, time_taken = cracker.dictionary_attack(
        zip_weak, "zip", dictionary=cracker.common_passwords
    )
    if success:
        print(f"成功破解密码: {password}")
        print(f"尝试次数: {attempts}, 耗时: {time_taken:.2f}秒, 速度: {attempts/time_taken:.2f} 密码/秒")
    else:
        print("字典攻击失败")
    print()
    
    # 对弱密码ZIP进行暴力破解
    print("[暴力破解 - 弱密码ZIP]")
    success, password, attempts, time_taken = cracker.brute_force_attack(
        zip_weak, "zip", charset="digits", min_length=4, max_length=6
    )
    if success:
        print(f"成功破解密码: {password}")
        print(f"尝试次数: {attempts}, 耗时: {time_taken:.2f}秒, 速度: {attempts/time_taken:.2f} 密码/秒")
    else:
        print("暴力破解失败")
    print()
    
    # 对强密码ZIP进行混合攻击
    print("[混合攻击 - 强密码ZIP]")
    success, password, attempts, time_taken = cracker.hybrid_attack(
        zip_strong, "zip", dictionary=cracker.common_passwords, suffix_length=2
    )
    if success:
        print(f"成功破解密码: {password}")
        print(f"尝试次数: {attempts}, 耗时: {time_taken:.2f}秒, 速度: {attempts/time_taken:.2f} 密码/秒")
    else:
        print("混合攻击失败")
    print()
    
    # 可视化攻击性能比较
    print("\n生成攻击性能比较图表...")
    cracker.visualize_attack_comparison()
    
    # 可视化密码强度
    test_passwords = [
        "password", "123456", "qwerty", "letmein", 
        "P@ssw0rd", "Secur3P@ss!", "Tr0ub4dor&3", "CorrectHorseBatteryStaple"
    ]
    print("\n生成密码强度分布图表...")
    cracker.visualize_password_strength(test_passwords)
    
    print("\n教学演示完成！")