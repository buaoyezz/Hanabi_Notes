from enum import Enum
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property, QRect, Signal, QSize, QObject, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QStackedWidget, QScrollArea
from PySide6.QtGui import QColor, QPalette


class SidebarMode(Enum):
    PROJECT_LIST = 0  # 项目列表模式
    OUTLINE = 1       # 大纲模式

class SidebarManager(QObject):
    # 侧边栏宽度变化信号
    widthChanged = Signal(int)
    # 侧边栏可见性变化信号
    visibilityChanged = Signal(bool)
    # 侧边栏模式变化信号
    modeChanged = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._visible = False
        self._width = 0
        self._targetWidth = 250  # 展开后的目标宽度
        self._mode = SidebarMode.PROJECT_LIST
        self._animation = None
        self.expandedWidth = 240  # 展开宽度
        self.collapsedWidth = 60  # 收起宽度
        self.currentWidth = self.collapsedWidth  # 当前宽度
        self.isAnimating = False  # 是否正在动画中
        
    # 初始化动画
    def initAnimation(self, sidebar):
        self._animation = QPropertyAnimation(sidebar, b"minimumWidth")
        self._animation.setDuration(200)  # 动画持续时间（毫秒）
        self._animation.setEasingCurve(QEasingCurve.InOutQuad)  # 缓动曲线
        
        # 连接动画完成信号
        self._animation.finished.connect(self.onAnimationFinished)
        
    def onAnimationFinished(self):
        """动画完成后的处理"""
        self.isAnimating = False
    
    # 侧边栏宽度属性
    def getWidth(self):
        return self._width
        
    def setWidth(self, width):
        if self._width != width:
            self._width = width
            self.widthChanged.emit(width)
            
    width = Property(int, getWidth, setWidth)
    
    # 切换侧边栏可见性
    def toggleVisibility(self, sidebar):
        if self.isAnimating:
            return
            
        if sidebar.width() == self.collapsedWidth:
            sidebar.setExpanded(True)
            self.showSidebar(sidebar)
        else:
            sidebar.setExpanded(False)
            self.hideSidebar(sidebar)
    
    # 显示侧边栏
    def showSidebar(self, sidebar):
        if self.isAnimating or sidebar.width() == self.expandedWidth:
            return
            
        self.isAnimating = True
        sidebar.setMaximumWidth(self.expandedWidth)
        self._animation.setStartValue(sidebar.width())
        self._animation.setEndValue(self.expandedWidth)
        self._animation.start()
        self.currentWidth = self.expandedWidth
    
    # 隐藏侧边栏
    def hideSidebar(self, sidebar):
        if self.isAnimating or sidebar.width() == self.collapsedWidth:
            return
            
        self.isAnimating = True
        sidebar.setMaximumWidth(self.expandedWidth)  # 确保最大宽度足够
        self._animation.setStartValue(sidebar.width())
        self._animation.setEndValue(self.collapsedWidth)
        self._animation.start()
        self.currentWidth = self.collapsedWidth
    
    # 切换模式
    def setMode(self, mode):
        if self._mode != mode:
            self._mode = mode
            self.modeChanged.emit(mode.value)
    
    # 获取当前模式
    def getMode(self):
        return self._mode

# 创建侧边栏项目类
class SidebarItem(QFrame):
    clicked = Signal()
    
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        self.setStyleSheet("""
            SidebarItem {
                background-color: transparent;
                border-radius: 6px;
                padding: 8px;
                margin: 2px 5px;
            }
            SidebarItem:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        self.titleLabel = QLabel(title)
        self.titleLabel.setStyleSheet("color: #e0e5ec; font-size: 14px;")
        layout.addWidget(self.titleLabel)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

# 创建侧边栏标签切换按钮
class SidebarTabButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #e0e5ec;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:checked {
                background-color: rgba(255, 255, 255, 0.15);
                font-weight: bold;
            }
        """)

# 创建项目列表页面
class ProjectListPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(2)
        
        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollArea.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: rgba(255, 255, 255, 0.05);
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(255, 255, 255, 0.2);
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        contentWidget = QWidget()
        contentLayout = QVBoxLayout(contentWidget)
        contentLayout.setContentsMargins(5, 5, 5, 5)
        contentLayout.setSpacing(2)
        
        # 添加演示项目
        demoProjects = ["个人笔记", "工作计划", "学习笔记", "旅行日记", "读书笔记"]
        for project in demoProjects:
            item = SidebarItem(project)
            contentLayout.addWidget(item)
        
        contentLayout.addStretch(1)  # 添加伸缩因子，使项目靠上对齐
        scrollArea.setWidget(contentWidget)
        layout.addWidget(scrollArea)

# 创建大纲页面
class OutlinePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 0)
        
        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollArea.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: rgba(255, 255, 255, 0.05);
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(255, 255, 255, 0.2);
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        contentWidget = QWidget()
        contentLayout = QVBoxLayout(contentWidget)
        contentLayout.setContentsMargins(0, 0, 0, 0)
        contentLayout.setSpacing(0)
        
        # 添加演示大纲项目
        outlineItems = ["第一章", "第二章", "第三章", "附录A", "附录B"]
        for item in outlineItems:
            outlineItem = SidebarItem(item)
            contentLayout.addWidget(outlineItem)
        
        contentLayout.addStretch(1)  # 添加伸缩因子，使项目靠上对齐
        scrollArea.setWidget(contentWidget)
        layout.addWidget(scrollArea) 