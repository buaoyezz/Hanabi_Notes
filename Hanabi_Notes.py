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
from PySide6.QtCore import Qt, QPoint, Signal, QEvent, QTimer, QRect, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, 
                              QHBoxLayout, QPushButton, QTextEdit, QPlainTextEdit, QWidget, QSplitter, QStackedWidget,
                              QMessageBox, QScrollBar, QFileDialog)
from PySide6.QtGui import QFont, QColor, QCursor, QTextCursor, QTextFormat, QSyntaxHighlighter,QTextCharFormat

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
    from Aya_Hanabi.Hanabi_Core.ThemeManager.themeManager import ThemeManager
    from Aya_Hanabi.Hanabi_Page.SettingsPages import SettingsDialog, ThemeSettingsDialog
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
            from Aya_Hanabi.Hanabi_Page.SettingsPages import SettingsDialog, ThemeSettingsDialog
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
        
        if self.sidebar.activeTabIndex >= 0:
            fileName = os.path.splitext(os.path.basename(filePath))[0]
            self.sidebar.updateTabName(self.sidebar.activeTabIndex, fileName, filePath)
            
            # 更新文件信息
            for file_info in self.openFiles:
                if file_info.get('index') == self.sidebar.activeTabIndex:
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
                self.applyHighlighter(currentEditor)
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
    
    def applyHighlighter(self, editor):
        self.editorManager.applyHighlighter(editor, self.currentFileType)
    
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
        if theme_name:
            self.currentTheme = theme_name
            print(f"设置当前主题为: {self.currentTheme}")
        
        # 如果主题管理器尚未初始化，先初始化
        if not hasattr(self, 'themeManager') or not self.themeManager:
            self.themeManager = ThemeManager()
            self.themeManager.load_themes_from_directory()
            print("初始化主题管理器")
        
        # 设置当前主题
        success = self.themeManager.set_theme(self.currentTheme)
        print(f"设置主题结果: {success}, 当前主题: {self.currentTheme}")
        
        if hasattr(self.themeManager, 'current_theme_name'):
            print(f"主题管理器当前主题名称: {self.themeManager.current_theme_name}")
        
        if hasattr(self.themeManager, 'current_theme') and self.themeManager.current_theme:
            theme_name_attr = self.themeManager.current_theme.name if hasattr(self.themeManager.current_theme, 'name') else "未知"
            print(f"主题对象名称: {theme_name_attr}")
            
            # 检查主题数据
            bg_color = self.themeManager.current_theme.get("editor.background", "未设置")
            print(f"编辑器背景色: {bg_color}")
            
            # 亮色主题特殊处理
            if self.currentTheme == "light":
                print("执行亮色主题特殊处理")
                if hasattr(self.themeManager.current_theme, 'data') and 'editor' in self.themeManager.current_theme.data:
                    self.themeManager.current_theme.data['editor']['background'] = '#ffffff'
                    self.themeManager.current_theme.data['editor']['text_color'] = '#333333'
                    self.themeManager.current_theme.data['editor']['border_color'] = '#e5e5e5'
                    print("强制设置亮色主题编辑器属性")
        
        if not success:
            print(f"无法应用主题 {self.currentTheme}，使用默认主题")
            self.currentTheme = "dark"
            success = self.themeManager.set_theme("dark")
            if not success:
                print("无法应用默认主题")
                return
            
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
            print(f"更新编辑器 {i} 的样式")
            self.updateEditorStyle(editor, current_font_size)
            
        # 更新编辑器容器样式
        if hasattr(self, 'editorsStack'):
            print(f"准备更新编辑器容器样式，编辑器堆栈数量: {self.editorsStack.count()}")
            for i in range(self.editorsStack.count()):
                editorStack = self.editorsStack.widget(i)
                if editorStack:
                    print(f"处理编辑器堆栈 {i}, 子控件数量: {editorStack.count()}")
                    for j in range(editorStack.count()):
                        container = editorStack.widget(j)
                        if container:
                            print(f"更新容器 {i}.{j} 的样式")
                            self.updateEditorContainerStyle(container)
                    
        # 更新预览样式
        if hasattr(self, 'previewViews'):
            print(f"准备更新预览样式，预览视图数量: {len(self.previewViews)}")
            for i, preview in enumerate(self.previewViews):
                print(f"更新预览视图 {i}")
                self.updatePreview(i)
            
        # 更新标题栏样式
        if hasattr(self, 'titleBar'):
            print("更新标题栏样式")
            self.titleBar.updateStyle()
        
        # 更新侧边栏样式
        if hasattr(self, 'sidebar'):
            print("更新侧边栏样式")
            self.sidebar.updateStyle(self.themeManager)
        
        # 更新状态栏样式
        print("更新状态栏样式")
        self.updateStatusBarStyle()
        
        print(f"----------主题 {self.currentTheme} 应用完成----------")
    
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
        
        # 切换到新创建的编辑器
        editorIndex = len(self.editors) - 1
        self.editorsStack.setCurrentIndex(editorIndex)
        
        # 设置当前编辑器 - 修复保存问题
        self.currentEditor = editor
        
        print(f"新编辑器创建完成，索引: {editorIndex}")
        return editorIndex
    
    def openFile(self):
        # 使用FileManager中的open_file功能
        open_file(self)
    
    def saveFile(self, savePath=None):
        save_file(self, savePath)
    
    def newFile(self):
        # 使用FileManager中的new_file功能
        new_file(self)
    
    def closeFile(self, filePath):
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

    def showSettings(self):
        """显示设置对话框"""
        try:
            from Aya_Hanabi.Hanabi_Page.SettingsPages import SettingsDialog
            settings_dialog = SettingsDialog(self)
            settings_dialog.settingsChanged.connect(self.onSettingsChanged)
            settings_dialog.exec()
        except Exception as e:
            error_msg = f"打开设置对话框时出错: {e}"
            print(error_msg)
            log_to_file(error_msg)
            import traceback
            trace_info = traceback.format_exc()
            print(trace_info)
            log_to_file(trace_info)
            HanabiMessageBox.warning(self, "错误", f"打开设置对话框时出错: {str(e)}")
    
    def showThemeSettings(self):
        """显示主题设置对话框"""
        try:
            from Aya_Hanabi.Hanabi_Page.SettingsPages import ThemeSettingsDialog
            theme_dialog = ThemeSettingsDialog(self)
            theme_dialog.themeChanged.connect(self.onThemeChanged)
            theme_dialog.exec()
        except Exception as e:
            error_msg = f"打开主题设置对话框时出错: {e}"
            print(error_msg)
            log_to_file(error_msg)
            import traceback
            trace_info = traceback.format_exc()
            print(trace_info)
            log_to_file(trace_info)
            HanabiMessageBox.warning(self, "错误", f"打开主题设置对话框时出错: {str(e)}")
    
    def onSettingsChanged(self):
        """当设置改变时被调用"""
        try:
            # 重新加载设置
            settings_dir = os.path.join(os.path.expanduser("~"), ".hanabi_notes")
            settings_file = os.path.join(settings_dir, "settings.json")
            
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # 应用字体设置 (只检查字体大小变化)
                if "editor" in settings and "font" in settings["editor"]:
                    # 字体设置已更改，需要重新应用所有编辑器样式
                    font_size = settings["editor"]["font"].get("size", 15)
                    
                    # 更新所有编辑器样式
                    print(f"应用新的字体设置到所有编辑器")
                    for editor in self.editors:
                        self.updateEditorStyle(editor, font_size)
                
                # 应用其他设置
                # ...
                
                print("设置已更新")
        except Exception as e:
            print(f"应用设置时出错: {str(e)}")
            import traceback
            print(traceback.format_exc())
    
    def onThemeChanged(self, theme_name):
        """当主题改变时被调用"""
        try:
            # 获取当前字体大小，确保主题变化不会覆盖字体大小
            current_font_size = 15  # 默认大小
            if hasattr(self, 'statusBarWidget') and hasattr(self.statusBarWidget, 'currentFontSize'):
                current_font_size = self.statusBarWidget.currentFontSize
                print(f"主题切换前保存当前字体大小: {current_font_size}")
            
            # 应用主题
            self.applyTheme(theme_name)
            
            # 确保字体大小不变
            for editor in self.editors:
                self.updateEditorStyle(editor, current_font_size)
            
            print(f"主题已更改为: {theme_name}，保持字体大小: {current_font_size}")
        except Exception as e:
            print(f"应用主题时出错: {str(e)}")

    def closeEvent(self, event):
        """关闭程序时的事件处理"""
        # 检查是否有未保存的文件
        unsavedFiles = []
        for fileInfo in self.openFiles:
            if fileInfo.get('isModified', False):
                filePath = fileInfo.get('filePath')
                fileName = os.path.basename(filePath) if filePath else "未命名"
                unsavedFiles.append(fileName)
        
        # 如果有未保存的文件，提示用户
        if unsavedFiles:
            message = f"以下文件尚未保存:\n{', '.join(unsavedFiles)}\n\n是否保存这些文件？"
            reply = HanabiMessageBox.question(
                self, "未保存的文件", message)
            
            if reply == HanabiMessageBox.Yes_Result:
                # 保存所有未保存的文件
                for fileInfo in self.openFiles:
                    if fileInfo.get('isModified', False):
                        self.saveFileByIndex(fileInfo.get('index'))
            elif reply == HanabiMessageBox.Cancel_Result:
                # 取消关闭
                event.ignore()
                return
        
        # 备份所有打开的文件
        if hasattr(self, 'autoBackupManager') and self.autoBackupManager:
            self.autoBackupManager.backup_all_open_files()
        
        # 保存应用程序状态
        self.saveAppState()
        
        # 接受关闭事件
        event.accept()

    def saveFileByIndex(self, index):
        """根据索引保存文件"""
        try:
            # 查找对应的文件信息
            fileInfo = None
            for info in self.openFiles:
                if info.get('index') == index:
                    fileInfo = info
                    break
            
            if not fileInfo:
                print(f"无法找到索引为 {index} 的文件信息")
                return False
            
            # 获取编辑器索引和文件路径
            editorIndex = fileInfo.get('editorIndex')
            filePath = fileInfo.get('filePath')
            
            if editorIndex is None or editorIndex < 0 or editorIndex >= len(self.editors):
                print(f"无效的编辑器索引: {editorIndex}")
                return False
            
            # 获取编辑器内容
            editor = self.editors[editorIndex]
            content = editor.toPlainText()
            
            # 如果没有文件路径，需要提示用户选择保存位置
            if not filePath:
                return self.saveFile()
            
            # 保存文件
            with open(filePath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 更新文件状态
            fileInfo['isModified'] = False
            
            print(f"文件已保存: {filePath}")
            return True
        except Exception as e:
            print(f"保存文件时出错: {e}")
            return False

    def saveAppState(self):
        """保存应用程序状态"""
        try:
            # 创建配置目录
            config_dir = os.path.join(os.path.expanduser("~"), ".hanabi_notes")
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            # 保存最近文件列表
            if hasattr(self, 'recentFiles'):
                recent_files_path = os.path.join(config_dir, "recent_files.json")
                with open(recent_files_path, 'w', encoding='utf-8') as f:
                    json.dump(self.recentFiles, f, ensure_ascii=False)
            
            # 保存当前主题
            if hasattr(self, 'currentTheme'):
                settings_path = os.path.join(config_dir, "settings.json")
                settings = {}
                
                # 读取现有设置
                if os.path.exists(settings_path):
                    try:
                        with open(settings_path, 'r', encoding='utf-8') as f:
                            settings = json.load(f)
                    except:
                        settings = {}
                
                # 更新主题设置
                if 'appearance' not in settings:
                    settings['appearance'] = {}
                
                settings['appearance']['theme'] = self.currentTheme
                
                # 保存设置
                with open(settings_path, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, ensure_ascii=False, indent=2)
            
            print("应用程序状态已保存")
        except Exception as e:
            print(f"保存应用程序状态时出错: {e}")

    # 添加一个新方法用于处理编辑器堆栈改变的信号
    def onEditorStackChanged(self, index):
        """当编辑器堆栈当前索引改变时更新当前编辑器"""
        if 0 <= index < len(self.editors):
            self.currentEditor = self.editors[index]
            print(f"当前编辑器已更新为编辑器 {index}")
            
            # 更新当前文件路径
            for file_info in self.openFiles:
                if file_info.get('editorIndex') == index:
                    self.currentFilePath = file_info.get('filePath')
                    self.currentTitle = file_info.get('title', '未命名')
                    print(f"当前文件路径已更新: {self.currentFilePath}")
                    break
        else:
            print(f"警告: 无效的编辑器索引 {index}")
            

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
        if 'app_Optimizer' in globals() and app_Optimizer:
            app_Optimizer.cleanup()
        
        sys.exit(result)
    except Exception as e:
        print(f"应用程序启动出错: {e}")
        log_to_file(f"应用程序启动出错: {e}")
        log_to_file(traceback.format_exc())
        sys.exit(1)
    