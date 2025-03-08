from PySide6.QtWidgets import QStackedWidget, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QEasingCurve, QPropertyAnimation, QParallelAnimationGroup, QPoint, QTimer
from PySide6.QtGui import QFont, QFontDatabase
from pages.quick_start import QuickStartPage
from pages.about_page import AboutPage
from pages.log_page import LogPage
from pages.settings_pages import SettingsPage
from core.log.log_manager import log
from core.font.font_manager import FontManager
from core.font.font_pages_manager import FontPagesManager
from core.utils.config_manager import config_manager


class PagesManager:
    def __init__(self):
        # 基础组件初始化
        self.stacked_widget = QStackedWidget()
        self.pages = {}
        self.buttons = {}
        self.current_page = None
        self.animation_group = None
        
        # 创建字体管理器 (现在会使用单例模式)
        self.font_manager = FontManager()
        self.font_pages_manager = FontPagesManager()
        
        # 从配置中获取字体设置并应用
        font_name = config_manager.get_config('appearance', 'font')
        if font_name and font_name in self.font_manager.get_system_fonts():
            self.font_manager.set_current_font(font_name)
            log.info(f"PagesManager: 从配置中加载字体: {font_name}")
        
        # 创建页面实例
        self.quick_start_page = QuickStartPage()
        self.about_page = AboutPage()
        self.log_page = LogPage()
        self.settings_page = SettingsPage()
        
        # 初始化侧边栏
        self.sidebar = QWidget()
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(10, 10, 10, 10)
        self.sidebar_layout.setSpacing(2)
        
        # 使用字体管理器获取图标映射
        self.icons = {
            "快速开始": self.font_manager.get_icon_text('dashboard'),
            "日志": self.font_manager.get_icon_text('article'),
            "关于": self.font_manager.get_icon_text('info'),
            "设置": self.font_manager.get_icon_text('settings')
        }
        
        # 创建并存储按钮
        self.buttons = {
            name: self.create_sidebar_button(name)
            for name in ["快速开始", "日志", "关于", "设置"]
        }
        
        # 添加按钮到布局
        self.sidebar_layout.addWidget(self.buttons["快速开始"])
        self.sidebar_layout.addStretch(1)
        self.sidebar_layout.addWidget(self.buttons["日志"])
        self.sidebar_layout.addWidget(self.buttons["关于"])
        self.sidebar_layout.addWidget(self.buttons["设置"])
        
        # 添加页面映射
        self.pages = {
            "快速开始": self.quick_start_page,
            "日志": self.log_page,
            "关于": self.about_page,
            "设置": self.settings_page
        }
        
        # 将页面添加到堆叠窗口
        for page in self.pages.values():
            self.stacked_widget.addWidget(page)
        
        # 设置默认页面
        self.buttons["快速开始"].setChecked(True)
        self.stacked_widget.setCurrentWidget(self.quick_start_page)
        self.current_page = "快速开始"
        
        log.info("初始化页面管理器")
    
    def create_sidebar_button(self, text):
        btn = QPushButton()
        
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 0, 0, 0)
        layout.setSpacing(10)
        
        if text in self.icons:
            icon_label = QLabel(self.icons[text])
            self.font_manager.apply_icon_font(icon_label, size=20)
            icon_label.setStyleSheet("""
                QLabel {
                    color: #666666;
                    min-width: 24px;
                    max-width: 24px;
                }
            """)
            layout.addWidget(icon_label)
        
        text_label = QLabel(text)
        default_font = self.font_pages_manager.setFont("Microsoft YaHei UI", size=14)
        text_label.setFont(default_font)
        
        text_label.setStyleSheet("""
            QLabel {
                color: #333333;
            }
        """)
        layout.addWidget(text_label)
        
        # 创建容器并设置布局
        container = QWidget()
        container.setLayout(layout)
        
        # 设置按钮样式和属性
        btn.setFixedHeight(40)
        btn.setFixedWidth(150)
        btn.setCheckable(True)
        btn.clicked.connect(lambda: self.switch_page(text))
        
        # 设置布局
        btn.setLayout(layout)
        
        # 修改按钮样式表
        btn.setStyleSheet("""
            QPushButton {
                border: none;
                text-align: left;
                padding: 0;
                background: transparent;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: rgba(33, 150, 243, 0.1);
            }
            QPushButton:checked {
                background: transparent;
            }
            QPushButton:checked QLabel {
                color: #2196F3;
            }
        """)
        return btn
        
    def get_sidebar(self):
        return self.sidebar
        
    def add_page(self, name, page, button):
        if name in self.pages:
            log.warning(f"页面 {name} 已存在,将被覆盖")
            
        self.stacked_widget.addWidget(page)
        self.pages[name] = page
        self.buttons[name] = button
        log.info(f"添加页面: {name}")
    
    def switch_page(self, name):
        if name not in self.pages:
            log.error(f"页面 {name} 不存在")
            return
        
        if name == self.current_page:
            log.debug(f"已经在 {name} 页面，无需切换")
            self.buttons[name].setChecked(True)
            return
            
        # 停止当前正在运行的动画
        if self.animation_group and self.animation_group.state() == QPropertyAnimation.Running:
            self.animation_group.stop()
            
        # 取消其他按钮的选中状态
        for btn in self.buttons.values():
            btn.setChecked(False)
        
        # 设置当前按钮选中
        self.buttons[name].setChecked(True)
        
        # 直接切换页面，不使用动画
        self.stacked_widget.setCurrentWidget(self.pages[name])
        self.current_page = name
        log.info(f"切换到页面: {name}")
    
    def get_stacked_widget(self):
        return self.stacked_widget
        
    def stop_animations(self):
        if self.animation_group and self.animation_group.state() == QPropertyAnimation.Running:
            self.animation_group.stop()
            log.debug("停止所有动画")