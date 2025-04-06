import re
from PySide6.QtGui import QColor, QFont, QTextCharFormat
from .. import BaseHighlighter, log_highlight_error

class JSONHighlighter(BaseHighlighter):
    def __init__(self, document, is_light_theme=False):
        super().__init__(document, is_light_theme)
        # 设置JSON特定的属性
        self.multiline_comment_start = False  # 跟踪多行注释状态
    
    def _init_formats(self):
        # 基于亮暗主题选择合适的颜色
        if self.is_light_theme:
            # 亮色主题的颜色 - 参考VSCode和JetBrains的配色方案
            self.formats['key'] = self._create_format('#0451A5', bold=True)  # 深蓝色键
            self.formats['string'] = self._create_format('#0B7500')  # 深绿色字符串
            self.formats['number'] = self._create_format('#098658')  # 绿色数字
            self.formats['boolean'] = self._create_format('#0000FF')  # 蓝色布尔值
            self.formats['null'] = self._create_format('#0000FF')  # 蓝色null
            self.formats['punctuation'] = self._create_format('#000000')  # 黑色标点
            self.formats['comment'] = self._create_format('#008000', italic=True)  # 绿色注释
            self.formats['error'] = self._create_format('#FF0000')  # 红色错误
            self.formats['escape'] = self._create_format('#EE8434')  # 橙色转义字符
            self.formats['property_value'] = self._create_format('#0451A5')  # 深蓝色属性值
        else:
            # 暗色主题的颜色 - 参考VSCode Dark+和JetBrains Darcula
            self.formats['key'] = self._create_format('#9CDCFE', bold=True)  # 浅蓝色键
            self.formats['string'] = self._create_format('#CE9178')  # 橙色字符串
            self.formats['number'] = self._create_format('#B5CEA8')  # 浅绿色数字
            self.formats['boolean'] = self._create_format('#569CD6')  # 蓝色布尔值
            self.formats['null'] = self._create_format('#569CD6')  # 蓝色null
            self.formats['punctuation'] = self._create_format('#D4D4D4')  # 浅灰标点
            self.formats['comment'] = self._create_format('#6A9955', italic=True)  # 绿色注释
            self.formats['error'] = self._create_format('#F14C4C')  # 红色错误
            self.formats['escape'] = self._create_format('#D7BA7D')  # 金色转义字符
            self.formats['property_value'] = self._create_format('#9CDCFE')  # 浅蓝色属性值
    
    def highlightBlock(self, text):
        try:
            # 处理多行注释状态
            self._handle_multiline_comments(text)
            
            # 如果当前行在多行注释内，直接返回
            if self.multiline_comment_start:
                return
                
            # 处理单行注释 (// 和 #)
            self._highlight_single_line_comments(text)
            
            # 匹配JSON键（支持嵌套键和特殊字符）
            key_pattern = r'(?<!\\)"((?:\\"|[^"])+?)"(?=\s*:)'
            for match in re.finditer(key_pattern, text):
                # 确保不在注释内
                if not self._is_in_comment(text, match.start()):
                    self.setFormat(match.start(), match.end() - match.start(), self.formats['key'])
                    # 高亮转义字符
                    self._highlight_escapes(text, match.start(), match.end())
            
            # 匹配JSON字符串值（支持转义字符和特殊字符）
            string_pattern = r'(?<!\\)"(?:\\"|\\\\|\\\/|\\b|\\f|\\n|\\r|\\t|\\u[0-9a-fA-F]{4}|[^"\\])*"'
            for match in re.finditer(string_pattern, text):
                # 排除键部分且确保不在注释内
                if not re.search(r'\s*:\s*$', text[:match.start()]) and not self._is_in_comment(text, match.start()):
                    self.setFormat(match.start(), match.end() - match.start(), self.formats['string'])
                    # 高亮转义字符
                    self._highlight_escapes(text, match.start(), match.end())
            
            # 匹配JSON数字（支持科学计数法、十六进制和负数）
            number_pattern = r'(?<!\w)(-?(?:0[xX][0-9a-fA-F]+|\d+(?:\.\d+)?(?:[eE][+-]?\d+)?))(?!\w)'
            for match in re.finditer(number_pattern, text):
                if not self._is_in_comment(text, match.start()):
                    self.setFormat(match.start(), match.end() - match.start(), self.formats['number'])
            
            # 匹配JSON布尔值
            boolean_pattern = r'(?<!\w)(true|false)(?!\w)'
            for match in re.finditer(boolean_pattern, text):
                if not self._is_in_comment(text, match.start()):
                    self.setFormat(match.start(), match.end() - match.start(), self.formats['boolean'])
            
            # 匹配JSON null
            null_pattern = r'(?<!\w)(null)(?!\w)'
            for match in re.finditer(null_pattern, text):
                if not self._is_in_comment(text, match.start()):
                    self.setFormat(match.start(), match.end() - match.start(), self.formats['null'])
            
            # 匹配JSON标点符号
            punctuation_pattern = r'[\[\]\{\}:,]'
            for match in re.finditer(punctuation_pattern, text):
                if not self._is_in_comment(text, match.start()):
                    self.setFormat(match.start(), match.end() - match.start(), self.formats['punctuation'])
            
            # 检测并高亮JSON语法错误
            self._highlight_syntax_errors(text)
                
        except Exception as e:
            log_highlight_error(f"JSON语法高亮出错: {e}")
    
    def _highlight_escapes(self, text, start, end):
        """高亮字符串中的转义序列"""
        escape_pattern = r'\\(?:["\\\/bfnrt]|u[0-9a-fA-F]{4})'
        for match in re.finditer(escape_pattern, text[start:end]):
            esc_start = start + match.start()
            esc_length = match.end() - match.start()
            self.setFormat(esc_start, esc_length, self.formats['escape'])
    
    def _highlight_single_line_comments(self, text):
        """高亮单行注释 (// 和 #)"""
        # 匹配 // 注释
        comment_pattern = r'//.*$'
        match = re.search(comment_pattern, text)
        if match:
            self.setFormat(match.start(), match.end() - match.start(), self.formats['comment'])
            return True
        
        # 匹配 # 注释
        comment_pattern = r'#.*$'
        match = re.search(comment_pattern, text)
        if match:
            self.setFormat(match.start(), match.end() - match.start(), self.formats['comment'])
            return True
        
        return False
    
    def _handle_multiline_comments(self, text):
        """处理多行注释 /* ... */"""
        # 如果已经在多行注释中
        if self.multiline_comment_start:
            end_index = text.find('*/')
            if end_index != -1:
                # 找到注释结束标记
                self.setFormat(0, end_index + 2, self.formats['comment'])
                self.multiline_comment_start = False
                # 处理注释后的剩余文本
                if end_index + 2 < len(text):
                    remaining_text = text[end_index + 2:]
                    # 递归处理剩余文本
                    self.highlightBlock(remaining_text)
            else:
                # 整行都是注释
                self.setFormat(0, len(text), self.formats['comment'])
            return True
        
        # 检查是否有新的多行注释开始
        start_index = text.find('/*')
        if start_index != -1:
            end_index = text.find('*/', start_index)
            if end_index != -1:
                # 单行内完整的多行注释
                self.setFormat(start_index, end_index - start_index + 2, self.formats['comment'])
            else:
                # 多行注释开始但没有结束
                self.setFormat(start_index, len(text) - start_index, self.formats['comment'])
                self.multiline_comment_start = True
            return True
        
        return False
    
    def _is_in_comment(self, text, position):
        """检查位置是否在注释内"""
        # 检查是否在 // 注释内
        slash_pos = text.find('//', 0, position)
        if slash_pos != -1:
            return True
        
        # 检查是否在 # 注释内
        hash_pos = text.find('#', 0, position)
        if hash_pos != -1:
            return True
        
        return False
    
    def _highlight_syntax_errors(self, text):
        """检测并高亮基本的JSON语法错误"""
        # 检查未闭合的引号
        quote_count = text.count('"') - text.count('\\"')
        if quote_count % 2 != 0:
            # 找到最后一个非转义引号
            last_quote = -1
            i = 0
            while i < len(text):
                if text[i] == '"' and (i == 0 or text[i-1] != '\\'):
                    last_quote = i
                i += 1
            
            if last_quote != -1:
                # 高亮未闭合的引号
                self.setFormat(last_quote, 1, self.formats['error'])
        
        # 检查未闭合的括号
        for bracket_pair in [('{', '}'), ('[', ']')]:
            open_count = text.count(bracket_pair[0])
            close_count = text.count(bracket_pair[1])
            if open_count > close_count:
                # 有未闭合的开括号
                last_open = text.rfind(bracket_pair[0])
                if last_open != -1:
                    self.setFormat(last_open, 1, self.formats['error'])
            elif close_count > open_count:
                # 有未闭合的闭括号
                first_close = text.find(bracket_pair[1])
                if first_close != -1:
                    self.setFormat(first_close, 1, self.formats['error'])