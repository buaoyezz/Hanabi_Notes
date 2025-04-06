"""
Hello World 示例插件
展示Hanabi Notes插件系统的基本功能
"""

from Aya_Hanabi.Hanabi_Core.PluginManager import HanabiPlugin, PluginMetadata, PluginHooks


class HelloWorldPlugin(HanabiPlugin):
    """Hello World 示例插件类"""
    
    def __init__(self, app_instance=None):
        super().__init__(app_instance)
        
        # 设置插件元数据
        self.metadata = PluginMetadata(
            name="Hello World",
            version="1.0.0",
            description="一个简单的Hello World示例插件",
            author="Hanabi Team",
            min_app_version="1.0.0"
        )
    
    def initialize(self) -> bool:
        """初始化插件"""
        print("Hello World 插件初始化中...")
        
        # 注册钩子
        self.register_hook(PluginHooks.APP_STARTED, self.on_app_started)
        self.register_hook(PluginHooks.FILE_OPENED, self.on_file_opened)
        
        # 添加菜单动作
        self.add_menu_action({
            'text': 'Hello World',
            'callback': self.show_hello_world,
            'menu': 'plugins'  # 添加到插件菜单
        })
        
        # 添加工具栏动作
        self.add_toolbar_action({
            'text': 'Hello',
            'tooltip': 'Say Hello World',
            'callback': self.show_hello_world
        })
        
        print("Hello World 插件初始化完成")
        return super().initialize()
    
    def shutdown(self) -> bool:
        """关闭插件"""
        print("Hello World 插件正在关闭...")
        return super().shutdown()
    
    def on_app_started(self):
        """应用程序启动时执行"""
        print("欢迎使用 Hanabi Notes！- 来自 Hello World 插件")
        
        # 尝试显示一个欢迎消息（如果应用程序实例可用）
        if self.app and hasattr(self.app, 'titleBar'):
            try:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(
                    self.app,
                    "Hello World 插件",
                    "欢迎使用 Hanabi Notes！\n这是来自 Hello World 插件的欢迎消息。"
                )
            except Exception as e:
                print(f"显示欢迎消息失败: {e}")
    
    def on_file_opened(self, file_path):
        """文件打开时执行"""
        print(f"文件已打开: {file_path} - Hello World插件已感知")
    
    def show_hello_world(self):
        """显示Hello World消息"""
        try:
            # 如果应用程序实例可用
            if self.app:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(
                    self.app,
                    "Hello World",
                    "Hello, Hanabi World!"
                )
            else:
                print("Hello, Hanabi World!")
        except Exception as e:
            print(f"显示Hello World消息失败: {e}")


# 导出插件类，使插件管理器能够识别
__plugin_class__ = HelloWorldPlugin 