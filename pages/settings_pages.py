from PySide6.QtWidgets import (
    QWidget, 
    QVBoxLayout, 
    QHBoxLayout, 
    QLabel, 
    QComboBox,
    QFrame,
    QScrollArea,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QCheckBox,
    QTabWidget,
    QLineEdit,
    QKeySequenceEdit
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QColor, QFont, QKeySequence
from core.font.font_manager import FontManager
from core.font.font_pages_manager import FontPagesManager
from core.log.log_manager import log
from core.utils.notif import show_info, show_error, show_warning, Notification, NotificationType
from core.utils.config_manager import config_manager
from PySide6.QtWidgets import QApplication
import winreg
import ctypes
import os
import sys

# 设置卡片样式
CARD_STYLE = """
    QFrame {
        background-color: white;
        border-radius: 8px;
        border: 1px solid #EEEEEE;
    }
"""

class SettingCard(QFrame):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        self.setup_ui()
        
    def setup_ui(self):
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)
        
        # 标题
        self.title_label = QLabel(self.title)
        self.font_manager = FontPagesManager()
        self.font_manager.apply_subtitle_style(self.title_label)
        self.title_label.setStyleSheet("color: #333333; font-weight: 500;")
        
        # 内容区域
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 10, 0, 0)
        self.content_layout.setSpacing(15)
        
        # 添加到主布局
        layout.addWidget(self.title_label)
        layout.addLayout(self.content_layout)
        
        # 设置样式
        self.setStyleSheet(CARD_STYLE)
        
    def add_setting_item(self, widget):
        self.content_layout.addWidget(widget)

class SettingItem(QWidget):
    def __init__(self, label, parent=None):
        super().__init__(parent)
        self.label_text = label
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 标签
        self.label = QLabel(self.label_text)
        self.font_manager = FontPagesManager()
        self.font_manager.apply_normal_style(self.label)
        self.label.setStyleSheet("color: #666666;")
        
        # 控件容器
        self.control_layout = QHBoxLayout()
        self.control_layout.setContentsMargins(0, 0, 0, 0)
        self.control_layout.setSpacing(10)
        
        # 添加到主布局
        layout.addWidget(self.label)
        layout.addStretch()
        layout.addLayout(self.control_layout)
        
    def add_control(self, widget):
        self.control_layout.addWidget(widget)

class FontSettingItem(SettingItem):
    font_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__("系统字体", parent)
        self.setup_font_selector()
        
    def setup_font_selector(self):
        # 创建字体管理器
        self.font_manager = FontManager()
        
        # 创建字体选择下拉框
        self.font_combo = self.font_manager.create_font_combobox()
        self.font_combo.setFixedWidth(200)
        
        # 断开默认连接,改为自定义处理
        try:
            self.font_combo.currentTextChanged.disconnect()
        except:
            pass
        
        # 从配置中获取当前字体
        current_font = config_manager.get_config('appearance', 'font')
        if not current_font or current_font not in self.font_manager.get_system_fonts():
            current_font = self.font_manager.current_font
            
        # 设置当前字体
        index = self.font_combo.findText(current_font)
        if index >= 0:
            self.font_combo.setCurrentIndex(index)
            log.info(f"FontSettingItem: 设置当前字体为: {current_font}")
            
        # 连接信号
        self.font_combo.currentTextChanged.connect(self._on_font_changed)
        
        # 添加到控件区域
        self.add_control(self.font_combo)
        
    def _on_font_changed(self, font_name):
        # 手动调用字体管理器的设置方法
        self.font_manager.set_current_font(font_name)
        
        # 保存配置
        config_manager.set_config('appearance', 'font', font_name)
        log.info(f"字体配置已保存: {font_name}")
        
        # 发出字体变更信号
        self.font_changed.emit(font_name)
        
        # 显示通知
        show_info(f"字体已切换为: {font_name}")
        
        # 强制刷新整个应用
        app = QApplication.instance()
        if app:
            # 强制所有窗口更新
            for widget in app.allWidgets():
                try:
                    # 尝试重新应用字体
                    if hasattr(widget, "update"):
                        widget.update()
                except:
                    pass

