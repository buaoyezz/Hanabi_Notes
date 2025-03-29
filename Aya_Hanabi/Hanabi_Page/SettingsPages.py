import os
import json
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox, QTabWidget, QWidget,
                             QListWidget, QListWidgetItem, QScrollArea,
                             QGridLayout, QFrame, QSizePolicy, QSpacerItem,
                             QFileDialog, QMessageBox)
from PySide6.QtGui import QFont, QIcon, QPixmap, QImage, QColor, QFocusEvent
from PySide6.QtWidgets import QApplication
from Aya_Hanabi.Hanabi_Core.UI.messageBox import HanabiMessageBox, information, warning, critical, question, success

# 自定义无焦点组件基类
class NoFocusWidget:
    def focusInEvent(self, event):
        self.clearFocus()
        event.ignore()
        
    def setNoFocus(self):
        self.setFocusPolicy(Qt.NoFocus)

# 无焦点列表组件
class NoFocusListWidget(QListWidget, NoFocusWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setNoFocus()

# 无焦点按钮
class NoFocusButton(QPushButton, NoFocusWidget):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setNoFocus()

# 基本设置对话框
class SettingsDialog(QDialog):
    settingsChanged = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("设置")
        self.setMinimumSize(800, 500)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self.setFocusPolicy(Qt.NoFocus)
        
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
        
    def initUI(self):
        # 主布局
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)
        
        # 标题栏
        titleBar = QWidget()
        titleBar.setObjectName("titleBar")
        titleBar.setFixedHeight(50)
        titleBarLayout = QHBoxLayout(titleBar)
        titleBarLayout.setContentsMargins(20, 0, 20, 0)
        
        titleLabel = QLabel("设置中心")
        titleLabel.setObjectName("titleLabel")
        titleLabel.setFont(QFont("", 16, QFont.Bold))
        
        titleBarLayout.addWidget(titleLabel)
        
        mainLayout.addWidget(titleBar)
        
        # 内容区域
        contentWidget = QWidget()
        contentWidget.setObjectName("contentWidget")
        contentLayout = QHBoxLayout(contentWidget)
        contentLayout.setContentsMargins(0, 0, 0, 0)
        contentLayout.setSpacing(0)
        
        # 左侧导航栏
        navWidget = QWidget()
        navWidget.setObjectName("navWidget")
        navWidget.setFixedWidth(180)
        navLayout = QVBoxLayout(navWidget)
        navLayout.setContentsMargins(15, 15, 0, 15)
        navLayout.setSpacing(8)
        
        self.navListWidget = NoFocusListWidget()
        self.navListWidget.setObjectName("navListWidget")
        self.navListWidget.setFrameShape(QFrame.NoFrame)
        self.navListWidget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.navListWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 添加导航项
        generalItem = QListWidgetItem("常规设置")
        generalItem.setData(Qt.UserRole, "general")
        self.navListWidget.addItem(generalItem)
        
        appearanceItem = QListWidgetItem("外观")
        appearanceItem.setData(Qt.UserRole, "appearance")
        self.navListWidget.addItem(appearanceItem)
        
        editorItem = QListWidgetItem("编辑器")
        editorItem.setData(Qt.UserRole, "editor")
        self.navListWidget.addItem(editorItem)
        
        # 添加更多导航项
        aboutItem = QListWidgetItem("关于")
        aboutItem.setData(Qt.UserRole, "about")
        self.navListWidget.addItem(aboutItem)
        
        navLayout.addWidget(self.navListWidget)
        
        # 右侧内容区
        rightWidget = QWidget()
        rightWidget.setObjectName("rightWidget")
        rightLayout = QVBoxLayout(rightWidget)
        rightLayout.setContentsMargins(20, 20, 20, 20)
        
        self.contentStack = QTabWidget()
        self.contentStack.setObjectName("contentStack")
        self.contentStack.tabBar().setVisible(False)
        self.contentStack.setFocusPolicy(Qt.NoFocus)
        
        # 添加设置页面
        self.generalPage = QWidget()
        self.setupGeneralPage()
        
        self.appearancePage = QWidget()
        self.setupAppearancePage()
        
        self.editorPage = QWidget()
        self.setupEditorPage()
        
        self.aboutPage = QWidget()
        self.setupAboutPage()
        
        self.contentStack.addTab(self.generalPage, "常规设置")
        self.contentStack.addTab(self.appearancePage, "外观")
        self.contentStack.addTab(self.editorPage, "编辑器")
        self.contentStack.addTab(self.aboutPage, "关于")
        
        rightLayout.addWidget(self.contentStack)
        
        # 底部按钮区域
        buttonWidget = QWidget()
        buttonWidget.setObjectName("buttonWidget")
        buttonLayout = QHBoxLayout(buttonWidget)
        
        self.saveButton = NoFocusButton("保存")
        self.saveButton.setObjectName("saveButton")
        self.cancelButton = NoFocusButton("取消")
        self.cancelButton.setObjectName("cancelButton")
        
        buttonLayout.addStretch(1)
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
        from PySide6.QtWidgets import QCheckBox, QGroupBox, QFormLayout, QSpinBox, QFileDialog, QLineEdit
        
        generalLayout = QVBoxLayout(self.generalPage)
        generalLayout.setSpacing(20)
        
        # 启动选项
        startupGroup = QGroupBox("启动选项")
        startupGroup.setFocusPolicy(Qt.NoFocus)
        startupGroup.setObjectName("settingsGroup")
        startupLayout = QVBoxLayout(startupGroup)
        
        self.autoStartCheckbox = QCheckBox("系统启动时自动运行")
        self.autoStartCheckbox.setFocusPolicy(Qt.NoFocus)
        self.rememberWindowCheckbox = QCheckBox("记住窗口位置和大小")
        self.rememberWindowCheckbox.setFocusPolicy(Qt.NoFocus)
        self.reopenFilesCheckbox = QCheckBox("重新打开上次的文件")
        self.reopenFilesCheckbox.setFocusPolicy(Qt.NoFocus)
        
        startupLayout.addWidget(self.autoStartCheckbox)
        startupLayout.addWidget(self.rememberWindowCheckbox)
        startupLayout.addWidget(self.reopenFilesCheckbox)
        
        # 文件选项
        fileGroup = QGroupBox("文件选项")
        fileGroup.setFocusPolicy(Qt.NoFocus)
        fileGroup.setObjectName("settingsGroup")
        fileLayout = QFormLayout(fileGroup)
        
        self.defaultSavePathEdit = QLineEdit()
        self.defaultSavePathEdit.setFocusPolicy(Qt.NoFocus)
        self.defaultSavePathEdit.setReadOnly(True)
        self.defaultSavePathEdit.setPlaceholderText("选择默认保存路径...")
        
        browseSavePathBtn = NoFocusButton("浏览...")
        browseSavePathBtn.clicked.connect(self.browseSavePath)
        
        savePathLayout = QHBoxLayout()
        savePathLayout.addWidget(self.defaultSavePathEdit)
        savePathLayout.addWidget(browseSavePathBtn)
        
        self.autoSaveCheckbox = QCheckBox("自动保存")
        self.autoSaveCheckbox.setFocusPolicy(Qt.NoFocus)
        self.autoSaveIntervalSpinBox = QSpinBox()
        self.autoSaveIntervalSpinBox.setFocusPolicy(Qt.NoFocus)
        self.autoSaveIntervalSpinBox.setMinimum(1)
        self.autoSaveIntervalSpinBox.setMaximum(60)
        self.autoSaveIntervalSpinBox.setValue(5)
        self.autoSaveIntervalSpinBox.setSuffix(" 分钟")
        
        autoSaveLayout = QHBoxLayout()
        autoSaveLayout.addWidget(self.autoSaveCheckbox)
        autoSaveLayout.addWidget(self.autoSaveIntervalSpinBox)
        autoSaveLayout.addStretch(1)
        
        fileLayout.addRow("默认保存位置:", savePathLayout)
        fileLayout.addRow("自动保存:", autoSaveLayout)
        
        # 其他选项
        otherGroup = QGroupBox("其他选项")
        otherGroup.setFocusPolicy(Qt.NoFocus)
        otherGroup.setObjectName("settingsGroup")
        otherLayout = QVBoxLayout(otherGroup)
        
        self.showStatusBarCheckbox = QCheckBox("显示状态栏")
        self.showStatusBarCheckbox.setFocusPolicy(Qt.NoFocus)
        self.enableSoundEffectsCheckbox = QCheckBox("启用声音效果")
        self.enableSoundEffectsCheckbox.setFocusPolicy(Qt.NoFocus)
        
        otherLayout.addWidget(self.showStatusBarCheckbox)
        otherLayout.addWidget(self.enableSoundEffectsCheckbox)
        
        # 将所有组添加到主布局
        generalLayout.addWidget(startupGroup)
        generalLayout.addWidget(fileGroup)
        generalLayout.addWidget(otherGroup)
        generalLayout.addStretch(1)
        
        # 设置默认值
        self.loadGeneralSettings()
    
    def setupAppearancePage(self):
        from PySide6.QtWidgets import QGroupBox, QSlider, QWidget, QHBoxLayout, QLabel

        appearanceLayout = QVBoxLayout(self.appearancePage)
        
        # 主题模式选择
        themeGroup = QGroupBox("主题模式")
        themeGroup.setFocusPolicy(Qt.NoFocus)
        themeGroup.setObjectName("settingsGroup")
        themeLayout = QVBoxLayout(themeGroup)
        
        # 主题设置区域
        themeButton = NoFocusButton("打开主题设置")
        themeButton.setObjectName("themeButton")
        themeButton.clicked.connect(self.openThemeSettings)
        
        themeLayout.addWidget(themeButton)
        
        # 界面缩放选项
        scaleGroup = QGroupBox("界面缩放")
        scaleGroup.setFocusPolicy(Qt.NoFocus)
        scaleGroup.setObjectName("settingsGroup")
        scaleLayout = QVBoxLayout(scaleGroup)
        
        scaleSlider = QWidget()
        scaleSlider.setFocusPolicy(Qt.NoFocus)
        scaleSliderLayout = QHBoxLayout(scaleSlider)
        scaleSliderLayout.setContentsMargins(0, 0, 0, 0)
        
        scaleLabel = QLabel("100%")
        scaleLabel.setFocusPolicy(Qt.NoFocus)
        scaleLabel.setAlignment(Qt.AlignCenter)
        scaleLabel.setFixedWidth(50)
        
        smallerButton = NoFocusButton("-")
        smallerButton.setFixedSize(30, 30)
        smallerButton.setObjectName("smallerButton")
        
        largerButton = NoFocusButton("+")
        largerButton.setFixedSize(30, 30)
        largerButton.setObjectName("largerButton")
        
        scaleSliderLayout.addWidget(smallerButton)
        scaleSliderLayout.addStretch()
        scaleSliderLayout.addWidget(scaleLabel)
        scaleSliderLayout.addStretch()
        scaleSliderLayout.addWidget(largerButton)
        
        scaleLayout.addWidget(scaleSlider)
        
        # 添加外观选项到布局
        appearanceLayout.addWidget(themeGroup)
        appearanceLayout.addWidget(scaleGroup)
        appearanceLayout.addStretch(1)
        
    def setupEditorPage(self):
        from PySide6.QtWidgets import QComboBox, QCheckBox, QGroupBox, QFormLayout, QSpinBox, QFontComboBox
        
        editorLayout = QVBoxLayout(self.editorPage)
        editorLayout.setSpacing(20)
        
        # 字体设置
        fontGroup = QGroupBox("字体设置")
        fontGroup.setFocusPolicy(Qt.NoFocus)
        fontGroup.setObjectName("settingsGroup")
        fontLayout = QFormLayout(fontGroup)
        
        # 字体信息显示
        self.fontInfoLabel = QLabel("当前字体: Consolas, 15pt")
        self.fontInfoLabel.setFocusPolicy(Qt.NoFocus)
        
        # 字体选择按钮
        self.fontSelectButton = QPushButton("字体选择...")
        self.fontSelectButton.setFocusPolicy(Qt.NoFocus)
        self.fontSelectButton.clicked.connect(self.openFontDialog)
        
        # 字体预览标签
        self.fontPreviewLabel = QLabel("AaBbCcXxYyZz 1234567890 花火笔记，随你四季")
        self.fontPreviewLabel.setFocusPolicy(Qt.NoFocus)
        self.fontPreviewLabel.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        self.fontPreviewLabel.setMinimumHeight(60)
        self.fontPreviewLabel.setStyleSheet("padding: 8px;")
        self.fontPreviewLabel.setAlignment(Qt.AlignCenter)
        
        fontLayout.addRow(self.fontInfoLabel)
        fontLayout.addRow(self.fontSelectButton)
        fontLayout.addRow("预览:", self.fontPreviewLabel)
        
        # 编辑选项
        editGroup = QGroupBox("编辑选项")
        editGroup.setFocusPolicy(Qt.NoFocus)
        editGroup.setObjectName("settingsGroup")
        editLayout = QVBoxLayout(editGroup)
        
        self.autoIndentCheckbox = QCheckBox("自动缩进")
        self.autoIndentCheckbox.setFocusPolicy(Qt.NoFocus)
        self.lineNumbersCheckbox = QCheckBox("显示行号")
        self.lineNumbersCheckbox.setFocusPolicy(Qt.NoFocus)
        self.spellCheckCheckbox = QCheckBox("拼写检查")
        self.spellCheckCheckbox.setFocusPolicy(Qt.NoFocus)
        self.wordWrapCheckbox = QCheckBox("自动换行")
        self.wordWrapCheckbox.setFocusPolicy(Qt.NoFocus)
        
        editLayout.addWidget(self.autoIndentCheckbox)
        editLayout.addWidget(self.lineNumbersCheckbox)
        editLayout.addWidget(self.spellCheckCheckbox)
        editLayout.addWidget(self.wordWrapCheckbox)
        
        # 高级编辑设置
        advancedGroup = QGroupBox("高级设置")
        advancedGroup.setFocusPolicy(Qt.NoFocus)
        advancedGroup.setObjectName("settingsGroup")
        advancedLayout = QVBoxLayout(advancedGroup)
        
        self.codeHighlightCheckbox = QCheckBox("代码高亮")
        self.codeHighlightCheckbox.setFocusPolicy(Qt.NoFocus)
        self.autoCompleteCheckbox = QCheckBox("自动完成")
        self.autoCompleteCheckbox.setFocusPolicy(Qt.NoFocus)
        
        advancedLayout.addWidget(self.codeHighlightCheckbox)
        advancedLayout.addWidget(self.autoCompleteCheckbox)
        
        # 将所有组添加到主布局
        editorLayout.addWidget(fontGroup)
        editorLayout.addWidget(editGroup)
        editorLayout.addWidget(advancedGroup)
        editorLayout.addStretch(1)
        
        # 设置默认值
        self.loadEditorSettings()
        
    def setupAboutPage(self):
        aboutLayout = QVBoxLayout(self.aboutPage)
        
        # 添加Logo和标题
        logoContainer = QWidget()
        logoContainer.setFocusPolicy(Qt.NoFocus)
        logoLayout = QVBoxLayout(logoContainer)
        
        logoLabel = QLabel("Hanabi Notes")
        logoLabel.setFocusPolicy(Qt.NoFocus)
        logoLabel.setObjectName("logoLabel")
        logoLabel.setAlignment(Qt.AlignCenter)
        logoLabel.setFont(QFont("", 24, QFont.Bold))
        
        versionLabel = QLabel("版本 0.0.1")
        versionLabel.setFocusPolicy(Qt.NoFocus)
        versionLabel.setObjectName("versionLabel")
        versionLabel.setAlignment(Qt.AlignCenter)
        
        logoLayout.addWidget(logoLabel)
        logoLayout.addWidget(versionLabel)
        
        # 添加描述文字
        descLabel = QLabel("Hanabi Notes is a simple and easy-to-use note-taking application. \n Designed for writing and recording ideas. \n Next Generation of TsukiNotes")
        descLabel.setFocusPolicy(Qt.NoFocus)
        descLabel.setWordWrap(True)
        descLabel.setAlignment(Qt.AlignCenter)
        descLabel.setObjectName("descLabel")
        
        # 添加版权信息
        copyrightLabel = QLabel("© 2025 Clut Network. All rights reserved.")
        copyrightLabel.setFocusPolicy(Qt.NoFocus)
        copyrightLabel.setAlignment(Qt.AlignCenter)
        copyrightLabel.setObjectName("copyrightLabel")
        
        # 添加按钮
        buttonsContainer = QWidget()
        buttonsContainer.setFocusPolicy(Qt.NoFocus)
        buttonsLayout = QHBoxLayout(buttonsContainer)
        
        websiteButton = NoFocusButton("访问网站")
        websiteButton.setObjectName("linkButton")
        
        updateButton = NoFocusButton("检查更新")
        updateButton.setObjectName("linkButton")
        
        buttonsLayout.addStretch()
        buttonsLayout.addWidget(websiteButton)
        buttonsLayout.addWidget(updateButton)
        buttonsLayout.addStretch()
        
        # 添加到主布局
        aboutLayout.addStretch()
        aboutLayout.addWidget(logoContainer)
        aboutLayout.addSpacing(20)
        aboutLayout.addWidget(descLabel)
        aboutLayout.addSpacing(20)
        aboutLayout.addWidget(copyrightLabel)
        aboutLayout.addSpacing(20)
        aboutLayout.addWidget(buttonsContainer)
        aboutLayout.addStretch()
    
    def browseSavePath(self):
        from PySide6.QtWidgets import QFileDialog
        
        dirPath = QFileDialog.getExistingDirectory(
            self,
            "选择默认保存位置",
            self.defaultSavePathEdit.text() or os.path.expanduser("~")
        )
        
        if dirPath:
            self.defaultSavePathEdit.setText(dirPath)
    
    def openThemeSettings(self):
        try:
            mainWindow = self.parent()
            if mainWindow and hasattr(mainWindow, 'showThemeSettings'):
                self.accept()
                mainWindow.showThemeSettings()
            else:
                from Aya_Hanabi.Hanabi_Core.UI.messageBox import HanabiMessageBox, information, warning, critical, question, success
                information(self, "提示", "无法打开主题设置")
        except Exception as e:
            from Aya_Hanabi.Hanabi_Core.UI.messageBox import HanabiMessageBox, information, warning, critical, question, success
            warning(self, "错误", f"打开主题设置时出错: {str(e)}")
    
    def openFontDialog(self):
        try:
            # 导入字体预览对话框
            from Aya_Hanabi.Hanabi_Core.FontManager import FontPreviewDialog, FontManager
            
            # 获取当前字体设置
            fontFamily = self.settings["editor"]["font"].get("family", "Consolas")
            fontSize = self.settings["editor"]["font"].get("size", 15)
            
            # 创建当前字体对象
            currentFont = QFont(fontFamily, fontSize)
            
            # 创建并显示字体预览对话框
            fontDialog = FontPreviewDialog(self, currentFont)
            fontDialog.fontSelected.connect(self.onFontSelected)
            
            fontDialog.exec()
        except Exception as e:
            from Aya_Hanabi.Hanabi_Core.UI.messageBox import HanabiMessageBox, information, warning, critical, question, success
            warning(self, "错误", f"打开字体对话框时出错: {str(e)}")

    def loadGeneralSettings(self):
        startupSettings = self.settings["general"]["startup"]
        fileSettings = self.settings["general"]["file"]
        otherSettings = self.settings["general"]["other"]
        
        self.autoStartCheckbox.setChecked(startupSettings.get("auto_start", False))
        self.rememberWindowCheckbox.setChecked(startupSettings.get("remember_window", True))
        self.reopenFilesCheckbox.setChecked(startupSettings.get("reopen_files", True))
        
        self.defaultSavePathEdit.setText(fileSettings.get("default_save_path", ""))
        self.autoSaveCheckbox.setChecked(fileSettings.get("auto_save", True))
        self.autoSaveIntervalSpinBox.setValue(fileSettings.get("auto_save_interval", 5))
        
        self.showStatusBarCheckbox.setChecked(otherSettings.get("show_status_bar", True))
        self.enableSoundEffectsCheckbox.setChecked(otherSettings.get("enable_sound_effects", False))

    def onFontSelected(self, family, size, bold, italic):
        # 更新设置
        self.settings["editor"]["font"]["family"] = family
        self.settings["editor"]["font"]["size"] = size
        
        # 如果之前没有bold和italic设置，添加它们
        if "style" not in self.settings["editor"]["font"]:
            self.settings["editor"]["font"]["style"] = {}
        
        self.settings["editor"]["font"]["style"]["bold"] = bold
        self.settings["editor"]["font"]["style"]["italic"] = italic
        
        # 更新界面显示
        self.fontInfoLabel.setText(f"当前字体: {family}, {size}pt{' 粗体' if bold else ''}{' 斜体' if italic else ''}")
        
        # 更新预览标签的字体
        try:
            previewFont = QFont(family, size)
            previewFont.setBold(bold)
            previewFont.setItalic(italic)
            
            # 使用样式表强制应用字体
            self.fontPreviewLabel.setStyleSheet(f"""
                padding: 8px;
                font-family: "{family}";
                font-size: {size}pt;
                font-weight: {700 if bold else 400};
                font-style: {("italic" if italic else "normal")};
            """)
            
            # 同时也设置字体对象
            self.fontPreviewLabel.setFont(previewFont)
            
            # 更新文本以强制重新渲染
            currentText = self.fontPreviewLabel.text()
            self.fontPreviewLabel.setText("")
            self.fontPreviewLabel.setText(currentText)
            
            # 强制更新
            self.fontPreviewLabel.update()
            self.fontPreviewLabel.repaint()
            
            # 更新界面
            QApplication.processEvents()
            
            print(f"字体预览已更新: {family}, {size}pt, 粗体={bold}, 斜体={italic}")
        except Exception as e:
            print(f"更新字体预览时出错: {e}")

    def loadEditorSettings(self):
        fontSettings = self.settings["editor"]["font"]
        editingSettings = self.settings["editor"]["editing"]
        
        # 获取字体设置
        fontFamily = fontSettings.get("family", "Consolas")
        fontSize = fontSettings.get("size", 15)
        
        # 获取字体样式设置
        fontStyle = fontSettings.get("style", {})
        bold = fontStyle.get("bold", False)
        italic = fontStyle.get("italic", False)
        
        # 更新字体信息标签
        self.fontInfoLabel.setText(f"当前字体: {fontFamily}, {fontSize}pt{' 粗体' if bold else ''}{' 斜体' if italic else ''}")
        
        # 更新预览标签的字体
        try:
            previewFont = QFont(fontFamily, fontSize)
            previewFont.setBold(bold)
            previewFont.setItalic(italic)
            
            # 使用样式表强制应用字体
            self.fontPreviewLabel.setStyleSheet(f"""
                padding: 8px;
                font-family: "{fontFamily}";
                font-size: {fontSize}pt;
                font-weight: {700 if bold else 400};
                font-style: {("italic" if italic else "normal")};
            """)
            
            # 同时也设置字体对象
            self.fontPreviewLabel.setFont(previewFont)
            
            # 更新文本以强制重新渲染
            currentText = self.fontPreviewLabel.text()
            self.fontPreviewLabel.setText("")
            self.fontPreviewLabel.setText(currentText)
            
            # 强制更新
            self.fontPreviewLabel.update()
            self.fontPreviewLabel.repaint()
            
            # 更新界面
            QApplication.processEvents()
            
            print(f"加载字体设置: {fontFamily}, {fontSize}pt, 粗体={bold}, 斜体={italic}")
        except Exception as e:
            print(f"加载字体设置时出错: {e}")
        
        # 设置编辑选项
        self.autoIndentCheckbox.setChecked(editingSettings.get("auto_indent", True))
        self.lineNumbersCheckbox.setChecked(editingSettings.get("line_numbers", True))
        self.spellCheckCheckbox.setChecked(editingSettings.get("spell_check", False))
        self.wordWrapCheckbox.setChecked(editingSettings.get("word_wrap", True))
        
        # 设置高级选项默认值
        self.codeHighlightCheckbox.setChecked(True)
        self.autoCompleteCheckbox.setChecked(False)
    
    def saveSettings(self):
        # 更新设置字典
        
        # 常规设置
        self.settings["general"]["startup"]["auto_start"] = self.autoStartCheckbox.isChecked()
        self.settings["general"]["startup"]["remember_window"] = self.rememberWindowCheckbox.isChecked()
        self.settings["general"]["startup"]["reopen_files"] = self.reopenFilesCheckbox.isChecked()
        
        self.settings["general"]["file"]["default_save_path"] = self.defaultSavePathEdit.text()
        self.settings["general"]["file"]["auto_save"] = self.autoSaveCheckbox.isChecked()
        self.settings["general"]["file"]["auto_save_interval"] = self.autoSaveIntervalSpinBox.value()
        
        self.settings["general"]["other"]["show_status_bar"] = self.showStatusBarCheckbox.isChecked()
        self.settings["general"]["other"]["enable_sound_effects"] = self.enableSoundEffectsCheckbox.isChecked()
        
        # 编辑器设置 - 字体设置现在通过onFontSelected方法更新
        
        # 编辑设置
        self.settings["editor"]["editing"]["auto_indent"] = self.autoIndentCheckbox.isChecked()
        self.settings["editor"]["editing"]["line_numbers"] = self.lineNumbersCheckbox.isChecked()
        self.settings["editor"]["editing"]["spell_check"] = self.spellCheckCheckbox.isChecked()
        self.settings["editor"]["editing"]["word_wrap"] = self.wordWrapCheckbox.isChecked()
        
        # 保存高级设置
        if "advanced" not in self.settings["editor"]:
            self.settings["editor"]["advanced"] = {}
        self.settings["editor"]["advanced"]["code_highlight"] = self.codeHighlightCheckbox.isChecked()
        self.settings["editor"]["advanced"]["auto_complete"] = self.autoCompleteCheckbox.isChecked()
        
        # 保存设置到文件
        self.writeSettings()
        
        # 发出设置变更信号
        self.settingsChanged.emit()
        
        # 关闭对话框
        self.accept()
    
    def loadSettings(self):
        try:
            settings_dir = self.getSettingsDir()
            settings_file = os.path.join(settings_dir, "settings.json")
            
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    
                    # 深度更新设置字典
                    self.deepUpdate(self.settings, loaded_settings)
        except Exception as e:
            print(f"加载设置时出错: {str(e)}")
    
    def writeSettings(self):
        try:
            settings_dir = self.getSettingsDir()
            os.makedirs(settings_dir, exist_ok=True)
            
            settings_file = os.path.join(settings_dir, "settings.json")
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
                
            # 如果配置了自动启动，处理系统启动项
            self.setupAutoStart(self.settings["general"]["startup"]["auto_start"])
                
        except Exception as e:
            print(f"保存设置时出错: {str(e)}")
            from Aya_Hanabi.Hanabi_Core.UI.messageBox import HanabiMessageBox, information, warning, critical, question, success
            warning(self, "保存失败", f"保存设置时出错: {str(e)}")
    
    def getSettingsDir(self):
        app_data_dir = os.path.join(os.path.expanduser("~"), ".hanabi_notes")
        return app_data_dir
    
    def setupAutoStart(self, enable):
        try:
            import sys
            import platform
            
            system = platform.system()
            
            if system == "Windows":
                import winreg
                
                app_path = sys.executable
                app_name = "HanabiNotes"
                
                # Windows注册表路径
                key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
                
                try:
                    if enable:
                        # 添加到启动项
                        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
                        winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{app_path}"')
                        winreg.CloseKey(key)
                    else:
                        # 从启动项移除
                        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
                        try:
                            winreg.DeleteValue(key, app_name)
                        except:
                            pass
                        winreg.CloseKey(key)
                except Exception as e:
                    print(f"设置自启动时出错: {str(e)}")
            elif system == "Linux":
                # Linux自启动脚本路径
                autostart_dir = os.path.expanduser("~/.config/autostart")
                autostart_file = os.path.join(autostart_dir, "hanabi-notes.desktop")
                
                if enable:
                    # 创建自启动文件
                    os.makedirs(autostart_dir, exist_ok=True)
                    
                    with open(autostart_file, "w") as f:
                        f.write("[Desktop Entry]\n")
                        f.write("Type=Application\n")
                        f.write("Name=Hanabi Notes\n")
                        f.write(f"Exec={sys.executable}\n")
                        f.write("Terminal=false\n")
                        f.write("X-GNOME-Autostart-enabled=true\n")
                else:
                    # 删除自启动文件
                    if os.path.exists(autostart_file):
                        os.remove(autostart_file)
            elif system == "Darwin":
                # macOS自启动plist路径
                plist_dir = os.path.expanduser("~/Library/LaunchAgents")
                plist_file = os.path.join(plist_dir, "com.hanabi.notes.plist")
                
                if enable:
                    # 创建plist文件
                    os.makedirs(plist_dir, exist_ok=True)
                    
                    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.hanabi.notes</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>"""
                    
                    with open(plist_file, "w") as f:
                        f.write(plist_content)
                else:
                    # 删除plist文件
                    if os.path.exists(plist_file):
                        os.remove(plist_file)
        except Exception as e:
            print(f"设置自启动项时出错: {str(e)}")
    
    def deepUpdate(self, target, source):
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self.deepUpdate(target[key], value)
            else:
                target[key] = value
    
    def applyStyle(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
                border-radius: 10px;
            }
            
            #titleBar {
                background-color: #e8e8e8;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
            
            #titleLabel {
                color: #333333;
            }
            
            #contentWidget {
                background-color: #f5f5f5;
            }
            
            #navWidget {
                background-color: #e8e8e8;
                border-top-right-radius: 0px;
                border-bottom-left-radius: 10px;
            }
            
            #navListWidget {
                background-color: transparent;
                color: #333333;
                font-size: 14px;
            }
            
            #navListWidget::item {
                padding: 10px;
                border-radius: 5px;
            }
            
            #navListWidget::item:selected {
                background-color: #d0d0d0;
            }
            
            #navListWidget::item:hover:!selected {
                background-color: rgba(0, 0, 0, 0.05);
            }
            
            #rightWidget {
                background-color: #f5f5f5;
                border-bottom-right-radius: 10px;
                color: #333333;
            }
            
            #contentStack {
                background-color: transparent;
                border: none;
            }
            
            QLabel {
                color: #333333;
            }
            
            QPushButton {
                background-color: #e0e0e0;
                color: #333333;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
            }
            
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            
            #saveButton {
                background-color: #0066cc;
                color: white;
            }
            
            #saveButton:hover {
                background-color: #0055bb;
            }
            
            QCheckBox {
                color: #333333;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 1px solid #b0b0b0;
                background: #ffffff;
            }
            
            QCheckBox::indicator:checked {
                background: #0066cc;
                border: 1px solid #0066cc;
            }
            
            QComboBox, QSpinBox {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                padding: 5px;
            }
            
            QLineEdit {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                padding: 5px;
            }
            
            QGroupBox {
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                margin-top: 1.5ex;
                color: #333333;
                font-weight: bold;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            
            #settingsGroup {
                padding: 10px;
            }
            
            #smallerButton, #largerButton {
                font-size: 16px;
                font-weight: bold;
                padding: 0;
            }
            
            #logoLabel {
                color: #333333;
                font-size: 24px;
            }
            
            #versionLabel {
                color: #666666;
                font-size: 12px;
            }
            
            #descLabel {
                color: #333333;
                font-size: 14px;
                margin: 10px;
            }
            
            #copyrightLabel {
                color: #666666;
                font-size: 12px;
            }
            
            #linkButton {
                background-color: transparent;
                color: #0066cc;
                text-decoration: underline;
                border: none;
            }
            
            #linkButton:hover {
                color: #0055bb;
            }
        """)

    def refreshFontPreview(self):
        """刷新字体预览显示"""
        try:
            # 获取当前字体设置
            fontSettings = self.settings["editor"]["font"]
            fontFamily = fontSettings.get("family", "Consolas")
            fontSize = fontSettings.get("size", 15)
            
            fontStyle = fontSettings.get("style", {})
            bold = fontStyle.get("bold", False)
            italic = fontStyle.get("italic", False)
            
            # 创建字体对象
            font = QFont(fontFamily, fontSize)
            font.setBold(bold)
            font.setItalic(italic)
            
            # 使用样式表强制应用字体
            self.fontPreviewLabel.setStyleSheet(f"""
                padding: 8px;
                font-family: "{fontFamily}";
                font-size: {fontSize}pt;
                font-weight: {700 if bold else 400};
                font-style: {("italic" if italic else "normal")};
            """)
            
            # 同时也设置字体对象
            self.fontPreviewLabel.setFont(font)
            
            # 更新文本以强制重新渲染
            currentText = self.fontPreviewLabel.text()
            self.fontPreviewLabel.setText("")
            self.fontPreviewLabel.setText(currentText)
            
            # 强制更新
            self.fontPreviewLabel.update()
            self.fontPreviewLabel.repaint()
            
            # 更新界面
            QApplication.processEvents()
            
            print(f"字体已更新: {fontFamily}, {fontSize}pt, 粗体={bold}, 斜体={italic}")
        except Exception as e:
            print(f"刷新字体预览时出错: {e}")

    def showEvent(self, event):
        """当对话框显示时调用"""
        super().showEvent(event)
        # 显示时刷新字体预览
        self.refreshFontPreview()

