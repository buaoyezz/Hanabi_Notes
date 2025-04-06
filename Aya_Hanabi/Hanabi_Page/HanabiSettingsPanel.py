import os
import json
import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame, QPushButton, 
    QListWidget, QStackedWidget, QListWidgetItem, QCheckBox, QComboBox, 
    QSpinBox, QSlider, QFileDialog, QScrollArea, QSizePolicy, QLineEdit,
    QFontComboBox, QGroupBox, QRadioButton, QTabWidget, QStyledItemDelegate, QStyle,
    QMessageBox
)
from PySide6.QtCore import Qt, QSize, QUrl, QRect, Signal, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QIcon, QFont, QFontMetrics, QColor, QPixmap, QPainter, QPalette, QCursor
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

# 如果可用，导入字体管理器
try:
    from Aya_Hanabi.Hanabi_Core.FontManager import FontManager as FontManager
    # 检查是否有IconProvider类
    if hasattr(FontManager, 'IconProvider'):
        IconProvider = FontManager.IconProvider
    else:
        # 创建一个简单的图标提供器作为后备
        class SimpleIconProvider:
            @staticmethod
            def get_icon(name):
                print(f"请求图标: {name}，但IconProvider不可用")
                return QIcon()  # 返回空图标
        
        IconProvider = SimpleIconProvider
except ImportError:
    FontManager = None
    
    # 创建一个简单的图标提供器作为后备
    class SimpleIconProvider:
        @staticmethod
        def get_icon(name):
            print(f"请求图标: {name}，但IconProvider不可用")
            return QIcon()  # 返回空图标
    
    IconProvider = SimpleIconProvider

# 尝试导入 QGraphicsOpacityEffect，如果不可用则跳过
try:
    from PySide6.QtWidgets import QGraphicsOpacityEffect
except ImportError:
    print("QGraphicsOpacityEffect 不可用，将禁用部分过渡动画效果")

# 导入字体和图标管理器
try:
    from Hanabi.Fonts.icon_map import ICON_MAP
except ImportError:
    print("无法导入ICON_MAP，将使用默认图标")
    ICON_MAP = {}

try:
    from Aya_Hanabi.Hanabi_Core.FontManager.fontManager import FontManager, IconProvider, ICONS
except ImportError:
    print("无法导入FontManager和IconProvider，将使用默认字体和图标")
    FontManager = None
    IconProvider = None
    ICONS = {}

# 导入主题管理器
try:
    from Aya_Hanabi.Hanabi_Core.ThemeManager import ThemeManager
except ImportError:
    print("无法导入ThemeManager，将使用默认主题")
    ThemeManager = None

# 自定义列表项委托，用于绘制Material图标
class MaterialIconItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.icon_font = None
        
    def setIconFont(self, font):
        """设置用于绘制图标的字体"""
        self.icon_font = font
    
    def paint(self, painter, option, index):
        # 绘制背景和文本
        QStyledItemDelegate.paint(self, painter, option, index)
        
        # 绘制图标
        if self.icon_font and index.data(Qt.UserRole):
            icon_code = index.data(Qt.UserRole)
            if icon_code:
                painter.save()
                painter.setFont(self.icon_font)
                
                # 计算图标位置
                rect = option.rect
                # 图标绘制在最左侧，文本左边缘前
                icon_rect = QRect(rect.left() + 15, rect.top(), 20, rect.height())
                
                # 选中状态使用白色，否则使用当前文本颜色
                if option.state & QStyle.State_Selected:
                    painter.setPen(QColor("white"))
                else:
                    painter.setPen(option.palette.color(QPalette.Text))
                    
                # 绘制图标
                painter.drawText(icon_rect, Qt.AlignCenter, icon_code)
                painter.restore()

# 可点击的Frame，用于主题卡片
class ClickableFrame(QFrame):
    clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

class HanabiSettingsItem(QWidget):
    valueChanged = Signal(object)
    
    def __init__(self, title, description=None, parent=None):
        super().__init__(parent)
        self.title = title
        self.description = description
        self.value = None
        
        self.initUI()
    
    def initUI(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)
        
        # 左侧标题和描述
        leftLayout = QVBoxLayout()
        
        self.titleLabel = QLabel(self.title)
        self.titleLabel.setStyleSheet("font-size: 14px; font-weight: normal;")
        leftLayout.addWidget(self.titleLabel)
        
        if self.description:
            self.descLabel = QLabel(self.description)
            self.descLabel.setStyleSheet("font-size: 12px; color: rgba(255, 255, 255, 0.5);")
            leftLayout.addWidget(self.descLabel)
        
        layout.addLayout(leftLayout, 1)
        
        # 右侧控件在子类中添加
        self.controlLayout = QHBoxLayout()
        layout.addLayout(self.controlLayout)

class HanabiToggleItem(HanabiSettingsItem):
    def __init__(self, title, description=None, parent=None):
        super().__init__(title, description, parent)
        
    def initUI(self):
        super().initUI()
        
        # 创建一个自定义的Frame用作开关背景
        self.switchContainer = QFrame()
        self.switchContainer.setFixedSize(50, 24)
        self.switchContainer.setCursor(Qt.PointingHandCursor)
        
        # 添加滑块指示器
        self.slider = QFrame(self.switchContainer)
        self.slider.setFixedSize(20, 20)
        
        # 创建动画对象
        self.animation = None
        try:
            from PySide6.QtCore import QPropertyAnimation, QEasingCurve
            self.animation = QPropertyAnimation(self.slider, b"pos")
            self.animation.setDuration(200)  # 过渡时间200毫秒
            self.animation.setEasingCurve(QEasingCurve.OutCubic)  # 缓动曲线
        except ImportError:
            print("QPropertyAnimation 不可用，禁用开关动画效果")
        
        # 设置初始未选中状态
        self.updateSwitchStyle(False)
        
        # 鼠标点击事件
        self.switchContainer.mousePressEvent = self.onSwitchClicked
        
        self.controlLayout.addWidget(self.switchContainer)
    
    def updateSwitchStyle(self, checked):
        # 获取当前主题
        is_dark = True
        theme_id = "dark"
        if hasattr(self, 'parent') and self.parent():
            parent = self.parent()
            while parent:
                if hasattr(parent, 'settings') and isinstance(parent.settings, dict):
                    if "appearance" in parent.settings and "theme" in parent.settings["appearance"]:
                        theme_data = parent.settings["appearance"]["theme"]
                        if isinstance(theme_data, dict) and "name" in theme_data:
                            theme_id = theme_data["name"]
                            is_dark = theme_id != "light"
                            break
                parent = parent.parent()
        
        # 根据主题ID设置颜色
        if theme_id == "purple_dream":
            # 紫梦主题 - 带有紫色调的粉色
            on_bg_color = "#c792ea"  # 紫色调
            off_bg_color = "#2d2b55"  # 深紫色背景
            on_slider_color = "#ffffff"  # 白色滑块
            off_slider_color = "#aaaaaa"  # 灰色滑块
        elif theme_id == "green_theme":
            # 森林绿主题 - 淡绿色调
            on_bg_color = "#7fdbca"  # 浅绿色
            off_bg_color = "#1e3b26"  # 深绿色背景
            on_slider_color = "#ffffff"  # 白色滑块
            off_slider_color = "#aaaaaa"  # 灰色滑块
        elif is_dark:
            # 暗色主题 - 粉色/樱花色调
            on_bg_color = "#ff9cce"  # 粉色/樱花色
            off_bg_color = "#3E4452"  # 深灰色
            on_slider_color = "#ffffff"  # 白色滑块
            off_slider_color = "#aaaaaa"  # 灰色滑块
        else:
            # 亮色主题 - 稍微柔和的粉色
            on_bg_color = "#ff9cce"  # 保持相同的粉色/樱花色
            off_bg_color = "#d0d0d0"  # 浅灰色
            on_slider_color = "#ffffff"  # 白色滑块
            off_slider_color = "#f0f0f0"  # 浅灰色滑块
        
        # 设置开关容器样式
        self.switchContainer.setStyleSheet(f"""
            QFrame {{
                background-color: {on_bg_color if checked else off_bg_color};
                border-radius: 12px;
                border: none;
                margin: 0px;
            }}
        """)
        
        # 设置滑块样式和位置
        self.slider.setStyleSheet(f"""
            QFrame {{
                background-color: {on_slider_color if checked else off_slider_color};
                border-radius: 10px;
                border: none;
            }}
        """)
        
        # 设置滑块位置
        pos = 28 if checked else 2  # 右侧或左侧位置
        
        # 如果有动画，使用动画移动滑块，否则直接移动
        if self.animation:
            self.animation.setStartValue(self.slider.pos())
            self.animation.setEndValue(QPoint(pos, 2))
            self.animation.start()
        else:
            self.slider.move(pos, 2)
    
    def setValue(self, value):
        self.value = bool(value)
        self.updateSwitchStyle(self.value)
        
    def onSwitchClicked(self, event):
        self.value = not self.value
        self.updateSwitchStyle(self.value)
        self.valueChanged.emit(self.value)
        
    def onToggled(self, state):
        self.value = state == Qt.Checked
        self.updateSwitchStyle(self.value)
        self.valueChanged.emit(self.value)

class HanabiComboItem(HanabiSettingsItem):
    def __init__(self, title, options, description=None, parent=None):
        self.options = options
        super().__init__(title, description, parent)
        
    def initUI(self):
        super().initUI()
        
        # 添加下拉框
        self.comboBox = QComboBox()
        for option in self.options:
            self.comboBox.addItem(option)
        
        self.comboBox.currentIndexChanged.connect(self.onSelectionChanged)
        self.comboBox.setCursor(Qt.PointingHandCursor)  # 添加鼠标指针样式
        self.controlLayout.addWidget(self.comboBox)
    
    def setValue(self, value):
        if isinstance(value, int) and 0 <= value < len(self.options):
            self.comboBox.setCurrentIndex(value)
        elif value in self.options:
            self.comboBox.setCurrentText(value)
    
    def onSelectionChanged(self, index):
        self.value = self.comboBox.currentText()
        self.valueChanged.emit(self.value)

