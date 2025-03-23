import sys
import os
import re
import time
import json
import traceback
import platform
import threading
import tempfile
import datetime
from functools import partial
from pathlib import Path
from PySide6.QtCore import Qt, QPoint, Signal, QEvent, QTimer, QRect, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, 
                              QHBoxLayout, QPushButton, QTextEdit, QPlainTextEdit, QWidget, QSplitter, QStackedWidget,
                              QMessageBox, QScrollBar)
from PySide6.QtGui import QFont, QColor, QCursor, QTextCursor, QTextFormat, QSyntaxHighlighter,QTextCharFormat

# 导入文件管理相关功能
from Aya_Hanabi.Hanabi_Core.FileManager import (
    FileManager, open_file, save_file, new_file, delete_file, 
    close_file, change_file, AutoSave
)

# 添加调试日志功能
def log_to_file(message):
    """将调试信息写入日志文件"""
    try:
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        log_file = os.path.join(log_dir, "hanabi_debug.log")
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{message}\n")
    except Exception as e:
        print(f"写入日志文件出错: {e}")

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from Aya_Hanabi.Hanabi_Core.FontManager.fontManager import IconProvider, ICONS
    from Aya_Hanabi.Hanabi_Core.SidebarManager import SidebarMode
    from Aya_Hanabi.Hanabi_Core.SidebarManager.sidebarWidget import SidebarWidget
    from Aya_Hanabi.Hanabi_Core.ThemeManager import ThemeManager
    from Aya_Hanabi.Hanabi_Page.SettingsPages import SettingsDialog, ThemeSettingsDialog
    from Aya_Hanabi.Hanabi_HighLight import get_highlighter, detect_file_type
    try:
        from Aya_Hanabi.Hanabi_Core.App.init import app_Optimizer
        print("成功导入应用优化器")
    except ImportError as app_err:
        print(f"应用优化器导入失败: {app_err}")
        app_Optimizer = None
except ImportError as e:
    print(f"导入模块错误: {e}")
    alternative_path = os.path.join(os.path.dirname(current_dir), "HanabiNotes")
    if os.path.exists(alternative_path):
        sys.path.append(alternative_path)
        try:
            from Aya_Hanabi.Hanabi_Core.FontManager.fontManager import IconProvider, ICONS
            from Aya_Hanabi.Hanabi_Core.SidebarManager import SidebarMode
            from Aya_Hanabi.Hanabi_Core.SidebarManager.sidebarWidget import SidebarWidget
            from Aya_Hanabi.Hanabi_Core.ThemeManager import ThemeManager
            from Aya_Hanabi.Hanabi_Page.SettingsPages import SettingsDialog, ThemeSettingsDialog
            from Aya_Hanabi.Hanabi_HighLight import get_highlighter, detect_file_type
            try:
                from Aya_Hanabi.Hanabi_Core.App.init import app_Optimizer
                print("成功导入应用优化器(替代路径)")
            except ImportError as app_err:
                print(f"应用优化器导入失败(替代路径): {app_err}")
                app_Optimizer = None
        except ImportError as e2:
            print(f"尝试其他路径后仍然导入失败: {e2}")
            sys.exit(1)
    else:
        print("无法找到正确的模块路径")
        sys.exit(1)

try:
    from Aya_Hanabi.Hanabi_Styles.scrollbar_style import ScrollBarStyle
except ImportError as e:
    print(f"导入样式模块错误: {e}")
    
    class ScrollBarStyle:
        @staticmethod
        def get_style(base_color="#005780", handle_color="rgba(255, 255, 255, 0.3)"):
            return f"""
                QScrollBar:vertical {{
                    background-color: {base_color};
                    width: 6px;
                    margin: 0px;
                    border-radius: 3px;
                }}
                
                QScrollBar::handle:vertical {{
                    background-color: {handle_color};
                    min-height: 30px;
                    border-radius: 3px;
                }}
                
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                    height: 0px;
                }}
                
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                    background: none;
                }}
            """

class IconButton(QPushButton):
    def __init__(self, iconName, size=14, parent=None):
        icon = IconProvider.get_icon(iconName)
        super().__init__(icon, parent)
        self.setFont(IconProvider.get_icon_font(size))
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("border: none; background: transparent;")

class TitleBar(QWidget):
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

