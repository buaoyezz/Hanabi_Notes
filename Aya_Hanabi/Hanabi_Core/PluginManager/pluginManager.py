"""
Hanabi Notes 插件管理器
负责插件的加载、卸载和管理
"""

import os
import sys
import json
import logging
import importlib.util
import traceback
from typing import Dict, List, Any, Callable, Type, Optional, Set
from pathlib import Path

# 导入插件核心类
from .pluginCore import (
    HanabiPlugin, PluginMetadata, PluginHooks, FileHandler,
    PluginError, PluginLoadError, PluginInitError, PluginVersionError
)


class PluginManager:
    """插件管理器类，负责管理所有插件的生命周期"""
    
    def __init__(self, app_instance=None):
        """初始化插件管理器
        
        Args:
            app_instance: 应用程序实例
        """
        self.app = app_instance
        self.plugins: Dict[str, HanabiPlugin] = {}  # 已加载的插件
        self.plugin_paths: List[str] = []  # 插件搜索路径
        self.enabled_plugins: Set[str] = set()  # 已启用的插件ID
        self.file_handlers: Dict[str, List[FileHandler]] = {}  # 文件处理器
        self.hook_registry: Dict[str, List[Dict[str, Any]]] = {}  # 钩子注册表
        self.plugin_settings: Dict[str, Dict[str, Any]] = {}  # 插件设置
        self.is_initialized = False
    
    def initialize(self, plugin_dirs: List[str] = None) -> bool:
        """初始化插件管理器
        
        Args:
            plugin_dirs: 插件目录列表
            
        Returns:
            bool: 初始化是否成功
        """
        if self.is_initialized:
            return True
        
        # 设置默认插件目录
        if plugin_dirs is None:
            # 获取应用程序目录
            app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            plugin_dirs = [os.path.join(app_dir, "plugins")]
            
            # 添加用户插件目录
            user_plugin_dir = os.path.join(os.path.expanduser("~"), ".hanabi_notes", "plugins")
            plugin_dirs.append(user_plugin_dir)
        
        # 确保插件目录存在
        for plugin_dir in plugin_dirs:
            if not os.path.exists(plugin_dir):
                try:
                    os.makedirs(plugin_dir)
                    logging.info(f"创建插件目录: {plugin_dir}")
                except Exception as e:
                    logging.error(f"创建插件目录失败: {plugin_dir}, 错误: {e}")
        
        # 设置插件搜索路径
        self.plugin_paths = plugin_dirs
        
        # 加载插件设置
        self.load_plugin_settings()
        
        # 加载插件
        for plugin_dir in plugin_dirs:
            self.discover_plugins(plugin_dir)
        
        self.is_initialized = True
        return True
    
    def discover_plugins(self, plugin_dir: str) -> List[str]:
        """发现插件目录中的所有插件
        
        Args:
            plugin_dir: 插件目录
            
        Returns:
            List[str]: 发现的插件ID列表
        """
        discovered_plugins = []
        
        if not os.path.exists(plugin_dir):
            logging.warning(f"插件目录不存在: {plugin_dir}")
            return discovered_plugins
        
        # 遍历目录查找插件
        for item in os.listdir(plugin_dir):
            item_path = os.path.join(plugin_dir, item)
            
            # 检查是否是目录
            if os.path.isdir(item_path):
                # 检查是否包含 plugin.json 和 __init__.py
                plugin_json_path = os.path.join(item_path, "plugin.json")
                init_py_path = os.path.join(item_path, "__init__.py")
                
                if os.path.exists(plugin_json_path) and os.path.exists(init_py_path):
                    # 读取插件元数据
                    try:
                        with open(plugin_json_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        plugin_id = f"{metadata.get('name')}@{metadata.get('version')}"
                        
                        # 尝试加载插件
                        if self.load_plugin(item_path, metadata):
                            discovered_plugins.append(plugin_id)
                            logging.info(f"发现并加载插件: {plugin_id}")
                        else:
                            logging.error(f"加载插件失败: {plugin_id}")
                    except Exception as e:
                        logging.error(f"读取插件元数据失败: {item_path}, 错误: {e}")
        
        return discovered_plugins
    
    def load_plugin(self, plugin_path: str, metadata: Dict[str, Any]) -> bool:
        """加载单个插件
        
        Args:
            plugin_path: 插件路径
            metadata: 插件元数据
            
        Returns:
            bool: 是否加载成功
        """
        try:
            plugin_name = metadata.get('name')
            plugin_version = metadata.get('version')
            plugin_id = f"{plugin_name}@{plugin_version}"
            
            # 检查插件是否已加载
            if plugin_id in self.plugins:
                logging.warning(f"插件已加载: {plugin_id}")
                return True
            
            # 获取入口模块名
            plugin_module_name = os.path.basename(plugin_path)
            spec = importlib.util.spec_from_file_location(
                plugin_module_name,
                os.path.join(plugin_path, "__init__.py")
            )
            
            if spec is None:
                raise PluginLoadError(f"无法获取插件模块规范: {plugin_path}")
            
            # 加载模块
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            
            # 查找插件类
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    attr is not HanabiPlugin and
                    issubclass(attr, HanabiPlugin)):
                    plugin_class = attr
                    break
            
            if plugin_class is None:
                raise PluginLoadError(f"未找到插件类: {plugin_path}")
            
            # 创建插件实例
            plugin = plugin_class(self.app)
            
            # 设置元数据
            plugin_metadata = PluginMetadata.from_dict(metadata)
            plugin.metadata = plugin_metadata
            
            # 添加到插件列表
            self.plugins[plugin_id] = plugin
            
            # 加载插件设置
            if plugin_id in self.plugin_settings:
                plugin.load_settings(self.plugin_settings[plugin_id])
            
            # 检查插件是否应该启用
            if plugin_id in self.enabled_plugins:
                self.enable_plugin(plugin_id)
            
            return True
        except Exception as e:
            logging.error(f"加载插件失败: {plugin_path}, 错误: {e}")
            traceback.print_exc()
            return False
    
    def enable_plugin(self, plugin_id: str) -> bool:
        """启用插件
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            bool: 是否启用成功
        """
        if plugin_id not in self.plugins:
            logging.error(f"插件未加载: {plugin_id}")
            return False
        
        plugin = self.plugins[plugin_id]
        
        # 已启用则直接返回
        if plugin.is_enabled:
            return True
        
        try:
            # 初始化插件
            success = plugin.initialize()
            
            if success:
                # 注册插件的钩子
                for hook_name, callbacks in plugin._hooks.items():
                    for callback in callbacks:
                        self.register_hook(hook_name, plugin_id, callback)
                
                # 注册插件的菜单动作
                # TODO: 实现菜单动作注册
                
                # 注册插件的工具栏动作
                # TODO: 实现工具栏动作注册
                
                # 添加到已启用列表
                self.enabled_plugins.add(plugin_id)
                
                logging.info(f"插件已启用: {plugin_id}")
                return True
            else:
                logging.error(f"插件初始化失败: {plugin_id}")
                return False
        except Exception as e:
            logging.error(f"启用插件时出错: {plugin_id}, 错误: {e}")
            traceback.print_exc()
            return False
    
    def disable_plugin(self, plugin_id: str) -> bool:
        """禁用插件
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            bool: 是否禁用成功
        """
        if plugin_id not in self.plugins:
            logging.error(f"插件未加载: {plugin_id}")
            return False
        
        plugin = self.plugins[plugin_id]
        
        # 已禁用则直接返回
        if not plugin.is_enabled:
            return True
        
        try:
            # 关闭插件
            success = plugin.shutdown()
            
            if success:
                # 注销插件的钩子
                for hook_name in self.hook_registry:
                    self.hook_registry[hook_name] = [
                        hook for hook in self.hook_registry.get(hook_name, [])
                        if hook['plugin_id'] != plugin_id
                    ]
                
                # 注销插件的菜单动作
                # TODO: 实现菜单动作注销
                
                # 注销插件的工具栏动作
                # TODO: 实现工具栏动作注销
                
                # 从已启用列表中移除
                if plugin_id in self.enabled_plugins:
                    self.enabled_plugins.remove(plugin_id)
                
                logging.info(f"插件已禁用: {plugin_id}")
                return True
            else:
                logging.error(f"插件关闭失败: {plugin_id}")
                return False
        except Exception as e:
            logging.error(f"禁用插件时出错: {plugin_id}, 错误: {e}")
            return False
    
    def unload_plugin(self, plugin_id: str) -> bool:
        """卸载插件
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            bool: 是否卸载成功
        """
        if plugin_id not in self.plugins:
            logging.warning(f"插件未加载: {plugin_id}")
            return True
        
        # 先禁用插件
        if plugin_id in self.enabled_plugins:
            if not self.disable_plugin(plugin_id):
                logging.error(f"禁用插件失败，无法卸载: {plugin_id}")
                return False
        
        # 保存插件设置
        self.save_plugin_settings(plugin_id)
        
        # 从插件列表中移除
        del self.plugins[plugin_id]
        
        logging.info(f"插件已卸载: {plugin_id}")
        return True
    
    def get_plugin(self, plugin_id: str) -> Optional[HanabiPlugin]:
        """获取插件实例
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            Optional[HanabiPlugin]: 插件实例
        """
        return self.plugins.get(plugin_id)
    
    def get_plugins(self) -> Dict[str, HanabiPlugin]:
        """获取所有插件
        
        Returns:
            Dict[str, HanabiPlugin]: 所有插件的字典
        """
        return self.plugins
    
    def get_enabled_plugins(self) -> Dict[str, HanabiPlugin]:
        """获取所有已启用的插件
        
        Returns:
            Dict[str, HanabiPlugin]: 已启用插件的字典
        """
        return {
            plugin_id: plugin
            for plugin_id, plugin in self.plugins.items()
            if plugin.is_enabled
        }
    
    def register_hook(self, hook_name: str, plugin_id: str, callback: Callable) -> bool:
        """注册钩子
        
        Args:
            hook_name: 钩子名称
            plugin_id: 插件ID
            callback: 回调函数
            
        Returns:
            bool: 是否注册成功
        """
        if hook_name not in self.hook_registry:
            self.hook_registry[hook_name] = []
        
        self.hook_registry[hook_name].append({
            'plugin_id': plugin_id,
            'callback': callback
        })
        
        return True
    
    def trigger_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """触发钩子
        
        Args:
            hook_name: 钩子名称
            *args, **kwargs: 传递给钩子的参数
            
        Returns:
            List[Any]: 钩子函数的返回值列表
        """
        results = []
        
        if hook_name in self.hook_registry:
            for hook in self.hook_registry[hook_name]:
                try:
                    plugin_id = hook['plugin_id']
                    callback = hook['callback']
                    
                    # 检查插件是否启用
                    if plugin_id in self.enabled_plugins:
                        result = callback(*args, **kwargs)
                        results.append(result)
                except Exception as e:
                    logging.error(f"执行钩子时出错 {hook_name} (插件: {hook.get('plugin_id')}): {e}")
                    traceback.print_exc()
        
        return results
    
    def register_file_handler(self, plugin_id: str, handler: FileHandler) -> bool:
        """注册文件处理器
        
        Args:
            plugin_id: 插件ID
            handler: 文件处理器
            
        Returns:
            bool: 是否注册成功
        """
        for ext in handler.extensions:
            if ext not in self.file_handlers:
                self.file_handlers[ext] = []
            
            # 添加处理器
            handler_info = {
                'plugin_id': plugin_id,
                'handler': handler
            }
            self.file_handlers[ext].append(handler_info)
        
        return True
    
    def get_file_handlers(self, file_path: str) -> List[Dict[str, Any]]:
        """获取可以处理指定文件的处理器
        
        Args:
            file_path: 文件路径
            
        Returns:
            List[Dict[str, Any]]: 处理器信息列表
        """
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        handlers = []
        
        if ext in self.file_handlers:
            for handler_info in self.file_handlers[ext]:
                plugin_id = handler_info['plugin_id']
                
                # 检查插件是否启用
                if plugin_id in self.enabled_plugins:
                    handlers.append(handler_info)
        
        return handlers
    
    def load_plugin_settings(self) -> bool:
        """加载所有插件设置
        
        Returns:
            bool: 是否加载成功
        """
        try:
            settings_dir = os.path.join(os.path.expanduser("~"), ".hanabi_notes")
            settings_file = os.path.join(settings_dir, "plugin_settings.json")
            
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    self.plugin_settings = json.load(f)
                
                # 同时加载已启用插件列表
                self.enabled_plugins = set(self.plugin_settings.get('_enabled_plugins', []))
                
                logging.info(f"已加载插件设置，启用的插件数量: {len(self.enabled_plugins)}")
                return True
            else:
                logging.info("插件设置文件不存在，使用默认设置")
                self.plugin_settings = {'_enabled_plugins': []}
                return True
        except Exception as e:
            logging.error(f"加载插件设置失败: {e}")
            self.plugin_settings = {'_enabled_plugins': []}
            return False
    
    def save_plugin_settings(self, plugin_id: str = None) -> bool:
        """保存插件设置
        
        Args:
            plugin_id: 要保存的插件ID，为None则保存所有
            
        Returns:
            bool: 是否保存成功
        """
        try:
            settings_dir = os.path.join(os.path.expanduser("~"), ".hanabi_notes")
            
            # 确保目录存在
            if not os.path.exists(settings_dir):
                os.makedirs(settings_dir)
            
            # 更新已启用插件列表
            self.plugin_settings['_enabled_plugins'] = list(self.enabled_plugins)
            
            # 如果指定了插件ID，则只更新该插件的设置
            if plugin_id is not None and plugin_id in self.plugins:
                plugin = self.plugins[plugin_id]
                self.plugin_settings[plugin_id] = plugin.get_settings()
            else:
                # 更新所有插件的设置
                for pid, plugin in self.plugins.items():
                    self.plugin_settings[pid] = plugin.get_settings()
            
            # 保存到文件
            settings_file = os.path.join(settings_dir, "plugin_settings.json")
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.plugin_settings, f, ensure_ascii=False, indent=4)
            
            logging.info(f"已保存插件设置，插件数量: {len(self.plugins)}")
            return True
        except Exception as e:
            logging.error(f"保存插件设置失败: {e}")
            return False
    
    def shutdown(self) -> bool:
        """关闭插件管理器，禁用所有插件
        
        Returns:
            bool: 是否关闭成功
        """
        success = True
        
        # 禁用所有插件
        for plugin_id in list(self.enabled_plugins):
            if not self.disable_plugin(plugin_id):
                success = False
                logging.error(f"禁用插件失败: {plugin_id}")
        
        # 保存插件设置
        if not self.save_plugin_settings():
            success = False
            logging.error("保存插件设置失败")
        
        self.is_initialized = False
        return success

    def create_plugin_settings_panel(self) -> 'QWidget':
        """创建插件设置面板
        
        Returns:
            QWidget: 插件设置面板
        """
        try:
            from PySide6.QtWidgets import (
                QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                QListWidget, QListWidgetItem, QCheckBox, QTabWidget
            )
            from PySide6.QtCore import Qt, Signal
            
            class PluginSettingsPanel(QWidget):
                pluginsChanged = Signal()
                
                def __init__(self, plugin_manager, parent=None):
                    super().__init__(parent)
                    self.plugin_manager = plugin_manager
                    self.initUI()
                
                def initUI(self):
                    layout = QVBoxLayout(self)
                    
                    # 插件列表
                    self.pluginList = QListWidget()
                    self.pluginList.setMinimumWidth(200)
                    self.pluginList.currentRowChanged.connect(self.onPluginSelected)
                    
                    # 插件详情区域
                    self.detailsWidget = QWidget()
                    self.detailsLayout = QVBoxLayout(self.detailsWidget)
                    
                    # 初始详情内容
                    self.infoLabel = QLabel("选择一个插件查看详情")
                    self.infoLabel.setAlignment(Qt.AlignCenter)
                    self.detailsLayout.addWidget(self.infoLabel)
                    
                    # 水平布局
                    hLayout = QHBoxLayout()
                    hLayout.addWidget(self.pluginList)
                    hLayout.addWidget(self.detailsWidget, 1)
                    
                    layout.addLayout(hLayout)
                    
                    # 刷新插件列表
                    self.updatePluginList()
                
                def updatePluginList(self):
                    self.pluginList.clear()
                    
                    # 添加所有插件
                    for plugin_id, plugin in self.plugin_manager.plugins.items():
                        item = QListWidgetItem(plugin.metadata.name)
                        item.setData(Qt.UserRole, plugin_id)
                        self.pluginList.addItem(item)
                
                def onPluginSelected(self, row):
                    # 清空详情区域
                    while self.detailsLayout.count():
                        item = self.detailsLayout.takeAt(0)
                        if item.widget():
                            item.widget().setParent(None)
                    
                    if row < 0:
                        self.infoLabel = QLabel("选择一个插件查看详情")
                        self.infoLabel.setAlignment(Qt.AlignCenter)
                        self.detailsLayout.addWidget(self.infoLabel)
                        return
                    
                    # 获取插件信息
                    item = self.pluginList.item(row)
                    plugin_id = item.data(Qt.UserRole)
                    plugin = self.plugin_manager.plugins.get(plugin_id)
                    
                    if not plugin:
                        return
                    
                    # 创建详情界面
                    nameLabel = QLabel(f"<h2>{plugin.metadata.name}</h2>")
                    versionLabel = QLabel(f"版本: {plugin.metadata.version}")
                    authorLabel = QLabel(f"作者: {plugin.metadata.author}")
                    descLabel = QLabel(plugin.metadata.description)
                    descLabel.setWordWrap(True)
                    
                    # 启用/禁用复选框
                    enabledCheck = QCheckBox("启用")
                    enabledCheck.setChecked(plugin.is_enabled)
                    enabledCheck.toggled.connect(lambda checked, pid=plugin_id: self.togglePlugin(pid, checked))
                    
                    # 插件设置
                    settingsTab = QTabWidget()
                    
                    # 基本信息标签页
                    infoTab = QWidget()
                    infoLayout = QVBoxLayout(infoTab)
                    infoLayout.addWidget(nameLabel)
                    infoLayout.addWidget(versionLabel)
                    infoLayout.addWidget(authorLabel)
                    infoLayout.addWidget(descLabel)
                    infoLayout.addWidget(enabledCheck)
                    infoLayout.addStretch()
                    
                    settingsTab.addTab(infoTab, "基本信息")
                    
                    # 如果插件提供设置界面
                    settingsWidget = plugin.create_settings_widget()
                    if settingsWidget:
                        settingsTab.addTab(settingsWidget, "设置")
                    
                    self.detailsLayout.addWidget(settingsTab)
                
                def togglePlugin(self, plugin_id, enabled):
                    if enabled:
                        success = self.plugin_manager.enable_plugin(plugin_id)
                        if not success:
                            # 恢复复选框状态
                            self.onPluginSelected(self.pluginList.currentRow())
                    else:
                        success = self.plugin_manager.disable_plugin(plugin_id)
                        if not success:
                            # 恢复复选框状态
                            self.onPluginSelected(self.pluginList.currentRow())
                    
                    # 发送变更信号
                    self.pluginsChanged.emit()
            
            # 创建设置面板
            panel = PluginSettingsPanel(self)
            return panel
        except Exception as e:
            logging.error(f"创建插件设置面板失败: {e}")
            traceback.print_exc()
            
            # 返回一个空面板
            try:
                from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
                widget = QWidget()
                layout = QVBoxLayout(widget)
                label = QLabel(f"加载插件设置面板失败: {str(e)}")
                layout.addWidget(label)
                return widget
            except:
                # 如果连这都失败了，只能返回None
                return None