# 主题设置对话框
class ThemeSettingsDialog(QDialog):
    themeChanged = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        # 设置无焦点策略
        self.setFocusPolicy(Qt.NoFocus)
        
        # 尝试获取父窗口的主题管理器
        if hasattr(parent, 'themeManager'):
            self.themeManager = parent.themeManager
        # 如果没有主题管理器，尝试导入并创建一个
        else:
            try:
                from Aya_Hanabi.Hanabi_Core.ThemeManager import ThemeManager
                self.themeManager = ThemeManager()
                self.themeManager.load_themes_from_directory()
            except ImportError:
                print("无法导入ThemeManager，使用默认主题")
                self.themeManager = None
        
        self.setWindowTitle("主题设置")
        self.setMinimumSize(800, 500)
        
        # 应用样式
        self.applyStyle()
        
        # 初始化主题
        self.currentTheme = "dark"
        if self.themeManager:
            self.currentTheme = self.themeManager.current_theme_name
        
        self.initUI()
        
    def initUI(self):
        # 主布局
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)
        
        # 标题栏
        titleBar = QWidget()
        titleBar.setObjectName("titleBar")
        titleBar.setFixedHeight(50)
        titleBarLayout = QHBoxLayout(titleBar)
        titleBarLayout.setContentsMargins(20, 0, 20, 0)
        
        titleLabel = QLabel("主题设置")
        titleLabel.setObjectName("titleLabel")
        titleLabel.setFont(QFont("", 16, QFont.Bold))
        
        titleBarLayout.addWidget(titleLabel)
        
        mainLayout.addWidget(titleBar)
        
        # 内容区域
        contentWidget = QWidget()
        contentWidget.setObjectName("contentWidget")
        contentLayout = QVBoxLayout(contentWidget)
        contentLayout.setContentsMargins(20, 20, 20, 20)
        
        # 主题选择区域
        themeSelectorLabel = QLabel("选择主题")
        themeSelectorLabel.setFocusPolicy(Qt.NoFocus)
        themeSelectorLabel.setFont(QFont("", 14))
        contentLayout.addWidget(themeSelectorLabel)
        
        # 主题预览区
        themesContainer = QWidget()
        themesContainer.setFocusPolicy(Qt.NoFocus)
        themesLayout = QGridLayout(themesContainer)
        themesLayout.setContentsMargins(0, 10, 0, 10)
        themesLayout.setSpacing(20)
        
        self.themeCards = []
        
        if self.themeManager:
            try:
                themes = self.themeManager.get_all_themes()
                for i, (theme_name, display_name) in enumerate(themes):
                    card = self.createThemeCard(theme_name, display_name)
                    self.themeCards.append(card)
                    row, col = divmod(i, 3)
                    themesLayout.addWidget(card, row, col)
            except Exception as e:
                print(f"创建主题卡片时出错: {str(e)}")
                # 添加默认主题卡片
                self.addDefaultThemeCards(themesLayout)
        else:
            # 添加默认主题卡片
            self.addDefaultThemeCards(themesLayout)
        
        # 包装在滚动区域中
        scrollArea = QScrollArea()
        scrollArea.setFocusPolicy(Qt.NoFocus)
        scrollArea.setObjectName("themeScrollArea")
        scrollArea.setWidgetResizable(True)
        scrollArea.setFrameShape(QFrame.NoFrame)
        scrollArea.setWidget(themesContainer)
        
        contentLayout.addWidget(scrollArea, 1)
        
        # 底部按钮区域
        buttonWidget = QWidget()
        buttonWidget.setFocusPolicy(Qt.NoFocus)
        buttonWidget.setObjectName("buttonWidget")
        buttonLayout = QHBoxLayout(buttonWidget)
        
        self.importButton = NoFocusButton("导入主题")
        self.importButton.setObjectName("importButton")
        
        self.closeButton = NoFocusButton("关闭")
        self.closeButton.setObjectName("closeButton")
        
        buttonLayout.addWidget(self.importButton)
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(self.closeButton)
        
        contentLayout.addWidget(buttonWidget)
        
        mainLayout.addWidget(contentWidget, 1)
        
        # 连接信号
        self.closeButton.clicked.connect(self.accept)
        self.importButton.clicked.connect(self.importTheme)
        
        # 应用样式
        self.applyStyle()
        
    def addDefaultThemeCards(self, layout):
        # 添加默认的三个主题卡片
        darkCard = self.createThemeCard("dark", "暗色主题")
        lightCard = self.createThemeCard("light", "亮色主题")
        blueCard = self.createThemeCard("blue", "海蓝主题")
        
        self.themeCards.append(darkCard)
        self.themeCards.append(lightCard)
        self.themeCards.append(blueCard)
        
        layout.addWidget(darkCard, 0, 0)
        layout.addWidget(lightCard, 0, 1)
        layout.addWidget(blueCard, 0, 2)
    
    def createThemeCard(self, themeName, displayName):
        card = QFrame()
        card.setObjectName(f"themeCard_{themeName}")
        card.setFixedSize(220, 180)
        card.setCursor(Qt.PointingHandCursor)
        card.setProperty("themeName", themeName)
        card.setFocusPolicy(Qt.NoFocus)
        
        # 根据主题名称设置卡片样式
        if themeName == "dark":
            bg_color = "#1e2128"
            title_bar_color = "#1e2128"
            icon_bg_color = "#303540"
            icon_color = "#6b9fff"
            text_color = "#e0e5ec"
            editor_bg = "#1e2128"
            editor_text = "#e0e0e0"
            border_color = "#6b9fff"
            
            card.setStyleSheet(f"""
                #themeCard_dark {{
                background-color: {bg_color};
                border: 2px solid transparent;
                border-radius: 10px;
                }}
                #themeCard_dark:hover {{
                border-color: {border_color};
                }}
                #themePreview_dark {{
                background-color: {bg_color};
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                }}
                #themeTitle_dark, #themeDesc_dark {{
                color: {text_color};
                }}
                #previewTitleBar_dark {{
                background-color: {title_bar_color};
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                }}
                #previewIcon_dark {{
                background-color: {icon_bg_color};
                border-radius: 6px;
                color: {icon_color};
                }}
                #previewEditor_dark {{
                background-color: {editor_bg};
                color: {editor_text};
                border: none;
                border-bottom-left-radius: 4px;
                border-bottom-right-radius: 4px;
                }}
            """)
            if themeName == self.currentTheme:
                card.setStyleSheet(card.styleSheet() + f"""
                    #themeCard_dark {{
                    border-color: {border_color};
                    }}
                """)
        elif themeName == "light":
            bg_color = "#f5f5f5"
            title_bar_color = "#f5f5f5"
            icon_bg_color = "#e0e0e0"
            icon_color = "#333333"
            text_color = "#333333"
            editor_bg = "#ffffff"
            editor_text = "#333333"
            border_color = "#666666"
            
            card.setStyleSheet(f"""
                #themeCard_light {{
                background-color: {bg_color};
                border: 2px solid transparent;
                border-radius: 10px;
                }}
                #themeCard_light:hover {{
                border-color: {border_color};
                }}
                #themePreview_light {{
                background-color: {bg_color};
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                }}
                #themeTitle_light, #themeDesc_light {{
                color: {text_color};
                }}
                #previewTitleBar_light {{
                background-color: {title_bar_color};
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                }}
                #previewIcon_light {{
                background-color: {icon_bg_color};
                border-radius: 6px;
                color: {icon_color};
                }}
                #previewEditor_light {{
                background-color: {editor_bg};
                color: {editor_text};
                border: none;
                border-bottom-left-radius: 4px;
                border-bottom-right-radius: 4px;
                }}
            """)
            if themeName == self.currentTheme:
                card.setStyleSheet(card.styleSheet() + f"""
                    #themeCard_light {{
                    border-color: {border_color};
                    }}
                """)
        elif themeName == "blue":
            bg_color = "#0d2b45"
            title_bar_color = "#0d2b45"
            icon_bg_color = "#1d3e5c"
            icon_color = "#76c5ff"
            text_color = "#e0f0ff"
            editor_bg = "#0d2b45"
            editor_text = "#e0f0ff"
            border_color = "#76c5ff"
            
            card.setStyleSheet(f"""
                #themeCard_blue {{
                background-color: {bg_color};
                border: 2px solid transparent;
                border-radius: 10px;
                }}
                #themeCard_blue:hover {{
                border-color: {border_color};
                }}
                #themePreview_blue {{
                background-color: {bg_color};
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                }}
                #themeTitle_blue, #themeDesc_blue {{
                color: {text_color};
                }}
                #previewTitleBar_blue {{
                background-color: {title_bar_color};
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                }}
                #previewIcon_blue {{
                background-color: {icon_bg_color};
                border-radius: 6px;
                color: {icon_color};
                }}
                #previewEditor_blue {{
                background-color: {editor_bg};
                color: {editor_text};
                border: none;
                border-bottom-left-radius: 4px;
                border-bottom-right-radius: 4px;
                }}
            """)
            if themeName == self.currentTheme:
                card.setStyleSheet(card.styleSheet() + f"""
                    #themeCard_blue {{
                    border-color: {border_color};
                    }}
                """)
        else:
            # 自定义主题的默认样式
            bg_color = "#252932"
            title_bar_color = "#252932"
            icon_bg_color = "#303540"
            icon_color = "#6b9fff"
            text_color = "#e0e5ec"
            editor_bg = "#1e2128"
            editor_text = "#e0e0e0"
            border_color = "#6b9fff"
            
            # 尝试从主题管理器中获取实际颜色
            if self.themeManager and self.themeManager.themes.get(themeName):
                theme = self.themeManager.themes.get(themeName)
                if hasattr(theme, 'get'):
                    bg_color = theme.get("window.background", bg_color)
                    title_bar_color = theme.get("title_bar.background", title_bar_color)
                    icon_bg_color = theme.get("title_bar.icon_bg", icon_bg_color)
                    icon_color = theme.get("title_bar.icon_color", icon_color)
                    text_color = theme.get("title_bar.text_color", text_color)
                    editor_bg = theme.get("editor.background", editor_bg)
                    editor_text = theme.get("editor.text_color", editor_text)
                    border_color = icon_color # 使用图标颜色作为边框颜色
            
            card.setStyleSheet(f"""
                #themeCard_{themeName} {{
                background-color: {bg_color};
                border: 2px solid transparent;
                border-radius: 10px;
                }}
                #themeCard_{themeName}:hover {{
                border-color: {border_color};
                }}
                #themePreview_{themeName} {{
                background-color: {bg_color};
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                }}
                #themeTitle_{themeName}, #themeDesc_{themeName} {{
                color: {text_color};
                }}
                #previewTitleBar_{themeName} {{
                background-color: {title_bar_color};
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                }}
                #previewIcon_{themeName} {{
                background-color: {icon_bg_color};
                border-radius: 6px;
                color: {icon_color};
                }}
                #previewEditor_{themeName} {{
                background-color: {editor_bg};
                color: {editor_text};
                border: none;
                border-bottom-left-radius: 4px;
                border-bottom-right-radius: 4px;
                }}
            """)
            if themeName == self.currentTheme:
                card.setStyleSheet(card.styleSheet() + f"""
                    #themeCard_{themeName} {{
                    border-color: {border_color};
                    }}
                """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 10)
        layout.setSpacing(5)
        
        # 主题预览区
        previewWidget = QWidget()
        previewWidget.setFocusPolicy(Qt.NoFocus)
        previewWidget.setObjectName(f"themePreview_{themeName}")
        previewWidget.setFixedHeight(110)
        previewLayout = QVBoxLayout(previewWidget)
        previewLayout.setContentsMargins(10, 10, 10, 10)
        previewLayout.setSpacing(0)
        
        # 创建一个模拟的窗口预览
        # 标题栏
        titleBar = QWidget()
        titleBar.setFocusPolicy(Qt.NoFocus)
        titleBar.setObjectName(f"previewTitleBar_{themeName}")
        titleBar.setFixedHeight(22)
        titleBarLayout = QHBoxLayout(titleBar)
        titleBarLayout.setContentsMargins(8, 4, 8, 4)
        titleBarLayout.setSpacing(5)
        
        # 图标
        iconWidget = QLabel("H")
        iconWidget.setFocusPolicy(Qt.NoFocus)
        iconWidget.setObjectName(f"previewIcon_{themeName}")
        iconWidget.setFixedSize(14, 14)
        iconWidget.setAlignment(Qt.AlignCenter)
        iconWidget.setFont(QFont("", 8, QFont.Bold))
        
        titleBarLayout.addWidget(iconWidget)
        titleBarLayout.addWidget(QLabel("花火笔记"))
        titleBarLayout.addStretch(1)
        
        # 添加窗口控制按钮模拟
        controlsContainer = QWidget()
        controlsContainer.setFocusPolicy(Qt.NoFocus)
        controlsLayout = QHBoxLayout(controlsContainer)
        controlsLayout.setContentsMargins(0, 0, 0, 0)
        controlsLayout.setSpacing(4)
        
        for symbol in ["−", "□", "×"]:
            btn = QLabel(symbol)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.setFixedSize(12, 12)
            btn.setAlignment(Qt.AlignCenter)
            if symbol == "×":
                btn.setStyleSheet(f"color: {'#e81123' if themeName == self.currentTheme else 'gray'};")
            controlsLayout.addWidget(btn)
        
        titleBarLayout.addWidget(controlsContainer)
        
        # 模拟的编辑器
        editorWidget = QLabel()
        editorWidget.setFocusPolicy(Qt.NoFocus)
        editorWidget.setObjectName(f"previewEditor_{themeName}")
        editorWidget.setWordWrap(True)
        editorWidget.setText("# 标题\n这是一段示例文本\n- 列表项1\n- 列表项2")
        
        # 添加到预览布局
        previewLayout.addWidget(titleBar)
        previewLayout.addWidget(editorWidget, 1)
        
        layout.addWidget(previewWidget)
        
        # 主题标题和描述
        infoWidget = QWidget()
        infoWidget.setFocusPolicy(Qt.NoFocus)
        infoLayout = QVBoxLayout(infoWidget)
        infoLayout.setContentsMargins(10, 0, 10, 0)
        infoLayout.setSpacing(2)
        
        titleLabel = QLabel(displayName)
        titleLabel.setFocusPolicy(Qt.NoFocus)
        titleLabel.setObjectName(f"themeTitle_{themeName}")
        titleLabel.setFont(QFont("", 12, QFont.Bold))
        
        descLabel = QLabel("点击应用此主题")
        descLabel.setFocusPolicy(Qt.NoFocus)
        descLabel.setObjectName(f"themeDesc_{themeName}")
        descLabel.setFont(QFont("", 10))
        
        infoLayout.addWidget(titleLabel)
        infoLayout.addWidget(descLabel)
        
        layout.addWidget(infoWidget)
        
        # 添加点击事件
        card.mousePressEvent = lambda event, tn=themeName: self.onThemeCardClicked(tn)
        
        return card
    
    def onThemeCardClicked(self, themeName):
        if self.themeManager and themeName != self.currentTheme:
            try:
                self.themeManager.set_theme(themeName)
                self.currentTheme = themeName
                
                # 更新卡片选中状态
                for card in self.themeCards:
                    card_theme = card.property("themeName")
                    if card_theme == themeName:
                        # 选中状态
                        card.setStyleSheet(card.styleSheet().replace("border: 2px solid transparent", f"border: 2px solid {'#2196f3' if themeName == 'light' else '#76c5ff' if themeName == 'blue' else '#6b9fff'}"))
                    else:
                        # 非选中状态
                        card.setStyleSheet(card.styleSheet().replace(f"border: 2px solid {'#2196f3' if card_theme == 'light' else '#76c5ff' if card_theme == 'blue' else '#6b9fff'}", "border: 2px solid transparent"))
                
                # 发出主题变更信号
                self.themeChanged.emit(themeName)
            except Exception as e:
                print(f"应用主题时出错: {str(e)}")
    
    def importTheme(self):
        # 打开文件选择对话框
        filePath, _ = QFileDialog.getOpenFileName(
            self,
            "选择主题文件",
            "",
            "JSON文件 (.json)"
        )
        
        if not filePath:
            return
            
        try:
            # 读取主题文件
            with open(filePath, 'r', encoding='utf-8') as f:
                theme_data = json.load(f)
                
            # 检查基本结构
            if not isinstance(theme_data, dict) or "name" not in theme_data:
                warning(self, "导入错误", "无效的主题文件格式")
                return
                
            # 获取主题名称
            theme_name = theme_data.get("name")
            display_name = theme_data.get("display_name", theme_name)
            
            # 检查是否已存在同名主题
            if self.themeManager and theme_name in [theme[0] for theme in self.themeManager.get_all_themes()]:
                reply = question(
                    self, "主题已存在", f"主题 '{display_name}' 已存在。是否替换?", HanabiMessageBox.YesNo)
                
                if reply != HanabiMessageBox.Yes_Result:
                    return
            
            # 导入主题
            if self.themeManager:
                from Aya_Hanabi.Hanabi_Core.ThemeManager import Theme
                
                # 创建主题对象
                theme = Theme(theme_name, theme_data)
                
                # 添加到主题管理器
                self.themeManager.add_theme(theme)
                
                # 保存到文件
                self.themeManager.save_theme(theme)
                
                # 刷新主题卡片显示
                self.refreshThemeCards()
                
                information(self, "导入成功", f"主题 '{display_name}' 已成功导入")
            else:
                warning(self, "导入失败", "主题管理器不可用")
        except Exception as e:
            critical(self, "导入错误", f"导入主题时出错: {str(e)}")
            
    def refreshThemeCards(self):
        if not self.themeManager:
            return
            
        # 清除现有卡片
        for card in self.themeCards:
            card.setParent(None)
            card.deleteLater()
            
        self.themeCards = []
        
        # 重新获取主题列表
        try:
            # 找到装主题卡片的容器
            scrollArea = self.findChild(QScrollArea, "themeScrollArea")
            if not scrollArea:
                return
                
            themesContainer = scrollArea.widget()
            if not themesContainer:
                return
                
            # 清除旧布局
            if themesContainer.layout():
                QWidget().setLayout(themesContainer.layout())
                
            # 创建新布局
            themesLayout = QGridLayout(themesContainer)
            themesLayout.setContentsMargins(0, 10, 0, 10)
            themesLayout.setSpacing(20)
            
            # 添加主题卡片
            themes = self.themeManager.get_all_themes()
            for i, (theme_name, display_name) in enumerate(themes):
                card = self.createThemeCard(theme_name, display_name)
                self.themeCards.append(card)
                row, col = divmod(i, 3)
                themesLayout.addWidget(card, row, col)
        except Exception as e:
            print(f"刷新主题卡片时出错: {str(e)}")
    
    def applyStyle(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
                border-radius: 10px;
            }
            
            #titleBar {
                background-color: #e8e8e8;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
            
            #titleLabel {
                color: #333333;
            }
            
            #contentWidget {
                background-color: #f5f5f5;
            }
            
            #navWidget {
                background-color: #e8e8e8;
                border-top-right-radius: 0px;
                border-bottom-left-radius: 10px;
            }
            
            #navListWidget {
                background-color: transparent;
                color: #333333;
                font-size: 14px;
            }
            
            #navListWidget::item {
                padding: 10px;
                border-radius: 5px;
            }
            
            #navListWidget::item:selected {
                background-color: #d0d0d0;
            }
            
            #navListWidget::item:hover:!selected {
                background-color: rgba(0, 0, 0, 0.05);
            }
            
            #rightWidget {
                background-color: #f5f5f5;
                border-bottom-right-radius: 10px;
                color: #333333;
            }
            
            #contentStack {
                background-color: transparent;
                border: none;
            }
            
            QLabel {
                color: #333333;
            }
            
            QPushButton {
                background-color: #e0e0e0;
                color: #333333;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
            }
            
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            
            #saveButton {
                background-color: #0066cc;
                color: white;
            }
            
            #saveButton:hover {
                background-color: #0055bb;
            }
            
            QCheckBox {
                color: #333333;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 1px solid #b0b0b0;
                background: #ffffff;
            }
            
            QCheckBox::indicator:checked {
                background: #0066cc;
                border: 1px solid #0066cc;
            }
            
            QComboBox, QSpinBox {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                padding: 5px;
            }
            
            QLineEdit {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                padding: 5px;
            }
            
            QGroupBox {
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                margin-top: 1.5ex;
                color: #333333;
                font-weight: bold;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            
            #settingsGroup {
                padding: 10px;
            }
            
            #smallerButton, #largerButton {
                font-size: 16px;
                font-weight: bold;
                padding: 0;
            }
            
            #logoLabel {
                color: #333333;
                font-size: 24px;
            }
            
            #versionLabel {
                color: #666666;
                font-size: 12px;
            }
            
            #descLabel {
                color: #333333;
                font-size: 14px;
                margin: 10px;
            }
            
            #copyrightLabel {
                color: #666666;
                font-size: 12px;
            }
            
            #linkButton {
                background-color: transparent;
                color: #0066cc;
                text-decoration: underline;
                border: none;
            }
            
            #linkButton:hover {
                color: #0055bb;
            }
        """)

from PySide6.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication([])
    settingsDialog = SettingsDialog()
    settingsDialog.show()
    app.exec()

