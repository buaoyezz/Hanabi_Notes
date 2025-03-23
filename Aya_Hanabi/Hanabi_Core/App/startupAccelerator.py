# 启动加速器模块
import os
import sys
import time
import gc
import platform
import threading
from typing import Dict, List, Optional, Any

class StartupAccelerator:
    """应用启动加速优化器"""
    
    def __init__(self):
        self.start_time = time.time()
        self.loaded_resources = {}
        self.preloaded_modules = {}
        self.startup_phases = []
        self.phase_times = {}
        self.cached_resources = {}
        self.resource_locks = {}
    
    def preload_modules(self, module_list: List[str]) -> Dict[str, float]:
        """预加载模块
        
        Args:
            module_list: 要预加载的模块名列表
            
        Returns:
            各模块加载时间统计
        """
        results = {}
        
        for module_name in module_list:
            if module_name in sys.modules:
                # 模块已加载
                results[module_name] = 0
                self.preloaded_modules[module_name] = sys.modules[module_name]
                continue
                
            try:
                start = time.time()
                module = __import__(module_name, fromlist=['*'])
                duration = time.time() - start
                
                self.preloaded_modules[module_name] = module
                results[module_name] = duration
                print(f"预加载模块 {module_name} 完成 ({duration:.3f}s)")
            except ImportError as e:
                print(f"预加载模块 {module_name} 失败: {e}")
                results[module_name] = -1
        
        return results
    
    def optimize_imports(self) -> None:
        """优化Python导入机制
        
        修改sys.path和导入搜索路径，提高模块导入速度
        """
        # 将当前目录和常用目录移到path最前面
        current_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
        
        # 构建优化后的路径列表
        optimized_paths = [
            current_dir,  # 当前目录最优先
        ]
        
        # 将lib目录提前（如果存在）
        for path in sys.path:
            if path.endswith('lib') or path.endswith('site-packages'):
                if path not in optimized_paths:
                    optimized_paths.append(path)
        
        # 添加其余路径
        for path in sys.path:
            if path not in optimized_paths:
                optimized_paths.append(path)
        
        # 更新sys.path
        sys.path = optimized_paths
        print(f"已优化Python导入路径，共 {len(sys.path)} 个路径")
    
    def start_phase(self, name: str) -> None:
        """启动新的启动阶段
        
        Args:
            name: 阶段名称
        """
        self.startup_phases.append(name)
        self.phase_times[name] = [time.time(), None]
        print(f"启动阶段开始: {name}")
    
    def end_phase(self, name: str = None) -> float:
        """结束当前启动阶段
        
        Args:
            name: 阶段名称，如为None则使用最后一个未结束的阶段
            
        Returns:
            阶段耗时(秒)
        """
        if name is None and self.startup_phases:
            name = self.startup_phases[-1]
            
        if name in self.phase_times and self.phase_times[name][1] is None:
            end_time = time.time()
            self.phase_times[name][1] = end_time
            duration = end_time - self.phase_times[name][0]
            print(f"启动阶段结束: {name} (耗时 {duration:.3f}s)")
            return duration
        
        return 0
    
    def precache_resource(self, key: str, resource_loader: callable, *args, **kwargs) -> Any:
        """预缓存资源
        
        Args:
            key: 资源标识
            resource_loader: 资源加载函数
            *args, **kwargs: 传递给加载函数的参数
            
        Returns:
            加载的资源
        """
        # 创建资源锁，防止并发加载同一资源
        if key not in self.resource_locks:
            self.resource_locks[key] = threading.Lock()
            
        with self.resource_locks[key]:
            if key in self.cached_resources:
                return self.cached_resources[key]
                
            try:
                start_time = time.time()
                resource = resource_loader(*args, **kwargs)
                load_time = time.time() - start_time
                
                self.cached_resources[key] = resource
                print(f"预缓存资源 {key} 完成 ({load_time:.3f}s)")
                return resource
            except Exception as e:
                print(f"预缓存资源 {key} 失败: {e}")
                return None
    
    def get_cached_resource(self, key: str) -> Any:
        """获取已缓存的资源
        
        Args:
            key: 资源标识
            
        Returns:
            缓存的资源，不存在则返回None
        """
        return self.cached_resources.get(key)
    
    def optimize_process(self) -> None:
        """优化进程设置"""
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
        
        # 禁用Python垃圾回收器，将手动控制
        gc.disable()
        print("Python垃圾回收器已禁用，将在必要时手动运行")
    
    def get_startup_time(self) -> float:
        """获取总启动时间(秒)"""
        return time.time() - self.start_time
    
    def get_phase_stats(self) -> Dict[str, float]:
        """获取各阶段耗时统计"""
        stats = {}
        for phase, times in self.phase_times.items():
            start_time, end_time = times
            if end_time is None:
                end_time = time.time()
            stats[phase] = end_time - start_time
        return stats