class StatusBar(QWidget):
    fontSizeChanged = Signal(int)
    previewModeChanged = Signal(bool)
    highlightModeChanged = Signal(bool)
    scrollToLineRequested = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)
        # 初始化时不设置样式，在updateStyle中设置
        
        self.previewMode = False
        self.highlightMode = True  # 默认开启高亮
        self.currentFontSize = 15
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 3, 15, 3)
        layout.setSpacing(8)
        
        leftButtons = QHBoxLayout()
        leftButtons.setSpacing(12)
        
        buttonSize = 26
        
        settingsContainer = QWidget()
        settingsContainer.setFixedSize(buttonSize, buttonSize)
        settingsContainer.setStyleSheet("background-color: transparent;")
        settingsLayout = QHBoxLayout(settingsContainer)
        settingsLayout.setContentsMargins(0, 0, 0, 0)
        
        settingsBtn = IconButton("settings", 16)
        settingsBtn.setToolTip("设置")
        settingsLayout.addWidget(settingsBtn)
        
        highlightContainer = QWidget()
        highlightContainer.setFixedSize(buttonSize, buttonSize)
        highlightContainer.setStyleSheet("background-color: transparent;")
        highlightLayout = QHBoxLayout(highlightContainer)
        highlightLayout.setContentsMargins(0, 0, 0, 0)
        
        self.highlightBtn = IconButton("code", 16)
        self.highlightBtn.setToolTip("语法高亮开关")
        highlightLayout.addWidget(self.highlightBtn)
        
        fontSizeContainer = QWidget()
        fontSizeContainer.setFixedSize(buttonSize, buttonSize)
        fontSizeContainer.setStyleSheet("background-color: transparent;")
        fontSizeLayout = QHBoxLayout(fontSizeContainer)
        fontSizeLayout.setContentsMargins(0, 0, 0, 0)
        
        fontSizeBtn = IconButton("format_size", 16)
        fontSizeBtn.setToolTip("调整字体大小")
        fontSizeBtn.clicked.connect(self.showFontSizeMenu)
        fontSizeLayout.addWidget(fontSizeBtn)
        
        scrollTestContainer = QWidget()
        scrollTestContainer.setFixedSize(buttonSize, buttonSize)
        scrollTestContainer.setStyleSheet("background-color: transparent;")
        scrollTestLayout = QHBoxLayout(scrollTestContainer)
        scrollTestLayout.setContentsMargins(0, 0, 0, 0)
        
        scrollTestBtn = IconButton("linear_scale", 16)
        scrollTestBtn.setToolTip("测试滚动动画")
        scrollTestBtn.clicked.connect(self.testScrollAnimation)
        scrollTestLayout.addWidget(scrollTestBtn)
        
        leftButtons.addWidget(settingsContainer)
        leftButtons.addWidget(highlightContainer)
        leftButtons.addWidget(fontSizeContainer)
        leftButtons.addWidget(scrollTestContainer)
        
        leftContainer = QWidget()
        leftContainer.setStyleSheet("background-color: transparent;")
        leftContainer.setLayout(leftButtons)
        layout.addWidget(leftContainer)
        
        rightContainer = QWidget()
        rightContainer.setStyleSheet("background-color: transparent;")
        rightLayout = QHBoxLayout(rightContainer)
        rightLayout.setContentsMargins(0, 0, 0, 0)
        
        self.lineCount = QLabel("0 行")
        rightLayout.addWidget(self.lineCount)
        
        layout.addStretch(1)
        layout.addWidget(rightContainer)
        
        # 应用初始样式
        self.updateStyle()
        
        # 连接设置按钮点击事件
        settingsBtn.clicked.connect(self.openSettings)
        # 连接高亮按钮点击事件
        self.highlightBtn.clicked.connect(self.toggleHighlightMode)
    
    def updateStyle(self):
        """更新状态栏样式"""
        if hasattr(self.parent(), 'themeManager') and self.parent().themeManager:
            themeManager = self.parent().themeManager
            status_style, icon_style, active_icon_style = themeManager.get_status_bar_style()
            
            # 应用状态栏样式
            self.setStyleSheet(status_style)
            
            # 更新按钮样式
            for btn in self.findChildren(IconButton):
                if btn == self.highlightBtn and self.highlightMode:
                    btn.setStyleSheet(active_icon_style)
                else:
                    btn.setStyleSheet(icon_style)
            
            # 更新行数标签样式
            if themeManager.current_theme:
                text_color = themeManager.current_theme.get("status_bar.text_color", "white")
                self.lineCount.setStyleSheet(f"color: {text_color}; font-size: 12px; background-color: rgba(0, 0, 0, 0.2); padding: 3px 8px; border-radius: 4px;")
        else:
            # 默认样式
            self.setStyleSheet("background-color: #1a1d23; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px;")
            self.lineCount.setStyleSheet("color: white; font-size: 12px; background-color: rgba(0, 0, 0, 0.2); padding: 3px 8px; border-radius: 4px;")
            
            # 默认按钮样式
            button_style = "color: rgba(255, 255, 255, 0.7); hover { background-color: rgba(255, 255, 255, 0.1); border-radius: 8px; }"
            for btn in self.findChildren(IconButton):
                if btn == self.highlightBtn and self.highlightMode:
                    btn.setStyleSheet("color: #6b9fff; hover { background-color: rgba(255, 255, 255, 0.1); border-radius: 8px; }")
                else:
                    btn.setStyleSheet(button_style)
    
    def openSettings(self):
        try:
            print("正在尝试打开设置...")
            log_to_file("正在尝试打开设置...")
            
            parent_obj = self.parent()
            if hasattr(parent_obj, "showSettings"):
                parent_obj.showSettings()
            else:
                # 尝试使用顶层窗口
                from PySide6.QtWidgets import QApplication, QMainWindow
                main_windows = [w for w in QApplication.topLevelWidgets() if isinstance(w, QMainWindow)]
                for w in main_windows:
                    if hasattr(w, "showSettings"):
                        w.showSettings()
                        return
                
                # 如果找不到具有showSettings方法的窗口，显示默认消息
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(self, "设置", "设置功能即将推出！")
        except Exception as e:
            error_msg = f"打开设置时出错: {e}"
            print(error_msg)
            log_to_file(error_msg)
            import traceback
            trace_info = traceback.format_exc()
            print(trace_info)
            log_to_file(trace_info)
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "错误", f"打开设置时出错: {str(e)}")
    
    def toggleHighlightMode(self):
        self.highlightMode = not self.highlightMode
        
        if self.highlightMode:
            self.highlightBtn.setStyleSheet("color: #6b9fff; hover { background-color: rgba(255, 255, 255, 0.1); border-radius: 8px; }")
        else:
            self.highlightBtn.setStyleSheet("color: rgba(255, 255, 255, 0.7); hover { background-color: rgba(255, 255, 255, 0.1); border-radius: 8px; }")
        
        # 发送高亮状态变化信号
        try:
            self.highlightModeChanged.emit(self.highlightMode)
            print(f"高亮模式切换为: {self.highlightMode}")
        except Exception as e:
            print(f"在发送高亮状态变化信号时出错: {e}")
            log_to_file(f"在发送高亮状态变化信号时出错: {e}")
    
    # 为向后兼容保留
    def togglePreviewMode(self):
        self.previewMode = not self.previewMode
        self.previewModeChanged.emit(self.previewMode)
    
    def showFontSizeMenu(self):
        from PySide6.QtWidgets import QMenu, QAction
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1e2128;
                color: white;
                border: 1px solid #2a2e36;
                border-radius: 4px;
                padding: 4px;
            }
            QMenu::item {
                padding: 4px 25px 4px 10px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        
        fontSizes = [12, 14, 15, 16, 18, 20]
        for size in fontSizes:
            action = QAction(f"{size}px", self)
            action.triggered.connect(lambda checked, s=size: self.changeFontSize(s))
            if size == self.currentFontSize:
                action.setIcon(IconProvider.get_icon("check"))
            menu.addAction(action)
        
        pos = self.mapToGlobal(self.findChild(QWidget, "", options=Qt.FindChildrenRecursively).pos())
        pos.setY(pos.y() - menu.sizeHint().height())
        menu.exec(pos)
    
    def changeFontSize(self, size):
        self.currentFontSize = size
        self.fontSizeChanged.emit(size)

    def testScrollAnimation(self):
        import random
        random_line = random.randint(10, 100)
        self.scrollToLineRequested.emit(random_line)

class HanabiNotesApp(QMainWindow):
    def __init__(self):
        super(HanabiNotesApp, self).__init__()
        
        # 设置全局属性
        self.theme = "dark"
        self.currentFilePath = None
        self.currentTitle = "未命名"
        self.currentFileType = "text"
        self.highlightMode = True
        self.openFiles = []
        self.editors = []
        self.closedEditors = []  # 新增：跟踪已关闭的编辑器
        
        # 初始化优化器
        if 'app_Optimizer' in globals() and app_Optimizer:
            self.optimizer = app_Optimizer
            self.optimizer.start_memory_monitor()  # 启动内存监控
            print("应用优化器已启用")
        else:
            self.optimizer = None
        
        # 初始化UI
        self.initUI()
    
    def onFileLoaded(self, title, content):
        activeInfo = self.sidebar.getActiveTabInfo()
        if activeInfo:
            for file_info in self.openFiles:
                if file_info.get('index') == self.sidebar.activeTabIndex:
                    editorIndex = file_info.get('editorIndex')
                    if 0 <= editorIndex < len(self.editors):
                        self.editors[editorIndex].setPlainText(content)
                    break
        
        self.currentTitle = title
        self.setWindowTitle(f"Hanabi Notes - {title}")
    
    def onFileSaved(self, filePath, message):
        self.currentFilePath = filePath
        
        if self.sidebar.activeTabIndex >= 0:
            fileName = os.path.splitext(os.path.basename(filePath))[0]
            self.sidebar.updateTabName(self.sidebar.activeTabIndex, fileName, filePath)
            
            # 更新文件信息
            for file_info in self.openFiles:
                if file_info.get('index') == self.sidebar.activeTabIndex:
                    file_info['filePath'] = filePath
                    file_info['title'] = fileName
                    break
        
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "保存成功", message)
    
    def deleteFile(self):
        # 使用FileManager中的delete_file功能
        delete_file(self)
    
    def changeFontSize(self, size):
        for editor in self.editors:
            self.updateEditorStyle(editor, size)
    
    def togglePreviewMode(self, enabled):
        currentEditorIndex = self.editorsStack.currentIndex()
        if 0 <= currentEditorIndex < len(self.editors):
            editorStack = self.editorsStack.widget(currentEditorIndex)
            if editorStack and editorStack.count() >= 2:
                editorStack.setCurrentIndex(1 if enabled else 0)
    
    def toggleHighlightMode(self, enabled):
        self.highlightMode = enabled
        
        # 应用或移除高亮
        if 0 <= self.editorsStack.currentIndex() < len(self.editors):
            currentEditor = self.editors[self.editorsStack.currentIndex()]
            if enabled:
                self.applyHighlighter(currentEditor)
            else:
                if hasattr(currentEditor, 'highlighter') and currentEditor.highlighter:
                    currentEditor.highlighter.setDocument(None)
                    currentEditor.highlighter = None
    
    def onScrollToLineRequested(self, lineNumber):
        currentEditorIndex = self.editorsStack.currentIndex()
        if 0 <= currentEditorIndex < len(self.editors):
            editor = self.editors[currentEditorIndex]
            self.scrollToLine(editor, lineNumber)
    
    def updateEditorStyle(self, editor, fontSize=15):
        """更新编辑器样式"""
        print(f"开始更新编辑器样式，字体大小: {fontSize}")
        
        # 确定当前主题
        theme_name = "dark"  # 默认主题
        
        # 尝试从主题管理器获取当前主题名称
        if hasattr(self, 'themeManager'):
            if hasattr(self.themeManager, 'current_theme_name'):
                theme_name = self.themeManager.current_theme_name
                print(f"从主题管理器获取当前主题名称: {theme_name}")
            elif hasattr(self, 'currentTheme'):
                theme_name = self.currentTheme
                print(f"从应用程序获取当前主题名称: {theme_name}")
        
        # 检查是否为亮色主题
        is_light_theme = theme_name == "light"
        print(f"是否为亮色主题: {is_light_theme}")
        
        # 默认颜色
        bg_color = '#ffffff' if is_light_theme else '#282c34'
        text_color = '#333333' if is_light_theme else '#abb2bf'
        selection_bg = '#b3d4fc' if is_light_theme else '#528bff'
        selection_text = '#333333' if is_light_theme else '#ffffff'
        scrollbar_bg = '#f5f5f5' if is_light_theme else '#2c313a'
        scrollbar_handle = '#c1c1c1' if is_light_theme else '#4b5362'
        
        # 从主题中获取颜色（如果有）
        if hasattr(self, 'themeManager') and self.themeManager.current_theme:
            # 如果是Theme对象并有get方法
            if hasattr(self.themeManager.current_theme, 'get'):
                bg_color = self.themeManager.current_theme.get("editor.background", bg_color)
                text_color = self.themeManager.current_theme.get("editor.text_color", text_color)
                selection_bg = self.themeManager.current_theme.get("editor.selection_color", selection_bg)
            # 如果是Theme对象有data属性
            elif hasattr(self.themeManager.current_theme, 'data') and isinstance(self.themeManager.current_theme.data, dict):
                if 'editor' in self.themeManager.current_theme.data:
                    editor_data = self.themeManager.current_theme.data['editor']
                    bg_color = editor_data.get('background', bg_color)
                    text_color = editor_data.get('text_color', text_color)
                    selection_bg = editor_data.get('selection_color', selection_bg)
            # 如果是字典
            elif isinstance(self.themeManager.current_theme, dict):
                if 'editor' in self.themeManager.current_theme:
                    editor_data = self.themeManager.current_theme['editor']
                    bg_color = editor_data.get('background', bg_color)
                    text_color = editor_data.get('text_color', text_color)
                    selection_bg = editor_data.get('selection_color', selection_bg)
        
        # 设置配色方案
        editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: %s;
                color: %s;
                border: none;
                padding: 10px;
                selection-background-color: %s;
                selection-color: %s;
                font-family: %s;
            }
            QScrollBar:vertical {
                border: none;
                background: %s;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: %s;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QScrollBar:horizontal {
                border: none;
                background: %s;
                height: 10px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: %s;
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """ % (
            bg_color,  # 背景色
            text_color,  # 文本颜色
            selection_bg,  # 选择背景色
            selection_text,  # 选择文本颜色
            "Consolas, 'Microsoft YaHei UI', '微软雅黑', monospace",  # 字体
            scrollbar_bg,  # 滚动条背景色
            scrollbar_handle,  # 滚动条滑块色
            scrollbar_bg,  # 水平滚动条背景色
            scrollbar_handle  # 水平滚动条滑块色
        ))
        
        # 设置字体大小
        font = editor.font()
        font.setPointSize(fontSize)
        editor.setFont(font)
        
        print("编辑器样式更新完成")
    
    def updateEditorContainerStyle(self, container):
        """更新编辑器容器样式"""
        
        # 确定当前主题
        theme_name = "dark"  # 默认主题
        
        # 尝试获取当前主题名称
        if hasattr(self, 'themeManager') and self.themeManager:
            if hasattr(self.themeManager, 'current_theme_name'):
                theme_name = self.themeManager.current_theme_name
            elif hasattr(self, 'currentTheme'):
                theme_name = self.currentTheme
                
        # 检查是否为亮色主题
        is_light_theme = theme_name == "light"
        
        # 默认颜色
        bg_color = '#ffffff' if is_light_theme else '#282c34'
        border_color = '#e5e5e5' if is_light_theme else '#343a45'
        
        # 从主题获取颜色（如果可用）
        if hasattr(self, 'themeManager') and self.themeManager and self.themeManager.current_theme:
            # 主题对象有get方法
            if hasattr(self.themeManager.current_theme, 'get'):
                bg_color = self.themeManager.current_theme.get("editor.background", bg_color)
                border_color = self.themeManager.current_theme.get("editor.border_color", border_color)
            # 主题对象有data属性
            elif hasattr(self.themeManager.current_theme, 'data') and isinstance(self.themeManager.current_theme.data, dict):
                if 'editor' in self.themeManager.current_theme.data:
                    editor_data = self.themeManager.current_theme.data['editor']
                    bg_color = editor_data.get('background', bg_color)
                    border_color = editor_data.get('border_color', border_color)
            # 主题是字典
            elif isinstance(self.themeManager.current_theme, dict):
                if 'editor' in self.themeManager.current_theme:
                    editor_data = self.themeManager.current_theme['editor']
                    bg_color = editor_data.get('background', bg_color)
                    border_color = editor_data.get('border_color', border_color)
        
        # 设置容器样式
        container.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 5px;
            }}
        """)
    
    def updatePreview(self, editorIndex):
        """更新预览区域，将编辑器内容转换为预览格式"""
        if not hasattr(self, 'markdown') or not self.markdown:
            return
            
        if 0 <= editorIndex < len(self.editors) and editorIndex < len(self.previewViews):
            editor = self.editors[editorIndex]
            previewView = self.previewViews[editorIndex]
            
            text = editor.toPlainText()
            
            try:
                # 使用markdown库转换内容
                html = self.markdown.markdown(text, extensions=['tables', 'fenced_code'])
                
                # 添加基本样式
                is_light_theme = hasattr(self, 'currentTheme') and self.currentTheme == "light"
                
                bg_color = '#ffffff' if is_light_theme else '#282c34'
                text_color = '#333333' if is_light_theme else '#abb2bf'
                link_color = '#4183c4' if is_light_theme else '#61afef'
                code_bg = '#f5f5f5' if is_light_theme else '#3a3f4b'
                
                # 从主题获取颜色（如果可用）
                if hasattr(self, 'themeManager') and self.themeManager and self.themeManager.current_theme:
                    if hasattr(self.themeManager.current_theme, 'get'):
                        bg_color = self.themeManager.current_theme.get("editor.background", bg_color)
                        text_color = self.themeManager.current_theme.get("editor.text_color", text_color)
                
                styled_html = f"""
                <html>
                <head>
                    <style>
                        body {{ 
                            font-family: 'Microsoft YaHei UI', Arial, sans-serif; 
                            line-height: 1.6;
                            color: {text_color};
                            background-color: {bg_color};
                            padding: 5px;
                        }}
                        h1, h2, h3, h4, h5, h6 {{ 
                            margin-top: 24px;
                            margin-bottom: 16px;
                            font-weight: 600;
                            line-height: 1.25;
                        }}
                        h1 {{ font-size: 2em; border-bottom: 1px solid #eaecef; padding-bottom: .3em; }}
                        h2 {{ font-size: 1.5em; border-bottom: 1px solid #eaecef; padding-bottom: .3em; }}
                        a {{ color: {link_color}; text-decoration: none; }}
                        a:hover {{ text-decoration: underline; }}
                        code {{ 
                            font-family: "Consolas", "Courier New", monospace; 
                            background-color: {code_bg};
                            padding: 0.2em 0.4em;
                            border-radius: 3px;
                        }}
                        pre {{ 
                            background-color: {code_bg}; 
                            border-radius: 3px; 
                            padding: 16px;
                            overflow: auto;
                        }}
                        pre code {{ 
                            background-color: transparent; 
                            padding: 0;
                        }}
                        blockquote {{ 
                            padding: 0 1em; 
                            color: #6a737d; 
                            border-left: 0.25em solid #dfe2e5; 
                        }}
                        table {{ 
                            border-collapse: collapse; 
                            width: 100%; 
                            margin-bottom: 16px; 
                        }}
                        table th, table td {{ 
                            border: 1px solid #dfe2e5; 
                            padding: 6px 13px; 
                        }}
                        table tr {{ 
                            background-color: {bg_color}; 
                        }}
                        table tr:nth-child(2n) {{ 
                            background-color: #f6f8fa; 
                        }}
                    </style>
                </head>
                <body>
                    {html}
                </body>
                </html>
                """
                
                # 设置为纯文本，以便正确显示HTML格式
                previewView.setPlainText(styled_html)
            except Exception as e:
                previewView.setPlainText(f"预览生成出错: {str(e)}")
    
    def updateStatusBarStyle(self):
        """更新状态栏样式"""
        if hasattr(self, 'statusBarWidget'):
            self.statusBarWidget.updateStyle()
    
    def scrollToLine(self, editor, lineNumber):
        """滚动编辑器到指定行"""
        if not editor:
            return
        
        # 检查文档是否为空
        if editor.document().isEmpty():
            print("无法滚动到指定行：文档为空")
            return
            
        # 检查行号是否有效
        total_lines = editor.document().blockCount()
        if lineNumber <= 0 or lineNumber > total_lines:
            print(f"无法滚动到指定行：行号 {lineNumber} 超出范围 (1-{total_lines})")
            return
            
        block = editor.document().findBlockByLineNumber(lineNumber - 1)
        if block.isValid():
            # 创建文本光标并移动到指定行
            cursor = QTextCursor(block)
            editor.setTextCursor(cursor)
            
            # 确保该行在视图中间
            editor.centerCursor()
            
            # 高亮显示该行
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor("#4077c866"))  # 半透明蓝色高亮
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = editor.textCursor()
            selection.cursor.clearSelection()
            
            editor.setExtraSelections([selection])
            
            # 使用动画闪烁效果
            self.highlightCurrentLine(editor)
        else:
            print(f"无法滚动到指定行：行号 {lineNumber} 对应的文本块无效")
    
    def applyHighlighter(self, editor):
        """应用语法高亮器到编辑器"""
        if not hasattr(self, 'highlightMode') or not self.highlightMode:
            return
            
        # 清除现有的高亮器
        if hasattr(editor, 'highlighter') and editor.highlighter:
            editor.highlighter.setDocument(None)
        
        # 确定文件类型
        fileType = self.currentFileType
        
        # 确定是否为亮色主题
        is_light_theme = False
        if hasattr(self, 'currentTheme'):
            is_light_theme = self.currentTheme == "light"
        
        # 创建新的高亮器
        try:
            highlighter = get_highlighter(fileType, editor.document(), is_light_theme)
            if highlighter:
                editor.highlighter = highlighter
                print(f"已应用 {fileType} 语法高亮器")
            else:
                editor.highlighter = None
                print(f"未找到 {fileType} 对应的语法高亮器")
        except Exception as e:
            print(f"应用语法高亮器时出错: {e}")
            log_to_file(f"应用语法高亮器时出错: {e}")
            editor.highlighter = None
    
    def highlightCurrentLine(self, editor):
        """高亮当前行，带有闪烁效果"""
        if not editor:
            return
            
        # 检查文档是否为空
        if editor.document().isEmpty():
            print("无法高亮当前行：文档为空")
            return
            
        # 获取当前行的文本光标
        cursor = editor.textCursor()
        
        # 检查光标位置是否有效
        if cursor.position() < 0 or cursor.position() > editor.document().characterCount():
            print(f"无法高亮当前行：光标位置 {cursor.position()} 无效")
            return
            
        cursor.select(QTextCursor.LineUnderCursor)
        selection = QTextEdit.ExtraSelection()
        
        # 初始颜色
        highlight_color = QColor("#4077c866")  # 半透明蓝色高亮
        
        selection.format.setBackground(highlight_color)
        selection.format.setProperty(QTextFormat.FullWidthSelection, True)
        selection.cursor = cursor
        
        editor.setExtraSelections([selection])
        
        # 简单的闪烁效果
        def flash_highlight():
            nonlocal editor
            
            if not editor:
                return
                
            # 清除高亮
            editor.setExtraSelections([])
            
            # 延迟后恢复高亮
            QTimer.singleShot(300, lambda: self.restoreFormat(editor))
        
        # 延迟启动闪烁效果
        QTimer.singleShot(500, flash_highlight)
    
    def restoreFormat(self, editor):
        """恢复行高亮"""
        if not editor:
            return
            
        cursor = editor.textCursor()
        cursor.select(QTextCursor.LineUnderCursor)
        selection = QTextEdit.ExtraSelection()
        
        selection.format.setBackground(QColor("#4077c833"))  # 更淡的高亮
        selection.format.setProperty(QTextFormat.FullWidthSelection, True)
        selection.cursor = cursor
        
        editor.setExtraSelections([selection])
    
    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 设置完全透明的背景和去除边框
        self.setStyleSheet("background: transparent; border: none;")
        
        screen_geometry = QApplication.screenAt(QPoint(0, 0)).geometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()

        if screen_width >= 1920:
            width_ratio = 0.65
            height_ratio = 0.7
            min_width_ratio = 0.4
            min_height_ratio = 0.4
        elif screen_width >= 1366:
            width_ratio = 0.7
            height_ratio = 0.7
            min_width_ratio = 0.45
            min_height_ratio = 0.45
        else:
            width_ratio = 0.8
            height_ratio = 0.75
            min_width_ratio = 0.5
            min_height_ratio = 0.5
        
        window_width = min(int(screen_width * width_ratio), 1200)
        window_height = min(int(screen_height * height_ratio), 800)
        self.resize(window_width, window_height)
        
        min_width = int(screen_width * min_width_ratio)
        min_height = int(screen_height * min_height_ratio)
        min_width = max(min_width, 800)
        min_height = max(min_height, 600)
        self.setMinimumSize(min_width, min_height)
        
        self.dragging = False
        
        IconProvider.init_font()
        
        # 初始化主题管理器
        self.themeManager = ThemeManager()
        self.themeManager.load_themes_from_directory()
        self.currentTheme = "dark"  # 默认主题
        
        try:
            # 初始化文件管理器
            self.fileManager = FileManager()
            self.fileManager.fileLoaded.connect(self.onFileLoaded)
            self.fileManager.fileSaved.connect(self.onFileSaved)
            self.fileManager.fileDeleted.connect(lambda path: print(f"文件已删除: {path}"))
            
            # 初始化自动保存功能
            self.autoSave = AutoSave(self)
            self.autoSave.start()
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "错误", f"无法加载文件管理器模块: {str(e)}")
        
        self.openFiles = []
        self.currentFilePath = None
        self.currentTitle = "未命名"
        self.currentFileType = "text"  # 默认为普通文本
        self.highlightMode = True  # 默认开启高亮
        
        mainWidget = QWidget()
        mainWidget.setObjectName("mainWindow")
        # 样式将在applyTheme中设置
        self.setCentralWidget(mainWidget)
        
        mainLayout = QVBoxLayout(mainWidget)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)
        
        self.titleBar = TitleBar(self)
        mainLayout.addWidget(self.titleBar)
        
        contentContainer = QWidget()
        contentLayout = QHBoxLayout(contentContainer)
        contentLayout.setContentsMargins(0, 0, 0, 0)
        contentLayout.setSpacing(0)
        
        self.sidebar = SidebarWidget()
        self.sidebar.importBtn.clicked.connect(self.openFile)
        self.sidebar.exportBtn.clicked.connect(self.saveFile)
        self.sidebar.newNoteBtn.clicked.connect(self.newFile)
        self.sidebar.deleteBtn.clicked.connect(self.deleteFile)
        self.sidebar.fileChanged.connect(self.changeFile)
        self.sidebar.fileClosed.connect(self.closeFile)
        
        self.editorsStack = QStackedWidget()
        self.editors = []
        self.previewViews = []
        
        editorWidget = QWidget()
        editorWidget.setObjectName("editorContainer")
        editorLayout = QVBoxLayout(editorWidget)
        editorLayout.setContentsMargins(0, 0, 0, 0)
        editorLayout.setSpacing(0)
        
        editorLayout.addWidget(self.editorsStack)
        
        contentLayout.addWidget(self.sidebar)
        contentLayout.addWidget(editorWidget)
        
        mainLayout.addWidget(contentContainer, 1)
        
        self.statusBarWidget = StatusBar(self)
        mainLayout.addWidget(self.statusBarWidget)
        
        self.statusBarWidget.fontSizeChanged.connect(self.changeFontSize)
        self.statusBarWidget.previewModeChanged.connect(self.togglePreviewMode)
        self.statusBarWidget.highlightModeChanged.connect(self.toggleHighlightMode)
        self.statusBarWidget.scrollToLineRequested.connect(self.onScrollToLineRequested)
        
        try:
            import markdown
            self.markdown = markdown
        except ImportError:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "缺少依赖", "未安装markdown模块，预览功能不可用。请执行 pip install markdown 安装。")
            self.markdown = None
        
        # 创建初始编辑器并在openFiles列表中记录
        firstEditorIndex = self.createNewEditor()
        
        # 记录初始标签页信息 (对应于侧边栏中默认创建的"未命名"标签页)
        self.openFiles.append({
            'index': 0,  # 第一个标签页索引是0
            'editorIndex': firstEditorIndex,
            'filePath': None,
            'title': "未命名",
            'isVirtual': True  # 标记为虚拟标签页
        })
        print(f"初始标签页已添加到openFiles列表，编辑器索引: {firstEditorIndex}")
        
        # 所有UI组件创建完成后应用主题
        self.applyTheme(self.currentTheme)
        
    def applyTheme(self, theme_name=None):
        """应用主题到应用程序"""
        print(f"----------开始应用主题: {theme_name}----------")
        if theme_name:
            self.currentTheme = theme_name
            print(f"设置当前主题为: {self.currentTheme}")
        
        # 如果主题管理器尚未初始化，先初始化
        if not hasattr(self, 'themeManager') or not self.themeManager:
            self.themeManager = ThemeManager()
            self.themeManager.load_themes_from_directory()
            print("初始化主题管理器")
        
        # 设置当前主题
        success = self.themeManager.set_theme(self.currentTheme)
        print(f"设置主题结果: {success}, 当前主题: {self.currentTheme}")
        
        if hasattr(self.themeManager, 'current_theme_name'):
            print(f"主题管理器当前主题名称: {self.themeManager.current_theme_name}")
        
        if hasattr(self.themeManager, 'current_theme') and self.themeManager.current_theme:
            theme_name_attr = self.themeManager.current_theme.name if hasattr(self.themeManager.current_theme, 'name') else "未知"
            print(f"主题对象名称: {theme_name_attr}")
            
            # 检查主题数据
            bg_color = self.themeManager.current_theme.get("editor.background", "未设置")
            print(f"编辑器背景色: {bg_color}")
            
            # 亮色主题特殊处理
            if self.currentTheme == "light":
                print("执行亮色主题特殊处理")
                if hasattr(self.themeManager.current_theme, 'data') and 'editor' in self.themeManager.current_theme.data:
                    self.themeManager.current_theme.data['editor']['background'] = '#ffffff'
                    self.themeManager.current_theme.data['editor']['text_color'] = '#333333'
                    self.themeManager.current_theme.data['editor']['border_color'] = '#e5e5e5'
                    print("强制设置亮色主题编辑器属性")
        
        if not success:
            print(f"无法应用主题 {self.currentTheme}，使用默认主题")
            self.currentTheme = "dark"
            success = self.themeManager.set_theme("dark")
            if not success:
                print("无法应用默认主题")
                return
            
        # 应用窗口样式
        window_style = self.themeManager.get_window_style()
        if window_style and self.centralWidget():
            self.centralWidget().setStyleSheet(window_style)
            print("已应用窗口样式")
        
        # 更新编辑器样式
        fontSize = self.statusBarWidget.currentFontSize if hasattr(self, 'statusBarWidget') else 15
        
        print(f"准备更新编辑器样式，编辑器数量: {len(self.editors) if hasattr(self, 'editors') else 0}")
        for i, editor in enumerate(self.editors if hasattr(self, 'editors') else []):
            print(f"更新编辑器 {i} 的样式")
            self.updateEditorStyle(editor, fontSize)
            
        # 更新编辑器容器样式
        if hasattr(self, 'editorsStack'):
            print(f"准备更新编辑器容器样式，编辑器堆栈数量: {self.editorsStack.count()}")
            for i in range(self.editorsStack.count()):
                editorStack = self.editorsStack.widget(i)
                if editorStack:
                    print(f"处理编辑器堆栈 {i}, 子控件数量: {editorStack.count()}")
                    for j in range(editorStack.count()):
                        container = editorStack.widget(j)
                        if container:
                            print(f"更新容器 {i}.{j} 的样式")
                            self.updateEditorContainerStyle(container)
                    
        # 更新预览样式
        if hasattr(self, 'previewViews'):
            print(f"准备更新预览样式，预览视图数量: {len(self.previewViews)}")
            for i, preview in enumerate(self.previewViews):
                print(f"更新预览视图 {i}")
                self.updatePreview(i)
            
        # 更新标题栏样式
        if hasattr(self, 'titleBar'):
            print("更新标题栏样式")
            self.titleBar.updateStyle()
        
        # 更新侧边栏样式
        if hasattr(self, 'sidebar'):
            print("更新侧边栏样式")
            self.sidebar.updateStyle(self.themeManager)
        
        # 更新状态栏样式
        print("更新状态栏样式")
        self.updateStatusBarStyle()
        
        print(f"----------主题 {self.currentTheme} 应用完成----------")
    
    def createNewEditor(self):
        print("创建新编辑器")
        
        # 检查当前主题
        if hasattr(self, 'themeManager') and self.themeManager and hasattr(self.themeManager, 'current_theme_name'):
            print(f"创建新编辑器时的当前主题: {self.themeManager.current_theme_name}")
        
        editorStack = QStackedWidget()
        
        editorContainer = QWidget()
        editorContainer.setObjectName("editorContainer")
        # 初始样式将在后面通过updateEditorContainerStyle设置
        innerEditorLayout = QVBoxLayout(editorContainer)
        innerEditorLayout.setContentsMargins(15, 10, 15, 10)
        
        editor = QPlainTextEdit()
        editor.setObjectName(f"editor_{len(self.editors)}")
        
        # 确定当前主题
        theme_name = "unknown"
        if hasattr(self, 'themeManager') and self.themeManager and hasattr(self.themeManager, 'current_theme'):
            if hasattr(self.themeManager.current_theme, 'name'):
                theme_name = self.themeManager.current_theme.name
        
        print(f"创建编辑器时的当前主题: {theme_name}")
        
        # 设置编辑器样式
        self.updateEditorStyle(editor, 15)
        editor.setPlaceholderText("输入内容...")
        
        try:
            if hasattr(self, 'themeManager') and self.themeManager:
                scrollbar_style = self.themeManager.get_scrollbar_style()
            else:
                scrollbar_style = ScrollBarStyle.get_style(base_color="transparent", handle_color="rgba(255, 255, 255, 0.3)")
            
            print(f"添加滚动条样式: {scrollbar_style[:50]}...")
            editor.setStyleSheet(editor.styleSheet() + scrollbar_style)
            
            editor.verticalScrollBar().setStyleSheet(scrollbar_style)
        except Exception as e:
            print(f"添加滚动条样式时出错: {e}")
        
        innerEditorLayout.addWidget(editor)
        
        previewContainer = QWidget()
        previewContainer.setObjectName("previewContainer")
        previewLayout = QVBoxLayout(previewContainer)
        previewLayout.setContentsMargins(15, 10, 15, 10)
        
        previewView = QPlainTextEdit()
        previewView.setReadOnly(True)
        
        # 预览视图样式将在updatePreview中设置
        try:
            if hasattr(self, 'themeManager') and self.themeManager:
                scrollbar_style = self.themeManager.get_scrollbar_style()
            else:
                scrollbar_style = ScrollBarStyle.get_style(base_color="transparent", handle_color="rgba(255, 255, 255, 0.3)")
            previewView.setStyleSheet(previewView.styleSheet() + scrollbar_style)
        except Exception as e:
            print(f"为预览区域添加滚动样式时出错: {e}")
            
        previewLayout.addWidget(previewView)
        
        # 添加到堆栈中，确保编辑器在最上层（索引0）
        editorStack.addWidget(editorContainer)
        editorStack.addWidget(previewContainer)
        editorStack.setCurrentIndex(0)  # 确保显示编辑器而非预览
        
        # 添加到主堆栈
        self.editorsStack.addWidget(editorStack)
        
        # 记录编辑器和预览视图
        self.editors.append(editor)
        self.previewViews.append(previewView)
        
        # 连接信号
        editor.textChanged.connect(lambda: self.updateLineCount(editor))
        editor.textChanged.connect(lambda: self.updatePreview(len(self.editors) - 1))
        
        # 应用容器样式
        self.updateEditorContainerStyle(editorContainer)
        # 也应用相同的边框样式到预览容器
        self.updateEditorContainerStyle(previewContainer)
        # 应用预览样式
        self.updatePreview(len(self.editors) - 1)
        
        # 切换到新创建的编辑器
        editorIndex = len(self.editors) - 1
        self.editorsStack.setCurrentIndex(editorIndex)
        
        print(f"新编辑器创建完成，索引: {editorIndex}")
        return editorIndex
    
    def openFile(self):
        # 使用FileManager中的open_file功能
        open_file(self)
    
    def saveFile(self):
        # 使用FileManager中的save_file功能
        save_file(self)
        # 如果有自动保存功能，更新时间戳
        if hasattr(self, 'autoSave'):
            if self.currentFilePath:
                self.autoSave.file_saved(self.currentFilePath)
    
    def newFile(self):
        # 使用FileManager中的new_file功能
        new_file(self)
    
    def closeFile(self, filePath):
        # 使用FileManager中的close_file功能
        close_file(self, filePath)
    
    def printOpenFilesList(self):
        """打印当前打开的文件列表，用于调试"""
        print("\n--- 当前打开的文件列表 ---")
        for i, file_info in enumerate(self.openFiles):
            index = file_info.get('index', 'N/A')
            editor_index = file_info.get('editorIndex', 'N/A')
            file_path = file_info.get('filePath', 'None')
            title = file_info.get('title', 'Untitled')
            is_virtual = file_info.get('isVirtual', False)
            print(f"[{i}] 标签索引: {index}, 编辑器索引: {editor_index}, 路径: {file_path}, 标题: {title}, 虚拟标签: {is_virtual}")
        print("------------------------\n")

    def changeFile(self, filePath, fileName):
        # 使用FileManager中的change_file功能
        change_file(self, filePath, fileName)
        
    def updateLineCount(self, editor):
        """更新行数统计"""
        if not editor or not hasattr(self, 'statusBarWidget'):
            return
        
        # 获取文本文档
        doc = editor.document()
        
        # 获取文档总行数
        line_count = doc.blockCount()
        
        # 设置状态栏的行数显示
        try:
            self.statusBarWidget.lineCount.setText(f"{line_count} 行")
            print(f"更新行数显示: {line_count} 行")
        except Exception as e:
            print(f"更新行数显示时出错: {e}")
            log_to_file(f"更新行数显示时出错: {e}")
        
    def run(self):
        """运行应用程序"""
        # 显示窗口
        self.show()
        
        # 创建一个默认的文件（如果没有命令行参数指定打开的文件）
        if len(self.openFiles) == 0:
            self.newFile()
        
        # 应用主题
        self.applyTheme(self.currentTheme)
        
        # 窗口居中显示
        desktop = QApplication.primaryScreen().availableGeometry()
        geometry = self.frameGeometry()
        geometry.moveCenter(desktop.center())
        self.move(geometry.topLeft())
        
        # 输出优化统计信息
        if hasattr(self, 'optimizer') and self.optimizer:
            stats = self.optimizer.get_optimization_stats()
            print(f"应用优化统计: 启动耗时 {stats['startup_time']:.3f}秒, "
                  f"预加载模块 {stats['preloaded_modules']} 个")
        
        print("Hanabi Notes 启动完成")

    def register_file_associations(self):
        """注册文件关联，使Hanabi Notes可以打开相关文件类型"""
        # 此方法仅适用于Windows系统
        if platform.system() != "Windows":
            return False
        
        try:
            import winreg
            
            # 获取程序路径
            app_path = os.path.abspath(sys.argv[0])
            
            # 为Markdown文件添加关联
            file_types = [".md", ".markdown", ".txt"]
            
            for ext in file_types:
                # 创建文件类型注册表项
                key_path = f"{ext}"
                try:
                    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{key_path}") as key:
                        winreg.SetValue(key, "", winreg.REG_SZ, f"HanabiNotes{ext}")
                except Exception as e:
                    print(f"注册文件类型 {ext} 失败: {e}")
                    continue
                
                # 创建应用程序注册表项
                key_path = f"Software\\Classes\\HanabiNotes{ext}"
                try:
                    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                        winreg.SetValue(key, "", winreg.REG_SZ, f"Hanabi Notes {ext} 文件")
                        
                    # 添加打开命令
                    key_path = f"Software\\Classes\\HanabiNotes{ext}\\shell\\open\\command"
                    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                        winreg.SetValue(key, "", winreg.REG_SZ, f'"{app_path}" "%1"')
                except Exception as e:
                    print(f"注册应用程序打开命令失败 {ext}: {e}")
                    continue
            
            print("文件关联注册成功")
            return True
        except Exception as e:
            print(f"注册文件关联失败: {e}")
            return False

    def showSettings(self):
        """显示设置对话框"""
        try:
            from Aya_Hanabi.Hanabi_Page.SettingsPages import SettingsDialog
            settings_dialog = SettingsDialog(self)
            settings_dialog.settingsChanged.connect(self.onSettingsChanged)
            settings_dialog.exec()
        except Exception as e:
            error_msg = f"打开设置对话框时出错: {e}"
            print(error_msg)
            log_to_file(error_msg)
            import traceback
            trace_info = traceback.format_exc()
            print(trace_info)
            log_to_file(trace_info)
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "错误", f"打开设置对话框时出错: {str(e)}")
    
    def showThemeSettings(self):
        """显示主题设置对话框"""
        try:
            from Aya_Hanabi.Hanabi_Page.SettingsPages import ThemeSettingsDialog
            theme_dialog = ThemeSettingsDialog(self)
            theme_dialog.themeChanged.connect(self.onThemeChanged)
            theme_dialog.exec()
        except Exception as e:
            error_msg = f"打开主题设置对话框时出错: {e}"
            print(error_msg)
            log_to_file(error_msg)
            import traceback
            trace_info = traceback.format_exc()
            print(trace_info)
            log_to_file(trace_info)
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "错误", f"打开主题设置对话框时出错: {str(e)}")
    
    def onSettingsChanged(self):
        """当设置改变时被调用"""
        try:
            # 重新加载设置
            settings_dir = os.path.join(os.path.expanduser("~"), ".hanabi_notes")
            settings_file = os.path.join(settings_dir, "settings.json")
            
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # 应用字体设置
                if "editor" in settings and "font" in settings["editor"]:
                    font_size = settings["editor"]["font"].get("size", 15)
                    self.changeFontSize(font_size)
                
                # 应用其他设置
                # ...
                
                print("设置已更新")
        except Exception as e:
            print(f"应用设置时出错: {str(e)}")
    
    def onThemeChanged(self, theme_name):
        """当主题改变时被调用"""
        try:
            # 应用主题
            self.applyTheme(theme_name)
            print(f"主题已更改为: {theme_name}")
        except Exception as e:
            print(f"应用主题时出错: {str(e)}")

