from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QComboBox, 
                               QPushButton, QLabel, QTabWidget, QWidget, QColorDialog,
                               QScrollArea, QFormLayout, QGroupBox, QMessageBox, QLineEdit)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPalette

from .themeManager import ThemeManager, Theme

class ColorPickerButton(QPushButton):
    colorChanged = Signal(QColor)
    
    def __init__(self, color=None, parent=None):
        super().__init__(parent)
        self.color = color or QColor("#ffffff")
        self.setFixedSize(30, 20)
        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(self.showColorDialog)
        self.updateButtonColor()
        
    def updateButtonColor(self):
        self.setStyleSheet(f"""
            background-color: {self.color.name()};
            border: 1px solid #555555;
        """)
        
    def showColorDialog(self):
        color = QColorDialog.getColor(self.color, self, "选择颜色")
        if color.isValid():
            self.color = color
            self.updateButtonColor()
            self.colorChanged.emit(self.color)
            
    def setColor(self, color):
        if isinstance(color, str):
            self.color = QColor(color)
        else:
            self.color = color
        self.updateButtonColor()
        
    def getColor(self):
        return self.color.name()

class ThemeSettingsDialog(QDialog):
    themeChanged = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 尝试从父对象获取主题管理器
        if parent and hasattr(parent, 'themeManager'):
            self.themeManager = parent.themeManager
        else:
            # 如果父对象没有主题管理器，创建一个新的
            self.themeManager = ThemeManager()
            self.themeManager.load_themes_from_directory()
        
        self.setWindowTitle("主题设置")
        self.resize(600, 500)
        
        # 根据当前主题应用样式
        self.applyDialogStyle()
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(10)
        
        # 主题选择部分
        self.themeSelectLayout = QHBoxLayout()
        self.themeLabel = QLabel("当前主题:")
        self.themeComboBox = QComboBox()
        self.themeComboBox.setMinimumWidth(200)
        
        # 填充主题下拉框
        self.themes = self.themeManager.get_all_themes()
        for theme_name, display_name in self.themes:
            self.themeComboBox.addItem(display_name, theme_name)
            
        # 设置当前主题
        current_theme = self.themeManager.current_theme
        if current_theme:
            for i in range(self.themeComboBox.count()):
                if self.themeComboBox.itemData(i) == current_theme.name:
                    self.themeComboBox.setCurrentIndex(i)
                    break
                    
        self.themeComboBox.currentIndexChanged.connect(self.onThemeChanged)
        
        self.themeSelectLayout.addWidget(self.themeLabel)
        self.themeSelectLayout.addWidget(self.themeComboBox)
        self.themeSelectLayout.addStretch()
        
        self.layout.addLayout(self.themeSelectLayout)
        
        # 创建标签页
        self.tabWidget = QTabWidget()
        
        # 预览标签页
        self.previewTab = QWidget()
        self.previewLayout = QVBoxLayout(self.previewTab)
        self.previewLabel = QLabel("主题预览")
        self.previewLabel.setAlignment(Qt.AlignCenter)
        self.previewLayout.addWidget(self.previewLabel)
        
        # 创建预览控件
        self.previewWidget = ThemePreviewWidget()
        self.previewLayout.addWidget(self.previewWidget)
        
        # 自定义标签页
        self.customizeTab = QWidget()
        self.customizeLayout = QVBoxLayout(self.customizeTab)
        
        # 滚动区域
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setFrameShape(QScrollArea.NoFrame)
        
        self.customizeContent = QWidget()
        self.customizeScrollLayout = QVBoxLayout(self.customizeContent)
        self.customizeScrollLayout.setContentsMargins(0, 0, 10, 0)
        self.customizeScrollLayout.setSpacing(15)
        
        # 基础设置组
        self.baseGroupBox = QGroupBox("基础设置")
        self.baseLayout = QFormLayout(self.baseGroupBox)
        self.baseLayout.setContentsMargins(10, 15, 10, 10)
        self.baseLayout.setSpacing(10)
        
        self.newThemeNameEdit = QLineEdit()
        self.newThemeNameEdit.setPlaceholderText("输入自定义主题名称")
        self.baseLayout.addRow("新主题名称:", self.newThemeNameEdit)
        
        # 窗口设置组
        self.windowGroupBox = QGroupBox("窗口设置")
        self.windowLayout = QFormLayout(self.windowGroupBox)
        self.windowLayout.setContentsMargins(10, 15, 10, 10)
        self.windowLayout.setSpacing(10)
        
        self.windowBgButton = ColorPickerButton()
        self.windowBorderButton = ColorPickerButton()
        
        self.windowLayout.addRow("窗口背景:", self.windowBgButton)
        self.windowLayout.addRow("窗口边框:", self.windowBorderButton)
        
        # 编辑器设置组
        self.editorGroupBox = QGroupBox("编辑器设置")
        self.editorLayout = QFormLayout(self.editorGroupBox)
        self.editorLayout.setContentsMargins(10, 15, 10, 10)
        self.editorLayout.setSpacing(10)
        
        self.editorBgButton = ColorPickerButton()
        self.editorTextButton = ColorPickerButton()
        self.editorSelectionButton = ColorPickerButton()
        
        self.editorLayout.addRow("编辑器背景:", self.editorBgButton)
        self.editorLayout.addRow("文本颜色:", self.editorTextButton)
        self.editorLayout.addRow("选择颜色:", self.editorSelectionButton)
        
        # 状态栏设置组
        self.statusBarGroupBox = QGroupBox("状态栏设置")
        self.statusBarLayout = QFormLayout(self.statusBarGroupBox)
        self.statusBarLayout.setContentsMargins(10, 15, 10, 10)
        self.statusBarLayout.setSpacing(10)
        
        self.statusBarBgButton = ColorPickerButton()
        self.statusBarTextButton = ColorPickerButton()
        self.statusBarIconButton = ColorPickerButton()
        self.statusBarActiveIconButton = ColorPickerButton()
        
        self.statusBarLayout.addRow("状态栏背景:", self.statusBarBgButton)
        self.statusBarLayout.addRow("文本颜色:", self.statusBarTextButton)
        self.statusBarLayout.addRow("图标颜色:", self.statusBarIconButton)
        self.statusBarLayout.addRow("活动图标颜色:", self.statusBarActiveIconButton)
        
        # 添加所有设置组到滚动区域
        self.customizeScrollLayout.addWidget(self.baseGroupBox)
        self.customizeScrollLayout.addWidget(self.windowGroupBox)
        self.customizeScrollLayout.addWidget(self.editorGroupBox)
        self.customizeScrollLayout.addWidget(self.statusBarGroupBox)
        self.customizeScrollLayout.addStretch()
        
        self.scrollArea.setWidget(self.customizeContent)
        self.customizeLayout.addWidget(self.scrollArea)
        
        # 创建自定义主题按钮
        self.createCustomLayout = QHBoxLayout()
        self.createCustomLayout.setContentsMargins(0, 10, 0, 0)
        
        self.createThemeBtn = QPushButton("创建自定义主题")
        self.createThemeBtn.clicked.connect(self.createCustomTheme)
        self.createCustomLayout.addStretch()
        self.createCustomLayout.addWidget(self.createThemeBtn)
        
        self.customizeLayout.addLayout(self.createCustomLayout)
        
        # 添加标签页
        self.tabWidget.addTab(self.previewTab, "预览")
        self.tabWidget.addTab(self.customizeTab, "自定义")
        
        self.layout.addWidget(self.tabWidget)
        
        # 底部按钮
        self.buttonLayout = QHBoxLayout()
        self.applyButton = QPushButton("应用")
        self.applyButton.clicked.connect(self.applyTheme)
        self.closeButton = QPushButton("关闭")
        self.closeButton.clicked.connect(self.close)
        
        self.buttonLayout.addStretch()
        self.buttonLayout.addWidget(self.applyButton)
        self.buttonLayout.addWidget(self.closeButton)
        
        self.layout.addLayout(self.buttonLayout)
        
        # 更新颜色选择器的初始值
        self.updateColorButtons()
        
    def applyDialogStyle(self):
        """根据当前主题应用对话框样式"""
        bg_color = "#1e2128"
        text_color = "#e0e0e0"
        input_bg = "#252932"
        border_color = "#2a2e36"
        button_bg = "#3b4048"
        button_hover = "#494e5a"
        button_pressed = "#5a6175"
        button_disabled = "#31343a"
        disabled_text = "#777777"
        tab_bg = "#252932"
        tab_selected = "#303540"
        tab_hover = "#2a2e36"
        
        # 如果主题管理器可用并且有当前主题，使用它的颜色
        if hasattr(self, 'themeManager') and self.themeManager and self.themeManager.current_theme:
            theme = self.themeManager.current_theme
            bg_color = theme.get("window.background", bg_color)
            text_color = theme.get("editor.text_color", text_color)
            input_bg = theme.get("sidebar.background", input_bg)
            border_color = theme.get("window.border", border_color)
            # 可以添加更多主题颜色转换逻辑
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_color};
                color: {text_color};
                border: none;
                border-radius: 10px;
            }}
            QLabel {{
                color: {text_color};
            }}
            QComboBox {{
                background-color: {input_bg};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 4px;
                min-height: 25px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QPushButton {{
                background-color: {button_bg};
                color: {text_color};
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                min-height: 25px;
            }}
            QPushButton:hover {{
                background-color: {button_hover};
            }}
            QPushButton:pressed {{
                background-color: {button_pressed};
            }}
            QPushButton:disabled {{
                background-color: {button_disabled};
                color: {disabled_text};
            }}
            QTabWidget::pane {{
                border: 1px solid {border_color};
                background-color: {bg_color};
            }}
            QTabBar::tab {{
                background-color: {tab_bg};
                color: {text_color};
                padding: 8px 12px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {tab_selected};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {tab_hover};
            }}
            QGroupBox {{
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 15px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
            }}
            QLineEdit {{
                background-color: {input_bg};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 4px;
            }}
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 6px;
                margin: 0px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background-color: rgba(255, 255, 255, 0.3);
                min-height: 30px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: rgba(255, 255, 255, 0.5);
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
        
    def onThemeChanged(self, index):
        theme_name = self.themeComboBox.itemData(index)
        display_name = self.themeComboBox.currentText()
        print(f"----------主题切换开始----------")
        print(f"主题切换到: {theme_name} ({display_name})")
        
        # 设置自身主题管理器的当前主题
        success = self.themeManager.set_theme(theme_name)
        print(f"设置主题结果: {success}")
        if success and hasattr(self.themeManager, 'current_theme'):
            if hasattr(self.themeManager.current_theme, 'name'):
                print(f"当前主题名称: {self.themeManager.current_theme.name}")
        
        # 确保主题管理器有current_theme_name属性
        if hasattr(self.themeManager, 'current_theme_name'):
            print(f"主题管理器设置名称为: {self.themeManager.current_theme_name}")
        else:
            self.themeManager.current_theme_name = theme_name
            print(f"为主题管理器添加名称属性: {self.themeManager.current_theme_name}")
                
        self.updateColorButtons()
        self.updatePreview()
        
        # 发出主题变更信号
        print(f"发出themeChanged信号: {theme_name}")
        self.themeChanged.emit(theme_name)
        print(f"----------主题切换完成----------")
        
    def updateColorButtons(self):
        theme = self.themeManager.current_theme
        if not theme:
            return
            
        # 窗口设置
        self.windowBgButton.setColor(theme.get("window.background", "#1e2128"))
        self.windowBorderButton.setColor(theme.get("window.border", "#2a2e36"))
        
        # 编辑器设置
        self.editorBgButton.setColor(theme.get("editor.background", "#1e2128"))
        self.editorTextButton.setColor(theme.get("editor.text_color", "#e0e0e0"))
        self.editorSelectionButton.setColor(theme.get("editor.selection_color", "#404eff"))
        
        # 状态栏设置
        self.statusBarBgButton.setColor(theme.get("status_bar.background", "#1a1d23"))
        self.statusBarTextButton.setColor(theme.get("status_bar.text_color", "white"))
        self.statusBarIconButton.setColor(theme.get("status_bar.icon_color", "rgba(255, 255, 255, 0.7)"))
        self.statusBarActiveIconButton.setColor(theme.get("status_bar.active_icon_color", "#6b9fff"))
        
    def updatePreview(self):
        theme = self.themeManager.current_theme
        if theme:
            self.previewWidget.updatePreview(theme)
            
    def createCustomTheme(self):
        theme_name = self.newThemeNameEdit.text().strip()
        if not theme_name:
            QMessageBox.warning(self, "无效名称", "请输入有效的主题名称")
            return
            
        # 检查名称是否已存在
        if theme_name in [theme[0] for theme in self.themes]:
            QMessageBox.warning(self, "名称冲突", f"已存在名为 '{theme_name}' 的主题")
            return
            
        # 从当前主题创建自定义数据
        custom_data = {
            "display_name": theme_name,
            "window": {
                "background": self.windowBgButton.getColor(),
                "border": self.windowBorderButton.getColor()
            },
            "editor": {
                "background": self.editorBgButton.getColor(),
                "text_color": self.editorTextButton.getColor(),
                "selection_color": self.editorSelectionButton.getColor()
            },
            "status_bar": {
                "background": self.statusBarBgButton.getColor(),
                "text_color": self.statusBarTextButton.getColor(),
                "icon_color": self.statusBarIconButton.getColor(),
                "active_icon_color": self.statusBarActiveIconButton.getColor()
            }
        }
        
        # 基于当前主题创建新主题
        current_theme_name = self.themeComboBox.itemData(self.themeComboBox.currentIndex())
        new_theme = self.themeManager.create_custom_theme(current_theme_name, custom_data, theme_name)
        
        if new_theme:
            # 保存主题到文件
            self.themeManager.save_theme(new_theme)
            
            # 添加到下拉框
            self.themeComboBox.addItem(theme_name, theme_name)
            self.themes.append((theme_name, theme_name))
            
            # 选择新主题
            self.themeComboBox.setCurrentIndex(self.themeComboBox.count() - 1)
            
            QMessageBox.information(self, "成功", f"已创建新主题 '{theme_name}'")
        else:
            QMessageBox.warning(self, "错误", "创建主题失败")
            
    def applyTheme(self):
        """应用选中的主题"""
        print("点击了应用主题按钮")
        theme_index = self.themeComboBox.currentIndex()
        theme_name = self.themeComboBox.itemData(theme_index)
        print(f"要应用的主题: {theme_name}")
        
        # 设置主题管理器的当前主题
        success = self.themeManager.set_theme(theme_name)
        print(f"设置主题结果: {success}")
        
        # 确保主题管理器有current_theme_name属性
        if hasattr(self.themeManager, 'current_theme_name'):
            print(f"主题管理器当前主题名称: {self.themeManager.current_theme_name}")
        else:
            self.themeManager.current_theme_name = theme_name
            print(f"为主题管理器添加名称属性: {self.themeManager.current_theme_name}")
        
        # 发出主题变更信号
        print(f"发出themeChanged信号: {theme_name}")
        self.themeChanged.emit(theme_name)
        print("主题应用完成")

class ThemePreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(300)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建预览控件
        self.previewWindow = QWidget()
        self.previewWindow.setObjectName("previewWindow")
        self.previewWindow.setFixedHeight(280)
        
        self.previewLayout = QVBoxLayout(self.previewWindow)
        self.previewLayout.setContentsMargins(0, 0, 0, 0)
        self.previewLayout.setSpacing(0)
        
        # 标题栏预览
        self.titleBar = QWidget()
        self.titleBar.setObjectName("previewTitleBar")
        self.titleBar.setFixedHeight(40)
        
        titleBarLayout = QHBoxLayout(self.titleBar)
        titleBarLayout.setContentsMargins(10, 0, 10, 0)
        
        iconContainer = QWidget()
        iconContainer.setObjectName("previewIconContainer")
        iconContainer.setFixedSize(28, 28)
        
        iconLayout = QHBoxLayout(iconContainer)
        iconLayout.setContentsMargins(0, 0, 0, 0)
        
        iconLabel = QLabel("H")
        iconLabel.setObjectName("previewIconLabel")
        iconLabel.setAlignment(Qt.AlignCenter)
        iconLayout.addWidget(iconLabel)
        
        titleLabel = QLabel("Hanabi Notes")
        titleLabel.setObjectName("previewTitleLabel")
        
        titleBarLayout.addWidget(iconContainer)
        titleBarLayout.addWidget(titleLabel)
        titleBarLayout.addStretch()
        
        # 内容区预览
        contentArea = QWidget()
        contentArea.setObjectName("previewContentArea")
        
        contentLayout = QHBoxLayout(contentArea)
        contentLayout.setContentsMargins(10, 10, 10, 10)
        
        # 模拟编辑器
        editorArea = QWidget()
        editorArea.setObjectName("previewEditorArea")
        
        editorLabel = QLabel("# 标题\n\n这是一段示例文本，用于预览主题效果。\n\n* 项目 1\n* 项目 2\n\n```\n代码块\n```")
        editorLabel.setObjectName("previewEditor")
        editorLabel.setWordWrap(True)
        
        editorAreaLayout = QVBoxLayout(editorArea)
        editorAreaLayout.addWidget(editorLabel)
        
        contentLayout.addWidget(editorArea)
        
        # 状态栏预览
        statusBar = QWidget()
        statusBar.setObjectName("previewStatusBar")
        statusBar.setFixedHeight(36)
        
        statusBarLayout = QHBoxLayout(statusBar)
        statusBarLayout.setContentsMargins(10, 0, 10, 0)
        
        statusIconLabel = QLabel("⚙")
        statusIconLabel.setObjectName("previewStatusIcon")
        
        statusTextLabel = QLabel("5 行")
        statusTextLabel.setObjectName("previewStatusText")
        
        statusBarLayout.addWidget(statusIconLabel)
        statusBarLayout.addStretch()
        statusBarLayout.addWidget(statusTextLabel)
        
        # 添加所有部件到主布局
        self.previewLayout.addWidget(self.titleBar)
        self.previewLayout.addWidget(contentArea, 1)
        self.previewLayout.addWidget(statusBar)
        
        self.layout.addWidget(self.previewWindow)
        
    def updatePreview(self, theme):
        # 窗口样式
        windowBg = theme.get("window.background", "#1e2128")
        windowBorder = theme.get("window.border", "#2a2e36")
        windowRadius = theme.get("window.radius", "10px")
        
        self.previewWindow.setStyleSheet(f"""
            #previewWindow {{
                background-color: {windowBg};
                border: 1px solid {windowBorder};
                border-radius: {windowRadius};
            }}
        """)
        
        # 标题栏样式
        titleBarBg = theme.get("title_bar.background", "#1e2128")
        titleBarText = theme.get("title_bar.text_color", "white")
        titleBarIconBg = theme.get("title_bar.icon_bg", "#303540")
        titleBarIconColor = theme.get("title_bar.icon_color", "#6b9fff")
        
        self.titleBar.setStyleSheet(f"""
            #previewTitleBar {{
                background-color: {titleBarBg};
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }}
            #previewTitleLabel {{
                color: {titleBarText};
                font-size: 14px;
            }}
            #previewIconContainer {{
                background-color: {titleBarIconBg};
                border-radius: 14px;
            }}
            #previewIconLabel {{
                color: {titleBarIconColor};
                font-weight: bold;
                font-size: 16px;
            }}
        """)
        
        # 编辑器样式
        editorBg = theme.get("editor.background", "#1e2128")
        editorText = theme.get("editor.text_color", "#e0e0e0")
        
        editorStyle = f"""
            #previewEditorArea {{
                background-color: {editorBg};
            }}
            #previewEditor {{
                color: {editorText};
                font-family: monospace;
                font-size: 13px;
            }}
        """
        
        self.previewWindow.findChild(QWidget, "previewEditorArea").setStyleSheet(editorStyle)
        
        # 状态栏样式
        statusBarBg = theme.get("status_bar.background", "#1a1d23")
        statusBarText = theme.get("status_bar.text_color", "white")
        statusBarIcon = theme.get("status_bar.icon_color", "rgba(255, 255, 255, 0.7)")
        
        statusBarStyle = f"""
            #previewStatusBar {{
                background-color: {statusBarBg};
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }}
            #previewStatusText {{
                color: {statusBarText};
                font-size: 12px;
            }}
            #previewStatusIcon {{
                color: {statusBarIcon};
                font-size: 16px;
            }}
        """
        
        self.previewWindow.findChild(QWidget, "previewStatusBar").setStyleSheet(statusBarStyle) 