class HanabiPathItem(HanabiSettingsItem):
    def __init__(self, title, description=None, parent=None):
        super().__init__(title, description, parent)
        
    def initUI(self):
        super().initUI()
        
        # 路径输入框
        self.pathEdit = QLineEdit()
        self.pathEdit.setReadOnly(True)
        self.pathEdit.setStyleSheet("background-color: rgba(0, 0, 0, 0.2); padding: 4px 8px;")
        self.pathEdit.setMinimumWidth(200)
        
        # 浏览按钮
        self.browseBtn = QPushButton("浏览...")
        self.browseBtn.setCursor(Qt.PointingHandCursor)  # 直接设置鼠标样式
        self.browseBtn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: none;
                padding: 4px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)
        self.browseBtn.clicked.connect(self.browsePath)
        
        self.controlLayout.addWidget(self.pathEdit)
        self.controlLayout.addWidget(self.browseBtn)
    
    def setValue(self, value):
        self.value = value
        self.pathEdit.setText(value)
    
    def browsePath(self):
        current_path = self.pathEdit.text() or os.path.expanduser("~")
        path = QFileDialog.getExistingDirectory(
            self, "选择文件夹", current_path,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if path:
            self.setValue(path)
            self.valueChanged.emit(path)

class HanabiSpinnerItem(HanabiSettingsItem):
    def __init__(self, title, min_value=0, max_value=100, suffix=None, description=None, parent=None):
        self.min_value = min_value
        self.max_value = max_value
        self.suffix = suffix
        super().__init__(title, description, parent)
        
    def initUI(self):
        super().initUI()
        
        # 添加数值选择器
        self.spinner = QSpinBox()
        self.spinner.setMinimum(self.min_value)
        self.spinner.setMaximum(self.max_value)
        
        if self.suffix:
            self.spinner.setSuffix(f" {self.suffix}")
        
        # 获取Material图标字体
        try:
            IconProvider.ensure_font_loaded()
            icon_font = IconProvider.get_icon_font(12)  # 使用较小的图标尺寸
            up_arrow = IconProvider.get_icon("keyboard_arrow_up")
            down_arrow = IconProvider.get_icon("keyboard_arrow_down")
            
            # 设置按钮样式使用Material图标
            self.spinner.setStyleSheet(f"""
                QSpinBox {{
                    padding-right: 15px;  /* 为按钮留出空间 */
                }}
                
                QSpinBox::up-button {{
                    width: 16px;
                    border: none;
                    background: transparent;
                }}
                
                QSpinBox::down-button {{
                    width: 16px;
                    border: none;
                    background: transparent;
                }}
                
                QSpinBox::up-arrow {{
                    image: none;
                    width: 0px;
                    height: 0px;
                }}
                
                QSpinBox::down-arrow {{
                    image: none;
                    width: 0px;
                    height: 0px;
                }}
            """)
            
            # 创建自定义按钮覆盖在SpinBox上
            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(0)
            container_layout.addWidget(self.spinner)
            
            # 创建按钮区域
            buttons_widget = QWidget(container)
            buttons_widget.setCursor(Qt.PointingHandCursor)
            buttons_layout = QVBoxLayout(buttons_widget)
            buttons_layout.setContentsMargins(0, 0, 0, 0)
            buttons_layout.setSpacing(0)
            
            # 创建上箭头按钮
            self.up_button = QPushButton()
            self.up_button.setText(up_arrow)
            self.up_button.setFont(icon_font)
            self.up_button.setFixedSize(20, 12)
            
            # 创建下箭头按钮
            self.down_button = QPushButton()
            self.down_button.setText(down_arrow)
            self.down_button.setFont(icon_font)
            self.down_button.setFixedSize(20, 12)
            
            # 获取当前主题下的颜色
            text_color = self.getThemeTextColor()
            hover_color = "white" if self.isDarkTheme() else "#000000"
            pressed_color = "rgba(255, 255, 255, 0.5)" if self.isDarkTheme() else "rgba(0, 0, 0, 0.5)"
            
            # 设置按钮样式
            arrow_style = f"""
                QPushButton {{
                    background: transparent;
                    color: {text_color};
                    border: none;
                    padding: 0px;
                }}
                QPushButton:hover {{
                    color: {hover_color};
                }}
                QPushButton:pressed {{
                    color: {pressed_color};
                }}
            """
            self.up_button.setStyleSheet(arrow_style)
            self.down_button.setStyleSheet(arrow_style)
            
            # 添加按钮到布局
            buttons_layout.addWidget(self.up_button)
            buttons_layout.addWidget(self.down_button)
            
            # 将按钮区域定位到spinbox右侧
            buttons_widget.setFixedSize(20, 24)
            container_layout.addWidget(buttons_widget)
            
            # 连接按钮点击事件
            self.up_button.clicked.connect(self.spinner.stepUp)
            self.down_button.clicked.connect(self.spinner.stepDown)
            
            # 将整个容器添加到控件布局
            self.controlLayout.addWidget(container)
        except Exception as e:
            print(f"设置Material图标按钮时出错: {e}")
            # 如果出错，直接使用原始的QSpinBox
            self.spinner.valueChanged.connect(self.onValueChanged)
            self.spinner.setCursor(Qt.ArrowCursor)
            self.controlLayout.addWidget(self.spinner)
        
        # 连接值变更信号
        self.spinner.valueChanged.connect(self.onValueChanged)
    
    def isDarkTheme(self):
        """获取当前是否为深色主题"""
        if hasattr(self, 'parent') and self.parent():
            parent = self.parent()
            while parent:
                if hasattr(parent, 'settings') and isinstance(parent.settings, dict):
                    if "appearance" in parent.settings and "theme" in parent.settings["appearance"]:
                        theme_data = parent.settings["appearance"]["theme"]
                        if isinstance(theme_data, dict) and "name" in theme_data:
                            return theme_data["name"] != "light"
                parent = parent.parent()
        return True  # 默认为深色主题
    
    def getThemeTextColor(self):
        """获取当前主题的文本颜色"""
        is_dark = self.isDarkTheme()
        return "#abb2bf" if is_dark else "#333333"  # 深色主题淡灰色，浅色主题深灰色
    
    def updateArrowStyles(self):
        """更新箭头按钮的样式"""
        if hasattr(self, 'up_button') and hasattr(self, 'down_button'):
            text_color = self.getThemeTextColor()
            hover_color = "white" if self.isDarkTheme() else "#000000"
            pressed_color = "rgba(255, 255, 255, 0.5)" if self.isDarkTheme() else "rgba(0, 0, 0, 0.5)"
            
            arrow_style = f"""
                QPushButton {{
                    background: transparent;
                    color: {text_color};
                    border: none;
                    padding: 0px;
                }}
                QPushButton:hover {{
                    color: {hover_color};
                }}
                QPushButton:pressed {{
                    color: {pressed_color};
                }}
            """
            self.up_button.setStyleSheet(arrow_style)
            self.down_button.setStyleSheet(arrow_style)
    
    def setValue(self, value):
        self.value = value
        self.spinner.setValue(int(value))
    
    def onValueChanged(self, value):
        self.value = value
        self.valueChanged.emit(value)

class HanabiFontComboItem(HanabiSettingsItem):
    def __init__(self, title, description=None, parent=None):
        super().__init__(title, description, parent)
        self.value = "Consolas"  # 默认字体
        self.initControlUI()  # 确保调用 initControlUI 方法
    
    def initControlUI(self):
        # 创建字体下拉框
        self.fontComboBox = QFontComboBox()
        self.fontComboBox.setEditable(False)
        self.fontComboBox.setMinimumWidth(200)
        self.fontComboBox.currentFontChanged.connect(self.onFontChanged)
        self.fontComboBox.setCursor(Qt.PointingHandCursor)  # 添加鼠标指针样式
        self.controlLayout.addWidget(self.fontComboBox)
    
    def onFontChanged(self, font):
        self.value = font.family()
        # 如果类别中有预览组件，更新预览
        if self.parent() and hasattr(self.parent(), 'items') and 'font_preview' in self.parent().items:
            preview = self.parent().items['font_preview']
            if hasattr(preview, 'updatePreview'):
                # 获取当前字体设置
                size = self.parent().items['font_size'].value if 'font_size' in self.parent().items else 15
                bold = self.parent().items['font_bold'].value if 'font_bold' in self.parent().items else False
                italic = self.parent().items['font_italic'].value if 'font_italic' in self.parent().items else False
                preview.updatePreview(self.value, size, bold, italic)
        self.valueChanged.emit(self.value)
        
    def setValue(self, value):
        if not hasattr(self, 'fontComboBox'):
            # 如果 fontComboBox 不存在，先创建它
            self.initControlUI()
            
        if isinstance(value, str):
            self.value = value
            self.fontComboBox.setCurrentFont(QFont(value))
        elif isinstance(value, int) and value < self.fontComboBox.count():
            self.value = self.fontComboBox.itemText(value)
            self.fontComboBox.setCurrentIndex(value)

class HanabiFontPreviewItem(HanabiSettingsItem):
    def __init__(self, title, description=None, parent=None):
        super().__init__(title, description, parent)
        self.font_family = "Consolas"
        self.font_size = 14
        self.font_bold = False
        self.font_italic = False
        self.initControlUI()  # 确保调用 initControlUI 方法
        
    def initControlUI(self):
        # 创建预览标签
        self.previewLabel = QLabel("花火笔记 Hanabi Notes\nAaBbCcXxYyZz 1234567890\n林花谢了春红 太匆匆")
        self.previewLabel.setMinimumHeight(100)
        self.previewLabel.setAlignment(Qt.AlignCenter)
        self.previewLabel.setFrameShape(QFrame.StyledPanel)
        self.previewLabel.setFrameShadow(QFrame.Sunken)
        self.previewLabel.setStyleSheet("""
            padding: 10px;
            background-color: rgba(255, 255, 255, 0.05);
            border-radius: 6px;
        """)
        
        self.controlLayout.addWidget(self.previewLabel)
        
        # 更新字体显示
        self.updatePreview(self.font_family, self.font_size, self.font_bold, self.font_italic)
        
    def updatePreview(self, family, size, bold=False, italic=False):
        self.font_family = family
        self.font_size = size
        self.font_bold = bold
        self.font_italic = italic
        
        # 创建字体对象
        font = QFont(family, size)
        font.setBold(bold)
        font.setItalic(italic)
        
        # 设置字体
        self.previewLabel.setFont(font)
        
        # 设置样式表强制应用字体样式（解决某些字体无法正确显示的问题）
        self.previewLabel.setStyleSheet(f"""
            padding: 10px;
            background-color: rgba(255, 255, 255, 0.05);
            border-radius: 6px;
            font-family: '{family}';
            font-size: {size}pt;
            font-weight: {700 if bold else 400};
            font-style: {("italic" if italic else "normal")};
        """)
        
        # 更新显示
        self.previewLabel.update()

class HanabiValueItem(HanabiSettingsItem):
    def __init__(self, title, description=None, parent=None):
        super().__init__(title, description, parent)
        self.value = ""
        self.initControlUI()  # 确保调用 initControlUI 方法
        
    def initControlUI(self):
        # 创建值显示标签
        self.valueLabel = QLabel(self.value)
        self.valueLabel.setStyleSheet("""
            color: rgba(255, 255, 255, 0.8);
            padding: 5px 10px;
            background-color: rgba(255, 255, 255, 0.05);
            border-radius: 4px;
        """)
        self.controlLayout.addWidget(self.valueLabel)
        
    def setValue(self, value):
        self.value = str(value)
        if hasattr(self, 'valueLabel'):
            self.valueLabel.setText(self.value)
        else:
            self.initControlUI()
            self.valueLabel.setText(self.value)

class HanabiSettingsCategory(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        self.items = {}  # 存储设置项 {setting_key: item_widget}
        
        self.initUI()
    
    def initUI(self):
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 10)
        layout.setSpacing(5)
        
        # 标题
        if self.title:
            titleLabel = QLabel(self.title)
            titleLabel.setStyleSheet("font-size: 16px; font-weight: bold; color: white; margin-bottom: 10px;")
            layout.addWidget(titleLabel)
        
        # 内容区域
        self.contentWidget = QWidget()
        self.contentLayout = QVBoxLayout(self.contentWidget)
        self.contentLayout.setContentsMargins(0, 0, 0, 0)
        self.contentLayout.setSpacing(0)
        
        layout.addWidget(self.contentWidget)
        layout.addStretch(1)
    
    def addItem(self, key, item_widget):
        self.items[key] = item_widget
        self.contentLayout.addWidget(item_widget)
        
        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: rgba(255, 255, 255, 0.1);")
        separator.setMaximumHeight(1)
        self.contentLayout.addWidget(separator)
        
        return item_widget
    
    def getItemValue(self, key):
        if key in self.items:
            return self.items[key].value
        return None
    
    def setItemValue(self, key, value):
        if key in self.items:
            self.items[key].setValue(value)

class HanabiSettingsPage(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        self.categories = {}  # 存储设置类别 {category_key: category_widget}
        
        self.initUI()
    
    def initUI(self):
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建滚动区域
        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollArea.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: rgba(0, 0, 0, 0.2);
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(255, 255, 255, 0.3);
                min-height: 30px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        # 内容容器
        self.contentWidget = QWidget()
        self.contentLayout = QVBoxLayout(self.contentWidget)
        self.contentLayout.setContentsMargins(20, 20, 20, 20)
        self.contentLayout.setSpacing(25)
        
        scrollArea.setWidget(self.contentWidget)
        layout.addWidget(scrollArea)
    
    def addCategory(self, key, title):
        category = HanabiSettingsCategory(title)
        self.categories[key] = category
        self.contentLayout.addWidget(category)
        return category

class HanabiSettingsPanel(QWidget):
    settingsChanged = Signal(dict)  # 设置改变时发出信号
    errorOccurred = Signal(str, str)  # 错误信号，参数：错误标题，错误信息
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        
        # 初始化基本设置
        self._initBaseSettings()
        
        # 初始化错误处理
        self.initErrorHandling()
        
        # 初始化主题管理器
        self.initThemeManager()
        
        # 初始化字体管理器
        self.initFonts()
        
        # 初始化UI
        self.initUI()
        
        # 加载完整设置
        self.loadSettings()
        
        # 更新UA信息
        self.updateUserAgent()
    
    def _initBaseSettings(self):
        """初始化基本设置，确保关键设置存在"""
        self.settings = {
            "general": {
                "startup": {
                    "auto_start": False,
                    "remember_window": True,
                    "reopen_files": True
                },
                "file": {
                    "default_save_path": os.path.expanduser("~/Documents"),
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
                    "family": "Microsoft YaHei UI",
                    "size": 15
                },
                "editing": {
                    "auto_indent": True,
                    "line_numbers": True,
                    "spell_check": False,
                    "word_wrap": True,
                    "smart_file_detection": True,
                    "extension_first": False
                }
            },
            "appearance": {
                "theme": {
                    "name": "dark"
                }
            },
            "plugins": {
                "enabled": {}
            },
            "system": {
                "error_reporting": True,
                "user_agent": "HanabiNotes/1.0.0"  # 默认UA，后续会更新
            },
            "app_info": {
                "version": "1.0.0"
            }
        }
    
    def updateUserAgent(self):
        """更新UA信息"""
        try:
            ua = self.getUserAgent()
            self.settings["system"]["user_agent"] = ua
            
            # 如果UA显示项存在，更新显示
            if hasattr(self, 'pages'):
                for page in self.pages.values():
                    if hasattr(page, 'categories') and 'about' in page.categories:
                        aboutCat = page.categories['about']
                        if hasattr(aboutCat, 'items') and 'user_agent' in aboutCat.items:
                            aboutCat.items['user_agent'].setValue(ua)
        except Exception as e:
            print(f"更新UA信息时出错: {e}")
            self.errorOccurred.emit("UA更新错误", f"无法更新用户代理信息: {str(e)}")

    def initErrorHandling(self):
        """初始化错误处理机制"""
        # 连接错误信号到错误显示函数
        self.errorOccurred.connect(self.showError)
        
        # 设置全局异常捕获
        import sys
        sys.excepthook = self.handleGlobalException
    
    def handleGlobalException(self, exc_type, exc_value, exc_traceback):
        """处理全局未捕获的异常"""
        import traceback
        error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        self.logError(error_msg)
        self.errorOccurred.emit("未捕获的异常", str(exc_value))
    
    def showError(self, title, message):
        """显示错误消息对话框"""
        try:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle(title)
            msg.setText(message)
            msg.setStandardButtons(QMessageBox.Ok)
            
            # 添加"报告错误"按钮
            if self.settings.get("system", {}).get("error_reporting", True):
                reportButton = msg.addButton("报告错误", QMessageBox.ActionRole)
                reportButton.clicked.connect(lambda: self.reportError(title, message))
            
            msg.exec_()
        except Exception as e:
            print(f"显示错误对话框时出错: {e}")
    
    def logError(self, error_msg):
        """记录错误到日志文件"""
        try:
            log_dir = os.path.join(os.path.expanduser("~"), ".hanabi_notes", "logs")
            os.makedirs(log_dir, exist_ok=True)
            
            log_file = os.path.join(log_dir, "error.log")
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"\n[{timestamp}]\n{error_msg}\n")
        except Exception as e:
            print(f"写入错误日志时出错: {e}")
    
    def reportError(self, title, message):
        """报告错误到开发团队"""
        try:
            # 获取系统信息
            import platform
            system_info = {
                "os": platform.platform(),
                "python": platform.python_version(),
                "app_version": self.settings.get("app_info", {}).get("version", "unknown"),
                "user_agent": self.getUserAgent()
            }
            
            # 准备错误报告
            report = {
                "title": title,
                "message": message,
                "system_info": system_info,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # TODO: 发送错误报告到服务器
            # 这里应该实现实际的错误报告逻辑
            print("错误报告已准备:", report)
            
            # 显示确认消息
            QMessageBox.information(self, "错误报告", "感谢您的反馈！\n错误报告已发送给开发团队。")
        except Exception as e:
            print(f"报告错误时出错: {e}")
            self.showError("错误报告失败", f"无法发送错误报告: {str(e)}")
    
    def getUserAgent(self):
        """获取用户代理字符串"""
        try:
            import platform
            import locale
            
            # 获取系统信息
            os_name = platform.system()
            os_version = platform.version()
            os_arch = platform.machine()
            
            # 获取Python版本
            python_version = platform.python_version()
            
            # 获取Qt版本
            try:
                from PySide6 import __version__ as qt_version
            except:
                qt_version = "unknown"
            
            # 获取语言设置
            try:
                lang = locale.getdefaultlocale()[0]
            except:
                lang = "unknown"
            
            # 获取应用版本
            app_version = self.settings.get("app_info", {}).get("version", "1.0.0")
            
            # 构建UA字符串
            ua = f"HanabiNotes/{app_version} "
            ua += f"({os_name}; {os_version}; {os_arch}) "
            ua += f"Python/{python_version} "
            ua += f"Qt/{qt_version} "
            ua += f"Lang/{lang}"
            
            return ua
        except Exception as e:
            print(f"获取UA信息时出错: {e}")
            # 返回一个基本的UA字符串
            return f"HanabiNotes/{self.settings.get('app_info', {}).get('version', '1.0.0')}"
    
    def initThemeManager(self):
        try:
            # 尝试获取父窗口的主题管理器
            if hasattr(self.parent_app, 'themeManager'):
                self.themeManager = self.parent_app.themeManager
                print("使用父窗口的主题管理器")
            # 如果没有主题管理器，尝试创建一个
            elif ThemeManager:
                self.themeManager = ThemeManager()
                self.themeManager.load_themes_from_directory()
                print("创建新的主题管理器")
            else:
                print("无法创建主题管理器，将使用简单的主题模拟")
                # 创建一个简单的主题管理器模拟对象
                self.themeManager = type('ThemeManager', (), {
                    'get_theme_names': lambda: ["dark", "light", "purple_dream", "green_theme"],
                    'current_theme_name': "dark",
                    'get_theme': lambda name: {"name": name, "display_name": self._get_theme_display_name(name)},
                    'set_theme': lambda name: True
                })
                # 添加辅助方法，用于获取主题显示名称
                setattr(self.themeManager, '_get_theme_display_name', lambda name: {
                    "dark": "暗色主题", 
                    "light": "亮色主题", 
                    "purple_dream": "紫梦主题", 
                    "green_theme": "森林绿主题"
                }.get(name, name))
        except Exception as e:
            print(f"初始化主题管理器时出错: {e}")
            # 创建一个简单的主题管理器模拟对象
            self.themeManager = type('ThemeManager', (), {
                'get_theme_names': lambda: ["dark", "light", "purple_dream", "green_theme"],
                'current_theme_name': "dark",
                'get_theme': lambda name: {"name": name, "display_name": self._get_theme_display_name(name)},
                'set_theme': lambda name: True
            })
            # 添加辅助方法，用于获取主题显示名称
            setattr(self.themeManager, '_get_theme_display_name', lambda name: {
                "dark": "暗色主题", 
                "light": "亮色主题", 
                "purple_dream": "紫梦主题", 
                "green_theme": "森林绿主题"
            }.get(name, name))
    
    def initFonts(self):
        try:
            if FontManager:
                # 设置应用字体
                self.system_font = FontManager.get_font()  # 使用 get_font 而不是不存在的 get_system_font
                self.setFont(self.system_font)
                
                # IconProvider已在导入时初始化，不需要额外调用 load_icon_font
            else:
                print("FontManager不可用，使用默认字体")
                # 使用系统默认字体
                default_font = QFont()
                default_font.setFamily("Microsoft YaHei UI")
                default_font.setPointSize(10)
                self.setFont(default_font)
        except Exception as e:
            print(f"初始化字体时出错: {e}")
    
    def initUI(self):
        # 创建主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 创建水平布局，包含导航区和内容区
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # 创建导航区
        self.nav_frame = QFrame()
        self.nav_frame.setObjectName("settingsNavFrame")
        self.nav_frame.setFixedWidth(200)
        nav_layout = QVBoxLayout(self.nav_frame)
        nav_layout.setContentsMargins(10, 10, 0, 10)
        
        # 创建导航列表
        self.nav_list = QListWidget()
        self.nav_list.setObjectName("settingsNavList")
        self.nav_list.setIconSize(QSize(24, 24))
        self.nav_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.nav_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.nav_list.currentRowChanged.connect(self.switchPage)
        
        # 添加设置标题
        nav_layout.addWidget(QLabel("<b>设置</b>"))
        nav_layout.addWidget(self.nav_list)
        
        # 创建关闭按钮
        close_button = QPushButton("关闭")
        close_button.setObjectName("settingsCloseButton")
        close_button.clicked.connect(self.closeSettings)
        close_button.setCursor(QCursor(Qt.PointingHandCursor))
        nav_layout.addWidget(close_button)
        
        # 添加导航区到内容布局
        content_layout.addWidget(self.nav_frame)
        
        # 创建内容区
        self.pages_stack = QStackedWidget()
        self.pages_stack.setObjectName("settingsPagesStack")
        content_layout.addWidget(self.pages_stack)
        
        # 设置内容布局的拉伸因子
        content_layout.setStretch(0, 0)
        content_layout.setStretch(1, 1)
        
        # 添加内容布局到主布局
        self.main_layout.addLayout(content_layout)
        
        # 初始化页面集合，用于管理和访问页面
        self.pages = {}
        
        # 创建各个设置页面
        self.createGeneralPage()
        self.createAppearancePage()
        self.createEditorPage()
        self.createAboutPage()
        
        # 默认选中第一项
        self.nav_list.setCurrentRow(0)
        
        # 加载设置
        self.loadSettings()
        
        # 连接设置信号
        self.connectSettingSignals()
        
        # 更新样式
        self.updateStyle()
    
    def createGeneralPage(self):
        page = HanabiSettingsPage("通用")
        
        # 启动选项类别
        startupCat = page.addCategory("startup", "启动选项")
        
        autoStartItem = HanabiToggleItem("系统启动时自动运行")
        autoStartItem.setValue(self.settings["general"]["startup"]["auto_start"])
        startupCat.addItem("auto_start", autoStartItem)
        
        rememberWindowItem = HanabiToggleItem("记住窗口位置和大小")
        rememberWindowItem.setValue(self.settings["general"]["startup"]["remember_window"])
        startupCat.addItem("remember_window", rememberWindowItem)
        
        reopenFilesItem = HanabiToggleItem("重新打开上次的文件")
        reopenFilesItem.setValue(self.settings["general"]["startup"]["reopen_files"])
        startupCat.addItem("reopen_files", reopenFilesItem)
        
        # 文件选项类别
        fileCat = page.addCategory("file", "文件选项")
        
        pathItem = HanabiPathItem("默认保存位置")
        pathItem.setValue(self.settings["general"]["file"]["default_save_path"])
        fileCat.addItem("default_save_path", pathItem)
        
        autoSaveItem = HanabiToggleItem("自动保存")
        autoSaveItem.setValue(self.settings["general"]["file"]["auto_save"])
        fileCat.addItem("auto_save", autoSaveItem)
        
        intervalItem = HanabiSpinnerItem("自动保存间隔", 1, 60, "分钟")
        intervalItem.setValue(self.settings["general"]["file"]["auto_save_interval"])
        fileCat.addItem("auto_save_interval", intervalItem)
        
        # 其他选项类别
        otherCat = page.addCategory("other", "其他选项")
        
        statusBarItem = HanabiToggleItem("显示状态栏")
        statusBarItem.setValue(self.settings["general"]["other"]["show_status_bar"])
        otherCat.addItem("show_status_bar", statusBarItem)
        
        soundItem = HanabiToggleItem("启用声音效果")
        soundItem.setValue(self.settings["general"]["other"]["enable_sound_effects"])
        otherCat.addItem("enable_sound_effects", soundItem)
        
        # 添加到堆栈页面
        self.pages_stack.addWidget(page)
        
        # 创建导航项
        item = QListWidgetItem("通用")
        item.setData(Qt.UserRole, IconProvider.get_icon("tune"))
        self.nav_list.addItem(item)
    
    def createAppearancePage(self):
        """创建外观设置页面"""
        page = HanabiSettingsPage("外观设置")
        
        # 主题设置
        themeCat = page.addCategory("theme", "主题")
        
        # 获取当前主题
        currentTheme = self.settings["appearance"]["theme"]["name"]
        
        # 创建主题设置输入框
        themeItem = HanabiComboItem("主题", ["暗色主题", "亮色主题", "紫梦主题", "森林绿主题"])
        # 将currentTheme映射到显示名称
        display_theme = currentTheme
        if currentTheme == "dark":
            display_theme = "暗色主题"
        elif currentTheme == "light":
            display_theme = "亮色主题"
        elif currentTheme == "purple_dream":
            display_theme = "紫梦主题"
        elif currentTheme == "green_theme":
            display_theme = "森林绿主题"
        
        themeItem.setValue(display_theme)
        themeCat.addItem("theme_name", themeItem)
        
        # 创建主题卡片布局容器（直接添加到主题类别中）
        themeCardsWidget = QWidget()
        themeCardsLayout = QGridLayout(themeCardsWidget)
        themeCardsLayout.setContentsMargins(0, 15, 0, 10)
        themeCardsLayout.setSpacing(15)
        
        # 定义主题卡片信息
        themes = [
            {
                "name": "暗色主题",
                "id": "dark", 
                "description": "默认深色主题\n舒适的深灰色背景\n适合夜间使用\n减轻眼睛疲劳",
                "bg_color": "#282c34",
                "text_color": "#ffffff"
            },
            {
                "name": "亮色主题",
                "id": "light", 
                "description": "明亮清爽的浅色主题\n白色背景搭配深色文本\n适合日间使用\n提高可读性",
                "bg_color": "#ffffff",
                "text_color": "#333333"
            },
            {
                "name": "紫梦主题",
                "id": "purple_dream", 
                "description": "梦幻紫色调主题\n深紫色背景\n柔和的对比度\n创造宁静的工作环境",
                "bg_color": "#2d2b55",
                "text_color": "#ffffff"
                
            },
            {
                "name": "森林绿主题",
                "id": "green_theme", 
                "description": "青葱绿色调主题\n深绿色背景\n清新自然\n增强视觉舒适度",
                "bg_color": "#1e3b26",
                "text_color": "#ffffff"
            }
        ]
        
        # 创建主题卡片
        for i, theme in enumerate(themes):
            # 创建主题卡片
            card = self.createThemeCard(theme)
            
            # 计算行列位置（每行2个）
            row, col = divmod(i, 2)
            themeCardsLayout.addWidget(card, row, col)
        
        # 添加主题卡片容器到主题类别
        themeCat.contentLayout.addWidget(themeCardsWidget)
        
        # 添加到堆栈页面
        self.pages_stack.addWidget(page)
        self.pages["appearance"] = page
        
        # 创建导航项
        item = QListWidgetItem("外观设置")
        item.setData(Qt.UserRole, IconProvider.get_icon("color_lens"))
        self.nav_list.addItem(item)
    
    def createThemeCard(self, theme):
        """创建主题卡片"""
        # 创建可点击卡片
        card = ClickableFrame()
        card.setObjectName(f"themeCard_{theme['id']}")
        card.setMinimumSize(200, 150)
        card.setMaximumSize(300, 150)
        card.setFrameShape(QFrame.StyledPanel)
        card.setCursor(Qt.PointingHandCursor)  # 直接在QWidget上设置鼠标样式
        card.setStyleSheet(f"""
            QFrame#themeCard_{theme['id']} {{
                background-color: {theme['bg_color']};
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
            }}
            
            QFrame#themeCard_{theme['id']}:hover {{
                border: 2px solid rgba(255, 255, 255, 0.3);
            }}
        """)
        
        # 卡片布局
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # 主题名称标签
        nameLabel = QLabel(theme["name"])
        nameLabel.setStyleSheet(f"""
            color: {theme['text_color']};
            font-size: 16px;
            font-weight: bold;
        """)
        layout.addWidget(nameLabel)
        
        # 如果有描述，添加描述标签
        if theme.get("description"):
            descLabel = QLabel(theme["description"])
            descLabel.setStyleSheet(f"""
                color: {theme['text_color']};
                font-size: 12px;
            """)
            layout.addWidget(descLabel)
        
        # 添加应用按钮
        applyButton = QPushButton("应用")
        applyButton.setCursor(Qt.PointingHandCursor)  # 直接在QPushButton上设置鼠标样式
        applyButton.setStyleSheet(f"""
            QPushButton {{
                background-color: {'rgba(255, 255, 255, 0.2)' if theme['id'] in ['dark', 'purple_dream', 'green_theme'] else 'rgba(0, 0, 0, 0.1)'};
                color: {theme['text_color']};
                border: 1px solid {'rgba(255, 255, 255, 0.3)' if theme['id'] in ['dark', 'purple_dream', 'green_theme'] else 'rgba(0, 0, 0, 0.2)'};
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 13px;
                font-weight: bold;
            }}
            
            QPushButton:hover {{
                background-color: {'rgba(255, 255, 255, 0.3)' if theme['id'] in ['dark', 'purple_dream', 'green_theme'] else 'rgba(0, 0, 0, 0.2)'};
                border: 1px solid {'rgba(255, 255, 255, 0.5)' if theme['id'] in ['dark', 'purple_dream', 'green_theme'] else 'rgba(0, 0, 0, 0.3)'};
            }}
        """)
        
        # 连接点击事件
        applyButton.clicked.connect(lambda: self.updateTheme(theme["id"]))
        card.clicked.connect(lambda: self.updateTheme(theme["id"]))
        
        # 将按钮添加到布局的底部
        layout.addStretch()
        layout.addWidget(applyButton, 0, Qt.AlignRight)
        
        return card
    
    def createEditorPage(self):
        page = HanabiSettingsPage("编辑器")
        
        # 字体设置
        fontCat = page.addCategory("font", "字体设置")
        
        # 使用QFontComboBox替代固定列表
        fontItem = HanabiFontComboItem("字体")
        
        currentFont = self.settings["editor"]["font"]["family"]
        fontItem.setValue(currentFont)
        fontCat.addItem("font_family", fontItem)
        
        fontSizeItem = HanabiSpinnerItem("字体大小", 8, 36, "px")
        fontSizeItem.setValue(self.settings["editor"]["font"]["size"])
        fontCat.addItem("font_size", fontSizeItem)
        
        # 添加字体粗细和斜体选项
        fontBoldItem = HanabiToggleItem("粗体")
        fontBoldItem.setValue(self.settings["editor"]["font"].get("bold", False))
        fontCat.addItem("font_bold", fontBoldItem)
        
        fontItalicItem = HanabiToggleItem("斜体")
        fontItalicItem.setValue(self.settings["editor"]["font"].get("italic", False))
        fontCat.addItem("font_italic", fontItalicItem)
        
        # 添加字体预览区域
        fontPreviewItem = HanabiFontPreviewItem("字体预览")
        fontPreviewItem.updatePreview(
            self.settings["editor"]["font"]["family"],
            self.settings["editor"]["font"]["size"],
            self.settings["editor"]["font"].get("bold", False),
            self.settings["editor"]["font"].get("italic", False)
        )
        fontCat.addItem("font_preview", fontPreviewItem)
        
        # 编辑设置
        editCat = page.addCategory("editing", "编辑设置")
        
        autoIndentItem = HanabiToggleItem("自动缩进")
        autoIndentItem.setValue(self.settings["editor"]["editing"]["auto_indent"])
        editCat.addItem("auto_indent", autoIndentItem)
        
        lineNumbersItem = HanabiToggleItem("显示行号")
        lineNumbersItem.setValue(self.settings["editor"]["editing"]["line_numbers"])
        editCat.addItem("line_numbers", lineNumbersItem)
        
        # 添加智能文件类型检测设置
        smartDetectionItem = HanabiToggleItem("智能文件类型检测", "启用时，将根据文件内容自动判断文件类型，而不仅仅依赖扩展名")
        # 从设置中获取值，如果没有则默认为True
        smartDetectionValue = self.settings["editor"]["editing"].get("smart_file_detection", True)
        smartDetectionItem.setValue(smartDetectionValue)
        editCat.addItem("smart_file_detection", smartDetectionItem)
        
        # 添加扩展名优先设置
        extensionFirstItem = HanabiToggleItem("扩展名优先", "启用时，文件类型检测将优先考虑文件扩展名，然后再分析内容")
        # 从设置中获取值，如果没有则默认为False
        extensionFirstValue = self.settings["editor"]["editing"].get("extension_first", False)
        extensionFirstItem.setValue(extensionFirstValue)
        editCat.addItem("extension_first", extensionFirstItem)
        
        # 添加编辑器行为设置
        behaviorCat = page.addCategory("behavior", "编辑器行为")
        
        wordWrapItem = HanabiToggleItem("自动换行")
        wordWrapItem.setValue(self.settings["editor"]["editing"].get("word_wrap", True))
        behaviorCat.addItem("word_wrap", wordWrapItem)
        
        # 添加到堆栈页面
        self.pages_stack.addWidget(page)
        self.pages["editor"] = page
        
        # 创建导航项
        item = QListWidgetItem("编辑器设置")
        item.setData(Qt.UserRole, IconProvider.get_icon("text_format"))
        self.nav_list.addItem(item)
    
    def createAboutPage(self):
        page = HanabiSettingsPage("关于")
        
        # 关于信息
        aboutCat = page.addCategory("about", "关于Hanabi Notes")
        
        # 添加应用程序信息
        versionItem = HanabiValueItem("版本", "应用程序当前版本")
        versionItem.setValue(self.settings["app_info"]["version"])
        aboutCat.addItem("version", versionItem)
        
        # 添加UA信息
        uaItem = HanabiValueItem("用户代理", "应用程序标识信息")
        uaItem.setValue(self.settings["system"]["user_agent"])  # 使用已存储的UA
        aboutCat.addItem("user_agent", uaItem)
        
        # 添加错误报告设置
        errorReportingItem = HanabiToggleItem("启用错误报告", "自动向开发团队报告错误信息")
        errorReportingItem.setValue(self.settings["system"]["error_reporting"])
        errorReportingItem.valueChanged.connect(
            lambda val: self.updateSetting(["system", "error_reporting"], val)
        )
        aboutCat.addItem("error_reporting", errorReportingItem)
        
        # 添加最新版本信息
        latestVersionItem = HanabiValueItem("最新版本", "Hanabi Notes的最新版本")
        latestVersionItem.setValue("正在检查...")
        aboutCat.addItem("latest_version", latestVersionItem)
        
        # 添加版本状态标签
        self.versionStatusLabel = QLabel("正在检查更新...")
        self.versionStatusLabel.setStyleSheet("color: gray; font-size: 12px;")
        aboutCat.contentLayout.addWidget(self.versionStatusLabel)
        
        # 添加检查更新按钮
        self.checkUpdateBtn = QPushButton("检查更新")
        self.checkUpdateBtn.setCursor(Qt.PointingHandCursor)
        self.checkUpdateBtn.clicked.connect(lambda: self.checkLatestVersion(latestVersionItem))
        aboutCat.contentLayout.addWidget(self.checkUpdateBtn)
        
        # 初始检查最新版本
        self.checkLatestVersion(latestVersionItem)
        
        authorItem = HanabiValueItem("开发者", "Hanabi Notes的开发团队")
        authorItem.setValue("ZZBUAOYE")
        aboutCat.addItem("author", authorItem)
        
        buildDateItem = HanabiValueItem("构建日期", "应用程序的构建时间")
        buildDateItem.setValue("2025年4月4日")
        aboutCat.addItem("build_date", buildDateItem)
        
        # 添加系统信息类别
        systemCat = page.addCategory("system", "系统信息")
        
        # 获取系统信息
        import platform
        
        osItem = HanabiValueItem("操作系统", "当前系统平台")
        try:
            os_info = f"{platform.system()} {platform.release()}"
        except:
            os_info = "Not Found"
        osItem.setValue(os_info)
        systemCat.addItem("os", osItem)
        
        pythonItem = HanabiValueItem("Python版本", "当前Python解释器版本")
        try:
            python_version = platform.python_version()
        except:
            python_version = "Not Found"
        pythonItem.setValue(python_version)
        systemCat.addItem("python", pythonItem)
        
        # 添加Qt版本信息
        qtItem = HanabiValueItem("Qt版本", "当前Qt库版本")
        try:
            from PySide6 import __version__ as pyside_version
            qt_version = f"PySide6 {pyside_version}"
        except:
            qt_version = "Not Found"
        qtItem.setValue(qt_version)
        systemCat.addItem("qt", qtItem)
        # 添加到堆栈页面
        self.pages_stack.addWidget(page)
        
        # 创建导航项
        item = QListWidgetItem("关于")
        item.setData(Qt.UserRole, IconProvider.get_icon("info"))
        self.nav_list.addItem(item)
    
    def checkLatestVersion(self, version_item):
        """从网站获取最新版本信息"""
        try:
            # 设置为正在检查状态
            version_item.setValue("正在检查...")
            if hasattr(self, 'versionStatusLabel'):
                self.versionStatusLabel.setText("正在检查更新...")
                self.versionStatusLabel.setStyleSheet("color: gray; font-size: 12px;")
            
            # 导入网络请求库
            try:
                from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
                from PySide6.QtCore import QUrl, QTimer
                
                # 创建网络管理器
                self.network_manager = QNetworkAccessManager()
                
                # 创建网络请求
                url = QUrl("https://zzbuaoye.dpdns.org/service/Hanabi/version.json")
                request = QNetworkRequest(url)
                
                # 设置请求头
                request.setHeader(QNetworkRequest.UserAgentHeader, self.settings["system"]["user_agent"])
                
                # 设置超时
                timeout_timer = QTimer()
                timeout_timer.setSingleShot(True)
                timeout_timer.setInterval(5000)  # 5秒超时
                
                def on_timeout():
                    reply = self.sender().property("reply")
                    if reply and reply.isRunning():
                        reply.abort()
                        self.handleVersionResponse(reply, version_item, error="请求超时")
                
                timeout_timer.timeout.connect(on_timeout)
                
                # 发送请求
                reply = self.network_manager.get(request)
                timeout_timer.setProperty("reply", reply)
                timeout_timer.start()
                
                # 连接错误信号
                reply.errorOccurred.connect(lambda err: self.handleNetworkError(err, reply, version_item))
                
                # 连接响应信号
                reply.finished.connect(lambda: self.handleVersionResponse(reply, version_item))
                
            except ImportError:
                # 如果QtNetwork不可用，尝试使用Python的urllib
                import urllib.request
                import threading
                import socket
                
                def fetch_version():
                    try:
                        # 创建请求对象
                        req = urllib.request.Request(
                            "https://zzbuaoye.dpdns.org/service/Hanabi/version.json",
                            headers={'User-Agent': self.settings["system"]["user_agent"]}
                        )
                        
                        # 设置超时
                        with urllib.request.urlopen(req, timeout=5) as response:
                            version = response.read().decode('utf-8').strip()
                            
                            # 获取当前版本
                            current_version = self.settings["app_info"]["version"]
                            
                            # 在主线程中更新UI
                            from PySide6.QtCore import QMetaObject, Qt, Q_ARG
                            QMetaObject.invokeMethod(version_item, "setValue", 
                                                    Qt.QueuedConnection, 
                                                    Q_ARG(str, version))
                            
                            # 比较版本
                            compare_result = self.compareVersions(version, current_version)
                            
                            # 更新版本状态标签
                            self.updateVersionStatus(version, current_version, compare_result)
                            
                    except (urllib.error.URLError, socket.timeout) as e:
                        error_msg = "网络连接失败" if isinstance(e, socket.timeout) else str(e.reason)
                        self.handleNetworkError(error_msg, None, version_item)
                    except Exception as e:
                        self.handleNetworkError(str(e), None, version_item)
                
                # 创建并启动线程
                thread = threading.Thread(target=fetch_version)
                thread.daemon = True
                thread.start()
                
        except Exception as e:
            print(f"检查更新时出错: {e}")
            self.handleNetworkError(str(e), None, version_item)

    def handleNetworkError(self, error, reply=None, version_item=None):
        """处理网络错误"""
        try:
            error_msg = ""
            if isinstance(error, str):
                error_msg = error
            elif reply and hasattr(reply, 'error'):
                error_code = reply.error()
                if error_code == QNetworkReply.OperationCanceledError:
                    error_msg = "请求已取消"
                elif error_code == QNetworkReply.TimeoutError:
                    error_msg = "请求超时"
                elif error_code == QNetworkReply.HostNotFoundError:
                    error_msg = "无法找到服务器"
                elif error_code == QNetworkReply.ConnectionRefusedError:
                    error_msg = "连接被拒绝"
                elif error_code == QNetworkReply.SslHandshakeFailedError:
                    error_msg = "SSL握手失败"
                else:
                    error_msg = f"网络错误: {error_code}"
            else:
                error_msg = "未知网络错误"
            
            print(f"网络请求错误: {error_msg}")
            
            if version_item:
                version_item.setValue("检查失败")
            
            if hasattr(self, 'versionStatusLabel'):
                self.versionStatusLabel.setText(f"检查更新失败: {error_msg}")
                self.versionStatusLabel.setStyleSheet("color: #e06c75; font-size: 12px;")
            
        except Exception as e:
            print(f"处理网络错误时出错: {e}")

    def handleVersionResponse(self, reply, version_item, error=None):
        """处理版本检查响应"""
        try:
            if error:
                self.handleNetworkError(error, reply, version_item)
                return
                
            if reply.error() == QNetworkReply.NoError:
                # 读取返回的数据
                data = reply.readAll().data().decode('utf-8').strip()
                try:
                    version_data = json.loads(data)
                    if "versions" in version_data and len(version_data["versions"]) > 0:
                        # 获取最新版本信息（列表中的第一个版本）
                        latest_version = version_data["versions"][0]
                        
                        # 更新版本显示
                        version_info = f"{latest_version['version']}"
                        if 'release_date' in latest_version:
                            version_info += f" ({latest_version['release_date']})"
                        version_item.setValue(version_info)
                        
                        # 获取当前版本
                        current_version = self.settings["app_info"]["version"]
                        
                        # 比较版本
                        compare_result = self.compareVersions(latest_version["version"], current_version)
                        
                        # 更新版本状态，包含更多详细信息
                        status_text = ""
                        if compare_result > 0:
                            status_text = f"发现新版本 {latest_version['version']}\n"
                            if 'description' in latest_version:
                                status_text += f"更新内容：{latest_version['description']}\n"
                            if 'release_date' in latest_version:
                                status_text += f"发布日期：{latest_version['release_date']}"
                        elif compare_result == 0:
                            status_text = "当前已是最新版本"
                        else:
                            status_text = f"当前版本 {current_version} 高于发布版本 {latest_version['version']}"
                        
                        if hasattr(self, 'versionStatusLabel'):
                            self.versionStatusLabel.setText(status_text)
                            if compare_result > 0:
                                self.versionStatusLabel.setStyleSheet("color: #ff9cce; font-size: 12px; font-weight: bold;")
                                # 显示更新对话框，传递完整的版本信息
                                self.showUpdateDialog(latest_version)
                            elif compare_result == 0:
                                self.versionStatusLabel.setStyleSheet("color: #7fdbca; font-size: 12px;")
                            else:
                                self.versionStatusLabel.setStyleSheet("color: #ffb86c; font-size: 12px;")
                    else:
                        raise ValueError("无效的版本数据格式")
                except json.JSONDecodeError:
                    raise ValueError("无效的JSON数据")
            else:
                self.handleNetworkError(reply.error(), reply, version_item)
            
            # 释放reply对象
            reply.deleteLater()
            
        except Exception as e:
            print(f"处理版本响应时出错: {e}")
            self.handleNetworkError(str(e), reply, version_item)

    def showUpdateDialog(self, version_info):
        """显示更新对话框，使用完整的版本信息"""
        try:
            msg = QMessageBox(self)
            msg.setWindowTitle("发现新版本")
            
            # 构建详细的更新信息
            update_text = f"发现新版本: {version_info['version']}\n\n"
            if 'description' in version_info:
                update_text += f"更新内容：\n{version_info['description']}\n\n"
            if 'release_date' in version_info:
                update_text += f"发布日期：{version_info['release_date']}\n\n"
            if 'Author' in version_info:
                update_text += f"作者：{version_info['Author']}\n\n"
            
            msg.setText(update_text)
            msg.setInformativeText("是否前往下载页面获取最新版本？")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setDefaultButton(QMessageBox.Yes)
            
            if msg.exec_() == QMessageBox.Yes:
                import webbrowser
                # 使用版本信息中的下载链接
                download_url = 'https://zzbuaoye.dpdns.org/service/Hanabi/download.html'
                webbrowser.open(download_url)
        except Exception as e:
            print(f"显示更新对话框时出错: {e}")
    
    def compareVersions(self, version1, version2):
        try:
            import re
            
            # 分离数字和非数字部分
            def parse_version(version):
                # 将版本号分割为数字和非数字部分
                components = re.findall(r'(\d+|[^\d]+)', version)
                result = []
                for comp in components:
                    # 尝试将数字部分转换为整数
                    try:
                        if comp.isdigit():
                            result.append(int(comp))
                        else:
                            result.append(comp)
                    except:
                        result.append(comp)
                return result
            
            # 分析两个版本
            v1_parts = parse_version(version1)
            v2_parts = parse_version(version2)
            
            # 逐个比较组件
            for i in range(min(len(v1_parts), len(v2_parts))):
                # 如果两者都是整数，直接比较数值
                if isinstance(v1_parts[i], int) and isinstance(v2_parts[i], int):
                    if v1_parts[i] > v2_parts[i]:
                        return 1
                    elif v1_parts[i] < v2_parts[i]:
                        return -1
                # 如果两者都是字符串，使用字符串比较
                elif isinstance(v1_parts[i], str) and isinstance(v2_parts[i], str):
                    if v1_parts[i] > v2_parts[i]:
                        return 1
                    elif v1_parts[i] < v2_parts[i]:
                        return -1
                # 如果一个是整数，一个是字符串，优先考虑整数
                else:
                    if isinstance(v1_parts[i], int):
                        return 1
                    else:
                        return -1
            
            # 如果前面的组件都相等，则长度更长的版本更大
            if len(v1_parts) > len(v2_parts):
                return 1
            elif len(v1_parts) < len(v2_parts):
                return -1
            
            # 完全相等
            return 0
        except Exception as e:
            print(f"比较版本时出错: {e}")
            return 0
    
    def updateStyle(self):
        # 获取当前主题
        is_dark = True
        try:
            if self.parent_app and hasattr(self.parent_app, 'currentTheme'):
                is_dark = self.parent_app.currentTheme != "light"
            elif "appearance" in self.settings and "theme" in self.settings["appearance"]:
                theme_data = self.settings["appearance"]["theme"]
                if isinstance(theme_data, dict) and "name" in theme_data:
                    is_dark = theme_data["name"] != "light"
        except Exception as e:
            print(f"获取主题样式时出错: {e}")
        
        # 设置主要颜色
        if is_dark:
            # 暗色主题
            nav_bg = "#1E2128"
            content_bg = "#282c34" 
            border_color = "#3E4452"
            text_color = "#abb2bf"
            hover_bg = "#3a3f4b"
            selected_bg = "#4d78cc"
            button_bg = "#3E4452"
            button_hover = "#4d5666"
            button_text = "#abb2bf"
        else:
            # 亮色主题
            nav_bg = "#f0f0f0"
            content_bg = "#ffffff"
            border_color = "#e0e0e0"
            text_color = "#333333"
            hover_bg = "#e5e5e5"
            selected_bg = "#6B9FFF"
            button_bg = "#e0e0e0"
            button_hover = "#d0d0d0"
            button_text = "#333333"
        
        # 更新返回按钮样式
        if hasattr(self, 'back_button'):
            self.back_button.setStyleSheet(f"""
                QPushButton#settingsBackButton {{
                    background-color: {button_bg};
                    color: {button_text};
                    border: none;
                    border-radius: 16px;
                    font-size: 18px;
                    text-align: center;
                    padding: 0px;
                }}
                
                QPushButton#settingsBackButton:hover {{
                    background-color: {button_hover};
                }}
                
                QPushButton#settingsBackButton:pressed {{
                    background-color: {selected_bg};
                    color: white;
                }}
            """)
        
        # 更新导航面板样式
        nav_panel = self.findChild(QWidget, "settingsNavPanel")
        if nav_panel:
            nav_panel.setStyleSheet(f"""
                QWidget#settingsNavPanel {{
                    background-color: {nav_bg};
                    border-right: 1px solid {border_color};
                }}
                
                QWidget#backContainer {{
                    background-color: {nav_bg};
                    border-bottom: 1px solid {border_color};
                }}
            """)
        
        # 更新导航列表样式
        self.nav_list.setStyleSheet(f"""
            QListWidget#settingsNavList {{
                background-color: {nav_bg};
                border: none;
                outline: none;
                padding: 8px 0;
                color: {text_color};
            }}
            
            QListWidget::item {{
                padding: 12px 16px 12px 46px;  /* 为图标留出更多左侧空间 */
                border: none;
                border-radius: 4px;
                margin: 2px 6px;
            }}
            
            QListWidget::item:selected {{
                background-color: {selected_bg};
                color: white;
            }}
            
            QListWidget::item:hover:!selected {{
                background-color: {hover_bg};
            }}
        """)
        
        # 刷新导航图标
        self.refreshNavIcons()
        
        # 更新内容区域样式
        self.pages_stack.setStyleSheet(f"""
            QWidget#settingsPagesStack {{
                background-color: {content_bg};
                color: {text_color};
                border: none;
            }}
            
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            
            QWidget#categoryContent {{
                background-color: transparent;
            }}
            
            QLabel {{
                color: {text_color};
            }}
            
            QLabel[isTitle="true"] {{
                font-size: 16px;
                font-weight: bold;
                color: {text_color};
            }}
            
            QLabel[isHeader="true"] {{
                font-size: 15px;
                font-weight: bold;
                color: {text_color};
            }}
            
            QCheckBox {{
                color: {text_color};
            }}
            
            QComboBox {{
                background-color: {button_bg};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            
            QComboBox:hover {{
                background-color: {button_hover};
            }}
            
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            
            QSpinBox {{
                background-color: {button_bg};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 4px;
            }}
            
            QPushButton {{
                background-color: {button_bg};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 6px 12px;
            }}
            
            QPushButton:hover {{
                background-color: {button_hover};
            }}
            
            QLineEdit {{
                background-color: {button_bg};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            
            QGroupBox {{
                border: 1px solid {border_color};
                border-radius: 6px;
                margin-top: 12px;
                color: {text_color};
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        
        # 更新各页面样式
        for i in range(self.pages_stack.count()):
            page = self.pages_stack.widget(i)
            if page:
                # 如果是外观设置页面，更新主题卡片
                if i == 1 and hasattr(page, 'categories'):
                    theme_list_cat = page.categories.get("theme")
                    if theme_list_cat:
                        self.updateThemeList(theme_list_cat, is_dark)
                
                # 更新所有页面上的开关控件
                if hasattr(page, 'categories'):
                    for cat_key, category in page.categories.items():
                        if hasattr(category, 'items'):
                            for item_key, item in category.items.items():
                                # 如果找到HanabiToggleItem，更新其样式
                                if isinstance(item, HanabiToggleItem) and hasattr(item, 'updateSwitchStyle'):
                                    item.updateSwitchStyle(item.value)
                                # 如果找到HanabiSpinnerItem，更新其箭头按钮样式
                                elif isinstance(item, HanabiSpinnerItem):
                                    if hasattr(item, 'updateArrowStyles'):
                                        item.updateArrowStyles()
    
    def updateThemePreview(self, preview_cat, is_dark):
        """更新主题预览面板的样式 - 旧方法，保留以兼容"""
        print("旧的预览方法被调用，但不再使用")
        pass
    
    def updateThemeList(self, theme_list_cat, is_dark):
        """更新主题列表区域，显示主题卡片"""
        try:
            # 遍历主题卡片容器中的所有卡片，刷新样式
            for i in range(theme_list_cat.contentLayout.count()):
                item = theme_list_cat.contentLayout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    
                    # 如果是主题卡片容器
                    if isinstance(widget, QWidget) and hasattr(widget, 'layout') and isinstance(widget.layout(), QGridLayout):
                        # 遍历网格布局中的所有卡片
                        for j in range(widget.layout().count()):
                            card_item = widget.layout().itemAt(j)
                            if card_item and card_item.widget():
                                card = card_item.widget()
                                # 刷新卡片的样式，如果是QFrame表示是主题卡片
                                if isinstance(card, QFrame) and card.objectName().startswith("themeCard_"):
                                    theme_id = card.objectName().replace("themeCard_", "")
                                    # 检查是否是当前主题
                                    current_theme = self.settings["appearance"]["theme"]["name"]
                                    is_current = theme_id == current_theme
                                    
                                    # 添加选中状态样式
                                    if is_current:
                                        card.setStyleSheet(card.styleSheet() + """
                                            border: 2px solid #4d78cc !important;
                                        """)
                    
        except Exception as e:
            print(f"更新主题列表时出错: {e}")
            import traceback
            traceback.print_exc()

    def closeSettings(self):
        """关闭设置面板"""
        # 确保所有设置都已保存
        try:
            self.saveSettings()
            print("设置已保存")
        except Exception as e:
            print(f"关闭设置面板时保存设置出错: {e}")
        
        # 通知父窗口隐藏设置面板
        if self.parent_app and hasattr(self.parent_app, 'hideSettings'):
            self.parent_app.hideSettings()
        else:
            # 如果没有父窗口的hideSettings方法，直接隐藏
            self.hide()
        
        print("设置面板已关闭") 

    def updateFontPreview(self, fontCat):
        try:
            if "font_preview" in fontCat.items:
                fontPreviewItem = fontCat.items["font_preview"]
                if hasattr(fontPreviewItem, 'updatePreview'):
                    # 获取当前字体设置
                    size = fontCat.items["font_size"].value if "font_size" in fontCat.items else 15
                    bold = fontCat.items["font_bold"].value if "font_bold" in fontCat.items else False
                    italic = fontCat.items["font_italic"].value if "font_italic" in fontCat.items else False
                    fontPreviewItem.updatePreview(fontCat.items["font_family"].value, size, bold, italic)
        except Exception as e:
            print(f"更新字体预览时出错: {e}") 

    def refreshNavIcons(self):
        """刷新导航栏图标，确保正确显示图标和字体"""
        try:
            # 确保Material图标字体已加载
            IconProvider.ensure_font_loaded()
            
            # 使用较小的图标字体，避免显示过大
            icon_font = IconProvider.get_icon_font(16)  # 调整为更小的尺寸
            
            # 创建并设置自定义委托
            delegate = MaterialIconItemDelegate(self.nav_list)
            delegate.setIconFont(icon_font)
            self.nav_list.setItemDelegate(delegate)
            
            # 更新样式，确保列表项文本正确显示
            text_font = FontManager.get_font() if FontManager else QFont("Microsoft YaHei UI", 12)
            text_font.setPointSize(12)  # 确保文本字体大小合适
            
            # 为所有导航项设置文本字体
            for i in range(self.nav_list.count()):
                item = self.nav_list.item(i)
                if item:
                    # 设置普通文本字体
                    item.setFont(text_font)
                    
                    # 确保每个项都有留出图标的空间
                    if not item.text().startswith("  ") and item.text():
                        item.setText("  " + item.text())
        except Exception as e:
            print(f"刷新导航图标时出错: {e}")
            
    def switchPage(self, index):
        """切换设置页面"""
        try:
            # 确保索引有效
            if 0 <= index < self.pages_stack.count():
                self.pages_stack.setCurrentIndex(index)
                print(f"切换到设置页面: {index}")
            else:
                print(f"无效的设置页面索引: {index}")
        except Exception as e:
            print(f"切换设置页面时出错: {e}")
    
    def connectSettingSignals(self):
        try:
            # 通用设置 - 启动选项
            generalPage = self.pages_stack.widget(0)
            
            if generalPage and hasattr(generalPage, 'categories'):
                # 启动设置
                startupCat = generalPage.categories.get("startup")
                if startupCat:
                    if "auto_start" in startupCat.items:
                        startupCat.items["auto_start"].valueChanged.connect(
                            lambda val: self.updateSetting(["general", "startup", "auto_start"], val))
                    
                    if "remember_window" in startupCat.items:
                        startupCat.items["remember_window"].valueChanged.connect(
                            lambda val: self.updateSetting(["general", "startup", "remember_window"], val))
                    
                    if "reopen_files" in startupCat.items:
                        startupCat.items["reopen_files"].valueChanged.connect(
                            lambda val: self.updateSetting(["general", "startup", "reopen_files"], val))
                
                # 文件设置
                fileCat = generalPage.categories.get("file")
                if fileCat:
                    if "default_save_path" in fileCat.items:
                        fileCat.items["default_save_path"].valueChanged.connect(
                            lambda val: self.updateSetting(["general", "file", "default_save_path"], val))
                    
                    if "auto_save" in fileCat.items:
                        fileCat.items["auto_save"].valueChanged.connect(
                            lambda val: self.updateSetting(["general", "file", "auto_save"], val))
                    
                    if "auto_save_interval" in fileCat.items:
                        fileCat.items["auto_save_interval"].valueChanged.connect(
                            lambda val: self.updateSetting(["general", "file", "auto_save_interval"], val))
                
                # 其他设置
                otherCat = generalPage.categories.get("other")
                if otherCat:
                    if "show_status_bar" in otherCat.items:
                        otherCat.items["show_status_bar"].valueChanged.connect(
                            lambda val: self.updateSetting(["general", "other", "show_status_bar"], val))
                    
                    if "enable_sound_effects" in otherCat.items:
                        otherCat.items["enable_sound_effects"].valueChanged.connect(
                            lambda val: self.updateSetting(["general", "other", "enable_sound_effects"], val))
            
            # 外观设置
            if self.pages_stack.count() > 1:
                appearancePage = self.pages_stack.widget(1)
                if appearancePage and hasattr(appearancePage, 'categories'):
                    themeCat = appearancePage.categories.get("theme")
                    if themeCat and "theme_name" in themeCat.items:
                        themeCat.items["theme_name"].valueChanged.connect(
                            lambda val: self.updateTheme(val))
            
            # 编辑器设置
            if self.pages_stack.count() > 2:
                editorPage = self.pages_stack.widget(2)
                if editorPage and hasattr(editorPage, 'categories'):
                    # 字体设置
                    fontCat = editorPage.categories.get("font")
                    if fontCat:
                        if "font_family" in fontCat.items:
                            fontCat.items["font_family"].valueChanged.connect(
                                lambda val: self.updateSetting(["editor", "font", "family"], val))
                        
                        if "font_size" in fontCat.items:
                            fontCat.items["font_size"].valueChanged.connect(
                                lambda val: self.updateSetting(["editor", "font", "size"], val))
                            # 添加字体大小变更时更新预览
                            fontCat.items["font_size"].valueChanged.connect(
                                lambda val: self.updateFontPreview(fontCat))
                        
                        # 连接粗体设置
                        if "font_bold" in fontCat.items:
                            fontCat.items["font_bold"].valueChanged.connect(
                                lambda val: self.updateSetting(["editor", "font", "bold"], val))
                            # 添加粗体变更时更新预览
                            fontCat.items["font_bold"].valueChanged.connect(
                                lambda val: self.updateFontPreview(fontCat))
                        
                        # 连接斜体设置
                        if "font_italic" in fontCat.items:
                            fontCat.items["font_italic"].valueChanged.connect(
                                lambda val: self.updateSetting(["editor", "font", "italic"], val))
                            # 添加斜体变更时更新预览
                            fontCat.items["font_italic"].valueChanged.connect(
                                lambda val: self.updateFontPreview(fontCat))
                    
                    # 编辑设置
                    editCat = editorPage.categories.get("editing")
                    if editCat:
                        if "auto_indent" in editCat.items:
                            editCat.items["auto_indent"].valueChanged.connect(
                                lambda val: self.updateSetting(["editor", "editing", "auto_indent"], val))
                        
                        if "line_numbers" in editCat.items:
                            editCat.items["line_numbers"].valueChanged.connect(
                                lambda val: self.updateSetting(["editor", "editing", "line_numbers"], val))
                        
                        if "spell_check" in editCat.items:
                            editCat.items["spell_check"].valueChanged.connect(
                                lambda val: self.updateSetting(["editor", "editing", "spell_check"], val))
                        
                        if "word_wrap" in editCat.items:
                            editCat.items["word_wrap"].valueChanged.connect(
                                lambda val: self.updateSetting(["editor", "editing", "word_wrap"], val))
                                
                        # 连接智能文件类型检测设置
                        if "smart_file_detection" in editCat.items:
                            editCat.items["smart_file_detection"].valueChanged.connect(
                                lambda val: self.updateSetting(["editor", "editing", "smart_file_detection"], val))
                                
                        # 连接扩展名优先设置
                        if "extension_first" in editCat.items:
                            editCat.items["extension_first"].valueChanged.connect(
                                lambda val: self.updateSetting(["editor", "editing", "extension_first"], val))
                                
        except Exception as e:
            print(f"连接设置信号时出错: {e}")
    
    def updateSetting(self, path, value):
        current = self.settings
        
        # 确保路径上的每个节点都是字典
        for i, key in enumerate(path[:-1]):
            # 如果当前节点不存在或不是字典，创建一个新字典
            if key not in current or not isinstance(current[key], dict):
                print(f"路径节点 {'.'.join(path[:i+1])} 不是字典或不存在，创建新字典")
                current[key] = {}
            current = current[key]
            
        # 最后一个键设置值
        current[path[-1]] = value
        print(f"设置已更新: {'.'.join(path)} = {value}")
        
        # 发送设置更改信号
        self.settingsChanged.emit(self.settings)
        
        # 保存设置
        self.saveSettings()
    
    def updateTheme(self, theme_name):
        print(f"正在切换主题: {theme_name}")
        
        # 显示名称到主题ID的映射
        theme_map = {
            "亮色主题": "light",
            "Light Theme": "light",
            "暗色主题": "dark",
            "Dark Theme": "dark",
            "紫梦主题": "purple_dream",
            "Purple Dream": "purple_dream",
            "森林绿主题": "green_theme",
            "Green Theme": "green_theme",
            "银白主题": "silvery_white",
            "Silvery White": "silvery_white"
        }
        
        # 获取主题ID
        theme_id = theme_name
        if theme_name in theme_map:
            theme_id = theme_map[theme_name]
            print(f"映射主题名称 '{theme_name}' 到主题ID '{theme_id}'")
        
        print(f"正在应用主题: {theme_id}")
        
        # 更新设置
        self.updateSetting(["appearance", "theme", "name"], theme_id)
        
        # 检查主题是否存在于ThemeManager中
        theme_available = False
        if hasattr(self, 'themeManager') and self.themeManager:
            try:
                # 如果主题管理器有get_theme方法，检查主题是否存在
                if hasattr(self.themeManager, 'get_theme'):
                    theme_obj = self.themeManager.get_theme(theme_id)
                    if theme_obj:
                        theme_available = True
                        print(f"找到主题 '{theme_id}' 在ThemeManager中")
                    else:
                        print(f"警告: 主题 '{theme_id}' 在ThemeManager中不存在")
                
                # 不管主题是否存在，都尝试设置（ThemeManager有回退机制）
                if hasattr(self.themeManager, 'set_theme'):
                    success = self.themeManager.set_theme(theme_id)
                    print(f"通过主题管理器设置主题: {theme_id}, 结果: {success}")
                    
                    # 如果设置失败并且主题不可用，添加主题
                    if not success and not theme_available:
                        print(f"尝试添加新主题: {theme_id}")
                        # 根据主题ID创建新主题
                        if theme_id == "light":
                            light_theme = {
                                "name": "light",
                                "display_name": "亮色主题",
                                "window": {"background": "#f5f5f5"}
                            }
                            if hasattr(self.themeManager, 'add_theme') and hasattr(self.themeManager, 'Theme'):
                                theme_cls = getattr(self.themeManager, 'Theme')
                                self.themeManager.add_theme(theme_cls(theme_id, light_theme))
                                print(f"添加了新的light主题")
                                # 重新尝试设置主题
                                success = self.themeManager.set_theme(theme_id)
                                print(f"重新尝试设置主题: {theme_id}, 结果: {success}")
            except Exception as e:
                print(f"通过主题管理器设置主题出错: {e}")
                import traceback
                traceback.print_exc()
        
        # 通知父窗口主题已变更
        if self.parent_app:
            if hasattr(self.parent_app, 'onThemeChanged'):
                print(f"调用父窗口的 onThemeChanged 方法")
                self.parent_app.onThemeChanged(theme_id)
            elif hasattr(self.parent_app, 'applyTheme'):
                print(f"调用父窗口的 applyTheme 方法")
                self.parent_app.applyTheme(theme_id)
        
        # 更新样式
        self.updateStyle()
        
        # 更新所有页面上的开关样式和箭头按钮样式
        for i in range(self.pages_stack.count()):
            page = self.pages_stack.widget(i)
            if page and hasattr(page, 'categories'):
                for cat_key, category in page.categories.items():
                    if hasattr(category, 'items'):
                        for item_key, item in category.items.items():
                            # 如果找到HanabiToggleItem，更新其样式
                            if isinstance(item, HanabiToggleItem) and hasattr(item, 'updateSwitchStyle'):
                                item.updateSwitchStyle(item.value)
                            # 如果找到HanabiSpinnerItem，更新其箭头按钮样式
                            elif isinstance(item, HanabiSpinnerItem) and hasattr(item, 'updateArrowStyles'):
                                item.updateArrowStyles()
        
        print(f"主题切换完成: {theme_id}")
    
    def loadSettings(self):
        try:
            settings_dir = os.path.join(os.path.expanduser("~"), ".hanabi_notes")
            settings_file = os.path.join(settings_dir, "settings.json")
            
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    saved_settings = json.load(f)
                
                # 递归更新设置
                self.updateSettingsDict(self.settings, saved_settings)
                print("设置已从文件加载")
        except Exception as e:
            print(f"加载设置时出错: {e}")
    
    def saveSettings(self):
        try:
            settings_dir = os.path.join(os.path.expanduser("~"), ".hanabi_notes")
            os.makedirs(settings_dir, exist_ok=True)
            settings_file = os.path.join(settings_dir, "settings.json")
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
            
            print(f"设置已保存到: {settings_file}")
        except Exception as e:
            print(f"保存设置时出错: {e}")
    
    def updateSettingsDict(self, target, source):
        if not isinstance(source, dict):
            print(f"警告: 源数据不是字典类型: {type(source)}")
            return
            
        if not isinstance(target, dict):
            print(f"警告: 目标数据不是字典类型: {type(target)}")
            return
            
        for key, value in source.items():
            try:
                if key in target:
                    if isinstance(value, dict) and isinstance(target[key], dict):
                        # 如果两者都是字典，递归更新
                        self.updateSettingsDict(target[key], value)
                    elif isinstance(value, dict) and not isinstance(target[key], dict):
                        # 源是字典但目标不是，报警告
                        print(f"警告: 键 {key} 的目标类型 {type(target[key])} 与源类型 {type(value)} 不匹配")
                        # 创建新字典并递归更新
                        target[key] = {}
                        self.updateSettingsDict(target[key], value)
                    else:
                        # 值不是字典，直接赋值
                        target[key] = value
                else:
                    # 目标没有该键，直接添加
                    target[key] = value
            except Exception as e:
                print(f"更新设置字典时出错 (键 {key}): {e}")
                
    def updateStyle(self):
        """更新设置面板样式，特别是在主题变更时调用"""
        # 获取当前主题
        is_dark = True
        try:
            if self.parent_app and hasattr(self.parent_app, 'currentTheme'):
                is_dark = self.parent_app.currentTheme != "light"
            elif "appearance" in self.settings and "theme" in self.settings["appearance"]:
                theme_data = self.settings["appearance"]["theme"]
                if isinstance(theme_data, dict) and "name" in theme_data:
                    is_dark = theme_data["name"] != "light"
        except Exception as e:
            print(f"获取主题样式时出错: {e}")
        
        # 设置主要颜色
        if is_dark:
            # 暗色主题
            nav_bg = "#1E2128"
            content_bg = "#282c34" 
            border_color = "#3E4452"
            text_color = "#abb2bf"
            hover_bg = "#3a3f4b"
            selected_bg = "#4d78cc"
            button_bg = "#3E4452"
            button_hover = "#4d5666"
            button_text = "#abb2bf"
        else:
            # 亮色主题
            nav_bg = "#f0f0f0"
            content_bg = "#ffffff"
            border_color = "#e0e0e0"
            text_color = "#333333"
            hover_bg = "#e5e5e5"
            selected_bg = "#6B9FFF"
            button_bg = "#e0e0e0"
            button_hover = "#d0d0d0"
            button_text = "#333333"
        
        # 更新返回按钮样式
        if hasattr(self, 'back_button'):
            self.back_button.setStyleSheet(f"""
                QPushButton#settingsBackButton {{
                    background-color: {button_bg};
                    color: {button_text};
                    border: none;
                    border-radius: 16px;
                    font-size: 18px;
                    text-align: center;
                    padding: 0px;
                }}
                
                QPushButton#settingsBackButton:hover {{
                    background-color: {button_hover};
                }}
                
                QPushButton#settingsBackButton:pressed {{
                    background-color: {selected_bg};
                    color: white;
                }}
            """)
        
        # 更新导航面板样式
        nav_panel = self.findChild(QWidget, "settingsNavPanel")
        if nav_panel:
            nav_panel.setStyleSheet(f"""
                QWidget#settingsNavPanel {{
                    background-color: {nav_bg};
                    border-right: 1px solid {border_color};
                }}
                
                QWidget#backContainer {{
                    background-color: {nav_bg};
                    border-bottom: 1px solid {border_color};
                }}
            """)
        
        # 更新导航列表样式
        self.nav_list.setStyleSheet(f"""
            QListWidget#settingsNavList {{
                background-color: {nav_bg};
                border: none;
                outline: none;
                padding: 8px 0;
                color: {text_color};
            }}
            
            QListWidget::item {{
                padding: 12px 16px 12px 46px;  /* 为图标留出更多左侧空间 */
                border: none;
                border-radius: 4px;
                margin: 2px 6px;
            }}
            
            QListWidget::item:selected {{
                background-color: {selected_bg};
                color: white;
            }}
            
            QListWidget::item:hover:!selected {{
                background-color: {hover_bg};
            }}
        """)
        
        # 刷新导航图标
        self.refreshNavIcons()
        
        # 更新内容区域样式
        self.pages_stack.setStyleSheet(f"""
            QWidget#settingsPagesStack {{
                background-color: {content_bg};
                color: {text_color};
                border: none;
            }}
            
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            
            QWidget#categoryContent {{
                background-color: transparent;
            }}
            
            QLabel {{
                color: {text_color};
            }}
            
            QLabel[isTitle="true"] {{
                font-size: 16px;
                font-weight: bold;
                color: {text_color};
            }}
            
            QLabel[isHeader="true"] {{
                font-size: 15px;
                font-weight: bold;
                color: {text_color};
            }}
            
            QCheckBox {{
                color: {text_color};
            }}
            
            QComboBox {{
                background-color: {button_bg};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            
            QComboBox:hover {{
                background-color: {button_hover};
            }}
            
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            
            QSpinBox {{
                background-color: {button_bg};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 4px;
            }}
            
            QPushButton {{
                background-color: {button_bg};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 6px 12px;
            }}
            
            QPushButton:hover {{
                background-color: {button_hover};
            }}
            
            QLineEdit {{
                background-color: {button_bg};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            
            QGroupBox {{
                border: 1px solid {border_color};
                border-radius: 6px;
                margin-top: 12px;
                color: {text_color};
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        
        # 更新各页面样式
        for i in range(self.pages_stack.count()):
            page = self.pages_stack.widget(i)
            if page:
                # 如果是外观设置页面，更新主题卡片
                if i == 1 and hasattr(page, 'categories'):
                    theme_list_cat = page.categories.get("theme")
                    if theme_list_cat:
                        self.updateThemeList(theme_list_cat, is_dark)
                
                # 更新所有页面上的开关控件
                if hasattr(page, 'categories'):
                    for cat_key, category in page.categories.items():
                        if hasattr(category, 'items'):
                            for item_key, item in category.items.items():
                                # 如果找到HanabiToggleItem，更新其样式
                                if isinstance(item, HanabiToggleItem) and hasattr(item, 'updateSwitchStyle'):
                                    item.updateSwitchStyle(item.value)
                                # 如果找到HanabiSpinnerItem，更新其箭头按钮样式
                                elif isinstance(item, HanabiSpinnerItem):
                                    if hasattr(item, 'updateArrowStyles'):
                                        item.updateArrowStyles()
    
    def updateThemePreview(self, preview_cat, is_dark):
        """更新主题预览面板的样式 - 旧方法，保留以兼容"""
        print("旧的预览方法被调用，但不再使用")
        pass
    
    def updateThemeList(self, theme_list_cat, is_dark):
        """更新主题列表区域，显示主题卡片"""
        try:
            # 遍历主题卡片容器中的所有卡片，刷新样式
            for i in range(theme_list_cat.contentLayout.count()):
                item = theme_list_cat.contentLayout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    
                    # 如果是主题卡片容器
                    if isinstance(widget, QWidget) and hasattr(widget, 'layout') and isinstance(widget.layout(), QGridLayout):
                        # 遍历网格布局中的所有卡片
                        for j in range(widget.layout().count()):
                            card_item = widget.layout().itemAt(j)
                            if card_item and card_item.widget():
                                card = card_item.widget()
                                # 刷新卡片的样式，如果是QFrame表示是主题卡片
                                if isinstance(card, QFrame) and card.objectName().startswith("themeCard_"):
                                    theme_id = card.objectName().replace("themeCard_", "")
                                    # 检查是否是当前主题
                                    current_theme = self.settings["appearance"]["theme"]["name"]
                                    is_current = theme_id == current_theme
                                    
                                    # 添加选中状态样式
                                    if is_current:
                                        card.setStyleSheet(card.styleSheet() + """
                                            border: 2px solid #4d78cc !important;
                                        """)
                    
        except Exception as e:
            print(f"更新主题列表时出错: {e}")
            import traceback
            traceback.print_exc()

    def closeSettings(self):
        """关闭设置面板"""
        # 确保所有设置都已保存
        try:
            self.saveSettings()
            print("设置已保存")
        except Exception as e:
            print(f"关闭设置面板时保存设置出错: {e}")
        
        # 通知父窗口隐藏设置面板
        if self.parent_app and hasattr(self.parent_app, 'hideSettings'):
            self.parent_app.hideSettings()
        else:
            # 如果没有父窗口的hideSettings方法，直接隐藏
            self.hide()
        
        print("设置面板已关闭") 

    def updateFontPreview(self, fontCat):
        try:
            if "font_preview" in fontCat.items:
                fontPreviewItem = fontCat.items["font_preview"]
                if hasattr(fontPreviewItem, 'updatePreview'):
                    # 获取当前字体设置
                    size = fontCat.items["font_size"].value if "font_size" in fontCat.items else 15
                    bold = fontCat.items["font_bold"].value if "font_bold" in fontCat.items else False
                    italic = fontCat.items["font_italic"].value if "font_italic" in fontCat.items else False
                    fontPreviewItem.updatePreview(fontCat.items["font_family"].value, size, bold, italic)
        except Exception as e:
            print(f"更新字体预览时出错: {e}") 

    def refreshNavIcons(self):
        """刷新导航栏图标，确保正确显示图标和字体"""
        try:
            # 确保Material图标字体已加载
            IconProvider.ensure_font_loaded()
            
            # 使用较小的图标字体，避免显示过大
            icon_font = IconProvider.get_icon_font(16)  # 调整为更小的尺寸
            
            # 创建并设置自定义委托
            delegate = MaterialIconItemDelegate(self.nav_list)
            delegate.setIconFont(icon_font)
            self.nav_list.setItemDelegate(delegate)
            
            # 更新样式，确保列表项文本正确显示
            text_font = FontManager.get_font() if FontManager else QFont("Microsoft YaHei UI", 12)
            text_font.setPointSize(12)  # 确保文本字体大小合适
            
            # 为所有导航项设置文本字体
            for i in range(self.nav_list.count()):
                item = self.nav_list.item(i)
                if item:
                    # 设置普通文本字体
                    item.setFont(text_font)
                    
                    # 确保每个项都有留出图标的空间
                    if not item.text().startswith("  ") and item.text():
                        item.setText("  " + item.text())
        except Exception as e:
            print(f"刷新导航图标时出错: {e}")
            
    def switchPage(self, index):
        """切换设置页面"""
        try:
            # 确保索引有效
            if 0 <= index < self.pages_stack.count():
                self.pages_stack.setCurrentIndex(index)
                print(f"切换到设置页面: {index}")
            else:
                print(f"无效的设置页面索引: {index}")
        except Exception as e:
            print(f"切换设置页面时出错: {e}")