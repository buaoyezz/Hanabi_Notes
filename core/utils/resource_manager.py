'''
资源管理器
负责管理应用的资源，包括图标、图片等
'''

from PySide6.QtGui import QIcon, QPixmap
import os
import sys
from core.log.log_manager import log

class ResourceManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ResourceManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.cache = {}
            log.info("资源管理器初始化完成")
    
    def get_resource_path(self, relative_path):
        """获取资源路径(相对或绝对)"""
        if hasattr(sys, '_MEIPASS'):
            # 打包后的路径
            base_path = sys._MEIPASS
        else:
            # 开发环境的路径
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)
    
    def get_icon(self, name):
        """获取图标对象"""
        if name in self.cache:
            return self.cache[name]
        
        try:
            # 尝试加载不同格式的图标
            for ext in ['png', 'ico', 'svg']:
                icon_path = self.get_resource_path(os.path.join("resources", f"{name}.{ext}"))
                if os.path.exists(icon_path):
                    icon = QIcon(icon_path)
                    if not icon.isNull():
                        self.cache[name] = icon
                        log.info(f"成功加载图标: {name}")
                        return icon
            
            log.error(f"未找到图标: {name}")
            return None
        except Exception as e:
            log.error(f"加载图标'{name}'失败: {str(e)}")
            return None
    
    def get_pixmap(self, name):
        """获取图片对象"""
        try:
            # 尝试加载不同格式的图片
            for ext in ['png', 'jpg', 'jpeg', 'bmp']:
                image_path = self.get_resource_path(os.path.join("resources", f"{name}.{ext}"))
                if os.path.exists(image_path):
                    pixmap = QPixmap(image_path)
                    if not pixmap.isNull():
                        log.info(f"成功加载图片: {name}")
                        return pixmap
            
            log.error(f"未找到图片: {name}")
            return None
        except Exception as e:
            log.error(f"加载图片'{name}'失败: {str(e)}")
            return None
    
    def clear_cache(self):
        """清除资源缓存"""
        self.cache.clear()
        log.info("已清除资源缓存") 