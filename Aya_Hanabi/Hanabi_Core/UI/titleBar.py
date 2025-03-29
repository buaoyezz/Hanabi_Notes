import sys
import os
from PySide6.QtCore import Qt, QPoint, QEvent, QTimer, QRect
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout
from PySide6.QtGui import QCursor

from Aya_Hanabi.Hanabi_Core.UI.iconButton import IconButton

class TitleBar(QWidget):
    """
    自定义标题栏类，实现无边框窗口的标题栏功能
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(40)
        self.startPos = None
        
        # 初始样式将在updateStyle中设置
        self.updateStyle()
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 15, 0)
        layout.setSpacing(0)
        
        leftContainer = QWidget()
        leftContainer.setObjectName("titleBarIcon")
        leftContainer.setStyleSheet("border-top-left-radius: 10px;")
        titleLayout = QHBoxLayout(leftContainer)
        titleLayout.setContentsMargins(8, 0, 15, 0)
        titleLayout.setSpacing(5)
        titleLayout.setAlignment(Qt.AlignLeft)
        
        iconContainer = QWidget()
        iconContainer.setObjectName("iconContainer")
        iconContainer.setFixedSize(28, 28)
        iconLayout = QHBoxLayout(iconContainer)
        iconLayout.setContentsMargins(0, 0, 0, 0)
        
        self.iconLabel = QLabel("H")
        self.iconLabel.setObjectName("iconLabel")
        self.iconLabel.setAlignment(Qt.AlignCenter)
        iconLayout.addWidget(self.iconLabel)
        
        titleLayout.addWidget(iconContainer)
        
        self.titleLabel = QLabel("Hanabi Notes")
        self.titleLabel.setObjectName("titleLabel")
        titleLayout.addWidget(self.titleLabel)
        
        layout.addWidget(leftContainer, 0, Qt.AlignLeft)
        
        iconContainer.installEventFilter(self)
        leftContainer.installEventFilter(self)
        
        middleContainer = QWidget()
        middleContainer.setObjectName("titleBarMiddle")
        layout.addWidget(middleContainer, 1)
        
        buttonLayout = QHBoxLayout()
        buttonLayout.setSpacing(18)
        
        rightContainer = QWidget()
        rightContainer.setObjectName("titleBarRight")
        rightContainer.setLayout(buttonLayout)
        
        self.minButton = IconButton("minimize", 16)
        self.minButton.setObjectName("minButton")
        self.minButton.clicked.connect(self.parent.showMinimized)
        
        self.maxButton = IconButton("crop_square", 16)
        self.maxButton.setObjectName("maxButton")
        self.maxButton.clicked.connect(self.toggleMaximize)
        
        self.closeButton = IconButton("close", 16)
        self.closeButton.setObjectName("closeButton")
        self.closeButton.clicked.connect(self.parent.close)
        
        buttonLayout.addWidget(self.minButton)
        buttonLayout.addWidget(self.maxButton)
        buttonLayout.addWidget(self.closeButton)
        
        layout.addWidget(rightContainer)
        
    def updateStyle(self):
        """更新标题栏样式"""
        if hasattr(self.parent, 'themeManager') and self.parent.themeManager:
            themeManager = self.parent.themeManager
            title_style, icon_bg_style, icon_label_style = themeManager.get_title_bar_style()
            
            # 获取当前主题名
            theme_name = ""
            if hasattr(themeManager.current_theme, 'name'):
                theme_name = themeManager.current_theme.name
            
            # 应用标题栏样式但不覆盖布局相关属性
            self.setStyleSheet(title_style)
            
            # 获取主题颜色
            if themeManager.current_theme:
                # 亮色主题特殊处理
                if theme_name == "light":
                    bg_color = "#f5f5f5"  # 确保亮色主题使用浅色背景
                    text_color = "#333333"
                    min_max_color = "rgba(0, 0, 0, 0.6)"
                    close_color = "rgba(0, 0, 0, 0.6)"
                    close_hover = "#e81123"
                    min_max_hover = "rgba(0, 0, 0, 0.8)"
                    hover_bg = "rgba(0, 0, 0, 0.05)"
                else:
                    bg_color = themeManager.current_theme.get("title_bar.background", "#1e2128")
                    text_color = themeManager.current_theme.get("title_bar.text_color", "white")
                    min_max_color = themeManager.current_theme.get("title_bar.controls_color", "rgba(255, 255, 255, 0.8)")
                    close_color = themeManager.current_theme.get("title_bar.close_color", "rgba(255, 255, 255, 0.8)")
                    close_hover = themeManager.current_theme.get("title_bar.close_hover", "#e81123")
                    min_max_hover = themeManager.current_theme.get("title_bar.controls_hover", "rgba(255, 255, 255, 1.0)")
                    hover_bg = themeManager.current_theme.get("title_bar.button_hover_bg", "rgba(255, 255, 255, 0.1)")
            else:
                # 默认值
                bg_color = "#1e2128"
                text_color = "white"
                min_max_color = "rgba(255, 255, 255, 0.8)"
                close_color = "rgba(255, 255, 255, 0.8)"
                close_hover = "#e81123"
                min_max_hover = "rgba(255, 255, 255, 1.0)"
                hover_bg = "rgba(255, 255, 255, 0.1)"
            
            # 设置子控件样式
            if hasattr(self, 'iconLabel'):
                self.iconLabel.setStyleSheet(icon_label_style)
            
            if hasattr(self, 'titleLabel'):
                self.titleLabel.setStyleSheet(f"color: {text_color}; font-size: 15px; font-weight: 500;")
            
            # 设置容器样式，使用直接查找而不是依赖对象名
            iconContainer = self.findChild(QWidget, "iconContainer")
            if iconContainer:
                iconContainer.setStyleSheet(icon_bg_style)
            
            titleBarIcon = self.findChild(QWidget, "titleBarIcon")
            if titleBarIcon:
                titleBarIcon.setStyleSheet(f"""
                    background-color: {bg_color}; 
                    border-top-left-radius: 10px;
                """)
            
            titleBarMiddle = self.findChild(QWidget, "titleBarMiddle")
            if titleBarMiddle:
                titleBarMiddle.setStyleSheet(f"background-color: {bg_color};")
            
            titleBarRight = self.findChild(QWidget, "titleBarRight")
            if titleBarRight:
                titleBarRight.setStyleSheet(f"""
                    background-color: {bg_color}; 
                    border-top-right-radius: 10px;
                """)
            
            # 设置按钮样式
            button_style = f"""
                QPushButton {{
                    color: {min_max_color}; 
                    background-color: transparent;
                    border: none;
                    border-radius: 8px;
                    padding: 2px;
                }}
                QPushButton:hover {{
                    color: {min_max_hover};
                    background-color: {hover_bg};
                }}
            """
            
            close_button_style = f"""
                QPushButton {{
                    color: {close_color}; 
                    background-color: transparent;
                    border: none;
                    border-radius: 8px;
                    padding: 2px;
                }}
                QPushButton:hover {{
                    color: white;
                    background-color: {close_hover};
                }}
            """
            
            if hasattr(self, 'minButton'):
                self.minButton.setStyleSheet(button_style)
                
            if hasattr(self, 'maxButton'):
                self.maxButton.setStyleSheet(button_style)
                
            if hasattr(self, 'closeButton'):
                self.closeButton.setStyleSheet(close_button_style)
        else:
            # 默认样式
            self.setStyleSheet("background-color: #1e2128; border-top-left-radius: 10px; border-top-right-radius: 10px;")
        
    def toggleMaximize(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
        else:
            self.parent.showMaximized()
            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.startPos = event.globalPosition().toPoint()
            
    def mouseMoveEvent(self, event):
        if self.startPos and not self.parent.isMaximized():
            delta = event.globalPosition().toPoint() - self.startPos
            self.parent.move(self.parent.x() + delta.x(), self.parent.y() + delta.y())
            self.startPos = event.globalPosition().toPoint()

    def eventFilter(self, obj, event):
        if hasattr(self.parent, 'sidebar'):
            if obj.objectName() in ["iconContainer", "titleBarIcon"]:
                if event.type() == QEvent.Enter:
                    self.parent.sidebar.expandBar()
                    return True
                elif event.type() == QEvent.Leave:
                    global_pos = QCursor.pos()
                    sidebar_rect = self.parent.sidebar.rect()
                    sidebar_global_pos = self.parent.sidebar.mapToGlobal(QPoint(0, 0))
                    sidebar_global_rect = QRect(sidebar_global_pos, self.parent.sidebar.size())
                    
                    if not sidebar_global_rect.contains(global_pos):
                        if hasattr(self.parent.sidebar, "checkAndCollapseBar"):
                            QTimer.singleShot(1000, self.parent.sidebar.checkAndCollapseBar)
                    return True
        
        return super().eventFilter(obj, event) 