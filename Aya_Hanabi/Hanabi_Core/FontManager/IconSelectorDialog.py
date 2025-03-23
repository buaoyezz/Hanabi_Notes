import os
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QLineEdit, QScrollArea, QWidget,
                            QGridLayout, QSlider, QListWidget, QListWidgetItem,
                            QToolButton, QSizePolicy, QFrame)
from PySide6.QtGui import QFont, QColor, QIcon

from .fontManager import IconProvider, ICONS

class IconButton(QToolButton):
    def __init__(self, icon_name, icon_text, parent=None):
        super().__init__(parent)
        
        self.icon_name = icon_name
        self.icon_text = icon_text
        
        # 设置工具提示显示图标名称
        self.setToolTip(icon_name)
        
        # 获取图标字体
        font = IconProvider.get_icon_font(24)
        
        # 设置按钮样式
        self.setFont(font)
        self.setText(icon_text)
        self.setFixedSize(60, 60)
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.setStyleSheet("""
            QToolButton {
                border: 1px solid transparent;
                border-radius: 5px;
                padding: 6px;
                background: transparent;
                font-size: 24px;
            }
            
            QToolButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            QToolButton:pressed {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)

class IconSelectorDialog(QDialog):
    iconSelected = Signal(str, str)  # 图标名称、图标文本
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("图标选择器")
        self.setMinimumSize(800, 500)
        
        # 初始化图标字体
        IconProvider.init_font()
        
        # 获取所有图标名称列表
        self.icon_names = IconProvider.get_all_icon_names()
        
        # 搜索筛选后的图标列表
        self.filtered_icons = self.icon_names.copy()
        
        # 当前选中的图标
        self.selected_icon_name = ""
        self.selected_icon_text = ""
        
        # 初始化UI
        self.initUI()
        
    def initUI(self):
        # 主布局
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(20, 20, 20, 20)
        mainLayout.setSpacing(15)
        
        # 顶部搜索区域
        searchLayout = QHBoxLayout()
        
        searchLabel = QLabel("搜索图标:")
        self.searchEdit = QLineEdit()
        self.searchEdit.setPlaceholderText("输入图标名称关键字...")
        self.searchEdit.textChanged.connect(self.filterIcons)
        
        searchLayout.addWidget(searchLabel)
        searchLayout.addWidget(self.searchEdit, 1)
        
        # 添加图标大小滑块
        sizeLayout = QHBoxLayout()
        
        sizeLabel = QLabel("图标大小:")
        
        self.sizeSlider = QSlider(Qt.Horizontal)
        self.sizeSlider.setRange(16, 48)
        self.sizeSlider.setValue(24)
        self.sizeSlider.setTickPosition(QSlider.TicksBelow)
        self.sizeSlider.setTickInterval(8)
        self.sizeSlider.valueChanged.connect(self.updateIconSize)
        
        self.sizeValueLabel = QLabel("24px")
        
        sizeLayout.addWidget(sizeLabel)
        sizeLayout.addWidget(self.sizeSlider, 1)
        sizeLayout.addWidget(self.sizeValueLabel)
        
        # 常用图标区域
        commonIconsFrame = QFrame()
        commonIconsFrame.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        commonIconsLayout = QVBoxLayout(commonIconsFrame)
        
        commonTitleLabel = QLabel("常用图标")
        commonTitleLabel.setStyleSheet("font-weight: bold;")
        
        commonIconsGrid = QGridLayout()
        commonIconsGrid.setSpacing(5)
        
        # 添加常用图标
        common_icons = {k: v for k, v in ICONS.items()}
        col_count = 8
        
        row = 0
        col = 0
        
        for icon_name, icon_text in common_icons.items():
            iconBtn = IconButton(icon_name, icon_text, self)
            iconBtn.clicked.connect(lambda checked=False, n=icon_name, t=icon_text: self.selectIcon(n, t))
            
            commonIconsGrid.addWidget(iconBtn, row, col)
            
            col += 1
            if col >= col_count:
                col = 0
                row += 1
                
        commonIconsLayout.addWidget(commonTitleLabel)
        commonIconsLayout.addLayout(commonIconsGrid)
        
        # 所有图标区域
        self.allIconsScrollArea = QScrollArea()
        self.allIconsScrollArea.setWidgetResizable(True)
        self.allIconsScrollArea.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        
        # 创建图标网格
        self.createIconGrid()
        
        # 底部按钮区域
        buttonLayout = QHBoxLayout()
        
        self.selectedIconLabel = QLabel("未选择图标")
        
        cancelButton = QPushButton("取消")
        cancelButton.clicked.connect(self.reject)
        
        self.okButton = QPushButton("确定")
        self.okButton.clicked.connect(self.acceptIcon)
        self.okButton.setEnabled(False)
        
        buttonLayout.addWidget(self.selectedIconLabel, 1)
        buttonLayout.addWidget(cancelButton)
        buttonLayout.addWidget(self.okButton)
        
        # 添加所有组件到主布局
        mainLayout.addLayout(searchLayout)
        mainLayout.addLayout(sizeLayout)
        mainLayout.addWidget(commonIconsFrame)
        mainLayout.addWidget(self.allIconsScrollArea, 1)
        mainLayout.addLayout(buttonLayout)
        
    def createIconGrid(self):
        # 创建滚动区域的内容控件
        scrollWidget = QWidget()
        scrollLayout = QVBoxLayout(scrollWidget)
        
        allTitleLabel = QLabel("所有图标")
        allTitleLabel.setStyleSheet("font-weight: bold;")
        
        self.iconsGrid = QGridLayout()
        self.iconsGrid.setSpacing(5)
        
        # 添加所有图标
        col_count = 8
        
        scrollLayout.addWidget(allTitleLabel)
        scrollLayout.addLayout(self.iconsGrid)
        scrollLayout.addStretch(1)
        
        self.allIconsScrollArea.setWidget(scrollWidget)
        
        # 填充图标
        self.populateIcons()
        
    def populateIcons(self):
        # 先清除现有图标
        while self.iconsGrid.count():
            item = self.iconsGrid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 重新添加过滤后的图标
        col_count = 8
        row = 0
        col = 0
        
        for icon_name in self.filtered_icons:
            icon_text = IconProvider.get_icon(icon_name)
            
            iconBtn = IconButton(icon_name, icon_text, self)
            iconBtn.clicked.connect(lambda checked=False, n=icon_name, t=icon_text: self.selectIcon(n, t))
            
            self.iconsGrid.addWidget(iconBtn, row, col)
            
            col += 1
            if col >= col_count:
                col = 0
                row += 1
    
    def updateIconSize(self, size):
        # 更新图标大小
        self.sizeValueLabel.setText(f"{size}px")
        
        # 更新所有IconButton的样式
        for i in range(self.iconsGrid.count()):
            item = self.iconsGrid.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, IconButton):
                    font = IconProvider.get_icon_font(size)
                    widget.setFont(font)
        
    def filterIcons(self, text):
        # 根据输入文本过滤图标
        if not text:
            self.filtered_icons = self.icon_names.copy()
        else:
            self.filtered_icons = [name for name in self.icon_names if text.lower() in name.lower()]
            
        # 重新填充图标
        self.populateIcons()
        
    def selectIcon(self, icon_name, icon_text):
        # 保存选中的图标
        self.selected_icon_name = icon_name
        self.selected_icon_text = icon_text
        
        # 更新显示
        self.selectedIconLabel.setText(f"已选择: {icon_name}")
        
        # 设置图标预览
        icon_font = IconProvider.get_icon_font(24)
        self.selectedIconLabel.setFont(icon_font)
        
        # 启用确定按钮
        self.okButton.setEnabled(True)
        
    def acceptIcon(self):
        # 发出选中图标信号
        if self.selected_icon_name:
            self.iconSelected.emit(self.selected_icon_name, self.selected_icon_text)
            
        # 关闭对话框
        self.accept() 