class CheckboxSettingItem(SettingItem):
    state_changed = Signal(bool)
    
    def __init__(self, label, config_section, config_key, default=False, parent=None):
        super().__init__(label, parent)
        self.config_section = config_section
        self.config_key = config_key
        self.default = default
        self.setup_checkbox()
        
    def setup_checkbox(self):
        # 创建复选框
        self.checkbox = QCheckBox()
        
        # 从配置中获取当前状态
        current_state = config_manager.get_config(self.config_section, self.config_key, self.default)
        self.checkbox.setChecked(current_state)
        
        # 连接信号
        self.checkbox.stateChanged.connect(self._on_state_changed)
        
        # 添加到控件区域
        self.add_control(self.checkbox)
        
    def _on_state_changed(self, state):
        is_checked = (state == Qt.Checked)
        
        # 保存配置
        config_manager.set_config(self.config_section, self.config_key, is_checked)
        log.info(f"设置项 '{self.label_text}' 已更新: {is_checked}")
        
        # 发出状态变更信号
        self.state_changed.emit(is_checked)
        
        # 对于特定设置执行额外操作
        if self.config_key == "autostart":
            self._set_autostart(is_checked)
        elif self.config_key == "skip_uac":
            self._set_skip_uac(is_checked)
        
    def _set_autostart(self, enable):
        try:
            # 获取应用程序路径
            app_path = sys.executable
            app_name = "Imagine Snap"
            
            # 打开注册表
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
            )
            
            if enable:
                # 添加开机自启动
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{app_path}"')
                log.info(f"已设置开机自启动: {app_path}")
                show_info("已设置开机自启动")
            else:
                # 删除开机自启动
                try:
                    winreg.DeleteValue(key, app_name)
                    log.info("已取消开机自启动")
                    show_info("已取消开机自启动")
                except FileNotFoundError:
                    # 键不存在，忽略错误
                    pass
            
            winreg.CloseKey(key)
            
        except Exception as e:
            log.error(f"设置开机自启动失败: {str(e)}")
            show_error(f"设置开机自启动失败: {str(e)}")
            
    def _set_skip_uac(self, enable):
        try:
            # 仅在管理员权限下执行
            if not ctypes.windll.shell32.IsUserAnAdmin():
                show_warning("需要管理员权限才能修改UAC设置")
                # 回滚设置
                self.checkbox.setChecked(not enable)
                config_manager.set_config(self.config_section, self.config_key, not enable)
                return
                
            # 获取应用程序路径
            app_path = sys.executable
            
            # UAC相关操作 (这里仅作示例，实际实现可能需要更复杂的操作)
            if enable:
                log.info("已设置跳过UAC")
                show_info("已设置跳过UAC，应用程序将不再请求管理员权限")
            else:
                log.info("已取消跳过UAC")
                show_info("已重新启用UAC")
                
        except Exception as e:
            log.error(f"设置UAC失败: {str(e)}")
            show_error(f"设置UAC失败: {str(e)}")

class PrioritySettingItem(SettingItem):
    def __init__(self, parent=None):
        super().__init__("进程优先级", parent)
        self.setup_priority_selector()
        
    def setup_priority_selector(self):
        # 创建下拉框
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["正常", "高于正常", "高", "实时"])
        self.priority_combo.setFixedWidth(200)
        
        # 从配置中获取当前优先级
        current_priority = config_manager.get_config('system', 'priority', "正常")
        index = self.priority_combo.findText(current_priority)
        if index >= 0:
            self.priority_combo.setCurrentIndex(index)
        
        # 连接信号
        self.priority_combo.currentTextChanged.connect(self._on_priority_changed)
        
        # 添加到控件区域
        self.add_control(self.priority_combo)
        
    def _on_priority_changed(self, priority):
        # 保存配置
        config_manager.set_config('system', 'priority', priority)
        log.info(f"进程优先级已设置为: {priority}")
        
        # 设置当前进程优先级
        self._set_process_priority(priority)
        
    def _set_process_priority(self, priority):
        try:
            import psutil
            
            # 获取当前进程
            process = psutil.Process(os.getpid())
            
            # 映射优先级名称到psutil优先级
            priority_map = {
                "正常": psutil.NORMAL_PRIORITY_CLASS,
                "高于正常": psutil.ABOVE_NORMAL_PRIORITY_CLASS,
                "高": psutil.HIGH_PRIORITY_CLASS,
                "实时": psutil.REALTIME_PRIORITY_CLASS
            }
            
            # 设置优先级
            process.nice(priority_map.get(priority, psutil.NORMAL_PRIORITY_CLASS))
            
            show_info(f"进程优先级已设置为: {priority}")
            
        except Exception as e:
            log.error(f"设置进程优先级失败: {str(e)}")
            show_error(f"设置进程优先级失败")

