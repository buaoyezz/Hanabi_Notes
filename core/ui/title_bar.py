from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap
import os
import sys
from core.font.font_manager import FontManager
from core.log.log_manager import log

# 不再需要这个函数，因为将使用resource_manager
# def resource_path(relative_path):
#     if hasattr(sys, '_MEIPASS'):
#         base_path = sys._MEIPASS
#     else:
#         base_path = os.path.abspath(".")
#     return os.path.join(base_path, relative_path)

class TitleBar(QWidget):
    def __init__(self, parent=None, resource_manager=None):
        super().__init__(parent)
        self.moving = False
        self.offset = None
        self.resource_manager = resource_manager
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(0)
        
        # 添加logo
        self.logo_label = QLabel()
        try:
            if self.resource_manager:
                # 使用resource_manager加载logo
                logo_pixmap = self.resource_manager.get_pixmap("small_256")
                if logo_pixmap:
                    # 调整logo尺寸为20x20
                    scaled_pixmap = logo_pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.logo_label.setPixmap(scaled_pixmap)
                    self.logo_label.setFixedSize(20, 20)
                    log.info("成功通过resource_manager加载logo")
                else:
                    log.error("无法通过resource_manager加载logo图片")
            else:
                log.warning("未提供resource_manager，无法加载logo")
        except Exception as e:
            log.error(f"加载logo时出错: {str(e)}")
            
        layout.addWidget(self.logo_label)
        
        # 减小logo和标题之间的间距
        layout.addSpacing(2)
        
        # 创建字体管理器
        self.font_manager = FontManager()
        log.info("初始化标题栏字体管理器")
        
        # 设置背景色和高度，移除底部边框
        self.setFixedHeight(40)
        self.setStyleSheet("""
            QWidget {
                background: transparent;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
            QPushButton {
                background: transparent;
                color: #666666;
                border: none;
                width: 20px;
                height: 20px;
                padding: 4px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #F5F5F5;
            }
            QPushButton#closeButton:hover {
                background-color: #FF6B6B;
                color: white;
            }
        """)
        
        # 标题文本
        self.title_label = QLabel()
        self.title_label.setStyleSheet("""
            QLabel {
                background: transparent;
                color: #333333;
                font-weight: bold;
                padding: 0;
            }
        """)
        
        # 应用字体
        self.font_manager.apply_font(self.title_label)
        # 设置标题字体大小
        font = self.title_label.font()
        font.setPointSize(12)
        self.title_label.setFont(font)
        
        # 最小化和关闭按钮
        self.min_button = QPushButton("─")
        self.close_button = QPushButton("✕")
        # 应用字体到按钮
        self.font_manager.apply_font(self.min_button)
        self.font_manager.apply_font(self.close_button)
        
        # 修改按钮样式
        btn_style = """
            QPushButton {
                background: transparent;
                color: #666666;
                border: none;
                width: 20px;
                height: 20px;
                padding: 4px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #E5E5E5;
            }
            QPushButton#closeButton:hover {
                background-color: #FF4D4D;
                color: white;
            }
        """
        self.min_button.setStyleSheet(btn_style)
        self.close_button.setStyleSheet(btn_style)
        self.close_button.setObjectName("closeButton")
        
        # 在添加标题文本之前添加一些间距
        layout.addSpacing(5)
        layout.addWidget(self.title_label)
        layout.addStretch()
        layout.addWidget(self.min_button)
        layout.addWidget(self.close_button)
        
        # 连接信号
        self.min_button.clicked.connect(self.window().showMinimized)
        self.close_button.clicked.connect(self.window().close)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.moving = True
            self.offset = event.position()
            log.debug("开始拖动窗口")
            
    def mouseMoveEvent(self, event):
        if self.moving:
            new_pos = event.globalPosition().toPoint() - self.offset.toPoint()
            window = self.window()
            screen = QApplication.primaryScreen().geometry()
            new_x = max(screen.left(), min(new_pos.x(), screen.right() - window.width()))
            new_y = max(screen.top(), min(new_pos.y(), screen.bottom() - window.height()))
            window.move(new_x, new_y)
            
    def mouseReleaseEvent(self, event):
        self.moving = False
        log.debug("结束拖动窗口") 