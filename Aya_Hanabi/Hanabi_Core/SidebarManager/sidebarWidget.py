from PySide6.QtCore import Qt, Signal, Slot, QSize, QPropertyAnimation, QEasingCurve, QEvent, QTimer, QPoint, QRect
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QScrollArea, QStackedWidget, QFileDialog, QGridLayout,
                             QTreeWidget, QTreeWidgetItem, QMenu, QFileSystemModel, QToolTip)
from PySide6.QtGui import QColor, QFont, QCursor, QPalette

from Aya_Hanabi.Hanabi_Core.FontManager.fontManager import IconProvider
from Aya_Hanabi.Hanabi_Core.SidebarManager import SidebarMode
from Aya_Hanabi.Hanabi_Styles.scrollbar_style import ScrollBarStyle
from Aya_Hanabi.Hanabi_Animation.scroll_animation import ScrollFadeAnimation, ScrollAnimation, SidebarAnimation
from Aya_Hanabi.Hanabi_Animation.toolbar_animation import SidebarActionManager
from Aya_Hanabi.Hanabi_Animation.button_animation import ButtonHoverAnimation
from Aya_Hanabi.Hanabi_Animation.animation_manager import AnimationManager, AnimationConfig
from Aya_Hanabi.Hanabi_Animation.sidebar_controller import SidebarController
from Aya_Hanabi.Hanabi_Core.FileManager import *

class ActionButton(QPushButton):
    def __init__(self, iconName, tooltipText, parent=None):
        super().__init__(parent)
        self.setFixedSize(26, 26)
        self.setText(iconName)
        self.setFont(IconProvider.get_icon_font(16))
        self.setToolTip(tooltipText)
        self.setCursor(Qt.PointingHandCursor)
        
        # 增加颜色不透明度，使图标更加明显
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: rgba(0, 0, 0, 0.9);  /* 增加不透明度 */
                border-radius: 13px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.1);
            }
            QPushButton:pressed {
                background-color: rgba(0, 0, 0, 0.15);
            }
        """)
        
        self.hoverAnimation = ButtonHoverAnimation(self)
        self.setWindowOpacity(1.0)  # 确保按钮初始状态完全不透明
        
    def enterEvent(self, event):
        super().enterEvent(event)
        self.hoverAnimation.enterEvent()
        
    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.hoverAnimation.leaveEvent()
    
    def updateStyle(self, hovered=False, themeManager=None):
        icon_color = "#333333"  # default Color
        hover_bg = "rgba(0, 0, 0, 0.05)"  # set bg 
        normal_bg = "transparent"
        
        if themeManager and hasattr(themeManager, 'current_theme') and themeManager.current_theme:
            try:
                icon_color = themeManager.current_theme.get("sidebar.icon_color", "#333333")
                
                # 判断是否为暗色主题
                is_dark_theme = False
                if hasattr(themeManager, 'current_theme_name'):
                    is_dark_theme = themeManager.current_theme_name in ["dark", "purple_dream", "green_theme"]
                    
                # 根据主题类型调整悬停背景透明度
                if is_dark_theme:
                    # 暗色主题增强悬停效果，提高透明度
                    hover_bg = themeManager.current_theme.get("sidebar.hover_tab_bg", "rgba(255, 255, 255, 0.08)")
                    # 暗色主题下提高图标颜色亮度
                    icon_color = themeManager.current_theme.get("sidebar.icon_color", "rgba(255, 255, 255, 0.9)")
                else:
                    hover_bg = themeManager.current_theme.get("sidebar.hover_tab_bg", "rgba(0, 0, 0, 0.05)")
                    # 浅色主题下确保图标颜色足够深
                    icon_color = themeManager.current_theme.get("sidebar.icon_color", "rgba(0, 0, 0, 0.9)")
            except Exception as e:
                print(f"ActionButton.updateStyle获取主题属性时出错: {e}")
            
        if hovered:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {hover_bg};
                    border: none;
                    color: {icon_color};
                    border-radius: 13px;
                }}
                QPushButton:pressed {{
                    background-color: rgba(0, 0, 0, 0.15);
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {normal_bg};
                    border: none;
                    color: {icon_color};
                    border-radius: 13px;
                }}
                QPushButton:hover {{
                    background-color: {hover_bg};
                }}
                QPushButton:pressed {{
                    background-color: rgba(0, 0, 0, 0.15);
                }}
            """)
            
        # 确保按钮保持完全不透明
        self.setWindowOpacity(1.0)