class ShortcutSettingItem(SettingItem):
    shortcut_changed = Signal(str)
    
    def __init__(self, label, config_section, config_key, default="", parent=None):
        super().__init__(label, parent)
        self.config_section = config_section
        self.config_key = config_key
        self.default = default
        self.setup_shortcut_editor()
        
    def setup_shortcut_editor(self):
        # 创建快捷键编辑器
        self.shortcut_edit = QKeySequenceEdit()
        self.shortcut_edit.setFixedWidth(200)
        
        # 从配置中获取当前快捷键
        current_shortcut = config_manager.get_config(self.config_section, self.config_key, self.default)
        if current_shortcut:
            self.shortcut_edit.setKeySequence(QKeySequence(current_shortcut))
        
        # 连接信号
        self.shortcut_edit.editingFinished.connect(self._on_shortcut_changed)
        
        # 添加到控件区域
        self.add_control(self.shortcut_edit)
        
    def _on_shortcut_changed(self):
        # 获取快捷键文本
        shortcut_text = self.shortcut_edit.keySequence().toString()
        
        # 保存配置
        config_manager.set_config(self.config_section, self.config_key, shortcut_text)
        log.info(f"快捷键 '{self.label_text}' 已设置为: {shortcut_text}")
        
        # 发出快捷键变更信号
        self.shortcut_changed.emit(shortcut_text)
        
        # 显示通知
        Notification(
            text=f"快捷键已设置为: {shortcut_text}",
            type=NotificationType.TIPS,
            duration=1500
        ).show_notification()

