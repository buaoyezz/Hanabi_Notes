# 应用优化器主类
import gc
import os
import sys
import time
import threading
import platform
from typing import Dict, List, Optional

# 尝试导入psutil，如果失败则提供友好提示
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("警告: psutil模块未安装，应用优化功能将受限")
    print("建议执行: pip install psutil")

class AppOptimizer:
    """Hanabi Notes应用优化器，提供内存优化和启动加速"""
    
    def __init__(self):
        if not PSUTIL_AVAILABLE:
            self.process = None
            print("AppOptimizer: psutil未安装，部分功能不可用")
        else:
            self.process = psutil.Process(os.getpid())
        self.memory_threshold = 200 * 1024 * 1024  # 默认200MB阈值
        self.preloaded_modules = {}
        self.is_monitoring = False
        self.monitor_thread = None
        self.startup_time = time.time()
        self.optimization_stats = {
            "memory_cleaned": 0,
            "gc_collections": 0,
            "startup_time": 0,
            "preloaded_modules": 0
        }
    
    def preload_modules(self, modules_list: List[str]) -> Dict[str, float]:
        """预加载模块以加速应用启动
        
        Args:
            modules_list: 要预加载的模块名称列表
            
        Returns:
            模块加载时间统计
        """
        result = {}
        print("正在预加载模块...")
        
        for module_name in modules_list:
            try:
                start_time = time.time()
                if module_name not in sys.modules:
                    __import__(module_name)
                    self.preloaded_modules[module_name] = sys.modules[module_name]
                    load_time = time.time() - start_time
                    result[module_name] = load_time
                    print(f"  预加载模块 {module_name} 完成 ({load_time:.3f}秒)")
                else:
                    self.preloaded_modules[module_name] = sys.modules[module_name]
                    result[module_name] = 0
                    print(f"  模块 {module_name} 已加载")
            except ImportError as e:
                print(f"  预加载模块 {module_name} 失败: {e}")
                result[module_name] = -1
        
        self.optimization_stats["preloaded_modules"] = len(self.preloaded_modules)
        return result
    
    def optimize_memory(self, force: bool = False) -> int:
        """优化内存使用，清理未使用的对象
        
        Args:
            force: 是否强制执行优化，忽略内存使用阈值
            
        Returns:
            清理前后的内存差值(字节)
        """
        memory_before = self.get_memory_usage()
        
        # 如果内存使用低于阈值且不强制执行，则跳过
        if memory_before < self.memory_threshold and not force:
            return 0
        
        # 执行垃圾回收
        gc.collect()
        self.optimization_stats["gc_collections"] += 1
        
        # 在Windows上尝试额外的内存释放
        if platform.system() == "Windows":
            try:
                import ctypes
                ctypes.windll.kernel32.SetProcessWorkingSetSize(
                    ctypes.windll.kernel32.GetCurrentProcess(), -1, -1)
            except Exception as e:
                print(f"Windows内存释放失败: {e}")
        
        memory_after = self.get_memory_usage()
        memory_cleaned = memory_before - memory_after
        
        self.optimization_stats["memory_cleaned"] += memory_cleaned
        
        if memory_cleaned > 0:
            print(f"内存优化完成: 释放 {memory_cleaned / 1024 / 1024:.2f} MB")
        
        return memory_cleaned
    
    def get_memory_usage(self) -> int:
        """获取当前进程的内存使用量(字节)"""
        if not PSUTIL_AVAILABLE or not self.process:
            return 0  # 如果没有psutil，返回0表示无法监控
            
        try:
            return self.process.memory_info().rss
        except Exception as e:
            print(f"获取内存使用信息失败: {e}")
            return 0
    
    def start_memory_monitor(self, interval: int = 60) -> None:
        """启动内存监控线程
        
        Args:
            interval: 监控间隔(秒)
        """
        if self.is_monitoring:
            return
            
        # 如果没有psutil，不启动监控
        if not PSUTIL_AVAILABLE:
            print("内存监控无法启动: 缺少psutil模块")
            return
            
        def _monitor_task():
            while self.is_monitoring:
                current_usage = self.get_memory_usage()
                print(f"内存监控: 当前使用 {current_usage / 1024 / 1024:.2f} MB")
                
                if current_usage > self.memory_threshold:
                    print(f"内存使用超过阈值 {self.memory_threshold / 1024 / 1024:.2f} MB，执行优化")
                    self.optimize_memory()
                
                time.sleep(interval)
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(
            target=_monitor_task, 
            daemon=True, 
            name="HanabiMemoryMonitor"
        )
        self.monitor_thread.start()
        print(f"内存监控已启动，间隔 {interval} 秒，阈值 {self.memory_threshold / 1024 / 1024:.2f} MB")
    
    def stop_memory_monitor(self) -> None:
        """停止内存监控线程"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
            self.monitor_thread = None
            print("内存监控已停止")
    
    def set_memory_threshold(self, threshold_mb: int) -> None:
        """设置内存优化阈值
        
        Args:
            threshold_mb: 阈值(MB)
        """
        self.memory_threshold = threshold_mb * 1024 * 1024
        print(f"内存优化阈值已设置为 {threshold_mb} MB")
    
    def accelerate_startup(self) -> float:
        """执行启动加速优化
        
        Returns:
            启动耗时(秒)
        """
        # 预加载常用模块
        common_modules = [
            "PySide6.QtWidgets",
            "PySide6.QtCore",
            "PySide6.QtGui",
            "os", 
            "sys",
            "json",
            "datetime"
        ]
        
        self.preload_modules(common_modules)
        
        # 设置进程优先级
        try:
            if platform.system() == "Windows":
                import ctypes
                process_handle = ctypes.windll.kernel32.GetCurrentProcess()
                ctypes.windll.kernel32.SetPriorityClass(process_handle, 0x00008000)  # HIGH_PRIORITY_CLASS
                print("进程优先级已设置为高")
            elif platform.system() == "Linux":
                os.nice(-10)  # 提高进程优先级
                print("进程优先级已提高")
        except Exception as e:
            print(f"设置进程优先级失败: {e}")
        
        # 禁用不必要的功能
        try:
            # 禁用Python垃圾回收器，我们会手动控制
            gc.disable()
            print("Python垃圾回收器已禁用，将由内存监控器管理")
        except Exception as e:
            print(f"禁用垃圾回收器失败: {e}")
        
        startup_time = time.time() - self.startup_time
        self.optimization_stats["startup_time"] = startup_time
        print(f"启动加速完成，启动耗时: {startup_time:.3f} 秒")
        
        return startup_time
    
    def get_optimization_stats(self) -> Dict[str, float]:
        """获取优化统计信息"""
        return self.optimization_stats
    
    def cleanup(self) -> None:
        """清理资源，应用退出前调用"""
        self.stop_memory_monitor()
        gc.enable()  # 重新启用垃圾回收器
        self.optimize_memory(force=True)
        print("应用优化器已清理资源")