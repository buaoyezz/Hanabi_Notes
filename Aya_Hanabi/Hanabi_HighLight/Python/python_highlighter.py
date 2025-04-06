
import re
from PySide6.QtGui import QColor, QFont, QTextCharFormat
from .. import BaseHighlighter, log_highlight_error

class PythonHighlighter(BaseHighlighter):
    def __init__(self, document, is_light_theme=False):
        super().__init__(document, is_light_theme)
    
    def _init_formats(self):

        if self.is_light_theme:

            self.formats['keyword'] = self._create_format('#0000FF', bold=True)  # 蓝色关键字
            self.formats['string'] = self._create_format('#008000')  # 绿色字符串
            self.formats['comment'] = self._create_format('#808080', italic=True)  # 灰色注释
            self.formats['number'] = self._create_format('#FF8000')  # 橙色数字
            self.formats['function'] = self._create_format('#800080')  # 紫色函数
            self.formats['class'] = self._create_format('#000080', bold=True)  # 深蓝色类
            self.formats['decorator'] = self._create_format('#808000')  # 橄榄色装饰器
        else:
            # 暗色主题的颜色
            self.formats['keyword'] = self._create_format('#569CD6', bold=True)  # 蓝色关键字
            self.formats['string'] = self._create_format('#CE9178')  # 橙色字符串
            self.formats['comment'] = self._create_format('#6A9955', italic=True)  # 绿色注释
            self.formats['number'] = self._create_format('#B5CEA8')  # 浅绿色数字
            self.formats['function'] = self._create_format('#DCDCAA')  # 黄色函数
            self.formats['class'] = self._create_format('#4EC9B0', bold=True)  # 青色类
            self.formats['decorator'] = self._create_format('#C586C0')  # 粉色装饰器
            self.formats['builtin'] = self._create_format('#4FC1FF')  # 内置函数
    
    def highlightBlock(self, text):
        try:
            # 关键字规则
            keywords = [
                'and', 'as', 'assert', 'break', 'class', 'continue', 'def', 
                'del', 'elif', 'else', 'except', 'False', 'finally', 'for', 
                'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'None', 
                'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'True', 
                'try', 'while', 'with', 'yield'
            ]
            

            builtins = [
                'abs', 'all', 'any', 'bin', 'bool', 'bytearray', 'bytes', 'callable',
                'chr', 'classmethod', 'compile', 'complex', 'delattr', 'dict', 'dir',
                'divmod', 'enumerate', 'eval', 'exec', 'filter', 'float', 'format',
                'frozenset', 'getattr', 'globals', 'hasattr', 'hash', 'help', 'hex',
                'id', 'input', 'int', 'isinstance', 'issubclass', 'iter', 'len', 'list',
                'locals', 'map', 'max', 'memoryview', 'min', 'next', 'object', 'oct',
                'open', 'ord', 'pow', 'print', 'property', 'range', 'repr', 'reversed',
                'round', 'set', 'setattr', 'slice', 'sorted', 'staticmethod', 'str',
                'sum', 'super', 'tuple', 'type', 'vars', 'zip', '__import__'
            ]
            
            # Python关键字高亮
            for keyword in keywords:
                pattern = r'\b' + keyword + r'\b'
                try:
                    for match in re.finditer(pattern, text):
                        start = match.start()
                        length = match.end() - start
                        self.setFormat(start, length, self.formats['keyword'])
                except Exception:
                    pass
            
            # 内置函数高亮
            for builtin in builtins:
                pattern = r'\b' + builtin + r'\b'
                try:
                    for match in re.finditer(pattern, text):
                        start = match.start()
                        length = match.end() - start
                        self.setFormat(start, length, self.formats['builtin'])
                except Exception:
                    pass
            
            # 字符串高亮
            # 单引号字符串
            try:
                string_re = re.compile(r"'[^'\n]*'")
                for match in string_re.finditer(text):
                    start = match.start()
                    length = match.end() - start
                    self.setFormat(start, length, self.formats['string'])
            except Exception:
                pass
                

            try:
                string_re = re.compile(r'"[^"\n]*"')
                for match in string_re.finditer(text):
                    start = match.start()
                    length = match.end() - start
                    self.setFormat(start, length, self.formats['string'])
            except Exception:
                pass
            

            try:
                triple_single = re.compile(r"'''.*?'''", re.DOTALL)
                for match in triple_single.finditer(text):
                    start = match.start()
                    length = match.end() - start
                    self.setFormat(start, length, self.formats['string'])
            except Exception:
                pass
                
            try:
                triple_double = re.compile(r'""".*?"""', re.DOTALL)
                for match in triple_double.finditer(text):
                    start = match.start()
                    length = match.end() - start
                    self.setFormat(start, length, self.formats['string'])
            except Exception:
                pass
            

            try:
                comment_re = re.compile(r'#.*$')
                match = comment_re.search(text)
                if match:
                    start = match.start()
                    length = match.end() - start
                    self.setFormat(start, length, self.formats['comment'])
            except Exception:
                pass
            

            try:
                number_re = re.compile(r'\b[0-9]+\b')
                for match in number_re.finditer(text):
                    start = match.start()
                    length = match.end() - start
                    self.setFormat(start, length, self.formats['number'])
            except Exception:
                pass
            

            try:
                function_re = re.compile(r'\b[A-Za-z_][A-Za-z0-9_]*(?=\s*\()')
                for match in function_re.finditer(text):
                    start = match.start()
                    length = match.end() - start
                    func_name = text[start:start+length]
                    # 不要高亮关键字函数（如if, for等）和内置函数
                    if func_name not in keywords and func_name not in builtins:
                        self.setFormat(start, length, self.formats['function'])
            except Exception:
                pass
            
            # 类定义高亮
            try:
                class_re = re.compile(r'(?:^|\s)class\s+([A-Za-z_][A-Za-z0-9_]*)')
                for match in class_re.finditer(text):
                    if len(match.groups()) > 0:

                        start = match.start(1)
                        length = match.end(1) - start
                        self.setFormat(start, length, self.formats['class'])
            except Exception:
                pass
            

            try:
                decorator_re = re.compile(r'@[A-Za-z_][A-Za-z0-9_]*')
                for match in decorator_re.finditer(text):
                    start = match.start()
                    length = match.end() - start
                    self.setFormat(start, length, self.formats['decorator'])
            except Exception:
                pass
                
        except Exception as e:
            # 如果出现任何错误，记录错误并避免崩溃
            log_highlight_error(f"Python语法高亮出错: {e}") 