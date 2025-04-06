import os
import json
import random
import traceback
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
                              QMenu, QApplication, QMessageBox,
                              QMainWindow)
from PySide6.QtGui import QCursor, QAction

from Aya_Hanabi.Hanabi_Core.UI.iconButton import IconButton
from Aya_Hanabi.Hanabi_Core.FontManager.fontManager import IconProvider
from Aya_Hanabi.Hanabi_Core.UI.messageBox import HanabiMessageBox, information, warning, critical, question, success

# 导入日志函数
def log_to_file(message):
    try:
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        log_file = os.path.join(log_dir, "hanabi_debug.log")
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{message}\n")
    except Exception as e:
        print(f"写入日志文件出错: {e}")

class StatusBar(QWidget):
    fontSizeChanged = Signal(int)
    previewModeChanged = Signal(bool)
    highlightModeChanged = Signal(bool)
    scrollToLineRequested = Signal(int)
    
    # 类级别的状态标志，防止递归调用
    _settings_opening = False
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        # 初始化时不设置样式，在updateStyle中设置
        
        self.previewMode = False
        self.highlightMode = True  # 默认开启高亮
        self.currentFileType = "text"  # 默认文件类型
        self.cursorPosition = {"line": 1, "column": 1}  # 默认光标位置
        
        # 从设置文件读取字体大小
        self.currentFontSize = self.loadFontSizeFromSettings()
        print(f"状态栏初始化时的字体大小: {self.currentFontSize}")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 15, 0)
        layout.setSpacing(8)
        
        leftButtons = QHBoxLayout()
        leftButtons.setSpacing(12)
        leftButtons.setContentsMargins(0, 0, 0, 0)
        
        buttonSize = 26
        
        settingsContainer = QWidget()
        settingsContainer.setFixedSize(buttonSize, buttonSize)
        settingsContainer.setStyleSheet("background-color: transparent;")
        settingsLayout = QHBoxLayout(settingsContainer)
        settingsLayout.setContentsMargins(0, 0, 0, 0)
        
        settingsBtn = IconButton("settings", 16)
        settingsBtn.setToolTip("设置")
        settingsLayout.addWidget(settingsBtn)
        
        highlightContainer = QWidget()
        highlightContainer.setFixedSize(buttonSize, buttonSize)
        highlightContainer.setStyleSheet("background-color: transparent;")
        highlightLayout = QHBoxLayout(highlightContainer)
        highlightLayout.setContentsMargins(0, 0, 0, 0)
        
        self.highlightBtn = IconButton("code", 16)
        self.highlightBtn.setToolTip("语法高亮开关")
        highlightLayout.addWidget(self.highlightBtn)
        
        fontSizeContainer = QWidget()
        fontSizeContainer.setFixedSize(buttonSize, buttonSize)
        fontSizeContainer.setStyleSheet("background-color: transparent;")
        fontSizeLayout = QHBoxLayout(fontSizeContainer)
        fontSizeLayout.setContentsMargins(0, 0, 0, 0)
        
        fontSizeBtn = IconButton("format_size", 16)
        fontSizeBtn.setToolTip("调整字体大小")
        fontSizeBtn.clicked.connect(self.showFontSizeMenu)
        fontSizeLayout.addWidget(fontSizeBtn)
        
        scrollTestContainer = QWidget()
        scrollTestContainer.setFixedSize(buttonSize, buttonSize)
        scrollTestContainer.setStyleSheet("background-color: transparent;")
        scrollTestLayout = QHBoxLayout(scrollTestContainer)
        scrollTestLayout.setContentsMargins(0, 0, 0, 0)
        
        scrollTestBtn = IconButton("linear_scale", 16)
        scrollTestBtn.setToolTip("测试滚动动画")
        scrollTestBtn.clicked.connect(self.testScrollAnimation)
        scrollTestLayout.addWidget(scrollTestBtn)
        
        leftButtons.addWidget(settingsContainer)
        leftButtons.addWidget(highlightContainer)
        leftButtons.addWidget(fontSizeContainer)
        leftButtons.addWidget(scrollTestContainer)
        
        leftContainer = QWidget()
        leftContainer.setStyleSheet("background-color: transparent;")
        leftContainer.setLayout(leftButtons)
        layout.addWidget(leftContainer)
        
        # 中间区域 - 文件类型显示
        middleContainer = QWidget()
        middleContainer.setStyleSheet("background-color: transparent;")
        middleLayout = QHBoxLayout(middleContainer)
        middleLayout.setContentsMargins(0, 0, 0, 0)
        middleLayout.setSpacing(15)
        
        self.fileTypeLabel = QLabel("文本文件")
        self.fileTypeLabel.setToolTip("当前文件类型")
        middleLayout.addWidget(self.fileTypeLabel)
        
        layout.addWidget(middleContainer)
        
        # 右侧区域
        rightContainer = QWidget()
        rightContainer.setStyleSheet("background-color: transparent;")
        rightLayout = QHBoxLayout(rightContainer)
        rightLayout.setContentsMargins(0, 0, 0, 0)
        rightLayout.setSpacing(15)
        
        # 光标位置显示
        self.cursorPositionLabel = QLabel("第1行 第1列")
        self.cursorPositionLabel.setToolTip("当前光标位置")
        rightLayout.addWidget(self.cursorPositionLabel)
        
        # 行数显示
        self.lineCount = QLabel("0 行")
        rightLayout.addWidget(self.lineCount)
        
        layout.addStretch(1)
        layout.addWidget(rightContainer)
        
        # 应用初始样式
        self.updateStyle()
        
        # 连接设置按钮点击事件
        settingsBtn.clicked.connect(self.openSettings)
        # 连接高亮按钮点击事件
        self.highlightBtn.clicked.connect(self.toggleHighlightMode)
    
    def loadFontSizeFromSettings(self):
        # 从设置文件读取字体大小，如果没有则使用默认值15
        try:
            settings_dir = os.path.join(os.path.expanduser("~"), ".hanabi_notes")
            settings_file = os.path.join(settings_dir, "settings.json")
            
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                if "editor" in settings and "font" in settings["editor"]:
                    font_settings = settings["editor"]["font"]
                    if "size" in font_settings:
                        size = font_settings.get("size", 15)
                        print(f"从设置文件读取字体大小: {size}")
                        return size
        except Exception as e:
            print(f"读取字体大小设置时出错: {e}")
        
        print("使用默认字体大小: 15")
        return 15  # 默认字体大小
    
    def updateStyle(self):
        """更新状态栏样式"""
        if hasattr(self.parent(), 'themeManager') and self.parent().themeManager:
            themeManager = self.parent().themeManager
            
            # 直接从主题获取颜色设置
            bg_color = themeManager.current_theme.get("status_bar.background", "#1a1d23")
            text_color = themeManager.current_theme.get("status_bar.text_color", "#e0e0e0")
            icon_color = themeManager.current_theme.get("status_bar.icon_color", "rgba(255, 255, 255, 0.7)")
            active_icon_color = themeManager.current_theme.get("status_bar.active_icon_color", "#6b9fff")
            bg_hover_color = themeManager.current_theme.get("status_bar.hover_bg", "rgba(0, 0, 0, 0.1)")
            line_count_bg = themeManager.current_theme.get("status_bar.line_count_bg", "rgba(0, 0, 0, 0.1)")
            
            # 判断是否为暗色主题，调整悬停效果
            is_dark_theme = False
            if hasattr(themeManager, 'current_theme_name'):
                is_dark_theme = themeManager.current_theme_name in ["dark", "purple_dream", "green_theme"]
            
            # 根据主题类型调整悬停背景透明度
            if is_dark_theme:
                bg_hover_color = themeManager.current_theme.get("status_bar.hover_bg", "rgba(255, 255, 255, 0.05)")
            
            # 创建状态栏基本样式
            status_style = f"""
                QWidget {{
                    background-color: {bg_color};
                    color: {text_color};
                }}
            """
            
            # 应用状态栏样式
            self.setStyleSheet(status_style)
            
            # 更新按钮样式
            for btn in self.findChildren(IconButton):
                if btn == self.highlightBtn and self.highlightMode:
                    btn.updateStyle(icon_color=active_icon_color, hover_bg=bg_hover_color, active=True)
                else:
                    btn.updateStyle(icon_color=icon_color, hover_bg=bg_hover_color, active=False, active_color=active_icon_color)
            
            # 更新标签样式
            status_label_style = f"color: {text_color}; font-size: 12px; background-color: {line_count_bg}; padding: 3px 8px; border-radius: 4px;"
            self.lineCount.setStyleSheet(status_label_style)
            self.fileTypeLabel.setStyleSheet(status_label_style)
            self.cursorPositionLabel.setStyleSheet(status_label_style)
        else:
            # 如果没有主题管理器，则使用 ThemeManager 中的默认主题
            try:
                from Aya_Hanabi.Hanabi_Core.ThemeManager.themeManager import ThemeManager
                from Aya_Hanabi.Hanabi_Core.UI.messageBox import HanabiMessageBox, information, warning, critical, question, success
                tmpThemeManager = ThemeManager()
                
                # 获取默认主题的颜色设置
                bg_color = tmpThemeManager.current_theme.get("status_bar.background", "#1a1d23")
                text_color = tmpThemeManager.current_theme.get("status_bar.text_color", "#e0e0e0")
                icon_color = tmpThemeManager.current_theme.get("status_bar.icon_color", "rgba(255, 255, 255, 0.7)")
                active_icon_color = tmpThemeManager.current_theme.get("status_bar.active_icon_color", "#6b9fff")
                bg_hover_color = tmpThemeManager.current_theme.get("status_bar.hover_bg", "rgba(0, 0, 0, 0.1)")
                line_count_bg = tmpThemeManager.current_theme.get("status_bar.line_count_bg", "rgba(0, 0, 0, 0.1)")
                
                # 判断是否为暗色主题，调整悬停效果
                is_dark_theme = False
                if hasattr(tmpThemeManager, 'current_theme_name'):
                    is_dark_theme = tmpThemeManager.current_theme_name in ["dark", "purple_dream", "green_theme"]
                
                # 根据主题类型调整悬停背景透明度
                if is_dark_theme:
                    bg_hover_color = tmpThemeManager.current_theme.get("status_bar.hover_bg", "rgba(255, 255, 255, 0.05)")
                
                # 创建状态栏基本样式
                status_style = f"""
                    QWidget {{
                        background-color: {bg_color};
                        color: {text_color};
                    }}
                """
                
                # 应用状态栏样式
                self.setStyleSheet(status_style)
                
                # 更新按钮样式
                for btn in self.findChildren(IconButton):
                    if btn == self.highlightBtn and self.highlightMode:
                        btn.updateStyle(icon_color=active_icon_color, hover_bg=bg_hover_color, active=True)
                    else:
                        btn.updateStyle(icon_color=icon_color, hover_bg=bg_hover_color, active=False, active_color=active_icon_color)
                
                # 更新标签样式
                status_label_style = f"color: {text_color}; font-size: 12px; background-color: {line_count_bg}; padding: 3px 8px; border-radius: 4px;"
                self.lineCount.setStyleSheet(status_label_style)
                self.fileTypeLabel.setStyleSheet(status_label_style)
                self.cursorPositionLabel.setStyleSheet(status_label_style)
            except Exception as e:
                print(f"使用默认主题管理器时出错: {e}")
                log_to_file(f"使用默认主题管理器时出错: {e}")
    
    def updateFileType(self, fileType):
        """更新文件类型显示"""
        self.currentFileType = fileType
        
        # 根据文件类型显示友好名称
        fileTypeMap = {
            "text": "文本文件",
            "python": "Python",
            "markdown": "Markdown",
            "html": "HTML",
            "javascript": "JavaScript",
            "json": "JSON",
            "c": "C",
            "cpp": "C++",
            "css": "CSS",
            "java": "Java",
            "xml": "XML",
            "sql": "SQL",
            "yaml": "YAML",
            "rst": "reStructuredText"
        }
        
        displayName = fileTypeMap.get(fileType, fileType.capitalize() if fileType else "未知类型")
        self.fileTypeLabel.setText(displayName)
        print(f"状态栏更新文件类型: {displayName}")
    
    def updateCursorPosition(self, line, column):
        """更新光标位置显示"""
        self.cursorPosition = {"line": line, "column": column}
        self.cursorPositionLabel.setText(f"第{line}行 第{column}列")
        print(f"状态栏更新光标位置: 第{line}行 第{column}列")
    
    def openSettings(self):
        # 使用类级别的标志来防止递归
        if StatusBar._settings_opening:
            print("警告：全局设置窗口已在打开中，已阻止重复调用")
            return
            
        StatusBar._settings_opening = True
        try:
            print("正在尝试打开设置...")
            log_to_file("正在尝试打开设置...")
            
            # 导入所需的模块
            from PySide6.QtWidgets import QMainWindow
            from PySide6.QtCore import QTimer
            
            parent_obj = self.parent()
            if hasattr(parent_obj, "showSettings"):
                try:
                    print("找到父对象的 showSettings 方法，使用延迟调用...")
                    log_to_file("找到父对象的 showSettings 方法，使用延迟调用...")
                    # 直接调用父对象的showSettings方法
                    parent_obj.showSettings()
                except Exception as inner_e:
                    error_msg = f"调用父对象的 showSettings 方法时出错: {inner_e}"
                    print(error_msg)
                    log_to_file(error_msg)
                    import traceback
                    trace_info = traceback.format_exc()
                    print(trace_info)
                    log_to_file(trace_info)
                    warning(self, "错误", f"打开设置时出错: {str(inner_e)}")
            else:
                # 尝试使用顶层窗口
                print("父对象没有 showSettings 方法，尝试在顶层窗口中查找...")
                log_to_file("父对象没有 showSettings 方法，尝试在顶层窗口中查找...")
                from PySide6.QtWidgets import QApplication
                main_windows = [w for w in QApplication.topLevelWidgets() if isinstance(w, QMainWindow)]
                for w in main_windows:
                    if hasattr(w, "showSettings"):
                        try:
                            print(f"在顶层窗口中找到 showSettings 方法，直接调用...")
                            log_to_file(f"在顶层窗口中找到 showSettings 方法，直接调用...")
                            # 直接调用方法，不使用延迟
                            w.showSettings()
                            return
                        except Exception as inner_e:
                            error_msg = f"调用顶层窗口的 showSettings 方法时出错: {inner_e}"
                            print(error_msg)
                            log_to_file(error_msg)
                            import traceback
                            trace_info = traceback.format_exc()
                            print(trace_info)
                            log_to_file(trace_info)
                            warning(self, "错误", f"打开设置时出错: {str(inner_e)}")
                
                # 如果找不到具有showSettings方法的窗口，显示默认消息
                print("找不到具有 showSettings 方法的窗口，显示默认消息...")
                log_to_file("找不到具有 showSettings 方法的窗口，显示默认消息...")
                information(self, "设置", "设置功能即将推出！")
        except Exception as e:
            error_msg = f"打开设置时出错: {e}"
            print(error_msg)
            log_to_file(error_msg)
            import traceback
            trace_info = traceback.format_exc()
            print(trace_info)
            log_to_file(trace_info)
            warning(self, "错误", f"打开设置时出错: {str(e)}")
        finally:
            # 20毫秒后释放锁，给对话框足够的时间初始化
            def release_lock():
                StatusBar._settings_opening = False
                print("设置窗口锁定已释放")
            QTimer.singleShot(1000, release_lock)
    
    def toggleHighlightMode(self):
        self.highlightMode = not self.highlightMode
        
        # 获取主题颜色
        if hasattr(self.parent(), 'themeManager') and self.parent().themeManager:
            themeManager = self.parent().themeManager
            active_icon_color = themeManager.current_theme.get("status_bar.active_icon_color", "#6b9fff")
            icon_color = themeManager.current_theme.get("status_bar.icon_color", "rgba(255, 255, 255, 0.7)")
            bg_hover_color = themeManager.current_theme.get("status_bar.hover_bg", "rgba(0, 0, 0, 0.1)")
            
            # 判断是否为暗色主题，调整悬停效果
            is_dark_theme = False
            if hasattr(themeManager, 'current_theme_name'):
                is_dark_theme = themeManager.current_theme_name in ["dark", "purple_dream", "green_theme"]
            
            # 根据主题类型调整悬停背景透明度
            if is_dark_theme:
                bg_hover_color = themeManager.current_theme.get("status_bar.hover_bg", "rgba(255, 255, 255, 0.05)")
        else:
            # 默认颜色
            active_icon_color = "#6b9fff"
            icon_color = "rgba(0, 0, 0, 0.7)"
            bg_hover_color = "rgba(0, 0, 0, 0.1)"
        
        # 更新按钮样式
        if self.highlightMode:
            self.highlightBtn.updateStyle(icon_color=active_icon_color, hover_bg=bg_hover_color, active=True)
        else:
            self.highlightBtn.updateStyle(icon_color=icon_color, hover_bg=bg_hover_color, active=False)
        
        # 发送高亮状态变化信号
        try:
            self.highlightModeChanged.emit(self.highlightMode)
            print(f"高亮模式切换为: {self.highlightMode}")
        except Exception as e:
            print(f"在发送高亮状态变化信号时出错: {e}")
            log_to_file(f"在发送高亮状态变化信号时出错: {e}")
    
    # 为向后兼容保留
    def togglePreviewMode(self):
        self.previewMode = not self.previewMode
        self.previewModeChanged.emit(self.previewMode)
    
    def showFontSizeMenu(self):
        """显示字体大小选择菜单"""
        menu = QMenu(self)
        
        # 获取主题颜色
        if hasattr(self.parent(), 'themeManager') and self.parent().themeManager:
            themeManager = self.parent().themeManager
            
            # 判断是否为暗色主题
            is_dark_theme = False
            if hasattr(themeManager, 'current_theme_name'):
                is_dark_theme = themeManager.current_theme_name in ["dark", "purple_dream", "green_theme"]
            
            if is_dark_theme:
                bg_color = themeManager.current_theme.get("window.background", "#1e2128")
                text_color = themeManager.current_theme.get("window.text_color", "#e0e0e0")
                border_color = themeManager.current_theme.get("window.border", "#2a2e36")
                highlight_color = themeManager.current_theme.get("status_bar.active_icon_color", "#6b9fff")
                hover_bg = themeManager.current_theme.get("status_bar.hover_bg", "rgba(255, 255, 255, 0.05)")
            else:
                bg_color = themeManager.current_theme.get("window.background", "#f8f8f8")
                text_color = themeManager.current_theme.get("window.text_color", "#333333")
                border_color = themeManager.current_theme.get("window.border", "#d0d0d0")
                highlight_color = themeManager.current_theme.get("status_bar.active_icon_color", "#0066cc")
                hover_bg = themeManager.current_theme.get("status_bar.hover_bg", "rgba(0, 0, 0, 0.05)")
        else:
            # 默认颜色
            bg_color = "#f8f8f8"
            text_color = "#333333"
            border_color = "#d0d0d0"
            highlight_color = "#0066cc"
            hover_bg = "rgba(0, 0, 0, 0.1)"
            
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 4px 25px 4px 10px;
                border-radius: 3px;
            }}
            QMenu::item:selected {{
                background-color: {hover_bg};
            }}
            QMenu::item[selected=true] {{
                font-weight: bold;
                color: {highlight_color};
            }}
        """)
        
        fontSizes = [12, 14, 15, 16, 18, 20, 22, 24]
        for size in fontSizes:
            action = QAction(f"{size}px", self)
            action.triggered.connect(lambda checked, s=size: self.changeFontSize(s))
            if size == self.currentFontSize:
                # 选中的字体大小使用不同的文本颜色和背景色来标记，而不是使用图标
                action.setText(f"✓ {size}px")
                # 设置特殊样式
                action.setProperty("selected", True)
            menu.addAction(action)
        
        pos = self.mapToGlobal(self.findChild(QWidget, "", options=Qt.FindChildrenRecursively).pos())
        pos.setY(pos.y() - menu.sizeHint().height())
        menu.exec(pos)
    
    def changeFontSize(self, size):
        """更改字体大小并发出信号"""
        # 只有在字体大小真的变化时才更新和发出信号
        if self.currentFontSize != size:
            self.currentFontSize = size
            print(f"状态栏字体大小已更改为: {size}")
            self.fontSizeChanged.emit(size)
            
            # 保存字体大小到设置文件
            try:
                settings_dir = os.path.join(os.path.expanduser("~"), ".hanabi_notes")
                if not os.path.exists(settings_dir):
                    os.makedirs(settings_dir)
                
                settings_file = os.path.join(settings_dir, "settings.json")
                settings = {}
                
                # 读取现有设置
                if os.path.exists(settings_file):
                    try:
                        with open(settings_file, 'r', encoding='utf-8') as f:
                            settings = json.load(f)
                    except:
                        settings = {}
                
                # 确保有编辑器和字体设置
                if 'editor' not in settings:
                    settings['editor'] = {}
                if 'font' not in settings['editor']:
                    settings['editor']['font'] = {}
                
                # 更新字体大小设置
                settings['editor']['font']['size'] = size
                
                # 保存设置
                with open(settings_file, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, ensure_ascii=False, indent=2)
                
                print(f"字体大小 {size} 已保存到设置文件")
            except Exception as e:
                print(f"保存字体大小设置时出错: {e}")
        else:
            print(f"字体大小未变化，仍为: {size}")
    
    def testScrollAnimation(self):
        random_line = random.randint(10, 100)
        self.scrollToLineRequested.emit(random_line) 