class TabButton(QPushButton):
    closeRequested = Signal(int)
    
    def __init__(self, index, iconName="description", parent=None):
        super().__init__(parent)
        self.index = index
        self.fileName = "未命名"
        self.filePath = None
        self.isActive = False
        
        self.setFixedSize(36, 36)
        self.setText(iconName)
        self.setFont(IconProvider.get_icon_font(18))
        self.setToolTip(self.fileName)
        self.setCursor(Qt.PointingHandCursor)
        # 确保按钮完全不透明
        self.setWindowOpacity(1.0)

        # 创建关闭按钮
        self.closeButton = QPushButton(self)
        self.closeButton.setFixedSize(16, 16)
        self.closeButton.setText(IconProvider.get_icon("close"))
        self.closeButton.setFont(IconProvider.get_icon_font(12))
        self.closeButton.setCursor(Qt.PointingHandCursor)
        self.closeButton.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: rgba(0, 0, 0, 0.7);  /* 增加不透明度 */
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.1);
                color: rgba(0, 0, 0, 0.9);  /* 悬停时更明显 */
            }
        """)
        # 初始隐藏关闭按钮
        self.closeButton.hide()
        self.closeButton.clicked.connect(lambda: self.closeRequested.emit(self.index))
        
        self.updateStyle()
        self.installEventFilter(self)
    
    def setFileName(self, name):
        self.fileName = name
        self.setToolTip(name)
    
    def setFilePath(self, path):
        self.filePath = path
    
    def setActive(self, active):
        self.isActive = active
        # 获取主题管理器（如果可用）
        themeManager = None
        if self.window() and hasattr(self.window(), 'themeManager'):
            themeManager = self.window().themeManager
        self.updateStyle(themeManager)
    
    def updateStyle(self, themeManager=None):
        # 默认颜色 - 与以前保持兼容
        active_bg = "#2f3440"
        active_hover_bg = "#3a3f50"
        text_color = "white"
        inactive_color = "rgba(255, 255, 255, 0.7)"
        
        # 检查主题管理器是否可用，以及是否存在current_theme
        if themeManager and hasattr(themeManager, 'current_theme') and themeManager.current_theme:
            # 判断主题类型
            is_dark_theme = True
            if hasattr(themeManager, 'current_theme_name'):
                theme_name = themeManager.current_theme_name
                is_dark_theme = theme_name not in ["light", "silvery_white"]
            
            # 根据主题调整悬停效果
            if is_dark_theme:
                # 增强暗色主题悬停效果
                hover_bg = themeManager.current_theme.get("sidebar.hover_tab_bg", "rgba(255, 255, 255, 0.08)")
                active_hover_bg = "rgba(255, 255, 255, 0.12)"
                # 更新关闭按钮样式
                close_button_color = "rgba(255, 255, 255, 0.7)"  # 增加不透明度
                close_button_hover_color = "rgba(255, 255, 255, 0.9)"  # 悬停时更明显
                self.closeButton.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {close_button_color};
                        border: none;
                        border-radius: 8px;
                    }}
                    QPushButton:hover {{
                        background-color: rgba(255, 255, 255, 0.15);
                        color: {close_button_hover_color};
                    }}
                """)
                # 暗色主题下提高图标颜色亮度
                text_color = themeManager.current_theme.get("sidebar.text_color", "rgba(255, 255, 255, 0.9)")
                inactive_color = themeManager.current_theme.get("sidebar.icon_color", "rgba(255, 255, 255, 0.7)")
            else:
                hover_bg = "rgba(0, 0, 0, 0.03)"
                active_hover_bg = "rgba(0, 0, 0, 0.18)"
                # 更新关闭按钮样式（默认浅色主题）
                self.closeButton.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: rgba(0, 0, 0, 0.7);
                        border: none;
                        border-radius: 8px;
                    }
                    QPushButton:hover {
                        background-color: rgba(0, 0, 0, 0.1);
                        color: rgba(0, 0, 0, 0.9);
                    }
                """)
                # 浅色主题下确保图标颜色足够深
                text_color = themeManager.current_theme.get("sidebar.text_color", "#333333")
                inactive_color = themeManager.current_theme.get("sidebar.icon_color", "rgba(0, 0, 0, 0.9)")
            
            active_bg = themeManager.current_theme.get("sidebar.active_tab_bg", active_bg)
        else:
            # 如果主题管理器不可用，使用默认样式
            hover_bg = "rgba(255, 255, 255, 0.08)"  # 默认悬停背景色
            # 使用默认关闭按钮样式
            self.closeButton.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: rgba(255, 255, 255, 0.7);
                    border: none;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.15);
                    color: rgba(255, 255, 255, 0.9);
                }
            """)
        
        if self.isActive:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {active_bg};
                    color: {text_color};
                    border: none;
                    border-radius: 18px;
                }}
                QPushButton:hover {{
                    background-color: {active_hover_bg};
                }}
            """)
            # 当标签页被激活时，显示关闭按钮
            self.closeButton.show()
            self.closeButton.move(22, 3)  # 调整关闭按钮位置
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {inactive_color};
                    border: none;
                    border-radius: 18px;
                }}
                QPushButton:hover {{
                    background-color: {hover_bg};
                }}
            """)
            # 非激活状态隐藏关闭按钮
            self.closeButton.hide()
            
        # 确保按钮保持完全不透明
        self.setWindowOpacity(1.0)
    
    def eventFilter(self, obj, event):
        if obj == self:
            if event.type() == QEvent.Enter:
                QToolTip.showText(QCursor.pos(), self.fileName)
                # 鼠标进入时显示关闭按钮
                self.closeButton.show()
                self.closeButton.move(22, 3)  # 调整关闭按钮位置
            elif event.type() == QEvent.Leave:
                QToolTip.hideText()
                # 鼠标离开时隐藏关闭按钮（除非是活动标签）
                if not self.isActive:
                    self.closeButton.hide()
        
        return super().eventFilter(obj, event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            super().mousePressEvent(event)
        elif event.button() == Qt.MiddleButton:
            self.closeRequested.emit(self.index)
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def contextMenuEvent(self, event):
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
        
        closeAction = menu.addAction("关闭")
        closeOthersAction = menu.addAction("关闭其他")
        menu.addSeparator()
        closeAllAction = menu.addAction("关闭所有")
        
        action = menu.exec(event.globalPos())
        
        if action == closeAction:
            self.closeRequested.emit(self.index)
        elif action == closeOthersAction:
            # 获取父SidebarWidget
            parent_widget = self.parent()
            while parent_widget and not isinstance(parent_widget, SidebarWidget):
                parent_widget = parent_widget.parent()
                
            if parent_widget:
                parent_widget.closeOtherTabs(self.index)
        elif action == closeAllAction:
            # 获取父SidebarWidget
            parent_widget = self.parent()
            while parent_widget and not isinstance(parent_widget, SidebarWidget):
                parent_widget = parent_widget.parent()
                
            if parent_widget:
                parent_widget.closeAllTabs()

class SidebarWidget(QWidget):
    fileChanged = Signal(str, str)
    fileClosed = Signal(str)
    fileOpened = Signal(str, str)
    closeAllTabsRequested = Signal()  # 添加关闭所有标签的信号
    
    def __init__(self, parent=None):
        """
        初始化侧边栏
        
        注意：要使关闭标签页功能正常工作，父窗口应实现以下方法：
        - isTextModified(filePath): 检查文件是否被修改
        - saveFile(filePath): 保存指定路径的文件
        """
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(60)
        
        # 只设置基本样式，颜色将从主题获取
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
            #sidebar {
                border-right: none;
            }
            QToolTip {
                padding: 4px;
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                background-color: #f5f5f5;
                color: #333333;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 10, 0, 10)
        main_layout.setSpacing(3)
        
        # 创建标签页滚动区域
        self.tabScrollArea = QScrollArea()
        self.tabScrollArea.setWidgetResizable(True)
        self.tabScrollArea.setObjectName("tabScrollArea")
        self.tabScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tabScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tabScrollArea.setFrameShape(QScrollArea.NoFrame)
        self.tabScrollArea.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        """)
        
        self.tabContainer = QWidget()
        self.tabContainer.setObjectName("tabContainer")
        
        # 标签页布局
        self.tab_layout = QVBoxLayout(self.tabContainer)
        self.tab_layout.setContentsMargins(3, 3, 3, 3)
        self.tab_layout.setSpacing(3)
        self.tab_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        
        # 应用滚动条样式 - 修改使用方式
        scrollbar = self.tabScrollArea.verticalScrollBar()
        scrollbar.setStyleSheet(ScrollBarStyle.get_style())  # 直接使用样式表字符串
        
        self.tabScrollArea.setWidget(self.tabContainer)
        
        self.tabs = []
        self.tab_count = 0  # 初始化标签计数
        self.current_tab_index = -1
        
        self._active_scroll_animation = None
        
        self.scrollAnimation = ScrollFadeAnimation(self.tabScrollArea)
        
        main_layout.addWidget(self.tabScrollArea)
        
        headerWidget = QWidget()
        headerWidget.setObjectName("sidebarHeader")
        
        self.headerLayout = QVBoxLayout(headerWidget)
        self.headerLayout.setContentsMargins(8, 12, 8, 8)
        self.headerLayout.setSpacing(10)
        
        self.actionBar = QWidget()
        self.actionBar.setObjectName("actionBar")
        
        self.actionLayout = QVBoxLayout(self.actionBar)
        self.actionLayout.setContentsMargins(4, 8, 4, 8)
        self.actionLayout.setSpacing(8)
        
        self.importBtn = ActionButton("file_upload", "导入笔记")
        self.importBtn.setFixedSize(36, 36)
        self.importBtn.setFont(IconProvider.get_icon_font(18))
        self.importBtn.clicked.connect(self.importNote)
        self.actionLayout.addWidget(self.importBtn, 0, Qt.AlignCenter)
        
        self.exportBtn = ActionButton("file_download", "导出笔记")
        self.exportBtn.setFixedSize(36, 36)
        self.exportBtn.setFont(IconProvider.get_icon_font(18))
        self.exportBtn.clicked.connect(self.exportNote)
        self.actionLayout.addWidget(self.exportBtn, 0, Qt.AlignCenter)
        
        self.newNoteBtn = ActionButton("note_add", "新建笔记")
        self.newNoteBtn.setFixedSize(36, 36)
        self.newNoteBtn.setFont(IconProvider.get_icon_font(18))
        self.newNoteBtn.clicked.connect(self.createNewNote)
        self.actionLayout.addWidget(self.newNoteBtn, 0, Qt.AlignCenter)
        
        self.deleteBtn = ActionButton("delete", "删除笔记")
        self.deleteBtn.setFixedSize(36, 36)
        self.deleteBtn.setFont(IconProvider.get_icon_font(18))
        self.deleteBtn.clicked.connect(self.deleteNote)
        self.actionLayout.addWidget(self.deleteBtn, 0, Qt.AlignCenter)
        
        self.headerLayout.addWidget(self.actionBar)
        
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: rgba(255, 255, 255, 0.1);")
        self.headerLayout.addWidget(separator)
        
        self.headerLayout.addWidget(self.tabScrollArea, 1)
        
        main_layout.addWidget(headerWidget, 1)
        
        bottomWidget = QWidget()
        bottomPalette = bottomWidget.palette()
        bottomPalette.setColor(QPalette.Window, QColor("#005780"))
        bottomWidget.setPalette(bottomPalette)
        bottomWidget.setAutoFillBackground(True)
        bottomWidget.setFixedHeight(0)
        main_layout.addWidget(bottomWidget)
        
        self.addTab("未命名")
        
        self.installEventFilter(self)
        
        QTimer.singleShot(20, self.preloadAnimation)
    
    def preloadAnimation(self):
        for child in self.findChildren(QWidget):
            child.setAttribute(Qt.WA_StyledBackground, True)
    
    def eventFilter(self, obj, event):
        if obj is self.tabScrollArea.viewport():
            if event.type() == QEvent.Enter:
                self.scrollAnimation.start_show_animation()
                return False
            elif event.type() == QEvent.Leave:
                return False
        
        for btn in self.tabs:
            if obj is btn:
                return btn.eventFilter(obj, event)
        
        return super().eventFilter(obj, event)
    
    def addTab(self, fileName, filePath=None):
        index = len(self.tabs)
        tabButton = TabButton(index)
        tabButton.setFileName(fileName)
        tabButton.setFilePath(filePath)
        
        # 设置按钮点击事件
        def create_activate_handler(idx):
            return lambda: self.activateTab(idx, True)
            
        tabButton.clicked.connect(create_activate_handler(index))
        
        # 设置中键关闭事件
        tabButton.closeRequested.connect(self.closeTab)
        
        # 检查是否有主题管理器，如果有则应用样式
        if self.window() and hasattr(self.window(), 'themeManager'):
            tabButton.updateStyle(self.window().themeManager)
        
        self.tabs.append(tabButton)
        self.tab_layout.addWidget(tabButton, 0, Qt.AlignCenter)
        self.tab_count = len(self.tabs)  # 更新标签页计数
        
        if self.current_tab_index == -1 or len(self.tabs) == 1:
            self.activateTab(index, True)
        
        return index
    
    def activateTab(self, index, forceReload=True):
        if 0 <= index < len(self.tabs):
            # 先取消当前活动标签页
            if 0 <= self.current_tab_index < len(self.tabs):
                self.tabs[self.current_tab_index].setActive(False)
            
            # 设置新的活动标签页
            self.current_tab_index = index
            self.tabs[index].setActive(True)
            self.scrollToActiveTab()
            
            # 获取标签页按钮信息
            tabButton = self.tabs[index]
            fileName = tabButton.fileName if hasattr(tabButton, 'fileName') else "未命名"
            filePath = tabButton.filePath if hasattr(tabButton, 'filePath') else None
            
            print(f"激活标签页: {index}, 文件名: {fileName}, 路径: {filePath}, 强制重载: {forceReload}")
            
            # 发送文件变更信号
            self.fileChanged.emit(filePath, fileName)
    
    def scrollToActiveTab(self):
        if 0 <= self.current_tab_index < len(self.tabs):
            tabButton = self.tabs[self.current_tab_index]
            if self._active_scroll_animation is not None:
                self._active_scroll_animation.stop()
            self._active_scroll_animation = ScrollAnimation.smooth_scroll_to(
                self.tabScrollArea, tabButton
            )
            self.scrollAnimation.show_temporarily()
    
    def closeTab(self, index):
        """关闭指定索引的标签页"""
        # 检查是否只有一个标签页，如果是则不允许关闭
        if len(self.tabs) <= 1:
            print("这是最后一个标签页，不允许关闭")
            from Aya_Hanabi.Hanabi_Core.UI.messageBox import information
            information(self, "操作提示", "至少需要保留一个标签页")
            return
            
        if 0 <= index < len(self.tabs):
            fileToClose = self.tabs[index].filePath
            
            # 获取当前文本是否已修改
            modifiedStatus = False
            if self.parent() and hasattr(self.parent(), 'isTextModified'):
                modifiedStatus = self.parent().isTextModified(fileToClose)
            
            # 如果文件被修改，显示保存提示
            if modifiedStatus:
                from Aya_Hanabi.Hanabi_Core.UI.messageBox import HanabiMessageBox, question
                result = question(self, "保存文件", f"文件 {self.tabs[index].fileName} 已修改，是否保存？", 
                               HanabiMessageBox.YesNoCancel)
                
                if result == HanabiMessageBox.Yes_Result:
                    # 保存文件
                    if self.parent() and hasattr(self.parent(), 'saveFile'):
                        self.parent().saveFile(fileToClose)
                elif result == HanabiMessageBox.Cancel_Result:
                    # 取消关闭操作
                    return
                # 如果选择"No"，则不保存继续关闭
            
            tab_to_remove = self.tabs[index]
            self.tab_layout.removeWidget(tab_to_remove)
            tab_to_remove.deleteLater()
            
            # 从列表中移除
            filePath = self.tabs[index].filePath
            self.tabs.pop(index)
            self.tab_count -= 1
            
            # 调整剩余标签的索引
            for i in range(index, self.tab_count):
                self.tabs[i].index = i
            
            # 如果关闭的是当前活动的标签，切换到其他标签
            if index == self.current_tab_index:
                if self.tab_count > 0:
                    # 优先切换到前一个标签
                    new_index = min(index, self.tab_count - 1)
                    self.activateTab(new_index)
                else:
                    self.current_tab_index = -1
                    
            # 发出文件关闭信号
            if filePath:
                self.fileClosed.emit(filePath)
    
    def updateTabName(self, index, fileName, filePath=None):
        if 0 <= index < len(self.tabs):
            tabButton = self.tabs[index]
            tabButton.setFileName(fileName)
            if filePath:
                tabButton.setFilePath(filePath)
    
    def getActiveTabInfo(self):
        if 0 <= self.current_tab_index < len(self.tabs):
            tabButton = self.tabs[self.current_tab_index]
            return {
                'index': self.current_tab_index,
                'fileName': tabButton.fileName,
                'filePath': tabButton.filePath
            }
        return None
    
    def importNote(self):
        """
        导入笔记文件
        使用FileManager的open_file功能导入笔记
        """
        # 寻找一次主窗口，并直接向主窗口发送信号
        main_app = self._findMainApplication()
        if main_app:
            print("已找到主应用程序，直接调用open_file函数")
            # 异步调用，避免可能的递归调用问题
            QTimer.singleShot(10, lambda: self._safeOpenFile(main_app))
        elif self.parent():
            print("未找到主应用程序，尝试使用父窗口")
            # 使用父窗口作为备选
            QTimer.singleShot(10, lambda: self._safeOpenFile(self.parent()))
        else:
            print("无法导入笔记：找不到父窗口或主应用程序")
    
    def _safeOpenFile(self, target):
        """安全地调用open_file函数，捕获任何可能的异常"""
        try:
            result = open_file(target)
            print(f"文件导入结果: {result[0] if isinstance(result, tuple) and len(result) > 0 else '无'}")
        except Exception as e:
            from Aya_Hanabi.Hanabi_Core.UI.messageBox import warning
            print(f"导入笔记时出错: {e}")
            import traceback
            traceback.print_exc()
            warning(self, "导入错误", f"无法导入笔记: {str(e)}")
    
    def _findMainApplication(self):
        """
        查找主应用程序窗口
        
        Returns:
            主应用程序窗口实例或None
        """
        # 方法1：通过parent()方法向上查找
        parent = self
        for _ in range(5):  # 最多向上查找5层，避免无限循环
            if not parent:
                break
                
            if hasattr(parent, 'openFiles') and hasattr(parent, 'editors'):
                print(f"通过parent()找到主窗口")
                return parent
                
            if hasattr(parent, 'parent'):
                parent = parent.parent()
            else:
                break
        
        # 方法2：如果方法1没找到，尝试window()方法
        if hasattr(self, 'window'):
            window = self.window()
            if hasattr(window, 'openFiles') and hasattr(window, 'editors'):
                print(f"通过window()找到主窗口")
                return window
        
        # 方法3：查看顶层窗口
        from PySide6.QtWidgets import QApplication
        for widget in QApplication.topLevelWidgets():
            if hasattr(widget, 'openFiles') and hasattr(widget, 'editors'):
                print(f"通过topLevelWidgets找到主窗口")
                return widget
        
        return None

    def exportNote(self):
        """
        导出笔记文件
        使用FileManager的saveFile功能导出笔记
        """
        # 寻找一次主窗口，并直接向主窗口发送信号
        main_app = self._findMainApplication()
        if main_app:
            print("已找到主应用程序，直接调用saveFile函数")
            # 异步调用，避免可能的递归调用问题
            QTimer.singleShot(10, lambda: self._safeSaveFile(main_app))
        elif self.parent():
            print("未找到主应用程序，尝试使用父窗口")
            # 使用父窗口作为备选
            QTimer.singleShot(10, lambda: self._safeSaveFile(self.parent()))
        else:
            print("无法导出笔记：找不到父窗口或主应用程序")
    
    def _safeSaveFile(self, target):
        """安全地调用saveFile函数，捕获任何可能的异常"""
        try:
            result = saveFile(target)
            print(f"文件导出结果: {result if result else '无'}")
        except Exception as e:
            from Aya_Hanabi.Hanabi_Core.UI.messageBox import warning
            print(f"导出笔记时出错: {e}")
            import traceback
            traceback.print_exc()
            warning(self, "导出错误", f"无法导出笔记: {str(e)}")

    def createNewNote(self):
        """
        创建新笔记
        使用FileManager的new_file功能创建新笔记
        """
        # 寻找一次主窗口，并直接向主窗口发送信号
        main_app = self._findMainApplication()
        if main_app:
            print("已找到主应用程序，直接调用new_file函数")
            # 异步调用，避免可能的递归调用问题
            QTimer.singleShot(10, lambda: self._safeCreateNewFile(main_app))
        elif self.parent():
            print("未找到主应用程序，尝试使用父窗口")
            # 使用父窗口作为备选
            QTimer.singleShot(10, lambda: self._safeCreateNewFile(self.parent()))
        else:
            print("无法创建新笔记：找不到父窗口或主应用程序")
    
    def _safeCreateNewFile(self, target):
        """安全地调用new_file函数，捕获任何可能的异常"""
        try:
            new_file(target)
            print(f"新笔记创建成功")
        except Exception as e:
            from Aya_Hanabi.Hanabi_Core.UI.messageBox import warning
            print(f"创建新笔记时出错: {e}")
            import traceback
            traceback.print_exc()
            warning(self, "创建错误", f"无法创建新笔记: {str(e)}")

    def deleteNote(self):
        """
        删除笔记
        使用FileManager的delete_file功能删除当前笔记
        """
        # 寻找一次主窗口，并直接向主窗口发送信号
        main_app = self._findMainApplication()
        if main_app:
            print("已找到主应用程序，直接调用delete_file函数")
            # 异步调用，避免可能的递归调用问题
            QTimer.singleShot(10, lambda: self._safeDeleteFile(main_app))
        elif self.parent():
            print("未找到主应用程序，尝试使用父窗口")
            # 使用父窗口作为备选
            QTimer.singleShot(10, lambda: self._safeDeleteFile(self.parent()))
        else:
            print("无法删除笔记：找不到父窗口或主应用程序")
    
    def _safeDeleteFile(self, target):
        """安全地调用delete_file函数，捕获任何可能的异常"""
        try:
            delete_file(target)
            print(f"笔记删除操作执行完成")
        except Exception as e:
            from Aya_Hanabi.Hanabi_Core.UI.messageBox import warning
            print(f"删除笔记时出错: {e}")
            import traceback
            traceback.print_exc()
            warning(self, "删除错误", f"无法删除笔记: {str(e)}")

    def updateStyle(self, themeManager=None):
        """更新侧边栏样式，包括标签样式"""
        # 更新侧边栏主体样式
        sidebar_bg = "#252932"  # 默认暗色背景
        icon_color = "rgba(255, 255, 255, 0.7)"  # 默认暗色图标
        is_dark_theme = True  # 默认使用暗色主题
        
        if themeManager and hasattr(themeManager, 'current_theme') and themeManager.current_theme:
            try:
                # 从主题获取侧边栏背景色
                sidebar_bg = themeManager.current_theme.get("sidebar.background", "#252932")
                icon_color = themeManager.current_theme.get("sidebar.icon_color", "rgba(255, 255, 255, 0.7)")
                
                # 判断是否为暗色主题
                is_dark_theme = True
                if hasattr(themeManager, 'current_theme_name'):
                    is_dark_theme = themeManager.current_theme_name not in ["light", "silvery_white"]
            except Exception as e:
                print(f"获取主题属性时出错: {e}")
        
        # 根据主题类型设置侧边栏样式
        if is_dark_theme:
            # 暗色主题样式
            self.setStyleSheet(f"""
                QWidget {{
                    background-color: transparent;
                }}
                #sidebar {{
                    background-color: {sidebar_bg};
                    border-right: none;
                }}
                QToolTip {{
                    background-color: #2d2d30;
                    color: #e0e0e0;
                    border: 1px solid #3f3f46;
                    border-radius: 4px;
                    padding: 4px;
                }}
            """)
        else:
            # 浅色主题样式
            self.setStyleSheet(f"""
                QWidget {{
                    background-color: transparent;
                }}
                #sidebar {{
                    background-color: {sidebar_bg};
                    border-right: none;
                }}
                QToolTip {{
                    background-color: #f5f5f5;
                    color: #333333;
                    border: 1px solid #c0c0c0;
                    border-radius: 4px;
                    padding: 4px;
                }}
            """)
        
        # 更新所有操作按钮的样式
        for btn in self.findChildren(ActionButton):
            btn.setWindowOpacity(1.0)
            if hasattr(btn, 'updateStyle'):
                try:
                    btn.updateStyle(False, themeManager)
                except Exception as e:
                    print(f"更新ActionButton样式时出错: {e}")
        
        # 更新TabButton样式 - 传递主题管理器给每个按钮
        for btn in self.tabs:
            btn.setWindowOpacity(1.0)  # 确保标签按钮完全不透明
            try:
                btn.updateStyle(themeManager)
            except Exception as e:
                print(f"更新TabButton样式时出错: {e}")
    
    def closeEvent(self, event):
        self.scrollAnimation.cleanup()
        super().closeEvent(event)

    # 添加展开侧边栏方法
    def expandBar(self):
        # 如果已经有侧边栏控制器，则使用它
        if hasattr(self, 'sidebarController') and self.sidebarController:
            self.sidebarController.expand()
        # 如果没有控制器但有动作管理器，则使用它
        elif hasattr(self, 'actionManager') and self.actionManager:
            self.actionManager.expand()

    # 添加检查并收起侧边栏方法
    def checkAndCollapseBar(self):
        # 检查鼠标是否在侧边栏区域外
        global_pos = QCursor.pos()
        sidebar_rect = self.rect()
        sidebar_global_pos = self.mapToGlobal(QPoint(0, 0))
        sidebar_global_rect = QRect(sidebar_global_pos, self.size())
        
        if not sidebar_global_rect.contains(global_pos):
            # 如果已经有侧边栏控制器，则使用它
            if hasattr(self, 'sidebarController') and self.sidebarController:
                self.sidebarController.collapse()
            # 如果没有控制器但有动作管理器，则使用它
            elif hasattr(self, 'actionManager') and self.actionManager:
                self.actionManager.collapse()

    def closeOtherTabs(self, keep_index):
        """关闭除了指定索引外的所有标签页"""
        # 检查所有要关闭的标签是否有未保存的修改
        modified_tabs = []
        for i in range(self.tab_count):
            if i != keep_index:
                fileToCheck = self.tabs[i].filePath
                if self.parent() and hasattr(self.parent(), 'isTextModified'):
                    if self.parent().isTextModified(fileToCheck):
                        modified_tabs.append((i, self.tabs[i].fileName))
        
        # 如果有多个修改过的文件，提供批量操作选项
        if len(modified_tabs) > 1:
            from Aya_Hanabi.Hanabi_Core.UI.messageBox import HanabiMessageBox, question
            modified_names = "\n".join([f"• {name}" for _, name in modified_tabs])
            result = question(self, "保存修改", f"以下文件已被修改，是否全部保存？\n{modified_names}", 
                           HanabiMessageBox.YesNoCancel)
            
            if result == HanabiMessageBox.Yes_Result:
                # 全部保存
                for tab_idx, _ in modified_tabs:
                    fileToSave = self.tabs[tab_idx].filePath
                    if self.parent() and hasattr(self.parent(), 'saveFile'):
                        self.parent().saveFile(fileToSave)
            elif result == HanabiMessageBox.Cancel_Result:
                # 取消操作
                return
            # 如果选择 No，则不保存继续关闭
        
        # 关闭除了keep_index外的所有标签
        tabs_to_close = [i for i in range(self.tab_count) if i != keep_index]
        # 从后往前关闭，避免索引变化问题
        for i in sorted(tabs_to_close, reverse=True):
            self.closeTab(i)
    
    def closeAllTabs(self):
        """关闭所有标签页"""
        # 检查是否只有一个标签页，如果是则不允许关闭全部
        if len(self.tabs) <= 1:
            from Aya_Hanabi.Hanabi_Core.UI.messageBox import information
            information(self, "操作提示", "至少需要保留一个标签页")
            return
            
        # 检查所有要关闭的标签是否有未保存的修改
        modified_tabs = []
        for i in range(self.tab_count):
            fileToCheck = self.tabs[i].filePath
            if self.parent() and hasattr(self.parent(), 'isTextModified'):
                if self.parent().isTextModified(fileToCheck):
                    modified_tabs.append((i, self.tabs[i].fileName))
        
        # 如果有多个修改过的文件，提供批量操作选项
        if len(modified_tabs) > 1:
            from Aya_Hanabi.Hanabi_Core.UI.messageBox import HanabiMessageBox, question
            modified_names = "\n".join([f"• {name}" for _, name in modified_tabs])
            result = question(self, "保存修改", f"以下文件已被修改，是否全部保存？\n{modified_names}", 
                           HanabiMessageBox.YesNoCancel)
            
            if result == HanabiMessageBox.Yes_Result:
                # 全部保存
                for tab_idx, _ in modified_tabs:
                    fileToSave = self.tabs[tab_idx].filePath
                    if self.parent() and hasattr(self.parent(), 'saveFile'):
                        self.parent().saveFile(fileToSave)
            elif result == HanabiMessageBox.Cancel_Result:
                # 取消操作
                return
            # 如果选择 No，则不保存继续关闭
        
        # 从后往前关闭标签页，但保留最后一个
        for i in range(self.tab_count - 1, 0, -1):
            self.closeTab(i)
        
        # 关闭所有后留下一个标签页，我们需要创建一个新的空白标签页
        if self.tab_count == 1:
            # 清空当前唯一标签页，而不是关闭它
            if self.parent() and hasattr(self.parent(), 'createNewNote'):
                # 使用现有的创建新笔记功能
                self.createNewNote()
            else:
                # 如果父窗口没有提供创建新笔记的功能，尝试直接清空编辑器
                if self.parent() and hasattr(self.parent(), 'currentEditor'):
                    self.parent().currentEditor.clear()
                # 更新标签页名称
                self.updateTabName(0, "未命名", None)
        
        # 发出关闭所有标签的信号
        self.closeAllTabsRequested.emit() 