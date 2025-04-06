import os
import json
from PySide6.QtCore import Qt, Signal, QSize, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox, QTabWidget, QWidget,
                             QListWidget, QListWidgetItem, QScrollArea,
                             QGridLayout, QFrame, QSizePolicy, QSpacerItem,
                             QFileDialog, QMessageBox, QCheckBox, QGroupBox,
                             QFormLayout, QSpinBox, QLineEdit, QFontComboBox,
                             QColorDialog, QToolButton, QTextBrowser, QStackedWidget,
                             QMenu)
from PySide6.QtGui import QFont, QIcon, QPixmap, QImage, QColor, QFocusEvent
from Aya_Hanabi.Hanabi_Core.UI.messageBox import HanabiMessageBox, information, warning, critical, question, success
from Aya_Hanabi.Hanabi_Core.UI.HanabiDialog import HanabiDialog
from Aya_Hanabi.Hanabi_Core.FontManager.fontManager import FontManager, IconProvider

# 自定义无焦点组件基类
class NoFocusWidget:
    def focusInEvent(self, event):
        self.clearFocus()
        event.ignore()
        
    def setNoFocus(self):
        self.setFocusPolicy(Qt.NoFocus)

# 基本设置对话框
class SettingsDialog(QDialog):
    settingsChanged = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("设置")
        self.setMinimumSize(800, 500)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self.setFocusPolicy(Qt.NoFocus)
        
        # 获取主题颜色设置
        self.theme_colors = self.get_theme_colors(parent)
        
        # 初始化设置
        self.settings = {
            "general": {
                "startup": {
                    "auto_start": False,
                    "remember_window": True,
                    "reopen_files": True
                },
                "file": {
                    "default_save_path": os.path.join(os.path.expanduser("~"), "Documents", "HanabiNotes"),
                    "auto_save": True,
                    "auto_save_interval": 5
                },
                "other": {
                    "show_status_bar": True,
                    "enable_sound_effects": False
                }
            },
            "editor": {
                "font": {
                    "family": "Consolas",
                    "size": 15
                },
                "editing": {
                    "auto_indent": True,
                    "line_numbers": True,
                    "spell_check": False,
                    "word_wrap": True
                }
            }
        }
        
        # 加载现有设置
        self.loadSettings()
        
        self.initUI()
        
    def get_theme_colors(self, parent):
        colors = {
            "primary": "#8B5CF6",
            "text": "#333333",
            "background": "#FFFFFF",
            "border": "#E5E7EB",
            "hover": "rgba(0, 0, 0, 0.05)",
            "is_dark": False,
            "font_family": "Microsoft YaHei"
        }
        
        if parent and hasattr(parent, 'themeManager') and parent.themeManager:
            theme_manager = parent.themeManager
            theme = getattr(theme_manager, 'current_theme', {})
            
            is_dark = False
            if hasattr(theme_manager, 'current_theme_name'):
                is_dark = theme_manager.current_theme_name in ["dark", "purple_dream", "green_theme"]
            
            colors["is_dark"] = is_dark
            
            if is_dark:
                colors["primary"] = theme.get("accent_color", "#8B5CF6")
                colors["text"] = theme.get("editor.text_color", "#E0E0E0")
                colors["background"] = theme.get("window.background", "#1E2128")
                colors["border"] = theme.get("window.border", "#333842")
                colors["hover"] = "rgba(255, 255, 255, 0.05)"
            else:
                colors["primary"] = theme.get("accent_color", "#6B9FFF")
                colors["text"] = theme.get("editor.text_color", "#333333")
                colors["background"] = theme.get("window.background", "#FFFFFF")
                colors["border"] = theme.get("window.border", "#E5E7EB")
                colors["hover"] = "rgba(0, 0, 0, 0.05)"
                
            if hasattr(parent, 'font_family'):
                colors["font_family"] = parent.font_family
        
        else:
            try:
                settings_dir = os.path.join(os.path.expanduser("~"), ".hanabi_notes")
                settings_file = os.path.join(settings_dir, "settings.json")
                
                if os.path.exists(settings_file):
                    with open(settings_file, 'r', encoding='utf-8') as f:
                        settings = json.load(f)
                    
                    theme_name = settings.get("appearance", {}).get("theme", "light")
                    colors["is_dark"] = theme_name in ["dark", "purple_dream", "green_theme"]
                    
                    if colors["is_dark"]:
                        colors["primary"] = "#8B5CF6"
                        colors["text"] = "#E0E0E0"
                        colors["background"] = "#1E2128"
                        colors["border"] = "#333842"
                        colors["hover"] = "rgba(255, 255, 255, 0.05)"
                        
                    if "editor" in settings and "font" in settings["editor"]:
                        font_settings = settings["editor"]["font"]
                        if "family" in font_settings:
                            colors["font_family"] = font_settings["family"]
            except Exception as e:
                print(f"读取主题设置时出错: {e}")
        
        return colors
        
    def initUI(self):
        # 创建基本UI框架
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(10, 10, 10, 10)
        
        # 内容区域
        contentWidget = QWidget()
        contentLayout = QHBoxLayout(contentWidget)
        
        # 左侧导航栏
        navWidget = QWidget()
        navWidget.setFixedWidth(160)
        navLayout = QVBoxLayout(navWidget)
        navLayout.setContentsMargins(0, 0, 10, 0)
        
        # 导航列表
        self.navListWidget = QListWidget()
        self.navListWidget.setFrameShape(QFrame.NoFrame)
        
        # 添加导航项
        self.navListWidget.addItem("常规设置")
        self.navListWidget.addItem("编辑器")
        self.navListWidget.addItem("外观")
        self.navListWidget.addItem("关于")
        
        navLayout.addWidget(self.navListWidget)
        
        # 右侧内容区域
        rightWidget = QWidget()
        rightLayout = QVBoxLayout(rightWidget)
        rightLayout.setContentsMargins(10, 0, 0, 0)
        
        # 内容堆栈
        self.contentStack = QTabWidget()
        self.contentStack.tabBar().setVisible(False)
        
        # 添加内容页面
        self.generalPage = QWidget()
        self.editorPage = QWidget()
        self.appearancePage = QWidget()
        self.aboutPage = QWidget()
        
        # 设置各页面内容
        self.setupGeneralPage()
        self.setupEditorPage()
        self.setupAppearancePage()
        self.setupAboutPage()
        
        self.contentStack.addTab(self.generalPage, "常规设置")
        self.contentStack.addTab(self.editorPage, "编辑器")
        self.contentStack.addTab(self.appearancePage, "外观")
        self.contentStack.addTab(self.aboutPage, "关于")
        
        rightLayout.addWidget(self.contentStack)
        
        # 底部按钮
        buttonWidget = QWidget()
        buttonLayout = QHBoxLayout(buttonWidget)
        buttonLayout.setContentsMargins(0, 10, 0, 0)
        
        self.cancelButton = QPushButton("取消")
        self.cancelButton.setDefault(False)
        self.cancelButton.setAutoDefault(False)
        self.cancelButton.setFixedWidth(100)
        
        self.saveButton = QPushButton("保存")
        self.saveButton.setDefault(True)
        self.saveButton.setAutoDefault(True)
        self.saveButton.setFixedWidth(100)
        
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.cancelButton)
        buttonLayout.addWidget(self.saveButton)
        
        rightLayout.addWidget(buttonWidget)
        
        contentLayout.addWidget(navWidget)
        contentLayout.addWidget(rightWidget)
        
        mainLayout.addWidget(contentWidget, 1)
        
        # 连接信号
        self.navListWidget.currentRowChanged.connect(self.contentStack.setCurrentIndex)
        self.saveButton.clicked.connect(self.saveSettings)
        self.cancelButton.clicked.connect(self.reject)
        
        # 默认选中第一项
        self.navListWidget.setCurrentRow(0)
        
        # 应用样式
        self.applyStyle()
    
    def setupGeneralPage(self):
        """设置'常规设置'页面的内容"""
        layout = QVBoxLayout(self.generalPage)
        
        # 启动组
        startupGroup = QGroupBox("启动选项")
        startupLayout = QVBoxLayout(startupGroup)
        
        self.autoStartCheckbox = QCheckBox("系统启动时自动运行")
        self.rememberWindowCheckbox = QCheckBox("记住窗口位置和大小")
        self.reopenFilesCheckbox = QCheckBox("重新打开上次的文件")
        
        # 加载设置值
        self.autoStartCheckbox.setChecked(self.settings["general"]["startup"]["auto_start"])
        self.rememberWindowCheckbox.setChecked(self.settings["general"]["startup"]["remember_window"])
        self.reopenFilesCheckbox.setChecked(self.settings["general"]["startup"]["reopen_files"])
        
        startupLayout.addWidget(self.autoStartCheckbox)
        startupLayout.addWidget(self.rememberWindowCheckbox)
        startupLayout.addWidget(self.reopenFilesCheckbox)
        
        # 文件组
        fileGroup = QGroupBox("文件选项")
        fileLayout = QFormLayout(fileGroup)
        
        self.defaultSavePathEdit = QLineEdit()
        self.defaultSavePathEdit.setText(self.settings["general"]["file"]["default_save_path"])
        self.defaultSavePathEdit.setReadOnly(True)
        
        browseSavePathBtn = QPushButton("浏览...")
        browseSavePathBtn.clicked.connect(self.browseSavePath)
        
        savePathLayout = QHBoxLayout()
        savePathLayout.addWidget(self.defaultSavePathEdit)
        savePathLayout.addWidget(browseSavePathBtn)
        
        self.autoSaveCheckbox = QCheckBox("启用")
        self.autoSaveCheckbox.setChecked(self.settings["general"]["file"]["auto_save"])
        
        self.autoSaveIntervalSpinBox = QSpinBox()
        self.autoSaveIntervalSpinBox.setMinimum(1)
        self.autoSaveIntervalSpinBox.setMaximum(60)
        self.autoSaveIntervalSpinBox.setValue(self.settings["general"]["file"]["auto_save_interval"])
        self.autoSaveIntervalSpinBox.setSuffix(" 分钟")
        
        autoSaveLayout = QHBoxLayout()
        autoSaveLayout.addWidget(self.autoSaveCheckbox)
        autoSaveLayout.addWidget(self.autoSaveIntervalSpinBox)
        autoSaveLayout.addStretch(1)
        
        fileLayout.addRow("默认保存位置:", savePathLayout)
        fileLayout.addRow("自动保存:", autoSaveLayout)
        
        # 其他选项组
        otherGroup = QGroupBox("其他选项")
        otherLayout = QVBoxLayout(otherGroup)
        
        self.showStatusBarCheckbox = QCheckBox("显示状态栏")
        self.showStatusBarCheckbox.setChecked(self.settings["general"]["other"]["show_status_bar"])
        
        self.enableSoundEffectsCheckbox = QCheckBox("启用声音效果")
        self.enableSoundEffectsCheckbox.setChecked(self.settings["general"]["other"]["enable_sound_effects"])
        
        otherLayout.addWidget(self.showStatusBarCheckbox)
        otherLayout.addWidget(self.enableSoundEffectsCheckbox)
        
        # 添加所有组到主布局
        layout.addWidget(startupGroup)
        layout.addWidget(fileGroup)
        layout.addWidget(otherGroup)
        layout.addStretch(1)
    
    def setupEditorPage(self):
        """设置'编辑器'页面的内容"""
        layout = QVBoxLayout(self.editorPage)
        
        # 字体和大小组
        fontGroup = QGroupBox("字体设置")
        fontLayout = QFormLayout(fontGroup)
        
        # 字体选择器
        self.fontComboBox = QFontComboBox()
        self.fontComboBox.setCurrentFont(QFont(self.settings["editor"]["font"]["family"]))
        
        # 字体大小选择器
        self.fontSizeSpinBox = QSpinBox()
        self.fontSizeSpinBox.setMinimum(8)
        self.fontSizeSpinBox.setMaximum(72)
        self.fontSizeSpinBox.setValue(self.settings["editor"]["font"]["size"])
        
        fontLayout.addRow("字体:", self.fontComboBox)
        fontLayout.addRow("大小:", self.fontSizeSpinBox)
        
        # 编辑选项组
        editingGroup = QGroupBox("编辑选项")
        editingLayout = QVBoxLayout(editingGroup)
        
        self.autoIndentCheckbox = QCheckBox("自动缩进")
        self.autoIndentCheckbox.setChecked(self.settings["editor"]["editing"]["auto_indent"])
        
        self.lineNumbersCheckbox = QCheckBox("显示行号")
        self.lineNumbersCheckbox.setChecked(self.settings["editor"]["editing"]["line_numbers"])
        
        self.spellCheckCheckbox = QCheckBox("拼写检查")
        self.spellCheckCheckbox.setChecked(self.settings["editor"]["editing"]["spell_check"])
        
        self.wordWrapCheckbox = QCheckBox("自动换行")
        self.wordWrapCheckbox.setChecked(self.settings["editor"]["editing"]["word_wrap"])
        
        editingLayout.addWidget(self.autoIndentCheckbox)
        editingLayout.addWidget(self.lineNumbersCheckbox)
        editingLayout.addWidget(self.spellCheckCheckbox)
        editingLayout.addWidget(self.wordWrapCheckbox)
        
        # 添加所有组到主布局
        layout.addWidget(fontGroup)
        layout.addWidget(editingGroup)
        layout.addStretch(1)
    
    def setupAppearancePage(self):
        """设置'外观'页面的内容"""
        layout = QVBoxLayout(self.appearancePage)
        
        # 主题选择按钮
        themeLabel = QLabel("主题设置")
        themeLabel.setFont(QFont("", 12, QFont.Bold))
        
        themeButton = QPushButton("打开主题设置")
        themeButton.clicked.connect(self.openThemeSettings)
        
        themeLayout = QVBoxLayout()
        themeLayout.addWidget(themeLabel)
        themeLayout.addWidget(themeButton)
        
        # 添加到主布局
        layout.addLayout(themeLayout)
        layout.addStretch(1)
    
    def setupAboutPage(self):
        """设置'关于'页面的内容"""
        layout = QVBoxLayout(self.aboutPage)
        
        # 应用标题
        titleLabel = QLabel("Hanabi Notes")
        titleLabel.setFont(QFont("", 18, QFont.Bold))
        titleLabel.setAlignment(Qt.AlignCenter)
        
        # 版本信息
        versionLabel = QLabel("版本: 1.0.0")
        versionLabel.setAlignment(Qt.AlignCenter)
        
        # 著作权信息
        copyrightLabel = QLabel("© 2023-2025 Hanabi Notes Team. 保留所有权利。")
        copyrightLabel.setAlignment(Qt.AlignCenter)
        
        # 描述
        descriptionText = QTextBrowser()
        descriptionText.setReadOnly(True)
        descriptionText.setOpenExternalLinks(True)
        descriptionText.setHtml("""
            <div style="text-align: center;">
                <p>Hanabi Notes 是一个简洁、美观、功能强大的笔记应用。</p>
                <p>支持多种格式的笔记，包括文本、Markdown、代码等。</p>
                <p>项目主页: <a href="https://github.com/username/hanabi-notes">https://github.com/username/hanabi-notes</a></p>
            </div>
        """)
        
        # 添加到主布局
        layout.addWidget(titleLabel)
        layout.addWidget(versionLabel)
        layout.addWidget(copyrightLabel)
        layout.addWidget(descriptionText)
        
    def browseSavePath(self):
        """浏览默认保存路径"""
        current_path = self.defaultSavePathEdit.text()
        if not current_path:
            current_path = os.path.expanduser("~")
            
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择默认保存目录", current_path,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if dir_path:
            self.defaultSavePathEdit.setText(dir_path)
    
    def openThemeSettings(self):
        """打开主题设置对话框"""
        try:
            parent = self.parent()
            if parent and hasattr(parent, 'showThemeSettings'):
                parent.showThemeSettings()
            else:
                theme_dialog = ThemeSettingsDialog(self)
                theme_dialog.exec()
        except Exception as e:
            print(f"打开主题设置对话框时出错: {e}")
    
    def loadSettings(self):
        """从配置文件加载设置"""
        try:
            settings_dir = os.path.join(os.path.expanduser("~"), ".hanabi_notes")
            settings_file = os.path.join(settings_dir, "settings.json")
            
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    saved_settings = json.load(f)
                
                # 更新设置
                if "general" in saved_settings:
                    self.updateSettingDict(self.settings["general"], saved_settings["general"])
                
                if "editor" in saved_settings:
                    self.updateSettingDict(self.settings["editor"], saved_settings["editor"])
        except Exception as e:
            print(f"加载设置时出错: {e}")
    
    def updateSettingDict(self, target, source):
        """递归更新设置字典"""
        for key, value in source.items():
            if key in target:
                if isinstance(value, dict) and isinstance(target[key], dict):
                    self.updateSettingDict(target[key], value)
                else:
                    target[key] = value
    
    def updateSetting(self, path, value):
        """更新单个设置值"""
        target = self.settings
        for p in path[:-1]:
            if p not in target:
                target[p] = {}
            target = target[p]
        
        target[path[-1]] = value
    
    def applyStyle(self):
        """应用样式到设置对话框"""
        # 应用基本样式
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
            }
            
            QListWidget {
                background-color: #F3F4F6;
                border: none;
                border-radius: 4px;
                color: #333333;
                font-size: 14px;
                padding: 5px;
            }
            
            QListWidget::item {
                padding: 8px 12px;
                border-radius: 4px;
            }
            
            QListWidget::item:selected {
                background-color: #6B9FFF;
                color: white;
            }
            
            QListWidget::item:hover:!selected {
                background-color: rgba(0, 0, 0, 0.05);
            }
            
            QPushButton {
                background-color: #6B9FFF;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background-color: #5A8AE8;
            }
            
            QPushButton:pressed {
                background-color: #4B7BD7;
            }
        """)
    
    def saveSettings(self):
        """保存设置到配置文件"""
        try:
            settings_dir = os.path.join(os.path.expanduser("~"), ".hanabi_notes")
            os.makedirs(settings_dir, exist_ok=True)
            settings_file = os.path.join(settings_dir, "settings.json")
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
            
            # 发送设置变更信号
            self.settingsChanged.emit()
            
            # 关闭对话框
            self.accept()
        except Exception as e:
            print(f"保存设置时出错: {e}")
            QMessageBox.warning(self, "错误", f"保存设置时出错: {str(e)}")

# 主题设置对话框
class ThemeSettingsDialog(QDialog):
    themeChanged = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("主题设置")
        self.setFixedSize(600, 400)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        
        # 读取当前主题
        self.current_theme = "light"
        if parent and hasattr(parent, "themeManager"):
            theme_manager = parent.themeManager
            if hasattr(theme_manager, "current_theme_name"):
                self.current_theme = theme_manager.current_theme_name
        
        self.initUI()
    
    def initUI(self):
        # 创建布局
        mainLayout = QVBoxLayout(self)
        
        # 标题
        titleLabel = QLabel("选择主题")
        titleLabel.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        mainLayout.addWidget(titleLabel)
        
        # 主题预览区域
        themesLayout = QGridLayout()
        themesLayout.setSpacing(20)
        
        # 添加主题选项
        self.addThemeOption(themesLayout, 0, 0, "light", "浅色主题", "#FFFFFF", "#333333")
        self.addThemeOption(themesLayout, 0, 1, "dark", "深色主题", "#1E2128", "#E0E0E0")
        self.addThemeOption(themesLayout, 1, 0, "purple_dream", "紫梦主题", "#2D1B69", "#E9E0FF")
        self.addThemeOption(themesLayout, 1, 1, "green_theme", "青葱主题", "#1D3B2A", "#D0E6C7")
        
        mainLayout.addLayout(themesLayout)
        
        # 底部按钮
        buttonLayout = QHBoxLayout()
        
        self.cancelButton = QPushButton("取消")
        self.cancelButton.clicked.connect(self.reject)
        
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.cancelButton)
        
        mainLayout.addStretch()
        mainLayout.addLayout(buttonLayout)
    
    def addThemeOption(self, layout, row, col, theme_id, theme_name, bg_color, text_color):
        # 创建主题预览框
        themeWidget = QWidget()
        themeWidget.setObjectName(f"theme_{theme_id}")
        themeWidget.setFixedSize(200, 120)
        themeWidget.setCursor(Qt.PointingHandCursor)
        
        # 设置样式
        is_selected = self.current_theme == theme_id
        border_color = "#6B9FFF" if is_selected else "transparent"
        
        themeWidget.setStyleSheet(f"""
            QWidget#theme_{theme_id} {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 8px;
            }}
        """)
        
        # 布局
        themeLayout = QVBoxLayout(themeWidget)
        
        # 主题名称
        nameLabel = QLabel(theme_name)
        nameLabel.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        nameLabel.setStyleSheet(f"color: {text_color};")
        nameLabel.setAlignment(Qt.AlignCenter)
        themeLayout.addWidget(nameLabel)
        
        # 选择指示器
        if is_selected:
            selectedLabel = QLabel("✓ 当前选择")
            selectedLabel.setFont(QFont("Microsoft YaHei", 10))
            selectedLabel.setStyleSheet(f"color: {text_color};")
            selectedLabel.setAlignment(Qt.AlignCenter)
            themeLayout.addWidget(selectedLabel)
        
        # 绑定点击事件
        themeWidget.mouseReleaseEvent = lambda event, t=theme_id: self.selectTheme(t)
        
        layout.addWidget(themeWidget, row, col)
    
    def selectTheme(self, theme_id):
        """选择主题"""
        self.themeChanged.emit(theme_id)
        self.accept()

# 使用HanabiDialog的新设计设置对话框
class HanabiSettingsDialog(HanabiDialog):
    settingsChanged = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent, title="设置中心", width=800, height=550)
        
        # 初始化设置
        self.settings = {
            "general": {
                "startup": {
                    "auto_start": False,
                    "remember_window": True,
                    "reopen_files": True
                },
                "file": {
                    "default_save_path": os.path.join(os.path.expanduser("~"), "Documents", "HanabiNotes"),
                    "auto_save": True,
                    "auto_save_interval": 5
                },
                "other": {
                    "show_status_bar": True,
                    "enable_sound_effects": False
                }
            },
            "editor": {
                "font": {
                    "family": "Consolas",
                    "size": 15
                },
                "editing": {
                    "auto_indent": True,
                    "line_numbers": True,
                    "spell_check": False,
                    "word_wrap": True
                }
            }
        }
        
        # 加载现有设置
        self.loadSettings()
        
        # 初始化界面
        self.initUI()
    
    def initUI(self):
        # 快速实现一个基本的设置对话框
        # 更详细的实现将在后续完成
        
        # 获取主题颜色
        text_color = self.theme_colors["text"]
        primary_color = self.theme_colors["primary"]
        bg_color = self.theme_colors["background"]
        border_color = self.theme_colors["border"]
        hover_color = self.theme_colors["hover"]
        font_family = self.theme_colors["font_family"]
        is_dark = self.theme_colors["is_dark"]
        
        # 创建主布局和内容
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(20)
        
        # 左侧导航栏
        nav_widget = QWidget()
        nav_widget.setObjectName("navWidget")
        nav_widget.setFixedWidth(200)
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(15, 15, 15, 15)
        nav_layout.setSpacing(8)
        
        # 添加标志和标题
        logo_label = QLabel(IconProvider.get_icon("settings"))
        logo_label.setFont(IconProvider.get_icon_font(28))
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet(f"color: {primary_color};")
        
        title_label = QLabel("设置中心")
        title_label.setFont(FontManager.get_font(font_family, 16, bold=True))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"color: {text_color};")
        
        # 导航列表
        self.navListWidget = QListWidget()
        self.navListWidget.setFrameShape(QFrame.NoFrame)
        self.navListWidget.setStyleSheet(f"""
            QListWidget {{
                background-color: {QColor(bg_color).darker(110).name() if is_dark else QColor(bg_color).lighter(90).name()};
                border: none;
                border-radius: 10px;
                color: {text_color};
                padding: 8px;
            }}
            QListWidget::item {{
                padding: 14px 12px;
                border-radius: 8px;
                margin-bottom: 4px;
            }}
            QListWidget::item:selected {{
                background-color: {primary_color};
                color: white;
            }}
            QListWidget::item:hover:!selected {{
                background-color: {hover_color};
            }}
        """)
        
        # 图标字体
        icon_font = IconProvider.get_icon_font(16)
        
        # 添加导航项
        generalItem = QListWidgetItem(IconProvider.get_icon("home") + " 常规设置")
        generalItem.setFont(icon_font)
        self.navListWidget.addItem(generalItem)
        
        editorItem = QListWidgetItem(IconProvider.get_icon("edit") + " 编辑器")
        editorItem.setFont(icon_font)
        self.navListWidget.addItem(editorItem)
        
        appearanceItem = QListWidgetItem(IconProvider.get_icon("palette") + " 外观")
        appearanceItem.setFont(icon_font)
        self.navListWidget.addItem(appearanceItem)
        
        aboutItem = QListWidgetItem(IconProvider.get_icon("info") + " 关于")
        aboutItem.setFont(icon_font)
        self.navListWidget.addItem(aboutItem)
        
        # 添加到导航布局
        nav_layout.addWidget(logo_label)
        nav_layout.addWidget(title_label)
        nav_layout.addSpacing(20)
        nav_layout.addWidget(self.navListWidget, 1)
        
        # 版本标签
        version_label = QLabel("花火笔记 v1.0.0")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet(f"color: {QColor(text_color).lighter(130).name() if is_dark else QColor(text_color).darker(130).name()};")
        nav_layout.addWidget(version_label)
        
        # 右侧内容区
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # 内容堆栈
        self.contentStack = QTabWidget()
        self.contentStack.tabBar().setVisible(False)
        self.contentStack.setStyleSheet("border: none;")
        
        # 添加页面
        self.generalPage = QWidget()
        self.editorPage = QWidget()
        self.appearancePage = QWidget()
        self.aboutPage = QWidget()
        
        # 简单内容（后续将增强）
        generalLayout = QVBoxLayout(self.generalPage)
        generalLayout.addWidget(QLabel("常规设置页面"))
        
        editorLayout = QVBoxLayout(self.editorPage)
        editorLayout.addWidget(QLabel("编辑器设置页面"))
        
        appearanceLayout = QVBoxLayout(self.appearancePage)
        appearanceLayout.addWidget(QLabel("外观设置页面"))
        
        aboutLayout = QVBoxLayout(self.aboutPage)
        aboutLayout.addWidget(QLabel("关于页面"))
        
        # 添加到堆栈
        self.contentStack.addTab(self.generalPage, "常规设置")
        self.contentStack.addTab(self.editorPage, "编辑器")
        self.contentStack.addTab(self.appearancePage, "外观")
        self.contentStack.addTab(self.aboutPage, "关于")
        
        content_layout.addWidget(self.contentStack)
        
        # 添加到主布局
        main_layout.addWidget(nav_widget)
        main_layout.addWidget(content_widget, 1)
        
        # 添加到对话框
        self.content_layout.addWidget(main_widget)
        
        # 添加底部按钮
        self.add_cancel_button("取消", "close")
        self.add_ok_button("保存设置", "save")
        
        # 连接信号
        self.navListWidget.currentRowChanged.connect(self.contentStack.setCurrentIndex)
        self.ok_button.clicked.connect(self.saveSettings)
        
        # 默认选中第一项
        self.navListWidget.setCurrentRow(0)
    
    def loadSettings(self):
        """从配置文件加载设置"""
        try:
            settings_dir = os.path.join(os.path.expanduser("~"), ".hanabi_notes")
            settings_file = os.path.join(settings_dir, "settings.json")
            
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    saved_settings = json.load(f)
                
                # 更新设置
                if "general" in saved_settings:
                    self.updateSettingDict(self.settings["general"], saved_settings["general"])
                
                if "editor" in saved_settings:
                    self.updateSettingDict(self.settings["editor"], saved_settings["editor"])
        except Exception as e:
            print(f"加载设置时出错: {e}")
    
    def updateSettingDict(self, target, source):
        """递归更新设置字典"""
        for key, value in source.items():
            if key in target:
                if isinstance(value, dict) and isinstance(target[key], dict):
                    self.updateSettingDict(target[key], value)
                else:
                    target[key] = value
    
    def updateSetting(self, path, value):
        """更新单个设置值"""
        target = self.settings
        for p in path[:-1]:
            if p not in target:
                target[p] = {}
            target = target[p]
        
        target[path[-1]] = value
    
    def saveSettings(self):
        """保存设置到配置文件"""
        try:
            settings_dir = os.path.join(os.path.expanduser("~"), ".hanabi_notes")
            os.makedirs(settings_dir, exist_ok=True)
            settings_file = os.path.join(settings_dir, "settings.json")
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
            
            # 发送设置变更信号
            self.settingsChanged.emit()
            
            # 设置结果并关闭对话框
            self.result_value = self.Ok_Result
            self.accept()
        except Exception as e:
            print(f"保存设置时出错: {e}")
            warning(self, "错误", f"保存设置时出错: {str(e)}")

# 应用程序测试代码
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    
    app = QApplication([])
    
    # 初始化字体管理器和图标
    FontManager.init()
    IconProvider.init_font()
    
    # 优先使用新的设置对话框
    try:
        settingsDialog = HanabiSettingsDialog()
        result = settingsDialog.exec()
        
        if result == HanabiDialog.Ok_Result:
            print("设置已保存")
        else:
            print("设置已取消")
    except Exception as e:
        # 回退到使用传统的设置对话框
        print(f"使用新对话框失败，回退到传统对话框: {e}")
        settingsDialog = SettingsDialog()
        if settingsDialog.exec():
            print("设置已保存")
        else:
            print("设置已取消")
    
    app.exec() 

class HanabiPluginsPanel(QWidget):
    """插件管理面板"""
    
    # 信号
    pluginsChanged = Signal()  # 插件变更时发出信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.plugin_manager = None
        self.plugins = []
        self.initUI()
        
        # 获取父窗口的插件管理器
        self.setupPluginManager()
        
        # 加载插件列表
        self.loadPlugins()
    
    def setupPluginManager(self):
        try:
            # 尝试获取插件管理器
            if self.parent and hasattr(self.parent, 'plugin_manager'):
                self.plugin_manager = self.parent.plugin_manager
                print("使用父窗口的插件管理器")
            elif self.parent and hasattr(self.parent, 'parent') and hasattr(self.parent.parent, 'plugin_manager'):
                self.plugin_manager = self.parent.parent.plugin_manager
                print("使用父窗口的父窗口的插件管理器")
            else:
                # 尝试导入插件管理器
                try:
                    from Aya_Hanabi.Hanabi_Core.PluginManager.pluginManager import PluginManager
                    self.plugin_manager = PluginManager()
                    print("创建新的插件管理器")
                except ImportError:
                    print("无法导入PluginManager，将禁用插件功能")
        except Exception as e:
            print(f"设置插件管理器时出错: {e}")
    
    def initUI(self):
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(15)
        
        # 创建顶部工具栏
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.setIcon(IconProvider.get_icon("refresh"))
        refresh_btn.clicked.connect(self.refreshPlugins)
        toolbar_layout.addWidget(refresh_btn)
        
        # 添加插件按钮
        add_btn = QPushButton("添加插件")
        add_btn.setIcon(IconProvider.get_icon("add"))
        add_btn.clicked.connect(self.addPlugin)
        toolbar_layout.addWidget(add_btn)
        
        toolbar_layout.addStretch(1)
        
        # 创建分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: rgba(255, 255, 255, 0.1);")
        
        # 创建插件列表区域
        plugins_widget = QWidget()
        plugins_layout = QVBoxLayout(plugins_widget)
        plugins_layout.setContentsMargins(0, 0, 0, 0)
        plugins_layout.setSpacing(0)
        
        # 创建列表和详情的水平布局
        split_layout = QHBoxLayout()
        split_layout.setContentsMargins(0, 0, 0, 0)
        split_layout.setSpacing(10)
        
        # 创建插件列表
        self.plugins_list = QListWidget()
        self.plugins_list.setFrameShape(QFrame.NoFrame)
        self.plugins_list.setIconSize(QSize(32, 32))
        self.plugins_list.setMinimumWidth(220)
        self.plugins_list.setMaximumWidth(280)
        self.plugins_list.currentRowChanged.connect(self.onPluginSelected)
        split_layout.addWidget(self.plugins_list, 1)
        
        # 创建详情区域
        details_container = QWidget()
        details_layout = QVBoxLayout(details_container)
        details_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建详情堆栈，用于显示插件详情或空状态
        self.details_stack = QStackedWidget()
        
        # 空状态页面
        empty_page = QWidget()
        empty_layout = QVBoxLayout(empty_page)
        empty_layout.setAlignment(Qt.AlignCenter)
        
        empty_icon = QLabel()
        empty_icon_pixmap = IconProvider.get_icon("extension").pixmap(64, 64)
        empty_icon.setPixmap(empty_icon_pixmap)
        empty_icon.setAlignment(Qt.AlignCenter)
        
        empty_text = QLabel("选择一个插件查看详情")
        empty_text.setAlignment(Qt.AlignCenter)
        empty_text.setStyleSheet("color: rgba(255, 255, 255, 0.5);")
        
        empty_layout.addWidget(empty_icon)
        empty_layout.addWidget(empty_text)
        
        # 详情页面
        self.details_page = QWidget()
        self.details_layout = QVBoxLayout(self.details_page)
        
        # 插件标题区域
        self.title_widget = QWidget()
        title_layout = QHBoxLayout(self.title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        self.plugin_icon = QLabel()
        self.plugin_icon.setFixedSize(48, 48)
        title_layout.addWidget(self.plugin_icon)
        
        title_info = QWidget()
        title_info_layout = QVBoxLayout(title_info)
        title_info_layout.setContentsMargins(0, 0, 0, 0)
        title_info_layout.setSpacing(2)
        
        self.plugin_name = QLabel()
        self.plugin_name.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_info_layout.addWidget(self.plugin_name)
        
        self.plugin_version = QLabel()
        self.plugin_version.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
        title_info_layout.addWidget(self.plugin_version)
        
        title_layout.addWidget(title_info, 1)
        
        # 创建操作按钮
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(5)
        
        self.settings_btn = QPushButton("")
        self.settings_btn.setIcon(IconProvider.get_icon("settings"))
        self.settings_btn.setToolTip("插件设置")
        self.settings_btn.clicked.connect(self.openPluginSettings)
        actions_layout.addWidget(self.settings_btn)
        
        self.toggle_btn = QPushButton("")
        self.toggle_btn.setIcon(IconProvider.get_icon("toggle_on"))
        self.toggle_btn.setToolTip("启用/禁用")
        self.toggle_btn.clicked.connect(self.togglePlugin)
        actions_layout.addWidget(self.toggle_btn)
        
        self.more_btn = QToolButton()
        self.more_btn.setIcon(IconProvider.get_icon("more_vert"))
        self.more_btn.setToolTip("更多操作")
        self.more_btn.setPopupMode(QToolButton.InstantPopup)
        actions_layout.addWidget(self.more_btn)
        
        # 创建更多操作菜单
        self.more_menu = QMenu(self.more_btn)
        self.uninstall_action = self.more_menu.addAction("卸载插件")
        self.uninstall_action.triggered.connect(self.uninstallPlugin)
        
        self.reload_action = self.more_menu.addAction("重新加载插件")
        self.reload_action.triggered.connect(self.reloadPlugin)
        
        self.more_menu.addSeparator()
        
        self.open_folder_action = self.more_menu.addAction("打开插件文件夹")
        self.open_folder_action.triggered.connect(self.openPluginFolder)
        
        self.more_btn.setMenu(self.more_menu)
        
        title_layout.addWidget(actions_widget)
        
        # 添加分隔线
        title_separator = QFrame()
        title_separator.setFrameShape(QFrame.HLine)
        title_separator.setFrameShadow(QFrame.Sunken)
        title_separator.setStyleSheet("background-color: rgba(255, 255, 255, 0.1);")
        
        # 添加详情区域
        self.description_label = QLabel()
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet("margin-top: 10px; margin-bottom: 10px;")
        
        # 添加作者区域
        author_widget = QWidget()
        author_layout = QHBoxLayout(author_widget)
        author_layout.setContentsMargins(0, 0, 0, 0)
        
        author_label = QLabel("作者:")
        author_label.setFixedWidth(80)
        author_layout.addWidget(author_label)
        
        self.author_value = QLabel()
        author_layout.addWidget(self.author_value, 1)
        
        # 添加主页区域
        homepage_widget = QWidget()
        homepage_layout = QHBoxLayout(homepage_widget)
        homepage_layout.setContentsMargins(0, 0, 0, 0)
        
        homepage_label = QLabel("主页:")
        homepage_label.setFixedWidth(80)
        homepage_layout.addWidget(homepage_label)
        
        self.homepage_value = QLabel()
        self.homepage_value.setOpenExternalLinks(True)
        homepage_layout.addWidget(self.homepage_value, 1)
        
        # 添加路径区域
        path_widget = QWidget()
        path_layout = QHBoxLayout(path_widget)
        path_layout.setContentsMargins(0, 0, 0, 0)
        
        path_label = QLabel("路径:")
        path_label.setFixedWidth(80)
        path_layout.addWidget(path_label)
        
        self.path_value = QLabel()
        self.path_value.setWordWrap(True)
        path_layout.addWidget(self.path_value, 1)
        
        # 添加依赖区域
        deps_widget = QWidget()
        deps_layout = QHBoxLayout(deps_widget)
        deps_layout.setContentsMargins(0, 0, 0, 0)
        
        deps_label = QLabel("依赖项:")
        deps_label.setFixedWidth(80)
        deps_layout.addWidget(deps_label)
        
        self.deps_value = QLabel()
        deps_layout.addWidget(self.deps_value, 1)
        
        # 将所有组件添加到详情布局
        self.details_layout.addWidget(self.title_widget)
        self.details_layout.addWidget(title_separator)
        self.details_layout.addWidget(self.description_label)
        self.details_layout.addWidget(author_widget)
        self.details_layout.addWidget(homepage_widget)
        self.details_layout.addWidget(path_widget)
        self.details_layout.addWidget(deps_widget)
        self.details_layout.addStretch(1)
        
        # 添加页面到堆栈
        self.details_stack.addWidget(empty_page)  # 索引0
        self.details_stack.addWidget(self.details_page)  # 索引1
        
        details_layout.addWidget(self.details_stack)
        
        split_layout.addWidget(details_container, 2)
        
        plugins_layout.addLayout(split_layout)
        
        # 添加所有元素到主布局
        main_layout.addWidget(toolbar)
        main_layout.addWidget(separator)
        main_layout.addWidget(plugins_widget, 1)
    
    def loadPlugins(self):
        """加载插件列表"""
        try:
            # 清除列表
            self.plugins_list.clear()
            self.plugins = []
            
            # 检查插件管理器是否可用
            if not self.plugin_manager:
                self.addPlaceholderItem("插件管理器不可用")
                return
            
            # 获取所有插件
            all_plugins = self.plugin_manager.get_plugins()
            
            # 如果没有插件，显示提示
            if not all_plugins:
                self.addPlaceholderItem("没有找到插件")
                return
            
            # 按照名称排序
            self.plugins = sorted(all_plugins, key=lambda p: p.metadata.name.lower())
            
            # 添加到列表
            for plugin in self.plugins:
                self.addPluginItem(plugin)
            
            # 默认选中第一个
            if self.plugins_list.count() > 0:
                self.plugins_list.setCurrentRow(0)
            else:
                # 如果没有项目，显示空状态
                self.details_stack.setCurrentIndex(0)
            
            print(f"已加载{len(self.plugins)}个插件")
        except Exception as e:
            print(f"加载插件列表时出错: {e}")
            import traceback
            traceback.print_exc()
            
            # 显示错误状态
            self.addPlaceholderItem(f"加载插件时出错: {e}")
    
    def addPlaceholderItem(self, message):
        """添加占位项"""
        item = QListWidgetItem(message)
        item.setIcon(IconProvider.get_icon("error"))
        item.setFlags(item.flags() & ~Qt.ItemIsEnabled)  # 设置为不可选中
        self.plugins_list.addItem(item)
        
        # 显示空状态
        self.details_stack.setCurrentIndex(0)
    
    def addPluginItem(self, plugin):
        """添加插件到列表"""
        # 创建列表项
        item = QListWidgetItem(plugin.metadata.name)
        
        # 设置图标
        plugin_icon = self.getPluginIcon(plugin)
        item.setIcon(plugin_icon)
        
        # 存储插件ID
        item.setData(Qt.UserRole, plugin.metadata.id)
        
        # 添加到列表
        self.plugins_list.addItem(item)
    
    def getPluginIcon(self, plugin):
        """获取插件图标"""
        # 先查找插件目录下的icon.png
        plugin_dir = plugin.metadata.path
        icon_path = os.path.join(plugin_dir, "icon.png")
        
        if os.path.exists(icon_path):
            return QIcon(icon_path)
        
        # 如果没有icon.png，查找metadata中的icon字段
        if hasattr(plugin.metadata, "icon") and plugin.metadata.icon:
            # 检查是否是绝对路径
            if os.path.isabs(plugin.metadata.icon) and os.path.exists(plugin.metadata.icon):
                return QIcon(plugin.metadata.icon)
            
            # 检查是否是相对路径
            rel_icon_path = os.path.join(plugin_dir, plugin.metadata.icon)
            if os.path.exists(rel_icon_path):
                return QIcon(rel_icon_path)
            
            # 检查是否是内置图标名称
            if IconProvider and hasattr(IconProvider, 'get_icon'):
                return IconProvider.get_icon(plugin.metadata.icon)
        
        # 使用默认图标
        return IconProvider.get_icon("extension")
    
    def onPluginSelected(self, index):
        """插件选中时的处理"""
        try:
            # 检查索引是否有效
            if index < 0 or index >= len(self.plugins):
                # 显示空状态
                self.details_stack.setCurrentIndex(0)
                return
            
            # 获取当前选中的插件
            plugin = self.plugins[index]
            
            # 设置详情页面
            self.updatePluginDetails(plugin)
            
            # 显示详情页面
            self.details_stack.setCurrentIndex(1)
        except Exception as e:
            print(f"处理插件选中事件时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def updatePluginDetails(self, plugin):
        """更新插件详情"""
        try:
            # 设置图标
            icon = self.getPluginIcon(plugin)
            self.plugin_icon.setPixmap(icon.pixmap(48, 48))
            
            # 设置名称和版本
            self.plugin_name.setText(plugin.metadata.name)
            self.plugin_version.setText(f"v{plugin.metadata.version}")
            
            # 设置描述
            self.description_label.setText(plugin.metadata.description or "无描述")
            
            # 设置作者
            self.author_value.setText(plugin.metadata.author or "未知")
            
            # 设置主页
            if plugin.metadata.homepage:
                self.homepage_value.setText(f'<a href="{plugin.metadata.homepage}">{plugin.metadata.homepage}</a>')
            else:
                self.homepage_value.setText("无")
            
            # 设置路径
            self.path_value.setText(plugin.metadata.path)
            
            # 设置依赖
            if hasattr(plugin.metadata, "dependencies") and plugin.metadata.dependencies:
                self.deps_value.setText(", ".join(plugin.metadata.dependencies))
            else:
                self.deps_value.setText("无")
            
            # 更新按钮状态
            # 检查是否启用
            if plugin.is_enabled:
                self.toggle_btn.setIcon(IconProvider.get_icon("toggle_on"))
                self.toggle_btn.setToolTip("禁用插件")
            else:
                self.toggle_btn.setIcon(IconProvider.get_icon("toggle_off"))
                self.toggle_btn.setToolTip("启用插件")
            
            # 检查是否支持设置
            if hasattr(plugin, "has_settings") and plugin.has_settings:
                self.settings_btn.setEnabled(True)
            else:
                self.settings_btn.setEnabled(False)
        except Exception as e:
            print(f"更新插件详情时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def refreshPlugins(self):
        """刷新插件列表"""
        try:
            # 检查插件管理器是否可用
            if not self.plugin_manager:
                QMessageBox.warning(self, "错误", "插件管理器不可用")
                return
            
            # 扫描插件目录
            self.plugin_manager.discover_plugins()
            
            # 重新加载插件列表
            self.loadPlugins()
        except Exception as e:
            print(f"刷新插件列表时出错: {e}")
            QMessageBox.warning(self, "错误", f"刷新插件列表时出错: {e}")
    
    def addPlugin(self):
        """添加插件"""
        try:
            # 检查插件管理器是否可用
            if not self.plugin_manager:
                QMessageBox.warning(self, "错误", "插件管理器不可用")
                return
            
            # 获取插件目录
            plugin_dir = self.plugin_manager.plugin_dir
            
            # 显示文件对话框
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择插件文件", "",
                "插件文件 (*.py *.zip);;所有文件 (*)", options=options
            )
            
            if not file_path:
                return
            
            # 安装插件
            success = self.plugin_manager.install_plugin(file_path)
            
            if success:
                QMessageBox.information(self, "成功", f"插件安装成功: {os.path.basename(file_path)}")
                
                # 发送插件变更信号
                self.pluginsChanged.emit()
                
                # 刷新插件列表
                self.refreshPlugins()
            else:
                QMessageBox.warning(self, "错误", f"插件安装失败: {os.path.basename(file_path)}")
        except Exception as e:
            print(f"添加插件时出错: {e}")
            QMessageBox.warning(self, "错误", f"添加插件时出错: {e}")
    
    def togglePlugin(self):
        """切换插件状态（启用/禁用）"""
        try:
            # 获取当前选中的插件
            index = self.plugins_list.currentRow()
            if index < 0 or index >= len(self.plugins):
                return
            
            plugin = self.plugins[index]
            
            # 切换状态
            if plugin.is_enabled:
                # 禁用插件
                success = self.plugin_manager.disable_plugin(plugin.metadata.id)
                if success:
                    QMessageBox.information(self, "成功", f"插件已禁用: {plugin.metadata.name}")
                else:
                    QMessageBox.warning(self, "错误", f"禁用插件失败: {plugin.metadata.name}")
            else:
                # 启用插件
                success = self.plugin_manager.enable_plugin(plugin.metadata.id)
                if success:
                    QMessageBox.information(self, "成功", f"插件已启用: {plugin.metadata.name}")
                else:
                    QMessageBox.warning(self, "错误", f"启用插件失败: {plugin.metadata.name}")
            
            # 发送插件变更信号
            self.pluginsChanged.emit()
            
            # 更新UI
            self.updatePluginDetails(plugin)
        except Exception as e:
            print(f"切换插件状态时出错: {e}")
            QMessageBox.warning(self, "错误", f"切换插件状态时出错: {e}")
    
    def openPluginSettings(self):
        """打开插件设置"""
        try:
            # 获取当前选中的插件
            index = self.plugins_list.currentRow()
            if index < 0 or index >= len(self.plugins):
                return
            
            plugin = self.plugins[index]
            
            # 调用插件管理器的打开设置方法
            self.plugin_manager.open_plugin_settings(plugin.metadata.id)
        except Exception as e:
            print(f"打开插件设置时出错: {e}")
            QMessageBox.warning(self, "错误", f"打开插件设置时出错: {e}")
    
    def uninstallPlugin(self):
        """卸载插件"""
        try:
            # 获取当前选中的插件
            index = self.plugins_list.currentRow()
            if index < 0 or index >= len(self.plugins):
                return
            
            plugin = self.plugins[index]
            
            # 确认对话框
            reply = QMessageBox.question(
                self, "确认卸载",
                f"确定要卸载插件 {plugin.metadata.name} 吗？\n这将删除插件的所有文件，此操作不可撤销。",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 卸载插件
                success = self.plugin_manager.uninstall_plugin(plugin.metadata.id)
                
                if success:
                    QMessageBox.information(self, "成功", f"插件已卸载: {plugin.metadata.name}")
                    
                    # 发送插件变更信号
                    self.pluginsChanged.emit()
                    
                    # 刷新插件列表
                    self.refreshPlugins()
                else:
                    QMessageBox.warning(self, "错误", f"卸载插件失败: {plugin.metadata.name}")
        except Exception as e:
            print(f"卸载插件时出错: {e}")
            QMessageBox.warning(self, "错误", f"卸载插件时出错: {e}")
    
    def reloadPlugin(self):
        """重新加载插件"""
        try:
            # 获取当前选中的插件
            index = self.plugins_list.currentRow()
            if index < 0 or index >= len(self.plugins):
                return
            
            plugin = self.plugins[index]
            
            # 重新加载插件
            success = self.plugin_manager.reload_plugin(plugin.metadata.id)
            
            if success:
                QMessageBox.information(self, "成功", f"插件已重新加载: {plugin.metadata.name}")
                
                # 发送插件变更信号
                self.pluginsChanged.emit()
                
                # 更新UI
                self.updatePluginDetails(plugin)
            else:
                QMessageBox.warning(self, "错误", f"重新加载插件失败: {plugin.metadata.name}")
        except Exception as e:
            print(f"重新加载插件时出错: {e}")
            QMessageBox.warning(self, "错误", f"重新加载插件时出错: {e}")
    
    def openPluginFolder(self):
        """打开插件文件夹"""
        try:
            # 获取当前选中的插件
            index = self.plugins_list.currentRow()
            if index < 0 or index >= len(self.plugins):
                return
            
            plugin = self.plugins[index]
            
            # 获取插件路径
            plugin_path = plugin.metadata.path
            
            # 使用系统默认程序打开文件夹
            import subprocess
            import platform
            
            if platform.system() == "Windows":
                os.startfile(plugin_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.call(["open", plugin_path])
            else:  # Linux
                subprocess.call(["xdg-open", plugin_path])
        except Exception as e:
            print(f"打开插件文件夹时出错: {e}")
            QMessageBox.warning(self, "错误", f"打开插件文件夹时出错: {e}") 