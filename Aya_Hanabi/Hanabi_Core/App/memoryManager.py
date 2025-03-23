# 内存管理器模块
import gc
import sys
import psutil
import os
import platform
import threading
import time
from typing import Dict, Optional, Callable

class MemoryManager:
    """内存管理器，提供内存监控和优化功能"""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.threshold_mb = 150  # 默认内存阈值(MB)
        self.monitor_interval = 30  # 默认监控间隔(秒)
        self.is_monitoring = False
        self.monitor_thread = None
        self.callbacks = []  # 内存警告回调函数列表
        self.init_stats()
        
    def init_stats(self) -> None:
        """初始化统计数据"""
        self.stats = {
            "peak_memory": 0,
            "cleaned_total": 0,
            "collection_count": 0,
            "warning_count": 0,
            "last_collection": 0
        }
    
    def get_memory_usage(self) -> float:
        """获取当前内存使用量(MB)"""
        try:
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            
            # 更新峰值记录
            if memory_mb > self.stats["peak_memory"]:
                self.stats["peak_memory"] = memory_mb
                
            return memory_mb
        except Exception as e:
            print(f"获取内存信息失败: {e}")
            return 0
    
    def collect_garbage(self, force: bool = False) -> float:
        """执行垃圾回收
        
        Args:
            force: 是否强制执行，忽略时间间隔限制
            
        Returns:
            清理的内存量(MB)，负值表示清理后内存反而增加
        """
        # 限制收集频率，防止过于频繁
        now = time.time()
        if not force and (now - self.stats["last_collection"]) < 10:  # 至少间隔10秒
            return 0
            
        self.stats["last_collection"] = now
        
        # 记录清理前内存
        before_mb = self.get_memory_usage()
        
        # 执行垃圾回收
        gc.collect()
        self.stats["collection_count"] += 1
        
        # 在Windows上额外尝试降低工作集大小
        if platform.system() == "Windows":
            try:
                import ctypes
                ctypes.windll.kernel32.SetProcessWorkingSetSize(
                    ctypes.windll.kernel32.GetCurrentProcess(), -1, -1)
            except Exception:
                pass
        
        # 计算清理效果
        after_mb = self.get_memory_usage()
        cleaned_mb = before_mb - after_mb
        
        # 更新统计
        if cleaned_mb > 0:
            self.stats["cleaned_total"] += cleaned_mb
            
        return cleaned_mb
    
    def start_monitoring(self) -> None:
        """启动内存监控线程"""
        if self.is_monitoring:
            return
            
        def _monitor_task():
            while self.is_monitoring:
                try:
                    current_mb = self.get_memory_usage()
                    
                    # 检查是否超过阈值
                    if current_mb > self.threshold_mb:
                        cleaned = self.collect_garbage()
                        self.stats["warning_count"] += 1
                        
                        # 调用注册的回调函数
                        for callback in self.callbacks:
                            try:
                                callback(current_mb, cleaned)
                            except Exception as e:
                                print(f"内存警告回调执行失败: {e}")
                                
                except Exception as e:
                    print(f"内存监控异常: {e}")
                    
                time.sleep(self.monitor_interval)
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(
            target=_monitor_task, 
            daemon=True, 
            name="MemoryMonitor"
        )
        self.monitor_thread.start()
        print(f"内存监控已启动: 阈值 {self.threshold_mb} MB, 间隔 {self.monitor_interval} 秒")
    
    def stop_monitoring(self) -> None:
        """停止内存监控"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
            self.monitor_thread = None
        print("内存监控已停止")
    
    def set_threshold(self, threshold_mb: int) -> None:
        """设置内存阈值
        
        Args:
            threshold_mb: 内存阈值(MB)
        """
        self.threshold_mb = max(50, threshold_mb)  # 最小值50MB
        print(f"内存阈值已设置为 {self.threshold_mb} MB")
    
    def set_interval(self, seconds: int) -> None:
        """设置监控间隔
        
        Args:
            seconds: 监控间隔(秒)
        """
        self.monitor_interval = max(5, seconds)  # 最小值5秒
        print(f"监控间隔已设置为 {self.monitor_interval} 秒")
    
    def add_warning_callback(self, callback: Callable[[float, float], None]) -> None:
        """添加内存警告回调函数
        
        Args:
            callback: 回调函数，接收两个参数(当前内存MB, 清理量MB)
        """
        if callback not in self.callbacks:
            self.callbacks.append(callback)
    
    def get_stats(self) -> Dict[str, float]:
        """获取内存管理统计信息"""
        return self.stats