if __name__ == "__main__":
    # 创建QApplication实例
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("Hanabi Notes")
    app.setOrganizationName("HanabiNotes")
    
    try:
        # 创建主窗口
        main_window = HanabiNotesApp()
        
        # 处理命令行参数（如果有）
        args = sys.argv[1:]
        
        # 检查是否有特殊命令行参数
        if "--register-file-types" in args:
            # 注册文件关联
            if main_window.register_file_associations():
                print("文件类型关联注册成功")
            else:
                print("文件类型关联注册失败")
            # 如果只是注册文件类型，不启动应用程序
            if len(args) == 1 and args[0] == "--register-file-types":
                sys.exit(0)
            # 移除这个参数，继续处理其他参数
            args.remove("--register-file-types")
            
        if args:
            # 只处理第一个不是选项的参数作为文件路径
            file_path = None
            for arg in args:
                if not arg.startswith("--"):
                    file_path = arg
                    break
                    
            if file_path and os.path.exists(file_path):
                print(f"从命令行打开文件: {file_path}")
                # 初始化窗口后再打开文件
                main_window.run()
                # 使用FileManager打开指定文件
                title = os.path.splitext(os.path.basename(file_path))[0]
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # 创建新标签并加载内容
                    main_window.fileManager.fileLoaded.emit(title, content)
                    # 更新文件路径
                    main_window.currentFilePath = file_path
                    main_window.currentTitle = title
                    # 更新UI
                    main_window.setWindowTitle(f"Hanabi Notes - {title}")
                except Exception as e:
                    print(f"打开命令行指定文件时出错: {e}")
                    log_to_file(f"打开命令行指定文件时出错: {e}")
                    # 出错时仍然正常启动程序
                    main_window.run()
            else:
                if file_path:
                    print(f"命令行指定的文件不存在: {file_path}")
                main_window.run()
        else:
            # 没有命令行参数，正常启动
            main_window.run()
        
        # 进入应用程序主循环
        result = app.exec()
        
        # 执行退出清理
        if 'app_Optimizer' in globals() and app_Optimizer:
            app_Optimizer.cleanup()
        
        sys.exit(result)
    except Exception as e:
        print(f"应用程序启动出错: {e}")
        log_to_file(f"应用程序启动出错: {e}")
        log_to_file(traceback.format_exc())
        sys.exit(1)
    