import os
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox, QFontComboBox,
                             QSpinBox, QListWidget, QListWidgetItem, QFrame,
                             QSplitter, QTextEdit, QScrollArea, QWidget, QCheckBox,
                             QFileDialog, QApplication)
from PySide6.QtGui import QFont, QColor, QIcon, QFontDatabase

from .fontManager import FontManager, IconProvider

class FontPreviewDialog(QDialog):
    fontSelected = Signal(str, int, bool, bool)  # 字体名称、大小、是否加粗、是否斜体
    
    def __init__(self, parent=None, current_font=None):
        super().__init__(parent)
        
        self.setWindowTitle("字体选择器")
        self.setMinimumSize(800, 500)
        
        # 如果没有提供当前字体，使用默认字体
        if current_font is None:
            self.current_font = FontManager.get_font()
        else:
            self.current_font = current_font
            
        # 初始化字体管理器
        FontManager.init()
        
        # 预览文本
        self.preview_text = (
            "AaBbCcXxYyZz 1234567890\n"
            "林花谢了春红，太匆匆\n"
            "无奈朝来寒雨晚来风\n"
            "胭脂泪，留人醉，几时重\n"
            "自是人生长恨水长东\n"
            "花火笔记 - HanabiNotes\n"
            "TsukiNotes的第二代"
        )
        
        self.initUI()
        
    def initUI(self):
        # 主布局
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(20, 20, 20, 20)
        mainLayout.setSpacing(15)
        
        # 字体选择区域
        fontSelectionWidget = QWidget()
        fontSelectionLayout = QHBoxLayout(fontSelectionWidget)
        fontSelectionLayout.setContentsMargins(0, 0, 0, 0)
        
        # 字体下拉框
        self.fontComboBox = QFontComboBox()
        self.fontComboBox.setCurrentFont(self.current_font)
        self.fontComboBox.currentFontChanged.connect(self.updateFontPreview)
        
        # 字体大小
        self.sizeSpinBox = QSpinBox()
        self.sizeSpinBox.setRange(6, 72)
        self.sizeSpinBox.setValue(self.current_font.pointSize() if self.current_font.pointSize() else 12)
        self.sizeSpinBox.valueChanged.connect(self.updateFontPreview)
        
        # 粗体复选框
        self.boldCheckBox = QCheckBox("粗体")
        self.boldCheckBox.setChecked(self.current_font.bold())
        self.boldCheckBox.stateChanged.connect(self.updateFontPreview)
        
        # 斜体复选框
        self.italicCheckBox = QCheckBox("斜体")
        self.italicCheckBox.setChecked(self.current_font.italic())
        self.italicCheckBox.stateChanged.connect(self.updateFontPreview)
        
        # 加载自定义字体按钮
        loadFontButton = QPushButton("加载字体...")
        # 简化图标设置，避免复杂操作
        loadFontButton.clicked.connect(self.loadCustomFont)
        
        fontSelectionLayout.addWidget(QLabel("字体:"))
        fontSelectionLayout.addWidget(self.fontComboBox, 1)
        fontSelectionLayout.addWidget(QLabel("大小:"))
        fontSelectionLayout.addWidget(self.sizeSpinBox)
        fontSelectionLayout.addWidget(self.boldCheckBox)
        fontSelectionLayout.addWidget(self.italicCheckBox)
        fontSelectionLayout.addWidget(loadFontButton)
        
        # 创建分隔器和内容区域
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧分类面板
        leftPanelWidget = QWidget()
        leftPanelLayout = QVBoxLayout(leftPanelWidget)
        leftPanelLayout.setContentsMargins(0, 0, 0, 0)
        
        # 字体分类标签
        fontCategoryLabel = QLabel("字体分类")
        fontCategoryLabel.setAlignment(Qt.AlignCenter)
        
        # 字体类别列表
        self.categoryList = QListWidget()
        self.categoryList.addItem("全部字体")
        self.categoryList.addItem("系统字体")
        self.categoryList.addItem("自定义字体")
        self.categoryList.addItem("等宽字体")
        self.categoryList.addItem("无衬线字体")
        self.categoryList.addItem("衬线字体")
        # 断开之前的连接避免初始化时触发
        try:
            self.categoryList.currentRowChanged.disconnect()
        except:
            pass
        self.categoryList.currentRowChanged.connect(self.filterFontsByCategory)
        
        leftPanelLayout.addWidget(fontCategoryLabel)
        leftPanelLayout.addWidget(self.categoryList)
        
        # 右侧预览面板
        rightPanelWidget = QWidget()
        rightPanelLayout = QVBoxLayout(rightPanelWidget)
        rightPanelLayout.setContentsMargins(0, 0, 0, 0)
        
        # 预览区域
        previewLabel = QLabel("预览")
        previewLabel.setAlignment(Qt.AlignCenter)
        
        # 使用纯文本显示，避免HTML或富文本可能导致的光标问题
        self.previewTextEdit = QTextEdit()
        self.previewTextEdit.setReadOnly(True)
        self.previewTextEdit.setPlainText(self.preview_text)
        
        rightPanelLayout.addWidget(previewLabel)
        rightPanelLayout.addWidget(self.previewTextEdit)
        
        # 添加左右面板到分隔器
        splitter.addWidget(leftPanelWidget)
        splitter.addWidget(rightPanelWidget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        
        # 底部按钮
        buttonLayout = QHBoxLayout()
        buttonLayout.setContentsMargins(0, 15, 0, 0)
        
        cancelButton = QPushButton("取消")
        cancelButton.clicked.connect(self.reject)
        
        okButton = QPushButton("确定")
        okButton.clicked.connect(self.acceptFont)
        
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(cancelButton)
        buttonLayout.addWidget(okButton)
        
        # 添加所有组件到主布局
        mainLayout.addWidget(fontSelectionWidget)
        mainLayout.addWidget(splitter, 1)
        mainLayout.addLayout(buttonLayout)
        
        # 默认选择"全部字体"类别
        self.categoryList.setCurrentRow(0)
        
        # 初始更新预览
        self.updateFontPreview()
        
    def updateFontPreview(self):
        try:
            # 获取当前选择的字体
            font = self.fontComboBox.currentFont()
            
            # 更新字体大小
            font.setPointSize(self.sizeSpinBox.value())
            
            # 更新粗体和斜体设置
            font.setBold(self.boldCheckBox.isChecked())
            font.setItalic(self.italicCheckBox.isChecked())
            
            # 获取字体属性
            fontFamily = font.family()
            fontSize = self.sizeSpinBox.value()
            bold = self.boldCheckBox.isChecked()
            italic = self.italicCheckBox.isChecked()
            
            # 使用样式表强制应用字体
            self.previewTextEdit.setStyleSheet(f"""
                font-family: "{fontFamily}";
                font-size: {fontSize}pt;
                font-weight: {700 if bold else 400};
                font-style: {("italic" if italic else "normal")};
            """)
            
            # 同时也设置字体对象
            self.previewTextEdit.setFont(font)
            
            # 保存当前滚动位置
            scrollValue = self.previewTextEdit.verticalScrollBar().value()
            
            # 清除现有内容并重新添加
            self.previewTextEdit.clear()
            self.previewTextEdit.setPlainText(self.preview_text)
            
            # 恢复滚动位置
            self.previewTextEdit.verticalScrollBar().setValue(scrollValue)
            
            # 强制刷新
            self.previewTextEdit.update()
            self.previewTextEdit.repaint()
            QApplication.processEvents()
            
            print(f"预览字体已更新: {fontFamily}, {fontSize}pt, 粗体={bold}, 斜体={italic}")
        except Exception as e:
            print(f"更新预览时出错: {str(e)}")
        
    def filterFontsByCategory(self, index):
        try:
            # 根据选择的类别过滤字体
            # 0: 全部字体
            # 1: 系统字体
            # 2: 自定义字体
            # 3: 等宽字体
            # 4: 无衬线字体
            # 5: 衬线字体
            
            # 保存当前所选字体
            current_font = self.fontComboBox.currentFont().family()
            
            # 阻止信号触发避免多次更新
            self.fontComboBox.blockSignals(True)
            
            # 清除当前字体列表
            self.fontComboBox.clear()
            
            if index == 0:  # 全部字体
                # 不过滤，显示所有字体
                all_fonts = FontManager.get_system_fonts()
                for font in all_fonts:
                    self.fontComboBox.addItem(font)
            elif index == 1:  # 系统字体
                # 移除自定义字体
                custom_fonts = FontManager.get_custom_fonts()
                for font in FontManager.get_system_fonts():
                    if font not in custom_fonts:
                        self.fontComboBox.addItem(font)
            elif index == 2:  # 自定义字体
                for font in FontManager.get_custom_fonts():
                    self.fontComboBox.addItem(font)
            elif index == 3:  # 等宽字体
                for font in FontManager.get_system_fonts():
                    # 创建一个测试用字体
                    test_font = QFont(font)
                    # 在Qt中判断是否是等宽字体的简单方法
                    if test_font.fixedPitch():
                        self.fontComboBox.addItem(font)
            elif index == 4:  # 无衬线字体
                for font in FontManager.get_system_fonts():
                    test_font = QFont(font)
                    if test_font.styleHint() == QFont.SansSerif:
                        self.fontComboBox.addItem(font)
            elif index == 5:  # 衬线字体
                for font in FontManager.get_system_fonts():
                    test_font = QFont(font)
                    if test_font.styleHint() == QFont.Serif:
                        self.fontComboBox.addItem(font)
            
            # 尝试找回之前选择的字体
            find_index = self.fontComboBox.findText(current_font)
            if find_index >= 0:
                self.fontComboBox.setCurrentIndex(find_index)
            elif self.fontComboBox.count() > 0:
                # 如果没有找到，使用第一个字体
                self.fontComboBox.setCurrentIndex(0)
            
            # 恢复信号
            self.fontComboBox.blockSignals(False)
            
            # 手动更新预览
            self.updateFontPreview()
        except Exception as e:
            print(f"过滤字体时出错: {str(e)}")
        
    def loadCustomFont(self):
        try:
            # 打开文件对话框选择字体文件
            file_paths, _ = QFileDialog.getOpenFileNames(
                self,
                "选择字体文件",
                "",
                "字体文件 (*.ttf *.otf)"
            )
            
            if not file_paths:
                return
                
            # 加载字体
            for file_path in file_paths:
                # 使用正确的QFontDatabase类
                font_id = QFontDatabase.addApplicationFont(file_path)
                if font_id != -1:
                    # 如果加载成功，获取字体族名
                    families = QFontDatabase.applicationFontFamilies(font_id)
                    if families:
                        # 添加到自定义字体列表
                        font_family = families[0]
                        FontManager._custom_fonts[font_family] = font_id
                        
            # 如果当前显示的是自定义字体类别，刷新列表
            if self.categoryList.currentRow() == 2:
                self.filterFontsByCategory(2)
            # 如果是全部字体类别，也需要刷新
            elif self.categoryList.currentRow() == 0:
                self.filterFontsByCategory(0)
        except Exception as e:
            print(f"加载自定义字体时出错: {str(e)}")
        
    def acceptFont(self):
        try:
            # 获取当前选择的字体信息
            font = self.fontComboBox.currentFont()
            family = font.family()
            size = self.sizeSpinBox.value()
            bold = self.boldCheckBox.isChecked()
            italic = self.italicCheckBox.isChecked()
            
            # 保存为默认字体
            FontManager.set_default_font(family, size)
            
            # 发出信号
            self.fontSelected.emit(family, size, bold, italic)
            
            # 关闭对话框
            self.accept()
        except Exception as e:
            print(f"接受字体选择时出错: {str(e)}") 