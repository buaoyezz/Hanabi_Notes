import os
import json
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QPlainTextEdit
from PySide6.QtGui import QFont, QColor, QTextCursor, QTextFormat

from Aya_Hanabi.Hanabi_HighLight import get_highlighter, detect_file_type
from Aya_Hanabi.Hanabi_Styles.scrollbar_style import ScrollBarStyle

class EditorManager:
    """
    编辑器管理类，包含编辑器样式、高亮、滚动等功能
    """
    def __init__(self, app=None):
        self.app = app
        self.current_file_type = "text"  # 默认文件类型
        
    def updateEditorStyle(self, editor, fontSize=15):
        """更新编辑器样式"""
        print(f"开始更新编辑器样式，字体大小: {fontSize}")
        
        # 确定当前主题
        theme_name = "dark"  # 默认主题
        
        # 尝试从主题管理器获取当前主题名称
        if hasattr(self.app, 'themeManager'):
            if hasattr(self.app.themeManager, 'current_theme_name'):
                theme_name = self.app.themeManager.current_theme_name
                print(f"从主题管理器获取当前主题名称: {theme_name}")
            elif hasattr(self.app, 'currentTheme'):
                theme_name = self.app.currentTheme
                print(f"从应用程序获取当前主题名称: {theme_name}")
        
        # 检查是否为亮色主题
        is_light_theme = theme_name == "light"
        print(f"是否为亮色主题: {is_light_theme}")
        
        # 判断是否应该保留用户字体大小
        should_preserve_font_size = False
        
        # 从主题管理器获取字体设置信息
        if hasattr(self.app, 'themeManager') and hasattr(self.app.themeManager, 'get_editor_font_settings'):
            font_settings = self.app.themeManager.get_editor_font_settings()
            should_preserve_font_size = font_settings.get('preserve_font_size', False)
        
        # 如果是通过changeFontSize传入的新字体大小，则使用传入的值
        # 这样可以确保用户通过菜单选择的字体大小能够生效
        if should_preserve_font_size and hasattr(self.app, 'statusBarWidget'):
            # 更新状态栏中保存的字体大小，以便保持一致
            self.app.statusBarWidget.currentFontSize = fontSize
            print(f"更新当前字体大小设置为: {fontSize}")
        
        # 默认颜色
        bg_color = '#ffffff' if is_light_theme else '#282c34'
        text_color = '#333333' if is_light_theme else '#abb2bf'
        selection_bg = '#b3d4fc' if is_light_theme else '#528bff'
        selection_text = '#333333' if is_light_theme else '#ffffff'
        scrollbar_bg = '#f5f5f5' if is_light_theme else '#2c313a'
        scrollbar_handle = '#c1c1c1' if is_light_theme else '#4b5362'
        
        # 默认字体
        font_family = "Consolas, 'Microsoft YaHei UI', '微软雅黑', monospace"
        
        # 从设置中读取字体信息
        try:
            settings_dir = os.path.join(os.path.expanduser("~"), ".hanabi_notes")
            settings_file = os.path.join(settings_dir, "settings.json")
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                if "editor" in settings and "font" in settings["editor"]:
                    font_settings = settings["editor"]["font"]
                    if "family" in font_settings:
                        custom_font = font_settings.get("family")
                        print(f"应用自定义字体: {custom_font}")
                        # 设置自定义字体，仍然保留后备字体
                        font_family = f"'{custom_font}', Consolas, 'Microsoft YaHei UI', '微软雅黑', monospace"
        except Exception as e:
            print(f"读取字体设置时出错: {e}")
            # 出错时使用默认字体
        
        # 从主题中获取颜色（如果有）
        if hasattr(self.app, 'themeManager') and self.app.themeManager.current_theme:
            # 如果是Theme对象并有get方法
            if hasattr(self.app.themeManager.current_theme, 'get'):
                bg_color = self.app.themeManager.current_theme.get("editor.background", bg_color)
                text_color = self.app.themeManager.current_theme.get("editor.text_color", text_color)
                selection_bg = self.app.themeManager.current_theme.get("editor.selection_color", selection_bg)
            # 如果是Theme对象有data属性
            elif hasattr(self.app.themeManager.current_theme, 'data') and isinstance(self.app.themeManager.current_theme.data, dict):
                if 'editor' in self.app.themeManager.current_theme.data:
                    editor_data = self.app.themeManager.current_theme.data['editor']
                    bg_color = editor_data.get('background', bg_color)
                    text_color = editor_data.get('text_color', text_color)
                    selection_bg = editor_data.get('selection_color', selection_bg)
            # 如果是字典
            elif isinstance(self.app.themeManager.current_theme, dict):
                if 'editor' in self.app.themeManager.current_theme:
                    editor_data = self.app.themeManager.current_theme['editor']
                    bg_color = editor_data.get('background', bg_color)
                    text_color = editor_data.get('text_color', text_color)
                    selection_bg = editor_data.get('selection_color', selection_bg)
        
        # 设置配色方案
        editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: %s;
                color: %s;
                border: none;
                padding: 10px;
                selection-background-color: %s;
                selection-color: %s;
                font-family: %s;
            }
            QScrollBar:vertical {
                border: none;
                background: %s;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: %s;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QScrollBar:horizontal {
                border: none;
                background: %s;
                height: 10px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: %s;
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """ % (
            bg_color,  # 背景色
            text_color,  # 文本颜色
            selection_bg,  # 选择背景色
            selection_text,  # 选择文本颜色
            font_family,  # 字体
            scrollbar_bg,  # 滚动条背景色
            scrollbar_handle,  # 滚动条滑块色
            scrollbar_bg,  # 水平滚动条背景色
            scrollbar_handle  # 水平滚动条滑块色
        ))
        
        # 设置字体大小和字体族
        font = QFont()
        # 尝试设置主字体族，提取出第一个字体作为主字体
        primary_font = font_family.split(',')[0].strip().replace("'", "").replace('"', '')
        font.setFamily(primary_font)
        font.setPointSize(fontSize)

        # 检查是否有粗体和斜体设置
        try:
            settings_dir = os.path.join(os.path.expanduser("~"), ".hanabi_notes")
            settings_file = os.path.join(settings_dir, "settings.json")
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                if "editor" in settings and "font" in settings["editor"]:
                    font_settings = settings["editor"]["font"]
                    if "bold" in font_settings and font_settings["bold"]:
                        font.setBold(True)
                    if "italic" in font_settings and font_settings["italic"]:
                        font.setItalic(True)
        except Exception as e:
            print(f"读取字体样式设置时出错: {e}")
        
        editor.setFont(font)
        
        print(f"编辑器样式更新完成，使用字体: {primary_font}, 大小: {fontSize}")
        
        # 应用滚动条样式
        try:
            if hasattr(self.app, 'themeManager') and self.app.themeManager:
                scrollbar_style = self.app.themeManager.get_scrollbar_style()
            else:
                scrollbar_style = ScrollBarStyle.get_style(base_color="transparent", handle_color="rgba(255, 255, 255, 0.3)")
            
            print(f"添加滚动条样式: {scrollbar_style[:50]}...")
            editor.setStyleSheet(editor.styleSheet() + scrollbar_style)
            
            editor.verticalScrollBar().setStyleSheet(scrollbar_style)
        except Exception as e:
            print(f"添加滚动条样式时出错: {e}")
    
    def updateEditorContainerStyle(self, container):
        """更新编辑器容器样式"""
        
        # 确定当前主题
        theme_name = "dark"  # 默认主题
        
        # 尝试获取当前主题名称
        if hasattr(self.app, 'themeManager') and self.app.themeManager:
            if hasattr(self.app.themeManager, 'current_theme_name'):
                theme_name = self.app.themeManager.current_theme_name
            elif hasattr(self.app, 'currentTheme'):
                theme_name = self.app.currentTheme
                
        # 检查是否为亮色主题
        is_light_theme = theme_name == "light"
        
        # 默认颜色
        bg_color = '#ffffff' if is_light_theme else '#282c34'
        border_color = '#e5e5e5' if is_light_theme else '#343a45'
        
        # 从主题获取颜色（如果可用）
        if hasattr(self.app, 'themeManager') and self.app.themeManager and self.app.themeManager.current_theme:
            # 主题对象有get方法
            if hasattr(self.app.themeManager.current_theme, 'get'):
                bg_color = self.app.themeManager.current_theme.get("editor.background", bg_color)
                border_color = self.app.themeManager.current_theme.get("editor.border_color", border_color)
            # 主题对象有data属性
            elif hasattr(self.app.themeManager.current_theme, 'data') and isinstance(self.app.themeManager.current_theme.data, dict):
                if 'editor' in self.app.themeManager.current_theme.data:
                    editor_data = self.app.themeManager.current_theme.data['editor']
                    bg_color = editor_data.get('background', bg_color)
                    border_color = editor_data.get('border_color', border_color)
            # 主题是字典
            elif isinstance(self.app.themeManager.current_theme, dict):
                if 'editor' in self.app.themeManager.current_theme:
                    editor_data = self.app.themeManager.current_theme['editor']
                    bg_color = editor_data.get('background', bg_color)
                    border_color = editor_data.get('border_color', border_color)
        
        # 设置容器样式
        container.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border: none;
                border-radius: 5px;
            }}
        """)
        
    def applyHighlighter(self, editor, file_type=None):
        """应用语法高亮器到编辑器"""
        if hasattr(self.app, 'highlightMode') and not self.app.highlightMode:
            return
            
        # 清除现有的高亮器
        if hasattr(editor, 'highlighter') and editor.highlighter:
            editor.highlighter.setDocument(None)
        
        # 确定文件类型
        fileType = file_type or self.current_file_type
        
        # 确定是否为亮色主题
        is_light_theme = False
        if hasattr(self.app, 'currentTheme'):
            is_light_theme = self.app.currentTheme == "light"
        
        # 创建新的高亮器
        try:
            highlighter = get_highlighter(fileType, editor.document(), is_light_theme)
            if highlighter:
                editor.highlighter = highlighter
                print(f"已应用 {fileType} 语法高亮器")
            else:
                editor.highlighter = None
                print(f"未找到 {fileType} 对应的语法高亮器")
        except Exception as e:
            print(f"应用语法高亮器时出错: {e}")
            editor.highlighter = None
            
    def scrollToLine(self, editor, lineNumber):
        """滚动编辑器到指定行"""
        if not editor:
            return
        
        # 检查文档是否为空
        if editor.document().isEmpty():
            print("无法滚动到指定行：文档为空")
            return
            
        # 检查行号是否有效
        total_lines = editor.document().blockCount()
        if lineNumber <= 0 or lineNumber > total_lines:
            print(f"无法滚动到指定行：行号 {lineNumber} 超出范围 (1-{total_lines})")
            return
            
        block = editor.document().findBlockByLineNumber(lineNumber - 1)
        if block.isValid():
            # 创建文本光标并移动到指定行
            cursor = QTextCursor(block)
            editor.setTextCursor(cursor)
            
            # 确保该行在视图中间
            editor.centerCursor()
            
            # 高亮显示该行
            selection = QPlainTextEdit.ExtraSelection()
            selection.format.setBackground(QColor("#4077c866"))  # 半透明蓝色高亮
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = editor.textCursor()
            selection.cursor.clearSelection()
            
            editor.setExtraSelections([selection])
            
            # 使用动画闪烁效果
            self.highlightCurrentLine(editor)
        else:
            print(f"无法滚动到指定行：行号 {lineNumber} 对应的文本块无效")
    
    def highlightCurrentLine(self, editor):
        """高亮当前行，带有闪烁效果"""
        if not editor:
            return
            
        # 检查文档是否为空
        if editor.document().isEmpty():
            print("无法高亮当前行：文档为空")
            return
            
        # 获取当前行的文本光标
        cursor = editor.textCursor()
        
        # 检查光标位置是否有效
        if cursor.position() < 0 or cursor.position() > editor.document().characterCount():
            print(f"无法高亮当前行：光标位置 {cursor.position()} 无效")
            return
            
        cursor.select(QTextCursor.LineUnderCursor)
        selection = QPlainTextEdit.ExtraSelection()
        
        # 初始颜色
        highlight_color = QColor("#4077c866")  # 半透明蓝色高亮
        
        selection.format.setBackground(highlight_color)
        selection.format.setProperty(QTextFormat.FullWidthSelection, True)
        selection.cursor = cursor
        
        editor.setExtraSelections([selection])
        
        # 简单的闪烁效果
        def flash_highlight():
            nonlocal editor
            
            if not editor:
                return
                
            # 清除高亮
            editor.setExtraSelections([])
            
            # 延迟后恢复高亮
            QTimer.singleShot(300, lambda: self.restoreFormat(editor))
        
        # 延迟启动闪烁效果
        QTimer.singleShot(500, flash_highlight)
    
    def restoreFormat(self, editor):
        """恢复行高亮"""
        if not editor:
            return
            
        cursor = editor.textCursor()
        cursor.select(QTextCursor.LineUnderCursor)
        selection = QPlainTextEdit.ExtraSelection()
        
        selection.format.setBackground(QColor("#4077c833"))  # 更淡的高亮
        selection.format.setProperty(QTextFormat.FullWidthSelection, True)
        selection.cursor = cursor
        
        editor.setExtraSelections([selection])
        
    def detectFileType(self, filePath):
        """根据文件路径检测文件类型"""
        if not filePath:
            return "text"
            
        suffix = os.path.splitext(filePath)[1].lower()
        file_type_map = {
            '.py': 'python',
            '.txt': 'text',
            '.md': 'markdown',
            '.html': 'html',
            '.htm': 'html',
            '.css': 'css',
            '.js': 'javascript',
            '.json': 'json',
            '.xml': 'xml',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.ini': 'ini',
            '.toml': 'toml',
            '.c': 'c',
            '.cpp': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            '.java': 'java',
            '.cs': 'cs',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.sql': 'sql'
        }
        
        file_type = file_type_map.get(suffix, 'text')
        self.current_file_type = file_type
        return file_type 