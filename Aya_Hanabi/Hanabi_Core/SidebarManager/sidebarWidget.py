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

class ActionButton(QPushButton):
    def __init__(self, iconName, tooltipText, parent=None):
        super().__init__(parent)
        self.setFixedSize(26, 26)
        self.setText(iconName)
        self.setFont(IconProvider.get_icon_font(16))
        self.setToolTip(tooltipText)
        self.setCursor(Qt.PointingHandCursor)
        
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #e0e5ec;
                border-radius: 13px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)
        
        self.hoverAnimation = ButtonHoverAnimation(self)
        
    def enterEvent(self, event):
        super().enterEvent(event)
        self.hoverAnimation.enterEvent()
        
    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.hoverAnimation.leaveEvent()
    
    def updateStyle(self, hovered=False, themeManager=None):
        icon_color = "#e0e5ec"  # 默认颜色
        hover_bg = "rgba(255, 255, 255, 0.15)"
        normal_bg = "transparent"
        
        if themeManager and themeManager.current_theme:
            icon_color = themeManager.current_theme.get("sidebar.icon_color", "#e0e5ec")
            hover_bg = themeManager.current_theme.get("sidebar.hover_tab_bg", "rgba(255, 255, 255, 0.1)")
            
        if hovered:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {hover_bg};
                    border: none;
                    color: {icon_color};
                    border-radius: 13px;
                }}
                QPushButton:pressed {{
                    background-color: rgba(255, 255, 255, 0.2);
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
                    background-color: rgba(255, 255, 255, 0.15);
                }}
            """)

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
        self.updateStyle()
        self.installEventFilter(self)
    
    def setFileName(self, name):
        self.fileName = name
        self.setToolTip(name)
    
    def setFilePath(self, path):
        self.filePath = path
    
    def setActive(self, active):
        self.isActive = active
        self.updateStyle()
    
    def updateStyle(self):
        if self.isActive:
            self.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.15);
                    color: white;
                    border: none;
                    border-radius: 18px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.2);
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: rgba(255, 255, 255, 0.7);
                    border: none;
                    border-radius: 18px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.1);
                }
            """)
    
    def eventFilter(self, obj, event):
        if obj == self:
            if event.type() == QEvent.Enter:
                QToolTip.showText(QCursor.pos(), self.fileName)
            elif event.type() == QEvent.Leave:
                QToolTip.hideText()
        
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

