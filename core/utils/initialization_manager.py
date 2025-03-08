from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from core.font.font_manager import FontManager
from core.log.log_manager import log
from core.pages_core.pages_manager import PagesManager
from core.utils.config_manager import config_manager
import os

class InitializationManager:
    @staticmethod
    def init_log_directory():
        # 确保日志目录存在
        log_dir = os.path.join(os.path.expanduser('~'), '.clutui_nextgen_example', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log.info("日志目录初始化完成")

    @staticmethod
    def init_application():
        app = QApplication([])
        # 设置应用程序属性
        app.setAttribute(Qt.AA_DontShowIconsInMenus, True)
        app.setQuitOnLastWindowClosed(True)
        
        # 加载配置
        config = config_manager.get_config()
        log.info("配置加载完成")
        
        # 初始化并应用字体
        font_manager = FontManager()
        
        # 从配置中获取字体设置
        font_name = config_manager.get_config('appearance', 'font', 'Microsoft YaHei UI')
        if font_name in font_manager.get_system_fonts():
            font_manager.set_current_font(font_name)
            log.info(f"InitializationManager: 从配置中加载字体: {font_name}")
        
        # 应用字体到应用程序
        font_manager.apply_font(app)
        
        # 设置全局样式
        app.setStyleSheet("""
            * {
                color: #333333;
            }
        """)
        
        log.info("应用程序初始化完成")
        return app

    @staticmethod
    def init_window_components(window):
        """初始化窗口组件"""
        # 初始化基本属性
        window.moving = False
        window.offset = None
        
        # 初始化管理器
        window.pages_manager = PagesManager()
        window.quick_start_page = window.pages_manager.quick_start_page
        window.font_manager = FontManager()
        
        log.info("窗口组件初始化完成") 