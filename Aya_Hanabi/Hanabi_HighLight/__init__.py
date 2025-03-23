import sys
import os
import re
from PySide6.QtGui import QColor, QFont, QTextCharFormat, QSyntaxHighlighter

# 记录错误的函数
def log_highlight_error(message):
    try:
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        log_file = os.path.join(log_dir, "hanabi_highlight.log")
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{message}\n")
    except Exception as e:
        print(f"写入高亮日志文件出错: {e}")

# 高亮基类
class BaseHighlighter(QSyntaxHighlighter):
    def __init__(self, document, is_light_theme=False):
        super().__init__(document)
        self.is_light_theme = is_light_theme
        self.formats = {}
        self._init_formats()
    
    def _init_formats(self):
        # 子类应该重写这个方法来初始化格式
        pass
    
    def _create_format(self, color, bold=False, italic=False):
        text_format = QTextCharFormat()
        text_format.setForeground(QColor(color))
        if bold:
            text_format.setFontWeight(QFont.Bold)
        if italic:
            text_format.setFontItalic(True)
        return text_format
    
    def highlightBlock(self, text):
        # 子类应该重写这个方法来实现高亮逻辑
        pass

# 基本文本高亮器
class BasicTextHighlighter(BaseHighlighter):
    def __init__(self, document, is_light_theme=False):
        super().__init__(document, is_light_theme)
    
    def _init_formats(self):
        # 基于亮暗主题选择合适的颜色
        if self.is_light_theme:
            # 亮色主题的颜色
            self.formats['number'] = self._create_format('#FF8000')  # 橙色数字
            self.formats['url'] = self._create_format('#0000FF', italic=True)  # 蓝色URL
            self.formats['email'] = self._create_format('#008000')  # 绿色邮箱
            self.formats['special_symbol'] = self._create_format('#800080')  # 紫色特殊符号
        else:
            # 暗色主题的颜色
            self.formats['number'] = self._create_format('#B5CEA8')  # 浅绿色数字
            self.formats['url'] = self._create_format('#569CD6', italic=True)  # 蓝色URL
            self.formats['email'] = self._create_format('#6A9955')  # 绿色邮箱
            self.formats['special_symbol'] = self._create_format('#C586C0')  # 粉色特殊符号
    
    def highlightBlock(self, text):
        try:
            # 数字高亮
            try:
                number_re = re.compile(r'\b[0-9]+\b')
                for match in number_re.finditer(text):
                    start = match.start()
                    length = match.end() - start
                    self.setFormat(start, length, self.formats['number'])
            except Exception:
                pass
            
            # URL高亮
            try:
                url_re = re.compile(r'https?://\S+|www\.\S+')
                for match in url_re.finditer(text):
                    start = match.start()
                    length = match.end() - start
                    self.setFormat(start, length, self.formats['url'])
            except Exception:
                pass
            
            # 邮箱高亮
            try:
                email_re = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
                for match in email_re.finditer(text):
                    start = match.start()
                    length = match.end() - start
                    self.setFormat(start, length, self.formats['email'])
            except Exception:
                pass
            
            # 特殊符号高亮
            try:
                symbol_re = re.compile(r'[!@#$%^&*()_+\-=\[\]{};:"\\|,.<>\/?]')
                for match in symbol_re.finditer(text):
                    start = match.start()
                    length = match.end() - start
                    self.setFormat(start, length, self.formats['special_symbol'])
            except Exception:
                pass
                
        except Exception as e:
            # 如果出现任何错误，记录错误并避免崩溃
            log_highlight_error(f"文本高亮出错: {e}")

# 获取高亮器
def get_highlighter(file_type, document, is_light_theme=False):
    try:
        if file_type.lower() == 'python':
            from .Python.python_highlighter import PythonHighlighter
            return PythonHighlighter(document, is_light_theme)
        elif file_type.lower() == 'markdown':
            from .MarkDown.markdown_highlighter import MarkdownHighlighter
            return MarkdownHighlighter(document, is_light_theme)
        else:
            # 返回基本文本高亮器
            return BasicTextHighlighter(document, is_light_theme)
    except Exception as e:
        log_highlight_error(f"获取高亮器出错: {e}")
        # 尝试返回基本文本高亮器
        try:
            return BasicTextHighlighter(document, is_light_theme)
        except Exception as e2:
            log_highlight_error(f"创建基本文本高亮器出错: {e2}")
            return None

# auto detect file type
def detect_file_type(file_path):
    if not file_path:
        return 'text'
        
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext in ['.py', '.pyw', '.pyc', '.pyo', '.pyd']:
        return 'python'
    elif ext in ['.md', '.markdown', '.mdown', '.mkdn', '.mkd', '.mdwn', '.mdtxt', '.mdtext', '.rmd']:
        return 'markdown'
    elif ext in ['.js', '.jsx', '.ts', '.tsx', '.json']:
        return 'javascript'
    elif ext in ['.html', '.htm', '.xml']:
        return 'html'
    elif ext in ['.css', '.scss', '.less']:
        return 'css'
    elif ext in ['.java', '.class']:
        return 'java'
    elif ext in ['.cpp', '.c', '.h', '.hpp']:
        return 'cpp'
    elif ext in ['.cs']:
        return 'csharp'
    elif ext in ['.go']:
        return 'go'
    elif ext in ['.php']:
        return 'php'
    elif ext in ['.rb']:
        return 'ruby'
    elif ext in ['.swift']:
        return 'swift'
    else:
        return 'text' 