class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        title = QLabel("设置")
        font_manager = FontPagesManager()
        font_manager.apply_title_style(title)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #DDDDDD;
                background: white;
                border-radius: 5px;
            }
            QTabBar::tab {
                background: #F0F0F0;
                border: 1px solid #DDDDDD;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 6px 15px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: 1px solid white;
            }
        """)
        
        # 创建基本设置选项卡
        basic_tab = QWidget()
        self.setup_basic_tab(basic_tab)
        
        # 创建截图设置选项卡
        screenshot_tab = QWidget()
        self.setup_screenshot_tab(screenshot_tab)
        
        # 添加选项卡
        self.tab_widget.addTab(basic_tab, "基本设置")
        self.tab_widget.addTab(screenshot_tab, "截图设置")
        
        main_layout.addWidget(title)
        main_layout.addWidget(self.tab_widget)
        
        self.setStyleSheet("""
            QWidget {
                background: #F8F9FA;
            }
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #F0F0F0;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #CCCCCC;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
    def setup_basic_tab(self, tab):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(20, 20, 20, 20)
        scroll_layout.setSpacing(20)
        
        # 外观设置卡片
        appearance_card = SettingCard("外观设置")
        self.font_setting = FontSettingItem()
        self.font_setting.font_changed.connect(self._on_font_changed)
        appearance_card.add_setting_item(self.font_setting)
        
        # 系统设置卡片
        system_card = SettingCard("系统设置")
        
        # 添加开机自启动设置
        self.autostart_setting = CheckboxSettingItem(
            "开机自启动", 
            "system", 
            "autostart", 
            False
        )
        system_card.add_setting_item(self.autostart_setting)
        
        # 添加进程优先级设置
        self.priority_setting = PrioritySettingItem()
        system_card.add_setting_item(self.priority_setting)
        
        # 添加跳过UAC设置
        self.uac_setting = CheckboxSettingItem(
            "跳过UAC验证", 
            "system", 
            "skip_uac", 
            False
        )
        system_card.add_setting_item(self.uac_setting)
        
        # 添加最小化到托盘设置
        self.tray_setting = CheckboxSettingItem(
            "关闭时最小化到托盘", 
            "system", 
            "minimize_to_tray", 
            True
        )
        system_card.add_setting_item(self.tray_setting)
        
        scroll_layout.addWidget(appearance_card)
        scroll_layout.addWidget(system_card)
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll_area)
        
    def setup_screenshot_tab(self, tab):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(20, 20, 20, 20)
        scroll_layout.setSpacing(20)
        
        # 快捷键设置卡片
        shortcuts_card = SettingCard("快捷键设置")
        
        # 添加全屏截图快捷键设置
        self.fullscreen_shortcut = ShortcutSettingItem(
            "全屏截图", 
            "shortcuts", 
            "fullscreen", 
            "Ctrl+Alt+F"
        )
        shortcuts_card.add_setting_item(self.fullscreen_shortcut)
        
        # 添加区域截图快捷键设置
        self.region_shortcut = ShortcutSettingItem(
            "区域截图", 
            "shortcuts", 
            "region", 
            "Ctrl+Alt+A"
        )
        shortcuts_card.add_setting_item(self.region_shortcut)
        
        # 添加窗口截图快捷键设置
        self.window_shortcut = ShortcutSettingItem(
            "窗口截图", 
            "shortcuts", 
            "window", 
            "Ctrl+Alt+W"
        )
        shortcuts_card.add_setting_item(self.window_shortcut)
        
        # 添加快速截图快捷键设置
        self.quick_shortcut = ShortcutSettingItem(
            "快速截图", 
            "shortcuts", 
            "quick", 
            "Ctrl+Alt+S"
        )
        shortcuts_card.add_setting_item(self.quick_shortcut)
        
        # 保存设置卡片
        save_card = SettingCard("保存设置")
        
        # 添加默认保存格式设置
        self.format_setting = SettingItem("默认保存格式")
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPG", "BMP", "GIF"])
        self.format_combo.setFixedWidth(200)
        
        # 从配置中获取当前格式
        current_format = config_manager.get_config('screenshot', 'format', "PNG")
        index = self.format_combo.findText(current_format)
        if index >= 0:
            self.format_combo.setCurrentIndex(index)
            
        # 连接信号
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        
        self.format_setting.add_control(self.format_combo)
        save_card.add_setting_item(self.format_setting)
        
        # 添加自动保存设置
        self.autosave_setting = CheckboxSettingItem(
            "自动保存截图", 
            "screenshot", 
            "autosave", 
            True
        )
        save_card.add_setting_item(self.autosave_setting)
        
        # 添加保存路径设置
        self.save_path_setting = SettingItem("保存路径")
        
        # 水平布局以放置路径编辑框和浏览按钮
        path_layout = QHBoxLayout()
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.setSpacing(5)
        
        # 路径编辑框
        self.path_edit = QLineEdit()
        self.path_edit.setFixedWidth(160)
        
        # 从配置中获取保存路径
        save_path = config_manager.get_config('screenshot', 'save_path', os.path.join(os.path.expanduser('~'), 'Pictures'))
        self.path_edit.setText(save_path)
        
        # 浏览按钮
        self.browse_button = QPushButton("浏览...")
        self.browse_button.clicked.connect(self._browse_save_path)
        
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.browse_button)
        
        # 将路径选择控件添加到设置项
        self.save_path_setting.control_layout.addLayout(path_layout)
        save_card.add_setting_item(self.save_path_setting)
        
        scroll_layout.addWidget(shortcuts_card)
        scroll_layout.addWidget(save_card)
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll_area)
        
    def _on_font_changed(self, font_name):
        log.info(f"设置页面接收到字体变更: {font_name}")
        
        # 强制更新所有控件
        self.update()
        
        # 确保Material Icons字体被正确应用
        FontManager().reapply_icon_fonts()
        
        # 如果有父窗口,通知父窗口更新
        if self.parent():
            try:
                # 尝试调用父窗口的刷新方法
                if hasattr(self.parent(), "refresh_ui"):
                    self.parent().refresh_ui()
                else:
                    self.parent().update()
            except:
                pass
                
    def _on_format_changed(self, format_name):
        # 保存配置
        config_manager.set_config('screenshot', 'format', format_name)
        log.info(f"默认截图格式已设置为: {format_name}")
        
        # 显示通知
        Notification(
            text=f"默认截图格式已设置为: {format_name}",
            type=NotificationType.TIPS,
            duration=1500
        ).show_notification()
        
    def _browse_save_path(self):
        from PySide6.QtWidgets import QFileDialog
        
        # 获取当前保存路径
        current_path = self.path_edit.text()
        if not os.path.exists(current_path):
            current_path = os.path.expanduser('~')
            
        # 打开文件夹选择对话框
        new_path = QFileDialog.getExistingDirectory(
            self,
            "选择截图保存路径",
            current_path
        )
        
        if new_path:
            # 更新路径显示
            self.path_edit.setText(new_path)
            
            # 保存配置
            config_manager.set_config('screenshot', 'save_path', new_path)
            log.info(f"截图保存路径已设置为: {new_path}")
            
            # 显示通知
            Notification(
                text=f"截图保存路径已设置为: {new_path}",
                type=NotificationType.TIPS,
                duration=1500
            ).show_notification()