class SidebarWidget(QWidget):
    fileChanged = Signal(str, str)
    fileClosed = Signal(str)
    fileOpened = Signal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(60)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1d23;
            }
            #sidebar {
                background-color: #1a1d23;
                border-right: none;
            }
            #sidebarHeader {
                background-color: #1a1d23;
                border-bottom: 1px solid #2d2d2d;
            }
            #actionBar {
                background-color: #1a1d23;
            }
            #tabContainer {
                background-color: #1a1d23;
            }
            QScrollArea {
                background-color: #1a1d23;
                border: none;
            }
            QWidget#tabScrollAreaViewport {
                background-color: #1a1d23;
            }
            QToolTip {
                background-color: #1e2128;
                color: white;
                border: 1px solid #3a3f4b;
                padding: 4px;
                border-radius: 3px;
            }
        """)
        
        self.expandedWidth = 60
        
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)
        
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
        
        self.tabScrollArea = QScrollArea()
        self.tabScrollArea.setObjectName("tabScrollArea")
        self.tabScrollArea.setWidgetResizable(True)
        self.tabScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tabScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        scrollAreaPalette = self.tabScrollArea.palette()
        scrollAreaPalette.setColor(QPalette.Window, QColor("#005780"))
        self.tabScrollArea.setPalette(scrollAreaPalette)
        self.tabScrollArea.setAutoFillBackground(True)
        
        scrollbar_style = ScrollBarStyle.get_style()
        self.tabScrollArea.setStyleSheet(scrollbar_style)
        
        self.tabScrollArea.viewport().setAutoFillBackground(True)
        viewportPalette = self.tabScrollArea.viewport().palette()
        viewportPalette.setColor(QPalette.Window, QColor("#005780"))
        self.tabScrollArea.viewport().setPalette(viewportPalette)
        
        self.tabContainer = QWidget()
        self.tabContainer.setObjectName("tabContainer")
        tabContainerPalette = self.tabContainer.palette()
        tabContainerPalette.setColor(QPalette.Window, QColor("#005780"))
        self.tabContainer.setPalette(tabContainerPalette)
        self.tabContainer.setAutoFillBackground(True)
        
        self.tabLayout = QVBoxLayout(self.tabContainer)
        self.tabLayout.setContentsMargins(4, 12, 4, 8)
        self.tabLayout.setSpacing(8)
        self.tabLayout.setAlignment(Qt.AlignTop)
        
        self.tabScrollArea.setWidget(self.tabContainer)
        
        self.tabButtons = []
        self.activeTabIndex = -1
        
        self._active_scroll_animation = None
        
        self.scrollAnimation = ScrollFadeAnimation(self.tabScrollArea)
        
        self.headerLayout.addWidget(self.tabScrollArea, 1)
        
        mainLayout.addWidget(headerWidget, 1)
        
        bottomWidget = QWidget()
        bottomPalette = bottomWidget.palette()
        bottomPalette.setColor(QPalette.Window, QColor("#005780"))
        bottomWidget.setPalette(bottomPalette)
        bottomWidget.setAutoFillBackground(True)
        bottomWidget.setFixedHeight(0)
        mainLayout.addWidget(bottomWidget)
        
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
        
        for btn in self.tabButtons:
            if obj is btn:
                return btn.eventFilter(obj, event)
        
        return super().eventFilter(obj, event)
    
    def addTab(self, fileName, filePath=None):
        index = len(self.tabButtons)
        tabButton = TabButton(index)
        tabButton.setFileName(fileName)
        tabButton.setFilePath(filePath)
        def create_activate_handler(idx):
            return lambda: self.activateTab(idx, True)
        tabButton.clicked.connect(create_activate_handler(index))
        tabButton.closeRequested.connect(self.closeTab)
        
        self.tabButtons.append(tabButton)
        self.tabLayout.addWidget(tabButton, 0, Qt.AlignCenter)
        
        if self.activeTabIndex == -1 or len(self.tabButtons) == 1:
            self.activateTab(index, True)
        
        return index
    
    def activateTab(self, index, forceReload=True):
        if 0 <= index < len(self.tabButtons):
            # 先取消当前活动标签页
            if 0 <= self.activeTabIndex < len(self.tabButtons):
                self.tabButtons[self.activeTabIndex].setActive(False)
            
            # 设置新的活动标签页
            self.activeTabIndex = index
            self.tabButtons[index].setActive(True)
            self.scrollToActiveTab()
            
            # 获取标签页按钮信息
            tabButton = self.tabButtons[index]
            fileName = tabButton.fileName if hasattr(tabButton, 'fileName') else "未命名"
            filePath = tabButton.filePath if hasattr(tabButton, 'filePath') else None
            
            print(f"激活标签页: {index}, 文件名: {fileName}, 路径: {filePath}, 强制重载: {forceReload}")
            
            # 发送文件变更信号
            self.fileChanged.emit(filePath, fileName)
    
    def scrollToActiveTab(self):
        if 0 <= self.activeTabIndex < len(self.tabButtons):
            tabButton = self.tabButtons[self.activeTabIndex]
            if self._active_scroll_animation is not None:
                self._active_scroll_animation.stop()
            self._active_scroll_animation = ScrollAnimation.smooth_scroll_to(
                self.tabScrollArea, tabButton
            )
            self.scrollAnimation.show_temporarily()
    
    def closeTab(self, index):
        if 0 <= index < len(self.tabButtons):
            tabButton = self.tabButtons[index]
            filePath = tabButton.filePath
            
            self.tabLayout.removeWidget(tabButton)
            tabButton.deleteLater()
            self.tabButtons.pop(index)
            
            for i, btn in enumerate(self.tabButtons):
                btn.index = i
                try:
                    btn.clicked.disconnect()
                except:
                    pass
                
                def create_activate_handler(idx):
                    return lambda: self.activateTab(idx, True)
                btn.clicked.connect(create_activate_handler(i))
            
            if len(self.tabButtons) == 0:
                self.activeTabIndex = -1
                self.addTab("未命名")
            elif index == self.activeTabIndex:
                newIndex = min(index, len(self.tabButtons) - 1)
                self.activateTab(newIndex, True)
            elif index < self.activeTabIndex:
                self.activeTabIndex -= 1
            
            if filePath:
                self.fileClosed.emit(filePath)
    
    def updateTabName(self, index, fileName, filePath=None):
        if 0 <= index < len(self.tabButtons):
            tabButton = self.tabButtons[index]
            tabButton.setFileName(fileName)
            if filePath:
                tabButton.setFilePath(filePath)
    
    def getActiveTabInfo(self):
        if 0 <= self.activeTabIndex < len(self.tabButtons):
            tabButton = self.tabButtons[self.activeTabIndex]
            return {
                'index': self.activeTabIndex,
                'fileName': tabButton.fileName,
                'filePath': tabButton.filePath
            }
        return None
    
    def importNote(self):
        pass

    def exportNote(self):
        pass

    def createNewNote(self):
        pass

    def deleteNote(self):
        pass

    def updateStyle(self, themeManager=None):
        """更新侧边栏样式，应用主题设置"""
        if not themeManager:
            return
            
        try:
            # 获取侧边栏主题样式
            bg_color = themeManager.current_theme.get("sidebar.background", "#1a1d23")
            border_color = themeManager.current_theme.get("sidebar.border_color", "#2d2d2d")
            text_color = themeManager.current_theme.get("sidebar.text_color", "#e0e5ec")
            
            self.setStyleSheet(f"""
                QWidget {{
                    background-color: {bg_color};
                }}
                #sidebar {{
                    background-color: {bg_color};
                    border-right: 1px solid {border_color};
                }}
                #sidebarHeader {{
                    background-color: {bg_color};
                    border-bottom: 1px solid {border_color};
                }}
                #actionBar {{
                    background-color: {bg_color};
                }}
                #tabContainer {{
                    background-color: {bg_color};
                }}
                QScrollArea {{
                    background-color: {bg_color};
                    border: none;
                }}
                QWidget#tabScrollAreaViewport {{
                    background-color: {bg_color};
                }}
                QToolTip {{
                    background-color: #1e2128;
                    color: {text_color};
                    border: 1px solid #3a3f4b;
                    padding: 4px;
                    border-radius: 3px;
                }}
            """)
            
            # 更新颜色调色板
            for widget in [self.tabScrollArea, self.tabScrollArea.viewport(), self.tabContainer]:
                palette = widget.palette()
                palette.setColor(QPalette.Window, QColor(bg_color))
                widget.setPalette(palette)
                widget.setAutoFillBackground(True)
                
            # 更新分隔线样式
            for child in self.findChildren(QWidget):
                if child.height() == 1 and "separator" in child.objectName():
                    child.setStyleSheet(f"background-color: {border_color};")
                    
            # 更新按钮样式
            for btn in self.findChildren(ActionButton):
                btn.updateStyle(False, themeManager)
                
            # 更新TabButton样式
            active_tab_bg = themeManager.current_theme.get("sidebar.active_tab_bg", "#2f3440")
            hover_tab_bg = themeManager.current_theme.get("sidebar.hover_tab_bg", "rgba(255, 255, 255, 0.1)")
            icon_color = themeManager.current_theme.get("sidebar.icon_color", "rgba(224, 229, 236, 0.7)")
            
            for btn in self.tabButtons:
                if btn.isActive:
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {active_tab_bg};
                            color: {text_color};
                            border: none;
                            border-radius: 18px;
                        }}
                        QPushButton:hover {{
                            background-color: {hover_tab_bg};
                        }}
                    """)
                else:
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: transparent;
                            color: {icon_color};
                            border: none;
                            border-radius: 18px;
                        }}
                        QPushButton:hover {{
                            background-color: {hover_tab_bg};
                        }}
                    """)
                
        except Exception as e:
            print(f"更新侧边栏样式时出错: {e}")
            
    def closeEvent(self, event):
        self.scrollAnimation.cleanup()
        super().closeEvent(event) 