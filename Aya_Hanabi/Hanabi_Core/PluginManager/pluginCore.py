"""
Hanabi Notes 插件核心模块
提供插件基类和插件接口定义
"""

import os
import sys
import importlib
import inspect
import logging
from typing import Dict, List, Any, Callable, Optional, Type


class PluginMetadata:
    """插件元数据类，存储插件的基本信息"""
    
    def __init__(self, 
                 name: str, 
                 version: str, 
                 description: str = "", 
                 author: str = "", 
                 min_app_version: str = "1.0.0",
                 icon: str = None):
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.min_app_version = min_app_version
        self.icon = icon
        
    def to_dict(self) -> Dict[str, Any]:
        """将元数据转换为字典形式"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "min_app_version": self.min_app_version,
            "icon": self.icon
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginMetadata':
        """从字典创建元数据对象"""
        return cls(
            name=data.get("name", "未命名插件"),
            version=data.get("version", "0.1.0"),
            description=data.get("description", ""),
            author=data.get("author", ""),
            min_app_version=data.get("min_app_version", "1.0.0"),
            icon=data.get("icon", None)
        )


class HanabiPlugin:
    """Hanabi Notes 插件基类
    
    所有插件必须继承此类并实现必要的方法
    """
    
    def __init__(self, app_instance=None):
        """初始化插件
        
        Args:
            app_instance: 应用程序实例引用
        """
        self.app = app_instance
        self._metadata = None
        self._enabled = False
        self._hooks = {}
        self._menu_actions = []
        self._toolbar_actions = []
        self._settings = {}
    
    @property
    def metadata(self) -> PluginMetadata:
        """获取插件元数据"""
        if self._metadata is None:
            # 默认元数据
            self._metadata = PluginMetadata(
                name=self.__class__.__name__,
                version="0.1.0",
                description="未提供描述"
            )
        return self._metadata
    
    @metadata.setter
    def metadata(self, meta: PluginMetadata):
        """设置插件元数据"""
        self._metadata = meta
    
    @property
    def is_enabled(self) -> bool:
        """插件是否已启用"""
        return self._enabled
    
    def get_id(self) -> str:
        """获取插件唯一ID"""
        return f"{self.metadata.name}@{self.metadata.version}"
    
    def initialize(self) -> bool:
        """初始化插件
        
        在插件加载时被调用，用于设置和准备插件
        
        Returns:
            bool: 初始化是否成功
        """
        self._enabled = True
        return True
    
    def shutdown(self) -> bool:
        """关闭插件
        
        在应用程序关闭或插件被禁用时调用
        
        Returns:
            bool: 关闭是否成功
        """
        self._enabled = False
        return True
    
    def register_hook(self, hook_name: str, callback: Callable) -> bool:
        """注册钩子函数
        
        Args:
            hook_name: 钩子名称
            callback: 回调函数
            
        Returns:
            bool: 注册是否成功
        """
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        
        self._hooks[hook_name].append(callback)
        return True
    
    def get_hooks(self, hook_name: str) -> List[Callable]:
        """获取指定名称的所有钩子函数
        
        Args:
            hook_name: 钩子名称
            
        Returns:
            List[Callable]: 钩子函数列表
        """
        return self._hooks.get(hook_name, [])
    
    def add_menu_action(self, action_info: Dict[str, Any]) -> bool:
        """添加菜单动作
        
        Args:
            action_info: 动作信息，包含 text, callback 等
            
        Returns:
            bool: 是否添加成功
        """
        self._menu_actions.append(action_info)
        return True
    
    def get_menu_actions(self) -> List[Dict[str, Any]]:
        """获取所有菜单动作
        
        Returns:
            List[Dict[str, Any]]: 菜单动作列表
        """
        return self._menu_actions
    
    def add_toolbar_action(self, action_info: Dict[str, Any]) -> bool:
        """添加工具栏动作
        
        Args:
            action_info: 动作信息，包含 text, icon, callback 等
            
        Returns:
            bool: 是否添加成功
        """
        self._toolbar_actions.append(action_info)
        return True
    
    def get_toolbar_actions(self) -> List[Dict[str, Any]]:
        """获取所有工具栏动作
        
        Returns:
            List[Dict[str, Any]]: 工具栏动作列表
        """
        return self._toolbar_actions
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """获取插件设置
        
        Args:
            key: 设置键
            default: 默认值
            
        Returns:
            Any: 设置值
        """
        return self._settings.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> None:
        """设置插件设置
        
        Args:
            key: 设置键
            value: 设置值
        """
        self._settings[key] = value
    
    def get_settings(self) -> Dict[str, Any]:
        """获取所有插件设置
        
        Returns:
            Dict[str, Any]: 设置字典
        """
        return self._settings
    
    def load_settings(self, settings: Dict[str, Any]) -> None:
        """加载插件设置
        
        Args:
            settings: 设置字典
        """
        self._settings.update(settings)

    def create_settings_widget(self) -> Optional['QWidget']:
        """创建插件设置界面
        
        Returns:
            Optional[QWidget]: 设置界面小部件，如果没有则返回 None
        """
        return None


# 定义常用钩子点
class PluginHooks:
    # 应用程序生命周期钩子
    APP_STARTED = "app_started"  # 应用程序启动完成
    APP_SHUTDOWN = "app_shutdown"  # 应用程序关闭
    
    # 文件操作钩子
    FILE_OPENED = "file_opened"  # 文件打开后
    FILE_SAVED = "file_saved"  # 文件保存后
    FILE_CLOSED = "file_closed"  # 文件关闭后
    FILE_CREATED = "file_created"  # 文件创建后
    FILE_DELETED = "file_deleted"  # 文件删除后
    
    # 编辑器操作钩子
    EDITOR_CREATED = "editor_created"  # 编辑器创建
    EDITOR_FOCUSED = "editor_focused"  # 编辑器获取焦点
    EDITOR_CHANGED = "editor_changed"  # 编辑器内容改变
    
    # 界面操作钩子
    UI_THEME_CHANGED = "ui_theme_changed"  # 主题改变
    SETTINGS_SAVED = "settings_saved"  # 设置保存

    # 自定义扩展钩子
    CUSTOM_ACTION = "custom_action"  # 自定义动作


class FileHandler:
    """文件处理器基类
    
    插件可以通过继承此类来处理特定类型的文件
    """
    
    def __init__(self, extensions: List[str]):
        """初始化文件处理器
        
        Args:
            extensions: 支持的文件扩展名列表
        """
        self.extensions = extensions
    
    def can_handle(self, file_path: str) -> bool:
        """检查是否可以处理指定文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否可以处理
        """
        _, ext = os.path.splitext(file_path)
        return ext.lower() in [e.lower() for e in self.extensions]
    
    def open_file(self, file_path: str) -> str:
        """打开文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 文件内容
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def save_file(self, file_path: str, content: str) -> bool:
        """保存文件
        
        Args:
            file_path: 文件路径
            content: 文件内容
            
        Returns:
            bool: 是否保存成功
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            logging.error(f"保存文件时出错: {e}")
            return False


class PluginError(Exception):
    """插件错误基类"""
    pass


class PluginLoadError(PluginError):
    """插件加载错误"""
    pass


class PluginInitError(PluginError):
    """插件初始化错误"""
    pass


class PluginVersionError(PluginError):
    """插件版本不兼容错误"""
    pass
