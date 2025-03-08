from PySide6.QtWidgets import (QLabel, QPushButton, QHBoxLayout, QWidget, 
                             QVBoxLayout, QFrame, QGraphicsDropShadowEffect, QMessageBox,
                             QGridLayout, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt, Signal, QUrl, QSize
from PySide6.QtGui import QColor, QDesktopServices, QIcon
from core.utils.notif import Notification
from core.log.log_manager import log
from core.ui.little_card import LittleCard
from core.utils.notif import Notification, NotificationType
from core.font.font_pages_manager import FontPagesManager

class FeatureCard(QFrame):
    clicked = Signal(str)
    
    def __init__(self, title, icon_name, description, parent=None):
        super().__init__(parent)
        self.title = title
        self.icon_name = icon_name
        self.description = description
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题和图标
        title_layout = QHBoxLayout()
        
        # 图标
        icon_label = QLabel()
        icon_label.setFixedSize(32, 32)
        # 此处假设有图标管理系统来获取图标
        # 实际实现可能需要根据项目的图标管理系统调整
        try:
            # 使用Material图标: screenshot, edit, save, settings
            from core.font.icon_map import ICON_MAP
            icon_text = QLabel(ICON_MAP.get(self.icon_name, ""))
            icon_text.setStyleSheet("""
                QLabel {
                    color: #2196F3;
                    font-family: 'Material Icons';
                    font-size: 28px;
                }
            """)
            title_layout.addWidget(icon_text)
        except Exception as e:
            log.error(f"加载图标失败: {str(e)}")
            
        title_layout.addSpacing(10)
        
        # 标题
        title_label = QLabel(self.title)
        self.font_manager = FontPagesManager()
        self.font_manager.apply_font(title_label, "title")
        title_label.setStyleSheet("""
            QLabel {
                color: #333333;
                background: transparent;
                font-weight: bold;
            }
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # 描述
        desc_label = QLabel(self.description)
        self.font_manager.apply_font(desc_label, "normal")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            QLabel {
                color: #666666;
                background: transparent;
                line-height: 140%;
            }
        """)
        layout.addWidget(desc_label)
        
        layout.addStretch()
        
        # 开始按钮
        start_button = QPushButton("开始使用")
        self.font_manager.apply_font(start_button, "normal")
        start_button.setCursor(Qt.PointingHandCursor)
        start_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 5px;
                padding: 8px 15px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        start_button.clicked.connect(lambda: self.clicked.emit(self.title))
        
        layout.addWidget(start_button, alignment=Qt.AlignRight)
        
        # 卡片样式
        self.setStyleSheet("""
            FeatureCard {
                background: white;
                border-radius: 10px;
                border: 1px solid #E0E0E0;
            }
            FeatureCard:hover {
                background: #F5F5F5;
                border: 1px solid #2196F3;
            }
        """)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.title)

class QuickStartPage(QWidget):
    category_clicked = Signal(str)
    switch_page_requested = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.feature_cards = {}
        self.font_manager = FontPagesManager()
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)
        
        # 顶部标题
        main_title = QLabel("Imagine Snap")
        self.font_manager.apply_font(main_title, "title")
        main_title.setStyleSheet("""
            QLabel {
                color: #333333; 
                letter-spacing: 1px;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        main_title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(main_title)
        
        # 说明文本
        description = QLabel("轻松高效的截图工具，满足您的所有截图需求")
        self.font_manager.apply_font(description, "normal")
        description.setStyleSheet("""
            QLabel {
                color: #666666;
                line-height: 24px;
            }
        """)
        description.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(description)
        
        main_layout.addSpacing(30)
        
        # 功能卡片配置
        cards_config = [
            {
                "title": "快速截图",
                "icon_name": "screenshot",
                "description": "支持全屏、区域和窗口截图，一键捕获您需要的内容。"
            },
            {
                "title": "图像编辑",
                "icon_name": "edit",
                "description": "内置专业编辑工具，可添加文字、箭头、标注和马赛克效果。"
            },
            {
                "title": "保存分享",
                "icon_name": "share",
                "description": "多种格式保存，支持一键分享到各大社交平台和云服务。"
            },
            {
                "title": "设置选项",
                "icon_name": "settings",
                "description": "自定义快捷键、输出格式、保存位置和截图效果。"
            }
        ]
        
        # 创建网格布局
        grid_layout = QGridLayout()
        grid_layout.setSpacing(20)
        
        # 添加功能卡片
        row, col = 0, 0
        for i, config in enumerate(cards_config):
            row = i // 2
            col = i % 2
            
            card = FeatureCard(
                title=config["title"],
                icon_name=config["icon_name"],
                description=config["description"]
            )
            card.clicked.connect(self.on_feature_clicked)
            self.feature_cards[config["title"]] = card
            grid_layout.addWidget(card, row, col)
        
        main_layout.addLayout(grid_layout)
        
        main_layout.addStretch()
        
        # 底部版权信息
        footer_layout = QHBoxLayout()
        
        # 版本信息
        version_label = QLabel("v1.0.0")
        self.font_manager.apply_font(version_label, "small")
        version_label.setStyleSheet("color: #999999;")
        footer_layout.addWidget(version_label)
        
        footer_layout.addStretch()
        
        # 快捷键提示
        shortcut_label = QLabel("快捷键: Ctrl+Alt+S 立即截图")
        self.font_manager.apply_font(shortcut_label, "small")
        shortcut_label.setStyleSheet("color: #666666;")
        footer_layout.addWidget(shortcut_label)
        
        main_layout.addLayout(footer_layout)
        
        # 设置整体样式
        self.setStyleSheet("""
            QWidget {
                background: #F8F9FA;
            }
        """)

    def on_feature_clicked(self, feature):
        feature_actions = {
            "快速截图": "screenshot_page",
            "图像编辑": "editor_page",
            "保存分享": "share_page", 
            "设置选项": "settings_page"
        }
        
        if feature in feature_actions:
            # 切换到相应页面
            target_page = feature_actions[feature]
            self.switch_page(target_page)
            
            # 显示通知
            Notification(
                text=f"正在打开{feature}",
                type=NotificationType.TIPS,
                duration=1000
            ).show_notification()
            
    def switch_page(self, page_name):
        self.switch_page_requested.emit(page_name)
        log.info(f"请求切换到页面: {page_name}") 