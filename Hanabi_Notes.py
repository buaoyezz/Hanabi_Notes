import sys
import os
import re
import time
import json
import traceback
import platform
import threading
import tempfile
import datetime
from functools import partial
from pathlib import Path
from PySide6.QtCore import Qt, QPoint, Signal, QEvent, QTimer, QRect, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QSequentialAnimationGroup
from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, 
                              QHBoxLayout, QPushButton, QTextEdit, QPlainTextEdit, QWidget, QSplitter, QStackedWidget,
                              QMessageBox, QScrollBar, QFileDialog, QGraphicsOpacityEffect)
from PySide6.QtGui import QFont, QColor, QCursor, QTextCursor, QTextFormat, QSyntaxHighlighter, QTextCharFormat

# 导入文件管理相关功能
from Aya_Hanabi.Hanabi_Core.FileManager import (
    FileManager, open_file, save_file, new_file, delete_file, 
    close_file, change_file, AutoSave
)

# 导入自动备份管理器
from Aya_Hanabi.Hanabi_Core.FileManager.autoBackup import AutoBackup


from Aya_Hanabi.Hanabi_Core.UI import TitleBar, StatusBar, IconButton
from Aya_Hanabi.Hanabi_Core.Editor import EditorManager
from Aya_Hanabi.Hanabi_Core.UI.messageBox import HanabiMessageBox, information, warning, critical, question, success

# 导入新的设置面板
try:
    from Aya_Hanabi.Hanabi_Page.HanabiSettingsPanel import HanabiSettingsPanel
    print("成功导入新的设置面板")
except ImportError as e:
    print(f"导入新的设置面板失败: {e}")
    HanabiSettingsPanel = None

# 插件系统已移除
PluginManager = None

# 添加调试日志功能
def log_to_file(message):
    try:
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        log_file = os.path.join(log_dir, "hanabi_debug.log")
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{message}\n")
    except Exception as e:
        print(f"写入日志文件出错: {e}")

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from Aya_Hanabi.Hanabi_Core.FontManager.fontManager import IconProvider, ICONS
    from Aya_Hanabi.Hanabi_Core.SidebarManager import SidebarMode
    from Aya_Hanabi.Hanabi_Core.SidebarManager.sidebarWidget import SidebarWidget
    from Aya_Hanabi.Hanabi_Core.ThemeManager import ThemeManager
    
    # 优先导入新的设置面板
    try:
        from Aya_Hanabi.Hanabi_Page.HanabiSettingsPanel import HanabiSettingsPanel
        print("成功从替代路径导入新的设置面板HanabiSettingsPanel")
        # 为了兼容性，仍然导入旧的设置对话框
        from Aya_Hanabi.Hanabi_Page.SettingsPages import SettingsDialog
        print("成功从替代路径导入旧的设置对话框SettingsDialog")
    except ImportError as e:
        print(f"从替代路径导入新的设置面板失败: {e}")
        # 回退到仅使用旧的设置对话框
        from Aya_Hanabi.Hanabi_Page.SettingsPages import SettingsDialog
        print("从替代路径回退到使用旧的设置对话框SettingsDialog")
        HanabiSettingsPanel = None
    
    # 主题设置对话框导入
    try:
        from Aya_Hanabi.Hanabi_Page.SettingsPages import ThemeSettingsDialog
        print("成功从替代路径导入ThemeSettingsDialog")
    except ImportError:
        try:
            from Aya_Hanabi.Hanabi_Page.Settings.LegacyTheme.ThemeSettingsDialog import ThemeSettingsDialog
            print("从替代路径的LegacyTheme导入ThemeSettingsDialog")
        except ImportError:
            print("无法从替代路径导入ThemeSettingsDialog，主题设置功能不可用")
    
    from Aya_Hanabi.Hanabi_HighLight import get_highlighter, detect_file_type
    try:
        from Aya_Hanabi.Hanabi_Core.App.init import app_Optimizer
        print("成功导入应用优化器")
    except ImportError as app_err:
        print(f"应用优化器导入失败: {app_err}")
        app_Optimizer = None
except ImportError as e:
    print(f"导入模块错误: {e}")
    alternative_path = os.path.join(os.path.dirname(current_dir), "HanabiNotes")
    if os.path.exists(alternative_path):
        sys.path.append(alternative_path)
        try:
            from Aya_Hanabi.Hanabi_Core.FontManager.fontManager import IconProvider, ICONS
            from Aya_Hanabi.Hanabi_Core.SidebarManager import SidebarMode
            from Aya_Hanabi.Hanabi_Core.SidebarManager.sidebarWidget import SidebarWidget
            from Aya_Hanabi.Hanabi_Core.ThemeManager import ThemeManager
            from Aya_Hanabi.Hanabi_Page.SettingsPages import SettingsDialog
            # 使用新位置的ThemeSettingsDialog
            try:
                from Aya_Hanabi.Hanabi_Page.SettingsPages import ThemeSettingsDialog
                print("成功从新位置导入ThemeSettingsDialog")
            except ImportError:
                from Aya_Hanabi.Hanabi_Page.SettingsPages import ThemeSettingsDialog
                print("从原始位置导入ThemeSettingsDialog")
            from Aya_Hanabi.Hanabi_HighLight import get_highlighter, detect_file_type
            try:
                from Aya_Hanabi.Hanabi_Core.App.init import app_Optimizer
                print("成功导入应用优化器(替代路径)")
            except ImportError as app_err:
                print(f"应用优化器导入失败(替代路径): {app_err}")
                app_Optimizer = None
        except ImportError as e2:
            print(f"尝试其他路径后仍然导入失败: {e2}")
            sys.exit(1)
    else:
        print("无法找到正确的模块路径")
        sys.exit(1)

try:
    from Aya_Hanabi.Hanabi_Styles.scrollbar_style import ScrollBarStyle
except ImportError as e:
    print(f"导入样式模块错误: {e}")
    
    class ScrollBarStyle:
        @staticmethod
        def get_style(base_color="#005780", handle_color="rgba(255, 255, 255, 0.3)"):
            return f"""
                QScrollBar:vertical {{
                    background-color: {base_color};
                    width: 6px;
                    margin: 0px;
                    border-radius: 3px;
                }}
                
                QScrollBar::handle:vertical {{
                    background-color: {handle_color};
                    min-height: 30px;
                    border-radius: 3px;
                }}
                
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                    height: 0px;
                }}
                
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                    background: none;
                }}
            """

class HanabiNotesApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # 设置窗口基本属性
        self.setWindowTitle("Hanabi Notes")
        self.resize(950, 700)
        
        # 初始化变量
        self.currentFilePath = None
        self.currentEditor = None
        self.currentTitle = "未命名"
        self.currentFileType = "text"  # 默认文件类型
        self.highlightMode = True
        self.lastDirectory = None
        self.openFiles = []  # 已打开文件的列表
        self.closedEditors = []  # 已关闭编辑器的列表
        
        # 窗口拖拽调整大小相关变量
        self.resizeEdgeWidth = 8  # 拖拽区域宽度
        self.isResizing = False
        self.resizeMode = None  # 调整方向: None, 'left', 'right', 'top', 'bottom', 'topleft', 'topright', 'bottomleft', 'bottomright'
        self.startPos = None
        self.startGeometry = None
        
        # 初始化自动保存
        self.autoSaveManager = AutoSave(self, interval=120)
        
        # 初始化自动备份
        self.autoBackupManager = AutoBackup(self, max_backups=10)
        
        # 初始化主题
        self.themeManager = ThemeManager()
        
        # 初始化编辑器管理器
        self.editorManager = EditorManager(self)
        
        # 初始化优化器
        if 'app_Optimizer' in globals() and app_Optimizer:
            self.optimizer = app_Optimizer
            self.optimizer.start_memory_monitor()  # 启动内存监控
            print("应用优化器已启用")
        else:
            self.optimizer = None
        
        # 初始化插件管理器
        try:
            from Aya_Hanabi.Hanabi_Core.PluginManager import PluginManager
            self.plugin_manager = PluginManager(self)
            self.plugin_manager.initialize()
            print("插件管理器已初始化")
        except ImportError as e:
            print(f"插件系统导入失败: {e}")
            self.plugin_manager = None
        except Exception as e:
            print(f"插件管理器初始化失败: {e}")
            self.plugin_manager = None
        
        # 初始化UI
        self.initUI()
    
    def mousePressEvent(self, event):
        """处理鼠标按下事件，检测是否在窗口边缘区域进行拖拽调整大小"""
        if event.button() == Qt.LeftButton:
            # 获取当前鼠标位置，检查是否在边缘区域
            pos = event.position().toPoint()
            resizeMode = self.getResizeMode(pos)
            
            if resizeMode:
                # 如果在边缘区域，标记为正在调整大小
                self.isResizing = True
                self.resizeMode = resizeMode
                self.startPos = pos
                self.startGeometry = self.geometry()
                event.accept()
                return
        
        # 如果不是调整大小操作，交给基类处理
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """处理鼠标移动事件，更新窗口大小或更新鼠标光标形状"""
        pos = event.position().toPoint()
        
        # 如果正在调整大小
        if self.isResizing and self.resizeMode:
            # 计算鼠标移动的距离
            dx = pos.x() - self.startPos.x()
            dy = pos.y() - self.startPos.y()
            
            # 获取初始几何信息
            newGeometry = QRect(self.startGeometry)
            
            # 根据调整模式更新窗口几何信息
            if 'left' in self.resizeMode:
                newGeometry.setLeft(self.startGeometry.left() + dx)
            if 'right' in self.resizeMode:
                newGeometry.setRight(self.startGeometry.right() + dx)
            if 'top' in self.resizeMode:
                newGeometry.setTop(self.startGeometry.top() + dy)
            if 'bottom' in self.resizeMode:
                newGeometry.setBottom(self.startGeometry.bottom() + dy)
            
            # 检查新大小是否满足最小尺寸要求
            if newGeometry.width() >= self.minimumWidth() and newGeometry.height() >= self.minimumHeight():
                self.setGeometry(newGeometry)
            
            event.accept()
            return
        elif not event.buttons() & Qt.LeftButton:
            # 如果没有按下鼠标，更新鼠标光标形状
            resizeMode = self.getResizeMode(pos)
            if resizeMode:
                if resizeMode == 'left' or resizeMode == 'right':
                    self.setCursor(Qt.SizeHorCursor)
                elif resizeMode == 'top' or resizeMode == 'bottom':
                    self.setCursor(Qt.SizeVerCursor)
                elif resizeMode == 'topleft' or resizeMode == 'bottomright':
                    self.setCursor(Qt.SizeFDiagCursor)
                elif resizeMode == 'topright' or resizeMode == 'bottomleft':
                    self.setCursor(Qt.SizeBDiagCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
        
        # 交给基类处理
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件，结束调整大小状态"""
        if event.button() == Qt.LeftButton and self.isResizing:
            self.isResizing = False
            self.resizeMode = None
            self.startPos = None
            self.startGeometry = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    def getResizeMode(self, pos):
        """
        根据鼠标位置判断调整窗口的模式
        返回值: None, 'left', 'right', 'top', 'bottom', 'topleft', 'topright', 'bottomleft', 'bottomright'
        """
        width = self.width()
        height = self.height()
        edge = self.resizeEdgeWidth
        
        # 判断鼠标是否在边缘区域
        onLeft = pos.x() < edge
        onRight = pos.x() > width - edge
        onTop = pos.y() < edge
        onBottom = pos.y() > height - edge
        
        # 根据位置确定调整模式
        if onTop and onLeft:
            return 'topleft'
        elif onTop and onRight:
            return 'topright'
        elif onBottom and onLeft:
            return 'bottomleft'
        elif onBottom and onRight:
            return 'bottomright'
        elif onLeft:
            return 'left'
        elif onRight:
            return 'right'
        elif onTop:
            return 'top'
        elif onBottom:
            return 'bottom'
        
        return None
    
    def onFileLoaded(self, filePath):
        """加载文件后的回调函数，设置当前文件路径和更新UI"""
        try:
            fileName = os.path.basename(filePath)
            self.currentFilePath = filePath
            
            # 根据文件后缀自动确定文件类型
            self.currentFileType = self.editorManager.detectFileType(filePath)
            
            # 设置对应的语法高亮
            if hasattr(self, 'currentEditor') and self.currentEditor is not None:
                if self.currentFileType == 'python':
                    self.currentEditor.setSyntaxHighlightFromName('python')
                elif self.currentFileType == 'markdown':
                    self.currentEditor.setSyntaxHighlightFromName('markdown')
                elif self.currentFileType == 'html':
                    self.currentEditor.setSyntaxHighlightFromName('html')
                elif self.currentFileType in ['javascript', 'json']:
                    self.currentEditor.setSyntaxHighlightFromName('javascript')
                elif self.currentFileType in ['c', 'cpp']:
                    self.currentEditor.setSyntaxHighlightFromName('cpp')
                else:
                    self.currentEditor.setSyntaxHighlightFromName('text')
                
                # 更新标签显示文件类型信息
                if self.tabWidget.count() > 0:
                    self.tabWidget.setTabToolTip(self.tabWidget.currentIndex(), f"{filePath} [{self.currentFileType}]")
            
            # 更新窗口标题和最近打开的文件列表
            self.setWindowTitle(f"{fileName} - Hanabi Notes")
            self.addToRecentFiles(filePath)
            self.updateWindowTitle()
            
            # 更新文件信息显示
            fileInfo = self.getFileInfo(filePath)
            self.updateFileInfo(fileInfo)
            
            # 更新文件已加载标志
            for fileData in self.openFiles:
                if fileData.get('filePath') == filePath:
                    fileData['isLoaded'] = True
                    break
            
            # 通知自动保存系统文件已加载
            if self.autoSaveManager:
                self.autoSaveManager.file_saved(filePath)
            
            print(f"文件已加载: {fileName}")
        except Exception as e:
            self.logError(f"加载文件后处理出错: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def onFileSaved(self, filePath, message):
        self.currentFilePath = filePath
        
        if self.sidebar.current_tab_index >= 0:
            fileName = os.path.splitext(os.path.basename(filePath))[0]
            self.sidebar.updateTabName(self.sidebar.current_tab_index, fileName, filePath)
            
            # 更新文件信息
            for file_info in self.openFiles:
                if file_info.get('index') == self.sidebar.current_tab_index:
                    file_info['filePath'] = filePath
                    file_info['title'] = fileName
                    break
        
        HanabiMessageBox.information(self, "保存成功", message)
    
    def deleteFile(self):
        # 使用FileManager中的delete_file功能
        delete_file(self)
    
    def changeFontSize(self, size):
        """更改所有编辑器的字体大小"""
        print(f"应用新的字体大小到所有编辑器: {size}")
        
        # 更新所有编辑器的字体样式
        for editor in self.editors:
            self.updateEditorStyle(editor, size)
        
        # 不使用showMessage方法，改为使用状态栏的其他方式或简单地打印日志
        try:
            if hasattr(self, 'statusBarWidget'):
                # 如果状态栏有message标签，可以用它显示消息
                if hasattr(self.statusBarWidget, 'message') and callable(getattr(self.statusBarWidget, 'setMessage', None)):
                    self.statusBarWidget.setMessage(f"字体大小已更改为 {size}px")
                elif hasattr(self.statusBarWidget, 'infoLabel') and hasattr(self.statusBarWidget.infoLabel, 'setText'):
                    # 如果有infoLabel，可以使用它
                    self.statusBarWidget.infoLabel.setText(f"字体大小已更改为 {size}px")
                else:
                    # 如果都没有，只打印日志
                    print(f"字体大小已更改为 {size}px")
        except Exception as e:
            # 如果出错，确保不影响主要功能
            print(f"显示字体大小变更消息时出错: {e}")
            print(f"字体大小已更改为 {size}px")
    
    def togglePreviewMode(self, enabled):
        currentEditorIndex = self.editorsStack.currentIndex()
        if 0 <= currentEditorIndex < len(self.editors):
            editorStack = self.editorsStack.widget(currentEditorIndex)
            if editorStack and editorStack.count() >= 2:
                editorStack.setCurrentIndex(1 if enabled else 0)
    
    def toggleHighlightMode(self, enabled):
        self.highlightMode = enabled
        
        # 应用或移除高亮
        if 0 <= self.editorsStack.currentIndex() < len(self.editors):
            currentEditor = self.editors[self.editorsStack.currentIndex()]
            if enabled:
                # 确保应用高亮时使用当前正确的文件类型
                self.applyHighlighter(currentEditor, self.currentFileType)
            else:
                if hasattr(currentEditor, 'highlighter') and currentEditor.highlighter:
                    currentEditor.highlighter.setDocument(None)
                    currentEditor.highlighter = None
    
    def onScrollToLineRequested(self, lineNumber):
        currentEditorIndex = self.editorsStack.currentIndex()
        if 0 <= currentEditorIndex < len(self.editors):
            editor = self.editors[currentEditorIndex]
            self.scrollToLine(editor, lineNumber)
    
    def updateEditorStyle(self, editor, fontSize=15):
        """更新编辑器样式"""
        self.editorManager.updateEditorStyle(editor, fontSize)
    
    def updateEditorContainerStyle(self, container):
        """更新编辑器容器样式"""
        self.editorManager.updateEditorContainerStyle(container)
    
    def updatePreview(self, editorIndex):
        """更新预览区域，将编辑器内容转换为预览格式"""
        try:
            if not hasattr(self, 'markdown') or not self.markdown:
                print("Markdown模块未加载，预览功能不可用")
                return
                
            if 0 <= editorIndex < len(self.editors) and editorIndex < len(self.previewViews):
                editor = self.editors[editorIndex]
                previewView = self.previewViews[editorIndex]
                
                text = editor.toPlainText()
                
                try:
                    # 使用markdown库转换内容
                    html = self.markdown.markdown(text, extensions=['tables', 'fenced_code'])
                    
                    # 添加基本样式
                    is_light_theme = hasattr(self, 'currentTheme') and self.currentTheme == "light"
                    
                    bg_color = '#ffffff' if is_light_theme else '#282c34'
                    text_color = '#333333' if is_light_theme else '#abb2bf'
                    link_color = '#4183c4' if is_light_theme else '#61afef'
                    code_bg = '#f5f5f5' if is_light_theme else '#3a3f4b'
                    
                    # 从主题获取颜色（如果可用）
                    if hasattr(self, 'themeManager') and self.themeManager and self.themeManager.current_theme:
                        if hasattr(self.themeManager.current_theme, 'get'):
                            bg_color = self.themeManager.current_theme.get("editor.background", bg_color)
                            text_color = self.themeManager.current_theme.get("editor.text_color", text_color)
                    
                    styled_html = f"""
                    <html>
                    <head>
                        <style>
                            body {{ 
                                font-family: 'Microsoft YaHei UI', Arial, sans-serif; 
                                line-height: 1.6;
                                color: {text_color};
                                background-color: {bg_color};
                                padding: 5px;
                            }}
                            h1, h2, h3, h4, h5, h6 {{ 
                                margin-top: 24px;
                                margin-bottom: 16px;
                                font-weight: 600;
                                line-height: 1.25;
                            }}
                            h1 {{ font-size: 2em; border-bottom: 1px solid #eaecef; padding-bottom: .3em; }}
                            h2 {{ font-size: 1.5em; border-bottom: 1px solid #eaecef; padding-bottom: .3em; }}
                            a {{ color: {link_color}; text-decoration: none; }}
                            a:hover {{ text-decoration: underline; }}
                            code {{ 
                                font-family: "Consolas", "Courier New", monospace; 
                                background-color: {code_bg};
                                padding: 0.2em 0.4em;
                                border-radius: 3px;
                            }}
                            pre {{ 
                                background-color: {code_bg}; 
                                border-radius: 3px; 
                                padding: 16px;
                                overflow: auto;
                            }}
                            pre code {{ 
                                background-color: transparent; 
                                padding: 0;
                            }}
                            blockquote {{ 
                                padding: 0 1em; 
                                color: #6a737d; 
                                border-left: 0.25em solid #dfe2e5; 
                            }}
                            table {{ 
                                border-collapse: collapse; 
                                width: 100%; 
                                margin-bottom: 16px; 
                            }}
                            table th, table td {{ 
                                border: 1px solid #dfe2e5; 
                                padding: 6px 13px; 
                            }}
                            table tr {{ 
                                background-color: {bg_color}; 
                            }}
                            table tr:nth-child(2n) {{ 
                                background-color: #f6f8fa; 
                            }}
                        </style>
                    </head>
                    <body>
                        {html}
                    </body>
                    </html>
                    """
                    
                    # 设置为纯文本，以便正确显示HTML格式
                    previewView.setPlainText(styled_html)
                except Exception as e:
                    previewView.setPlainText(f"预览生成出错: {str(e)}")
        except Exception as e:
            print(f"更新预览区域时出错: {str(e)}")
            # 不要抛出异常，避免应用崩溃
    
    def updateStatusBarStyle(self):
        if hasattr(self, 'statusBarWidget'):
            self.statusBarWidget.updateStyle()
    
    def scrollToLine(self, editor, lineNumber):
        self.editorManager.scrollToLine(editor, lineNumber)
    
    def applyHighlighter(self, editor, file_type):
        self.editorManager.applyHighlighter(editor, file_type)
    
    def highlightCurrentLine(self, editor):
        self.editorManager.highlightCurrentLine(editor)
    
    def restoreFormat(self, editor):
        self.editorManager.restoreFormat(editor)
    
    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 设置完全透明的背景和去除边框
        self.setStyleSheet("background: transparent; border: none;")
        
        screen_geometry = QApplication.screenAt(QPoint(0, 0)).geometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()

        if screen_width >= 1920:
            width_ratio = 0.65
            height_ratio = 0.7
            min_width_ratio = 0.4
            min_height_ratio = 0.4
        elif screen_width >= 1366:
            width_ratio = 0.7
            height_ratio = 0.7
            min_width_ratio = 0.45
            min_height_ratio = 0.45
        else:
            width_ratio = 0.8
            height_ratio = 0.75
            min_width_ratio = 0.5
            min_height_ratio = 0.5
        
        window_width = min(int(screen_width * width_ratio), 1200)
        window_height = min(int(screen_height * height_ratio), 800)
        self.resize(window_width, window_height)
        
        min_width = int(screen_width * min_width_ratio)
        min_height = int(screen_height * min_height_ratio)
        min_width = max(min_width, 800)
        min_height = max(min_height, 600)
        self.setMinimumSize(min_width, min_height)
        
        self.dragging = True
        
        IconProvider.init_font()
        
        # 初始化主题管理器
        self.themeManager = ThemeManager()
        self.themeManager.load_themes_from_directory()
        self.currentTheme = "dark"  # 默认主题
        
        try:
            # 初始化文件管理器
            self.fileManager = FileManager()
            self.fileManager.fileLoaded.connect(self.onFileLoaded)
            self.fileManager.fileSaved.connect(self.onFileSaved)
            self.fileManager.fileDeleted.connect(lambda path: print(f"文件已删除: {path}"))
            
            # 初始化自动保存功能
            self.autoSave = AutoSave(self)
            self.autoSave.start()
        except Exception as e:
            HanabiMessageBox.critical(self, "错误", f"无法加载文件管理器模块: {str(e)}")
        
        self.openFiles = []
        self.currentFilePath = None
        self.currentTitle = "未命名"
        self.currentFileType = "text"  # 默认为普通文本
        self.highlightMode = True  # 默认开启高亮
        
        mainWidget = QWidget()
        mainWidget.setObjectName("mainWindow")
        # 样式将在applyTheme中设置
        self.setCentralWidget(mainWidget)
        
        mainLayout = QVBoxLayout(mainWidget)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)
        
        self.titleBar = TitleBar(self)
        mainLayout.addWidget(self.titleBar)
        
        contentContainer = QWidget()
        contentLayout = QHBoxLayout(contentContainer)
        contentLayout.setContentsMargins(0, 0, 0, 0)
        contentLayout.setSpacing(0)
        
        self.sidebar = SidebarWidget()
        self.sidebar.importBtn.clicked.connect(self.openFile)
        self.sidebar.exportBtn.clicked.connect(self.saveFile)
        self.sidebar.newNoteBtn.clicked.connect(self.newFile)
        self.sidebar.deleteBtn.clicked.connect(self.deleteFile)
        self.sidebar.fileChanged.connect(self.changeFile)
        self.sidebar.fileClosed.connect(self.closeFile)
        
        self.editorsStack = QStackedWidget()
        self.editors = []
        self.previewViews = []
        
        # 添加堆栈改变信号连接，更新当前编辑器
        self.editorsStack.currentChanged.connect(self.onEditorStackChanged)
        
        editorWidget = QWidget()
        editorWidget.setObjectName("editorContainer")
        editorLayout = QVBoxLayout(editorWidget)
        editorLayout.setContentsMargins(0, 0, 0, 0)
        editorLayout.setSpacing(0)
        
        editorLayout.addWidget(self.editorsStack)
        
        contentLayout.addWidget(self.sidebar)
        contentLayout.addWidget(editorWidget)
        
        mainLayout.addWidget(contentContainer, 1)
        
        self.statusBarWidget = StatusBar(self)
        mainLayout.addWidget(self.statusBarWidget)
        
        self.statusBarWidget.fontSizeChanged.connect(self.changeFontSize)
        self.statusBarWidget.previewModeChanged.connect(self.togglePreviewMode)
        self.statusBarWidget.highlightModeChanged.connect(self.toggleHighlightMode)
        self.statusBarWidget.scrollToLineRequested.connect(self.onScrollToLineRequested)
        
        try:
            import markdown
            self.markdown = markdown
        except ImportError:
            HanabiMessageBox.warning(self, "缺少依赖", "未安装markdown模块，预览功能不可用。请执行 pip install markdown 安装。")
            self.markdown = None
        
        # 创建初始编辑器并在openFiles列表中记录
        firstEditorIndex = self.createNewEditor()
        
        # 记录初始标签页信息 (对应于侧边栏中默认创建的"未命名"标签页)
        self.openFiles.append({
            'index': 0,  # 第一个标签页索引是0
            'editorIndex': firstEditorIndex,
            'filePath': None,
            'title': "未命名",
            'isVirtual': True  # 标记为虚拟标签页
        })
        print(f"初始标签页已添加到openFiles列表，编辑器索引: {firstEditorIndex}")
        
        # 所有UI组件创建完成后应用主题
        self.applyTheme(self.currentTheme)
        
    def applyTheme(self, theme_name=None):
        """应用主题到应用程序"""
        print(f"----------开始应用主题: {theme_name}----------")
        theme_changed = False
        
        # 如果指定了主题名称，更新当前主题
        if theme_name and theme_name != self.currentTheme:
            self.currentTheme = theme_name
            theme_changed = True
            print(f"设置当前主题为: {self.currentTheme}")
        
        # 如果主题管理器尚未初始化，先初始化
        if not hasattr(self, 'themeManager') or not self.themeManager:
            try:
                from Aya_Hanabi.Hanabi_Core.ThemeManager.themeManager import ThemeManager
                self.themeManager = ThemeManager()
                self.themeManager.load_themes_from_directory()
                print("初始化主题管理器成功")
            except Exception as e:
                print(f"初始化主题管理器失败: {e}")
                return False
        
        # 设置当前主题
        try:
            print(f"通过主题管理器设置主题: {self.currentTheme}")
            success = self.themeManager.set_theme(self.currentTheme)
            print(f"设置主题结果: {success}")
            
            if not success:
                print(f"无法应用主题 {self.currentTheme}，尝试使用默认主题")
                # 尝试手动添加主题
                if self.currentTheme == "light":
                    try:
                        from Aya_Hanabi.Hanabi_Core.ThemeManager.themeManager import Theme
                        light_theme = {
                            "name": "light",
                            "display_name": "亮色主题",
                            "window": {
                                "background": "#f5f5f5",
                                "border": "#e0e0e0",
                                "radius": "10px"
                            },
                            "editor": {
                                "background": "#ffffff",
                                "text_color": "#333333",
                                "selection_color": "#a6c9ff",
                                "cursor_color": "#333333"
                            }
                        }
                        self.themeManager.add_theme(Theme("light", light_theme))
                        print("已添加亮色主题")
                        success = self.themeManager.set_theme("light")
                        print(f"重新尝试设置亮色主题，结果: {success}")
                    except Exception as e:
                        print(f"添加亮色主题失败: {e}")
                
                # 如果仍然失败，回退到暗色主题
                if not success:
                    self.currentTheme = "dark"
                    success = self.themeManager.set_theme("dark")
                    if not success:
                        print("无法应用默认主题，应用失败")
                        return False
        except Exception as e:
            print(f"设置主题时出错: {e}")
            try:
                # 尝试回退到默认主题
                self.currentTheme = "dark"
                self.themeManager.set_theme("dark")
                print("已回退到默认主题")
            except Exception as e2:
                print(f"回退到默认主题时也出错: {e2}")
                return False
        
        # 打印主题状态，帮助调试
        if hasattr(self.themeManager, 'current_theme_name'):
            print(f"主题管理器当前主题名称: {self.themeManager.current_theme_name}")
        
        # 检查主题数据
        theme_data_valid = False
        if hasattr(self.themeManager, 'current_theme') and self.themeManager.current_theme:
            theme_data_valid = True
            theme_name_attr = getattr(self.themeManager.current_theme, 'name', "未知")
            print(f"主题对象名称: {theme_name_attr}")
            
            # 检查主题数据
            bg_color = self.themeManager.current_theme.get("editor.background", "未设置")
            print(f"编辑器背景色: {bg_color}")
        else:
            print("警告: 主题数据不可用")
        
        try:        
            # 应用窗口样式
            window_style = self.themeManager.get_window_style()
            if window_style and self.centralWidget():
                self.centralWidget().setStyleSheet(window_style)
                print("已应用窗口样式")
            
            # 保存当前字体大小
            current_font_size = 15  # 默认值
            if hasattr(self, 'statusBarWidget') and hasattr(self.statusBarWidget, 'currentFontSize'):
                current_font_size = self.statusBarWidget.currentFontSize
            
            # 更新编辑器样式
            print(f"准备更新编辑器样式，编辑器数量: {len(self.editors) if hasattr(self, 'editors') else 0}")
            for i, editor in enumerate(self.editors if hasattr(self, 'editors') else []):
                try:
                    print(f"更新编辑器 {i} 的样式")
                    self.updateEditorStyle(editor, current_font_size)
                except Exception as e:
                    print(f"更新编辑器 {i} 样式时出错: {e}")
                    continue
                
            # 更新编辑器容器样式
            if hasattr(self, 'editorsStack'):
                print(f"准备更新编辑器容器样式，编辑器堆栈数量: {self.editorsStack.count()}")
                for i in range(self.editorsStack.count()):
                    try:
                        editorStack = self.editorsStack.widget(i)
                        if editorStack:
                            print(f"处理编辑器堆栈 {i}, 子控件数量: {editorStack.count()}")
                            for j in range(editorStack.count()):
                                container = editorStack.widget(j)
                                if container:
                                    print(f"更新容器 {i}.{j} 的样式")
                                    self.updateEditorContainerStyle(container)
                    except Exception as e:
                        print(f"更新编辑器容器 {i} 样式时出错: {e}")
                        continue
                        
            # 更新预览样式
            if hasattr(self, 'previewViews'):
                print(f"准备更新预览样式，预览视图数量: {len(self.previewViews)}")
                for i, preview in enumerate(self.previewViews):
                    try:
                        print(f"更新预览视图 {i}")
                        self.updatePreview(i)
                    except Exception as e:
                        print(f"更新预览视图 {i} 时出错: {e}")
                        continue
                
            # 更新标题栏样式
            if hasattr(self, 'titleBar'):
                try:
                    print("更新标题栏样式")
                    self.titleBar.updateStyle()
                except Exception as e:
                    print(f"更新标题栏样式时出错: {e}")
            
            # 更新侧边栏样式
            if hasattr(self, 'sidebar'):
                try:
                    print("更新侧边栏样式")
                    self.sidebar.updateStyle(self.themeManager)
                except Exception as e:
                    print(f"更新侧边栏样式时出错: {e}")
            
            # 更新状态栏样式
            try:
                print("更新状态栏样式")
                self.updateStatusBarStyle()
            except Exception as e:
                print(f"更新状态栏样式时出错: {e}")
                
            # 如果主题已更改，请求保存配置
            if theme_changed and theme_data_valid:
                try:
                    if hasattr(self.themeManager, 'save_theme_config'):
                        print("尝试保存主题配置")
                        self.themeManager.save_theme_config()
                        print("已保存主题配置")
                except Exception as e:
                    print(f"保存主题配置时出错: {e}")
            
            print(f"----------主题 {self.currentTheme} 应用完成----------")
            return True
            
        except Exception as e:
            print(f"应用主题过程中出错: {e}")
            import traceback
            print(traceback.format_exc())
            return False
    
    def createNewEditor(self):
        print("创建新编辑器")
        
        # 检查当前主题
        if hasattr(self, 'themeManager') and self.themeManager and hasattr(self.themeManager, 'current_theme_name'):
            print(f"创建新编辑器时的当前主题: {self.themeManager.current_theme_name}")
        
        editorStack = QStackedWidget()
        
        editorContainer = QWidget()
        editorContainer.setObjectName("editorContainer")
        # 初始样式将在后面通过updateEditorContainerStyle设置
        innerEditorLayout = QVBoxLayout(editorContainer)
        innerEditorLayout.setContentsMargins(15, 10, 15, 10)
        
        editor = QPlainTextEdit()
        editor.setObjectName(f"editor_{len(self.editors)}")
        
        # 确定当前主题
        theme_name = "unknown"
        if hasattr(self, 'themeManager') and self.themeManager and hasattr(self.themeManager, 'current_theme'):
            if hasattr(self.themeManager.current_theme, 'name'):
                theme_name = self.themeManager.current_theme.name
        
        print(f"创建编辑器时的当前主题: {theme_name}")
        
        # 获取字体大小设置
        font_size = 15  # 默认字体大小
        if hasattr(self, 'statusBarWidget') and hasattr(self.statusBarWidget, 'currentFontSize'):
            font_size = self.statusBarWidget.currentFontSize
            print(f"使用状态栏中的字体大小: {font_size}")
        
        # 设置编辑器样式
        self.updateEditorStyle(editor, font_size)
        editor.setPlaceholderText("输入内容...")
        
        try:
            if hasattr(self, 'themeManager') and self.themeManager:
                scrollbar_style = self.themeManager.get_scrollbar_style()
            else:
                scrollbar_style = ScrollBarStyle.get_style(base_color="transparent", handle_color="rgba(255, 255, 255, 0.3)")
            
            print(f"添加滚动条样式: {scrollbar_style[:50]}...")
            editor.setStyleSheet(editor.styleSheet() + scrollbar_style)
            
            editor.verticalScrollBar().setStyleSheet(scrollbar_style)
        except Exception as e:
            print(f"添加滚动条样式时出错: {e}")
        
        innerEditorLayout.addWidget(editor)
        
        previewContainer = QWidget()
        previewContainer.setObjectName("previewContainer")
        previewLayout = QVBoxLayout(previewContainer)
        previewLayout.setContentsMargins(15, 10, 15, 10)
        
        previewView = QPlainTextEdit()
        previewView.setReadOnly(True)
        
        # 预览视图样式将在updatePreview中设置
        try:
            if hasattr(self, 'themeManager') and self.themeManager:
                scrollbar_style = self.themeManager.get_scrollbar_style()
            else:
                scrollbar_style = ScrollBarStyle.get_style(base_color="transparent", handle_color="rgba(255, 255, 255, 0.3)")
            previewView.setStyleSheet(previewView.styleSheet() + scrollbar_style)
        except Exception as e:
            print(f"为预览区域添加滚动样式时出错: {e}")
            
        previewLayout.addWidget(previewView)
        
        # 添加到堆栈中，确保编辑器在最上层（索引0）
        editorStack.addWidget(editorContainer)
        editorStack.addWidget(previewContainer)
        editorStack.setCurrentIndex(0)  # 确保显示编辑器而非预览
        
        # 添加到主堆栈
        self.editorsStack.addWidget(editorStack)
        
        # 记录编辑器和预览视图
        self.editors.append(editor)
        self.previewViews.append(previewView)
        
        # 连接信号
        editor.textChanged.connect(lambda: self.updateLineCount(editor))
        editor.textChanged.connect(lambda: self.updatePreview(len(self.editors) - 1))
        
        # 应用容器样式
        self.updateEditorContainerStyle(editorContainer)
        # 也应用相同的边框样式到预览容器
        self.updateEditorContainerStyle(previewContainer)
        # 应用预览样式
        self.updatePreview(len(self.editors) - 1)
        
        # 确保为新创建的编辑器应用正确的主题样式
        editorIndex = len(self.editors) - 1
        if hasattr(self, 'themeManager') and self.themeManager:
            if hasattr(self.themeManager, 'current_theme_name'):
                print(f"为新创建的编辑器应用当前主题: {self.themeManager.current_theme_name}")
                self.updateEditorStyle(editor, font_size)
                self.updateEditorContainerStyle(editorContainer)
                self.updateEditorContainerStyle(previewContainer)
        
        # 切换到新创建的编辑器
        self.editorsStack.setCurrentIndex(editorIndex)
        
        # 设置当前编辑器 - 修复保存问题
        self.currentEditor = editor
        
        print(f"新编辑器创建完成，索引: {editorIndex}")
        return editorIndex
    
    def openFile(self):
        # 使用FileManager中的open_file功能
        open_file(self)
        
        # 触发插件钩子
        if self.plugin_manager:
            try:
                self.plugin_manager.trigger_hook('file_opened', self.currentFilePath)
            except Exception as e:
                print(f"触发插件钩子时出错: {e}")
    
    def saveFile(self, savePath=None):
        result = save_file(self, savePath)
        
        # 触发插件钩子
        if self.plugin_manager and self.currentFilePath:
            try:
                self.plugin_manager.trigger_hook('file_saved', self.currentFilePath)
            except Exception as e:
                print(f"触发插件钩子时出错: {e}")
        
        return result
    
    def newFile(self):
        # 使用FileManager中的new_file功能
        new_file(self)
    
    def closeFile(self, filePath):
        # 先触发插件钩子
        if self.plugin_manager:
            try:
                self.plugin_manager.trigger_hook('file_closed', filePath)
            except Exception as e:
                print(f"触发插件钩子时出错: {e}")
        
        # 使用FileManager中的close_file功能
        close_file(self, filePath)
    
    def printOpenFilesList(self):
        print("\n--- 当前打开的文件列表 ---")
        for i, file_info in enumerate(self.openFiles):
            index = file_info.get('index', 'N/A')
            editor_index = file_info.get('editorIndex', 'N/A')
            file_path = file_info.get('filePath', 'None')
            title = file_info.get('title', 'Untitled')
            is_virtual = file_info.get('isVirtual', False)
            print(f"[{i}] 标签索引: {index}, 编辑器索引: {editor_index}, 路径: {file_path}, 标题: {title}, 虚拟标签: {is_virtual}")
        print("------------------------\n")

    def changeFile(self, filePath, fileName):
        # 使用FileManager中的change_file功能
        change_file(self, filePath, fileName)
        
        # 确保currentEditor更新
        current_index = self.editorsStack.currentIndex()
        if 0 <= current_index < len(self.editors):
            self.currentEditor = self.editors[current_index]
            print(f"切换文件后更新当前编辑器为编辑器 {current_index}")
            
            # 如果启用了高亮，重新应用高亮以确保使用正确的文件类型
            if hasattr(self, 'highlightMode') and self.highlightMode:
                print(f"重新应用高亮，文件类型: {self.currentFileType}")
                self.applyHighlighter(self.currentEditor, self.currentFileType)

    def updateLineCount(self, editor):
        """更新行数统计"""
        if not editor or not hasattr(self, 'statusBarWidget'):
            return
        
        # 获取文本文档
        doc = editor.document()
        
        # 获取文档总行数
        line_count = doc.blockCount()
        
        # 设置状态栏的行数显示
        try:
            self.statusBarWidget.lineCount.setText(f"{line_count} 行")
            print(f"更新行数显示: {line_count} 行")
        except Exception as e:
            print(f"更新行数显示时出错: {e}")
            log_to_file(f"更新行数显示时出错: {e}")
        
    def run(self):
        """运行应用程序"""
        # 显示窗口
        self.show()
        
        # 创建一个默认的文件（如果没有命令行参数指定打开的文件）
        if len(self.openFiles) == 0:
            self.newFile()
        
        # 应用主题
        self.applyTheme(self.currentTheme)
        
        # 窗口居中显示
        desktop = QApplication.primaryScreen().availableGeometry()
        geometry = self.frameGeometry()
        geometry.moveCenter(desktop.center())
        self.move(geometry.topLeft())
        
        # 触发应用启动钩子
        if self.plugin_manager:
            try:
                self.plugin_manager.trigger_hook('app_started')
                print("已触发应用启动插件钩子")
            except Exception as e:
                print(f"触发应用启动钩子时出错: {e}")
        
        # 输出优化统计信息
        if hasattr(self, 'optimizer') and self.optimizer:
            stats = self.optimizer.get_optimization_stats()
            print(f"应用优化统计: 启动耗时 {stats['startup_time']:.3f}秒, "
                  f"预加载模块 {stats['preloaded_modules']} 个")
        
        print("Hanabi Notes 启动完成")

    def register_file_associations(self):
        """注册文件关联，使Hanabi Notes可以打开相关文件类型"""
        # 此方法仅适用于Windows系统
        if platform.system() != "Windows":
            return False
        
        try:
            import winreg
            
            # 获取程序路径
            app_path = os.path.abspath(sys.argv[0])
            
            # 为Markdown文件添加关联
            file_types = [".md", ".markdown", ".txt"]
            
            for ext in file_types:
                # 创建文件类型注册表项
                key_path = f"{ext}"
                try:
                    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{key_path}") as key:
                        winreg.SetValue(key, "", winreg.REG_SZ, f"HanabiNotes{ext}")
                except Exception as e:
                    print(f"注册文件类型 {ext} 失败: {e}")
                    continue
                
                # 创建应用程序注册表项
                key_path = f"Software\\Classes\\HanabiNotes{ext}"
                try:
                    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                        winreg.SetValue(key, "", winreg.REG_SZ, f"Hanabi Notes {ext} 文件")
                        
                    # 添加打开命令
                    key_path = f"Software\\Classes\\HanabiNotes{ext}\\shell\\open\\command"
                    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                        winreg.SetValue(key, "", winreg.REG_SZ, f'"{app_path}" "%1"')
                except Exception as e:
                    print(f"注册应用程序打开命令失败 {ext}: {e}")
                    continue
            
            print("文件关联注册成功")
            return True
        except Exception as e:
            print(f"注册文件关联失败: {e}")
            return False

    # 类级别状态标志
    _settings_dialog_visible = False
    _settings_dialog_instance = None
    _settings_widget = None  # 保存全屏设置页面的引用
    _main_content_widget = None  # 保存主内容区的引用

    def showSettings(self):
        """显示全屏设置页面"""
        # 如果已有全屏设置页面
        if self._settings_widget and self._settings_widget.isVisible():
            return
        
        try:
            print("准备显示全屏设置页面...")
            
            # 检查是否可以使用新的HanabiSettingsPanel
            use_new_panel = False
            try:
                # 直接尝试导入，确保使用最新版本
                from Aya_Hanabi.Hanabi_Page.HanabiSettingsPanel import HanabiSettingsPanel
                print("成功导入新的HanabiSettingsPanel")
                use_new_panel = True
                settings_dialog_class = HanabiSettingsPanel
            except ImportError as e:
                print(f"导入新的HanabiSettingsPanel失败: {e}")
                # 回退到旧版设置对话框
                print("回退到旧版设置对话框")
                from Aya_Hanabi.Hanabi_Page.SettingsPages import SettingsDialog
                settings_dialog_class = SettingsDialog
            
            # 首次调用时保存主内容引用
            if not self._main_content_widget:
                # 查找主内容控件（通常是editorsStack所在的容器）
                for widget in self.centralWidget().findChildren(QWidget):
                    if hasattr(self, 'editorsStack') and self.editorsStack in widget.findChildren(QWidget):
                        self._main_content_widget = widget
                        break
                if not self._main_content_widget:
                    # 如果找不到，使用中央小部件
                    self._main_content_widget = self.centralWidget()
            
            # 创建容器小部件来托管设置页面
            if not self._settings_widget:
                self._settings_widget = QWidget(self.centralWidget())
                self._settings_widget.setObjectName("settingsContainer")
                
                # 设置大小填充整个中央小部件
                self._settings_widget.setGeometry(self.centralWidget().rect())
                
                # 使用层叠布局，确保设置页面居中显示
                containerLayout = QVBoxLayout(self._settings_widget)
                containerLayout.setContentsMargins(50, 30, 50, 30)
                
                # 创建设置内容控件
                settingsContent = QWidget()
                settingsContent.setObjectName("settingsContent")
                
                # 设置内容布局
                contentLayout = QVBoxLayout(settingsContent)
                contentLayout.setContentsMargins(0, 0, 0, 0)
                
                if not use_new_panel:
                    # 只有在使用旧版设置时才添加标题栏
                    # 添加标题栏
                    titleBarWidget = QWidget()
                    titleBarWidget.setObjectName("settingsTitleBar")
                    titleBarWidget.setFixedHeight(50)
                    
                    titleBarLayout = QHBoxLayout(titleBarWidget)
                    titleBarLayout.setContentsMargins(15, 0, 15, 0)
                    
                    # 标题
                    titleLabel = QLabel("设置")
                    titleLabel.setObjectName("settingsTitleLabel")
                    titleLabel.setStyleSheet("""
                        font-size: 16px;
                        font-weight: bold;
                    """)
                    
                    # 返回按钮
                    backButton = QPushButton("返回")
                    backButton.setObjectName("settingsBackButton")
                    backButton.clicked.connect(self.hideSettings)
                    
                    titleBarLayout.addWidget(titleLabel)
                    titleBarLayout.addStretch()
                    titleBarLayout.addWidget(backButton)
                    
                    # 添加到内容布局
                    contentLayout.addWidget(titleBarWidget)
                
                # 创建设置对话框
                settings_panel = settings_dialog_class(self)
                
                if use_new_panel:
                    # 新版设置面板处理
                    # 连接设置变更信号
                    settings_panel.settingsChanged.connect(self.onSettingsChanged)
                else:
                    # 旧版设置对话框处理
                    # 删除窗口边框和标题栏
                    settings_panel.setWindowFlags(Qt.Widget)
                    # 不需要取消/确定按钮
                    if hasattr(settings_panel, 'cancelButton'):
                        settings_panel.cancelButton.setVisible(False)
                    if hasattr(settings_panel, 'saveButton'):
                        settings_panel.saveButton.setText("应用设置")
                    
                    # 连接设置变更信号
                    settings_panel.settingsChanged.connect(self.onSettingsChanged)
                
                # 检查是否有插件管理器并添加插件设置选项卡
                if hasattr(self, 'plugin_manager') and self.plugin_manager and hasattr(settings_panel, 'addPluginsPage'):
                    try:
                        # 创建插件设置面板
                        plugin_panel = self.plugin_manager.create_plugin_settings_panel()
                        if plugin_panel:
                            settings_panel.addPluginsPage(plugin_panel)
                            print("已添加插件设置页面")
                    except Exception as e:
                        print(f"添加插件设置页面失败: {e}")
                
                # 将设置面板添加到内容布局
                contentLayout.addWidget(settings_panel)
                
                # 将设置内容添加到容器布局
                containerLayout.addWidget(settingsContent)
                
                # 保存对话框实例引用
                self._settings_dialog_instance = settings_panel
            
            # 更新设置小部件大小
            self._settings_widget.setGeometry(self.centralWidget().rect())
            
            # 应用当前主题样式
            self.updateSettingsStyle()
            
            # 创建淡入效果（使用透明度效果替代模糊效果）
            settingsContent = self._settings_widget.findChild(QWidget, "settingsContent")
            if settingsContent:
                opacity_effect = QGraphicsOpacityEffect(settingsContent)
                opacity_effect.setOpacity(0.0)
                settingsContent.setGraphicsEffect(opacity_effect)
            else:
                opacity_effect = None
                
            # 先设置为可见，然后通过动画显示
            self._settings_widget.setVisible(True)
            self._settings_widget.setWindowOpacity(0)
            
            # 创建透明度和缩放动画
            self._fade_in_animation = QPropertyAnimation(self._settings_widget, b"windowOpacity")
            self._fade_in_animation.setDuration(300)
            self._fade_in_animation.setStartValue(0.0)
            self._fade_in_animation.setEndValue(1.0)
            self._fade_in_animation.setEasingCurve(QEasingCurve.OutCubic)
            
            # 创建内容动画组
            self._content_animation_group = QParallelAnimationGroup()
            
            # 获取设置内容控件
            settingsContent = self._settings_widget.findChild(QWidget, "settingsContent")
            if settingsContent:
                # 缩放动画
                scale_anim = QPropertyAnimation(settingsContent, b"geometry")
                scale_anim.setDuration(350)
                
                # 将内容从中心放大
                current_rect = settingsContent.geometry()
                center_x = current_rect.center().x()
                center_y = current_rect.center().y()
                width = max(int(current_rect.width() * 0.8), 10)
                height = max(int(current_rect.height() * 0.8), 10)
                
                # 确保起始矩形不会有负值
                start_rect = QRect(
                    max(0, center_x - width // 2),
                    max(0, center_y - height // 2),
                    width,
                    height
                )
                
                scale_anim.setStartValue(start_rect)
                scale_anim.setEndValue(current_rect)
                scale_anim.setEasingCurve(QEasingCurve.OutQuint)
                
                # 添加内容透明度动画
                if opacity_effect:
                    opacity_anim = QPropertyAnimation(opacity_effect, b"opacity")
                    opacity_anim.setDuration(400)
                    opacity_anim.setStartValue(0.0)
                    opacity_anim.setEndValue(1.0)
                    opacity_anim.setEasingCurve(QEasingCurve.OutCubic)
                    self._content_animation_group.addAnimation(opacity_anim)
                
                self._content_animation_group.addAnimation(scale_anim)
            
            # 启动动画
            self._fade_in_animation.start()
            self._content_animation_group.start()
            
            # 设置显示标志
            self._settings_dialog_visible = True
            
            print("全屏设置页面显示成功")
        except Exception as e:
            self._settings_dialog_visible = False
            self._settings_dialog_instance = None
            print(f"显示全屏设置页面时出错: {str(e)}")
            import traceback
            print(traceback.format_exc())
            from Aya_Hanabi.Hanabi_Core.UI.messageBox import warning
            warning(self, "错误", f"显示设置页面时出错: {str(e)}")
    
    def hideSettings(self):
        """隐藏全屏设置页面"""
        if self._settings_widget and self._settings_widget.isVisible():
            # 创建淡出动画
            fade_out_animation = QPropertyAnimation(self._settings_widget, b"windowOpacity")
            fade_out_animation.setDuration(300)
            fade_out_animation.setStartValue(1.0)
            fade_out_animation.setEndValue(0.0)
            fade_out_animation.setEasingCurve(QEasingCurve.InCubic)
            
            # 创建内容缩放动画
            content_animation_group = QParallelAnimationGroup()
            
            # 获取设置内容控件
            settingsContent = self._settings_widget.findChild(QWidget, "settingsContent")
            if settingsContent:
                # 缩放动画
                scale_anim = QPropertyAnimation(settingsContent, b"geometry")
                scale_anim.setDuration(350)
                
                # 将内容向中心缩小
                current_rect = settingsContent.geometry()
                center_x = current_rect.center().x()
                center_y = current_rect.center().y()
                width = max(int(current_rect.width() * 0.8), 10)
                height = max(int(current_rect.height() * 0.8), 10)
                
                # 确保结束矩形不会有负值
                end_rect = QRect(
                    max(0, center_x - width // 2),
                    max(0, center_y - height // 2),
                    width,
                    height
                )
                
                scale_anim.setStartValue(current_rect)
                scale_anim.setEndValue(end_rect)
                scale_anim.setEasingCurve(QEasingCurve.InQuint)
                
                # 如果有图形效果，添加透明度动画
                effect = settingsContent.graphicsEffect()
                if effect and isinstance(effect, QGraphicsOpacityEffect):
                    opacity_anim = QPropertyAnimation(effect, b"opacity")
                    opacity_anim.setDuration(350)
                    opacity_anim.setStartValue(1.0)
                    opacity_anim.setEndValue(0.0)
                    opacity_anim.setEasingCurve(QEasingCurve.InCubic)
                    content_animation_group.addAnimation(opacity_anim)
                    
                content_animation_group.addAnimation(scale_anim)
            
            # 连接动画完成信号到完全隐藏方法
            fade_out_animation.finished.connect(self._hideSettingsComplete)
            
            # 启动动画
            fade_out_animation.start()
            content_animation_group.start()
            
            # 保存动画引用（避免过早销毁）
            self._fade_out_animation = fade_out_animation
            self._content_out_animation = content_animation_group
            
            # 重置标志
            self._settings_dialog_visible = False
    
    def _hideSettingsComplete(self):
        """完成设置面板隐藏"""
        if self._settings_widget:
            self._settings_widget.setVisible(False)
            print("设置面板已完全隐藏")

    def onEditorStackChanged(self, index):
        """当编辑器堆栈当前索引改变时更新当前编辑器"""
        if 0 <= index < len(self.editors):
            # 更新当前编辑器引用
            self.currentEditor = self.editors[index]
            print(f"当前编辑器已更新为编辑器 {index}")
            
            # 标记是否找到匹配的文件信息
            found_matching_file = False
            
            # 更新当前文件路径
            for file_info in self.openFiles:
                if file_info.get('editorIndex') == index:
                    found_matching_file = True
                    # 保留原有的filePath（如果新路径为None但原有路径存在）
                    if file_info.get('filePath') is None and self.currentFilePath is not None:
                        print(f"保留原有文件路径: {self.currentFilePath}，而不是设置为None")
                    else:
                        self.currentFilePath = file_info.get('filePath')
                        
                    self.currentTitle = file_info.get('title', '未命名')
                    print(f"当前文件路径已更新: {self.currentFilePath}")
                    break
            
            # 如果没有找到匹配的文件信息，记录警告但不重置currentFilePath
            if not found_matching_file:
                print(f"警告: 未找到与编辑器索引 {index} 匹配的文件信息，保留现有的文件路径: {self.currentFilePath}")
        else:
            print(f"警告: 无效的编辑器索引 {index}")
            
    def onSettingsChanged(self, settings=None):
        """当设置改变时被调用"""
        try:
            print("设置已变更，开始应用新设置...")
            
            # 如果直接从信号接收了设置，就使用它
            if settings:
                print(f"从信号接收到设置变更: {settings.keys() if isinstance(settings, dict) else '未知格式'}")
                
                # 应用字体设置 (检查字体大小变化)
                if isinstance(settings, dict) and "editor" in settings and "font" in settings["editor"]:
                    # 获取所有字体设置
                    font_settings = settings["editor"]["font"]
                    font_size = font_settings.get("size", 15)
                    font_family = font_settings.get("family", "Consolas")
                    font_bold = font_settings.get("bold", False)
                    font_italic = font_settings.get("italic", False)
                    
                    print(f"应用字体设置: 字体={font_family}, 大小={font_size}, 粗体={font_bold}, 斜体={font_italic}")
                    
                    # 更新所有编辑器样式
                    for editor in self.editors:
                        self.updateEditorStyle(editor, font_size)
                    
                    # 更新状态栏中的字体大小显示
                    if hasattr(self, 'statusBarWidget'):
                        self.statusBarWidget.currentFontSize = font_size
                        if hasattr(self.statusBarWidget, 'fontSizeSpinBox'):
                            try:
                                self.statusBarWidget.fontSizeSpinBox.setValue(font_size)
                            except Exception as e:
                                print(f"更新字体大小微调框时出错: {e}")
                
                # 应用其他设置
                # 检查是否有主题设置
                if isinstance(settings, dict) and "theme" in settings and "name" in settings["theme"]:
                    theme_name = settings["theme"]["name"]
                    print(f"从设置中检测到主题变更: {theme_name}")
                    self.applyTheme(theme_name)
                
                # 保存设置到文件
                try:
                    self.saveSettingsToFile(settings)
                except Exception as e:
                    print(f"保存设置到文件时出错: {e}")
                
                print("所有设置已应用并保存")
                return
            
            # 如果没有直接收到设置，尝试从文件加载
            print("从文件加载设置...")
            settings = self.loadSettingsFromFile()
            if settings:
                print(f"从文件加载的设置: {settings.keys()}")
                # 递归调用以应用从文件加载的设置
                self.onSettingsChanged(settings)
            else:
                print("未能从文件加载设置")
                
        except Exception as e:
            print(f"应用设置时出错: {e}")
            import traceback
            print(traceback.format_exc())
    
    def saveSettingsToFile(self, settings):
        """将设置保存到文件"""
        try:
            # 创建设置目录
            settings_dir = os.path.join(os.path.expanduser("~"), ".hanabi_notes")
            if not os.path.exists(settings_dir):
                os.makedirs(settings_dir)
            
            settings_file = os.path.join(settings_dir, "settings.json")
            
            # 如果文件已存在，先读取现有设置
            existing_settings = {}
            if os.path.exists(settings_file):
                try:
                    with open(settings_file, 'r', encoding='utf-8') as f:
                        existing_settings = json.load(f)
                except Exception as e:
                    print(f"读取现有设置文件时出错: {e}")
            
            # 更新设置
            existing_settings.update(settings)
            
            # 保存到文件
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(existing_settings, f, ensure_ascii=False, indent=4)
            
            print(f"设置已保存到: {settings_file}")
            return True
        except Exception as e:
            print(f"保存设置到文件时出错: {e}")
            return False
    
    def loadSettingsFromFile(self):
        """从文件加载设置"""
        try:
            settings_dir = os.path.join(os.path.expanduser("~"), ".hanabi_notes")
            settings_file = os.path.join(settings_dir, "settings.json")
            
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                print(f"成功从 {settings_file} 加载设置")
                return settings
            else:
                print(f"设置文件不存在: {settings_file}")
                return None
        except Exception as e:
            print(f"从文件加载设置时出错: {e}")
            return None

    # 主题设置对话框状态标志
    _theme_dialog_visible = False
    _theme_dialog_instance = None

    def showThemeSettings(self):
        """显示主题设置对话框"""
        try:
            # 检查是否已有实例在运行
            if HanabiNotesApp._theme_dialog_instance:
                try:
                    if HanabiNotesApp._theme_dialog_instance.isVisible():
                        print("已有主题设置对话框实例在运行，将其置于前台")
                        HanabiNotesApp._theme_dialog_instance.raise_()
                        HanabiNotesApp._theme_dialog_instance.activateWindow()
                        return
                    else:
                        # 如果存在但不可见，关闭它
                        if hasattr(HanabiNotesApp._theme_dialog_instance, 'deleteLater'):
                            HanabiNotesApp._theme_dialog_instance.deleteLater()
                except Exception as e:
                    print(f"检查现有对话框实例时出错: {e}")
                    
            # 如果设置页面已打开，则直接切换到外观标签
            if self._settings_widget and self._settings_widget.isVisible():
                if self._settings_dialog_instance:
                    # 获取导航列表并切换到外观标签（通常是索引2）
                    if hasattr(self._settings_dialog_instance, 'navListWidget'):
                        appearance_index = 2  # 外观标签的索引
                        self._settings_dialog_instance.navListWidget.setCurrentRow(appearance_index)
                        return
                    
            # 检查主题管理器是否就绪
            print(f"当前主题管理器状态: {self.themeManager}")
            if hasattr(self.themeManager, 'current_theme_name'):
                print(f"当前主题: {self.themeManager.current_theme_name}")
                    
            # 尝试导入主题设置对话框类
            try:
                # 尝试从新位置导入
                from Aya_Hanabi.Hanabi_Page.SettingsPages import ThemeSettingsDialog
                print("成功从SettingsPages导入ThemeSettingsDialog")
            except ImportError as e:
                try:
                    # 如果失败，尝试其他可能的位置
                    from Aya_Hanabi.Hanabi_Page.Settings.LegacyTheme.ThemeSettingsDialog import ThemeSettingsDialog
                    print("从LegacyTheme导入ThemeSettingsDialog")
                except ImportError:
                    print("无法导入ThemeSettingsDialog，设置功能不可用")
                    HanabiMessageBox.warning(self, "错误", "无法加载主题设置模块，主题设置功能不可用。")
                    return
                    
            # 重置当前应用的实例引用和状态标志
            HanabiNotesApp._theme_dialog_instance = None
            HanabiNotesApp._theme_dialog_visible = False
                
            # 创建新的对话框实例
            try:
                print("创建新的主题设置对话框...")
                # 创建对话框实例（传递self作为parent对象）
                theme_dialog = ThemeSettingsDialog(self)
                
                # 确保对话框使用应用程序的主题管理器
                theme_dialog.themeManager = self.themeManager
                print(f"已将应用程序的主题管理器传递给对话框，当前主题: {self.themeManager.current_theme_name}")
                
                # 连接信号 - 添加调试输出
                print("连接主题变更信号...")
                theme_dialog.themeChanged.connect(lambda theme: print(f"收到主题变更信号: {theme}"))
                theme_dialog.themeChanged.connect(self.onThemeChanged)
                
                # 连接关闭信号
                theme_dialog.finished.connect(self._onThemeDialogClosed)
                
                # 保存对话框实例引用
                HanabiNotesApp._theme_dialog_instance = theme_dialog
                
                # 设置为顶层窗口
                theme_dialog.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
                
                # 显示对话框
                theme_dialog.show()
                theme_dialog.raise_()
                theme_dialog.activateWindow()
                
                # 设置显示标志
                HanabiNotesApp._theme_dialog_visible = True
                
                print("主题设置对话框显示成功")
                
            except Exception as e:
                HanabiNotesApp._theme_dialog_visible = False
                HanabiNotesApp._theme_dialog_instance = None
                error_msg = f"打开主题设置对话框时出错: {str(e)}"
                print(error_msg)
                try:
                    from Aya_Hanabi.Hanabi_Core.UI.messageBox import log_to_file, HanabiMessageBox
                    log_to_file(error_msg)
                    import traceback
                    trace_info = traceback.format_exc()
                    print(trace_info)
                    log_to_file(trace_info)
                    HanabiMessageBox.warning(self, "错误", f"打开主题设置对话框时出错: {str(e)}")
                except:
                    import traceback
                    print(traceback.format_exc())
                    
        except Exception as e:
            print(f"显示主题设置对话框过程中出错: {e}")
            import traceback
            print(traceback.format_exc())
    
    def _onThemeDialogClosed(self, result=None):
        """主题设置对话框关闭时的回调函数"""
        print(f"主题设置对话框已关闭，结果代码: {result}")
        HanabiNotesApp._theme_dialog_visible = False
        
        # 尝试主动清理实例
        try:
            if HanabiNotesApp._theme_dialog_instance is not None:
                print("清理主题设置对话框实例引用")
                
                # 先断开所有连接
                try:
                    # 如果对象有disconnect_all_signals方法，使用它
                    if hasattr(HanabiNotesApp._theme_dialog_instance, 'disconnect_all_signals'):
                        print("使用对象的disconnect_all_signals方法")
                        HanabiNotesApp._theme_dialog_instance.disconnect_all_signals()
                    else:
                        # 安全断开themeChanged信号
                        if hasattr(HanabiNotesApp._theme_dialog_instance, 'themeChanged'):
                            try:
                                if hasattr(HanabiNotesApp._theme_dialog_instance.themeChanged, 'receivers') and HanabiNotesApp._theme_dialog_instance.themeChanged.receivers() > 0:
                                    print("断开themeChanged信号")
                                    HanabiNotesApp._theme_dialog_instance.themeChanged.disconnect()
                            except (TypeError, RuntimeError) as e:
                                print(f"断开themeChanged信号时出错: {e}")
                            
                        # 安全断开finished信号
                        if hasattr(HanabiNotesApp._theme_dialog_instance, 'finished'):
                            try:
                                if hasattr(HanabiNotesApp._theme_dialog_instance.finished, 'receivers') and HanabiNotesApp._theme_dialog_instance.finished.receivers() > 0:
                                    print("断开finished信号")
                                    HanabiNotesApp._theme_dialog_instance.finished.disconnect()
                            except (TypeError, RuntimeError) as e:
                                print(f"断开finished信号时出错: {e}")
                except Exception as e:
                    print(f"断开信号连接时出错: {e}")
                
                # 标记为稍后删除
                if hasattr(HanabiNotesApp._theme_dialog_instance, 'deleteLater'):
                    HanabiNotesApp._theme_dialog_instance.deleteLater()
                    print("主题设置对话框实例已标记为稍后删除")
                
                # 清空引用
                HanabiNotesApp._theme_dialog_instance = None
                print("主题设置对话框实例引用已清空")
        except Exception as e:
            print(f"清理主题设置对话框实例时出错: {e}")
            # 确保引用被清空
            HanabiNotesApp._theme_dialog_instance = None
            
            # 强制垃圾回收以释放资源
            try:
                import gc
                gc.collect()
                print("已请求垃圾回收")
            except Exception as e:
                print(f"请求垃圾回收时出错: {e}")

    def onThemeChanged(self, theme_name):
        """当主题改变时被调用"""
        try:
            print(f"收到主题变更请求: {theme_name}")
            
            # 获取当前字体大小，确保主题变化不会覆盖字体大小
            current_font_size = 15  # 默认大小
            if hasattr(self, 'statusBarWidget') and hasattr(self.statusBarWidget, 'currentFontSize'):
                current_font_size = self.statusBarWidget.currentFontSize
                print(f"主题切换前保存当前字体大小: {current_font_size}")
            
            # 检查主题管理器状态
            if hasattr(self, 'themeManager') and self.themeManager:
                print(f"当前主题管理器状态正常，主题名称: {getattr(self.themeManager, 'current_theme_name', 'unknown')}")
                if hasattr(self.themeManager, 'set_theme') and callable(self.themeManager.set_theme):
                    result = self.themeManager.set_theme(theme_name)
                    print(f"直接设置主题结果: {result}")
            else:
                print("警告: 主题管理器不可用，无法直接设置主题")
            
            # 应用主题
            print(f"调用applyTheme方法应用主题: {theme_name}")
            self.applyTheme(theme_name)
            
            # 确保字体大小不变
            print(f"更新所有编辑器以保持字体大小: {current_font_size}")
            for editor in self.editors:
                self.updateEditorStyle(editor, current_font_size)
            
            print(f"主题已更改为: {theme_name}，保持字体大小: {current_font_size}")
            
            # 更新设置页面样式
            if hasattr(self, '_settings_widget') and self._settings_widget and self._settings_widget.isVisible():
                print("更新设置页面样式")
                self.updateSettingsStyle()
            
            # 更新设置对话框实例样式
            if hasattr(self, '_settings_dialog_instance') and self._settings_dialog_instance:
                print("更新设置对话框样式")
                # 检查是否是新版设置面板
                if hasattr(self._settings_dialog_instance, 'updateStyle') and callable(self._settings_dialog_instance.updateStyle):
                    try:
                        print("使用updateStyle方法更新设置面板样式")
                        self._settings_dialog_instance.updateStyle()
                    except Exception as style_err:
                        print(f"更新设置面板样式时出错: {style_err}")
                else:
                    # 处理旧版设置对话框的样式
                    print("设置对话框没有updateStyle方法，使用默认方式更新样式")
            
            # 尝试保存主题配置
            try:
                if hasattr(self, 'themeManager') and self.themeManager:
                    if hasattr(self.themeManager, 'save_theme_config'):
                        self.themeManager.save_theme_config()
                        print("已保存主题配置")
            except Exception as e:
                print(f"保存主题配置时出错: {e}")
            
        except Exception as e:
            print(f"应用主题时出错: {str(e)}")
            import traceback
            print(traceback.format_exc())
    
    def _onSettingsDialogClosed(self, result=None):
        """设置对话框关闭时的回调函数"""
        print(f"设置对话框已关闭，结果: {result}")
        self._settings_dialog_visible = False
        
        # 不需要手动释放资源，因为设置页面仍然保持在对象中，只是隐藏起来
        print("设置对话框已关闭")

    def updateSettingsStyle(self):
        """根据当前主题更新设置页面的样式"""
        if not self._settings_widget:
            return
        
        # 确定当前主题是否为暗色
        is_dark_theme = True  # 默认为暗色
        if hasattr(self, 'themeManager') and self.themeManager:
            if hasattr(self.themeManager, 'current_theme_name'):
                theme_name = self.themeManager.current_theme_name
                is_dark_theme = theme_name in ["dark", "purple_dream", "green_theme"]
        
        # 根据主题获取颜色
        if is_dark_theme:
            # 暗色主题 - 使用更现代的配色
            bg_color = "rgba(20, 22, 28, 0.85)"  # 半透明背景
            content_bg = "#1E2128"
            panel_bg = "#272A31"  # 更深的面板背景色
            title_bar_bg = "#2C313A"
            border_color = "#3A3F4B"  # 边框颜色
            text_color = "#FFFFFF"
            secondary_text = "#A0A8B7"  # 次要文本颜色
            button_bg = "#4D5566"  # 更现代的按钮颜色
            button_hover = "#5A6377"
            button_pressed = "#3C4456"
            accent_color = "#61AFEF"  # 强调色
        else:
            # 亮色主题 - 更现代风格
            bg_color = "rgba(245, 247, 250, 0.85)"  # 半透明背景
            content_bg = "#FFFFFF"
            panel_bg = "#F5F7FA"  # 面板背景色
            title_bar_bg = "#F0F2F5"
            border_color = "#E4E8F0"  # 边框颜色
            text_color = "#333333"
            secondary_text = "#6E7785"  # 次要文本颜色
            button_bg = "#4B96FF"
            button_hover = "#3A85EE"
            button_pressed = "#2A74DD"
            accent_color = "#2B7DE1"  # 强调色
        
        # 设置容器样式 - 更现代风格
        self._settings_widget.setStyleSheet(f"""
            #settingsContainer {{
                background-color: {bg_color};
                border: none;
            }}
            
            #settingsContent {{
                background-color: {content_bg};
                border-radius: 12px;
                color: {text_color};
            }}
            
            #settingsTitleBar {{
                background-color: {title_bar_bg};
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                border-bottom: 1px solid {border_color};
            }}
            
            #settingsTitleLabel {{
                color: {text_color};
                font-size: 16px;
                font-weight: 500;
            }}
            
            #settingsBackButton {{
                background-color: {button_bg};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
                min-width: 80px;
            }}
            
            #settingsBackButton:hover {{
                background-color: {button_hover};
            }}
            
            #settingsBackButton:pressed {{
                background-color: {button_pressed};
            }}
            
            /* 美化设置面板内的元素 */
            QLabel {{
                color: {text_color};
            }}
            
            QLabel[isHeader="true"] {{
                color: {text_color};
                font-weight: 500;
                font-size: 15px;
            }}
            
            QPushButton {{
                background-color: {button_bg};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }}
            
            QPushButton:hover {{
                background-color: {button_hover};
            }}
            
            QPushButton:pressed {{
                background-color: {button_pressed};
            }}
            
            QCheckBox {{
                color: {text_color};
                spacing: 8px;
            }}
            
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid {border_color};
            }}
            
            QCheckBox::indicator:unchecked {{
                background-color: {panel_bg};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {accent_color};
                /* 不使用SVG图标，而是使用实体符号 */
                font-family: "Material Icons";
                color: white;
                font-size: 16px;
                text-align: center;
                padding: 2px;
            }}
            
            QComboBox {{
                background-color: {panel_bg};
                border: 1px solid {border_color};
                border-radius: 6px;
                padding: 6px 12px;
                min-height: 24px;
                color: {text_color};
            }}
            
            QComboBox:hover {{
                border: 1px solid {accent_color};
            }}
            
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 20px;
                border: none;
                margin-right: 8px;
            }}
            
            QSpinBox, QLineEdit {{
                background-color: {panel_bg};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 6px;
                padding: 6px;
                min-height: 24px;
            }}
            
            QSpinBox:hover, QLineEdit:hover {{
                border: 1px solid {accent_color};
            }}
            
            /* 美化滚动条 */
            QScrollBar:vertical {{
                background-color: transparent;
                width: 8px;
                margin: 0px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {button_bg};
                min-height: 30px;
                border-radius: 4px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {button_hover};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
            
            /* 美化列表视图 */
            QListWidget {{
                background-color: {panel_bg};
                border: 1px solid {border_color};
                border-radius: 6px;
                outline: none;
                padding: 6px;
            }}
            
            QListWidget::item {{
                height: 36px;
                padding: 4px 8px;
                margin: 2px 0px;
                border-radius: 4px;
            }}
            
            QListWidget::item:hover {{
                background-color: rgba({button_hover.replace('#', '')}, 0.2);
            }}
            
            QListWidget::item:selected {{
                background-color: {accent_color};
                color: white;
            }}
        """)
        
        # 如果设置对话框实例存在，也应用主题样式
        if self._settings_dialog_instance:
            # 检查是否是新版设置面板
            if hasattr(self._settings_dialog_instance, 'updateStyle') and callable(self._settings_dialog_instance.updateStyle):
                try:
                    print("使用updateStyle方法更新设置面板样式")
                    self._settings_dialog_instance.updateStyle()
                except Exception as style_err:
                    print(f"更新设置面板样式时出错: {style_err}")
            else:
                # 处理旧版设置对话框的样式
                print("设置对话框没有updateStyle方法，使用默认方式更新样式")

if __name__ == "__main__":
    # 创建QApplication实例
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("Hanabi Notes")
    app.setOrganizationName("HanabiNotes")
    
    try:
        # 创建主窗口
        main_window = HanabiNotesApp()
        
        # 处理命令行参数（如果有）
        args = sys.argv[1:]
        
        # 检查是否有特殊命令行参数
        if "--register-file-types" in args:
            # 注册文件关联
            if main_window.register_file_associations():
                print("文件类型关联注册成功")
            else:
                print("文件类型关联注册失败")
            # 如果只是注册文件类型，不启动应用程序
            if len(args) == 1 and args[0] == "--register-file-types":
                sys.exit(0)
            # 移除这个参数，继续处理其他参数
            args.remove("--register-file-types")
            
        if args:
            # 只处理第一个不是选项的参数作为文件路径
            file_path = None
            for arg in args:
                if not arg.startswith("--"):
                    file_path = arg
                    break
                    
            if file_path and os.path.exists(file_path):
                print(f"从命令行打开文件: {file_path}")
                # 初始化窗口后再打开文件
                main_window.run()
                # 使用FileManager打开指定文件
                title = os.path.splitext(os.path.basename(file_path))[0]
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # 创建新标签并加载内容
                    main_window.fileManager.fileLoaded.emit(title, content)
                    # 更新文件路径
                    main_window.currentFilePath = file_path
                    main_window.currentTitle = title
                    # 更新UI
                    main_window.setWindowTitle(f"Hanabi Notes - {title}")
                except Exception as e:
                    print(f"打开命令行指定文件时出错: {e}")
                    log_to_file(f"打开命令行指定文件时出错: {e}")
                    # 出错时仍然正常启动程序
                    main_window.run()
            else:
                if file_path:
                    print(f"命令行指定的文件不存在: {file_path}")
                main_window.run()
        else:
            # 没有命令行参数，正常启动
            main_window.run()
        
        # 进入应用程序主循环
        result = app.exec()
        
        # 执行退出清理
        # 插件系统已移除
            
        # 清理优化器
        if 'app_Optimizer' in globals() and app_Optimizer:
            app_Optimizer.cleanup()
        
        sys.exit(result)
    except Exception as e:
        print(f"应用程序启动出错: {e}")
        log_to_file(f"应用程序启动出错: {e}")
        log_to_file(traceback.format_exc())
        sys.exit(1)    
