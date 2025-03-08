'''
入口程序
'''

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QIcon, QWindow
from core.utils.initialization_manager import InitializationManager
from core.log.log_manager import log
from core.utils.notif import Notification, NotificationType
from core.ui.title_bar import TitleBar
from core.window.window_manager import WindowManager
from core.utils.resource_manager import ResourceManager
import sys
import os
import ctypes
import json
import win32gui
import win32con

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        InitializationManager.init_log_directory()
        InitializationManager.init_window_components(self)
        WindowManager.init()  # 初始化窗口管理器（包括快捷键）
        log.info("初始化主窗口")
        
        # 设置应用图标
        resource_manager = ResourceManager()
        icon = resource_manager.get_icon("small_256")
        if icon:
            # 设置窗口图标
            self.setWindowIcon(icon)
            QApplication.setWindowIcon(icon)
            
            # 设置任务栏图标
            if os.name == 'nt':  # Windows系统
                try:
                    # 获取窗口句柄
                    hwnd = self.winId().__int__()
                    
                    # 加载图标文件
                    icon_path = resource_manager.get_resource_path(os.path.join("resources", "small_256.png"))
                    if os.path.exists(icon_path):
                        # 设置任务栏图标
                        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Imagine.Snap")
                        log.info("成功设置任务栏图标")
                except Exception as e:
                    log.error(f"设置任务栏图标失败: {str(e)}")
            
            log.info("成功加载应用图标")
        
        # 设置窗口基本属性
        self.setWindowTitle("Imagine Snap")
        self.setMinimumSize(600, 450)
        self.resize(1080, 650)
        
        # 设置窗口背景透明和无边框
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        
        # 创建主窗口部件
        main_widget = QWidget()
        main_widget.setObjectName("mainWidget")
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建标题栏并传入资源管理器
        self.title_bar = TitleBar(self, resource_manager)
        self.title_bar.title_label.setText("Imagine Snap")
        main_layout.addWidget(self.title_bar)
        
        # 创建内容区域容器
        content_container = QWidget()
        content_layout = QHBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # 右侧内容区
        right_content = QWidget()
        self.right_layout = QVBoxLayout(right_content)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建页面容器
        self.page_container = QWidget()
        self.page_layout = QVBoxLayout(self.page_container)
        self.page_layout.setContentsMargins(0, 0, 0, 0)
        self.page_layout.addWidget(self.pages_manager.get_stacked_widget())
        self.right_layout.addWidget(self.page_container)
        
        # 将左右两侧添加到内容布局
        content_layout.addWidget(self.pages_manager.get_sidebar())
        content_layout.addWidget(right_content)
        
        # 将内容容器添加到主布局
        main_layout.addWidget(content_container)
        
        # 设置主窗口样式
        main_widget.setStyleSheet("""
            QWidget#mainWidget {
                background-color: #F8F9FA;
                border-radius: 10px;
                border: 1px solid #E0E0E0;
            }
        """)
        
        self.setCentralWidget(main_widget)
        
        # 初始化关闭相关属性
        self._closing = False
        self._cleanup_timer = QTimer()
        self._cleanup_timer.setSingleShot(True)
        self._cleanup_timer.timeout.connect(self._finish_close)
        self._notifications = []

    def closeEvent(self, event):
        WindowManager.handle_close_event(self, event)
        if event.isAccepted():
            WindowManager.cleanup()  # 清理窗口管理器（注销快捷键）

    def _finish_close(self):
        WindowManager.finish_close(self)

    def switch_page(self, page_name):
        WindowManager.switch_page(self, page_name)

    def show_notification(self, text, type=NotificationType.TIPS, duration=1000):
        notification = Notification(
            text=text,
            type=type,
            duration=duration,
            parent=self
        )
        self._notifications.append(notification)
        notification.animation_finished.connect(
            lambda: self._notifications.remove(notification) if notification in self._notifications else None
        )
        notification.show_notification()

if __name__ == '__main__':
    try:
        app = InitializationManager.init_application()
        window = MainWindow()
        window.show()
        log.info("Imagine Snap 已经启动！")
        
        # 显示欢迎通知
        window.show_notification(
            text="欢迎使用 Imagine Snap",
            type=NotificationType.TIPS,
            duration=3000
        )
        
        exit_code = app.exec()
        window._finish_close()
        sys.exit(exit_code)
        
    except Exception as e:
        log.error(f"应用程序运行出错: {str(e)}")
        sys.exit(1)

