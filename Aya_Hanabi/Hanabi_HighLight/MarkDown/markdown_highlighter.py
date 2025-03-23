import re
from PySide6.QtGui import QColor, QFont, QTextCharFormat
from .. import BaseHighlighter, log_highlight_error

class MarkdownHighlighter(BaseHighlighter):
    def __init__(self, document, is_light_theme=False):
        super().__init__(document, is_light_theme)
    
    def _init_formats(self):
        # 基于亮暗主题选择合适的颜色
        if self.is_light_theme:
            # 亮色主题的颜色
            self.formats['header'] = self._create_format('#0066CC', bold=True)  # 蓝色标题
            self.formats['emphasis'] = self._create_format('#000000', italic=True)  # 黑色斜体
            self.formats['strong'] = self._create_format('#000000', bold=True)  # 黑色粗体
            self.formats['code'] = self._create_format('#990000', bold=False)  # 红色代码
            self.formats['link'] = self._create_format('#006633')  # 绿色链接
            self.formats['list'] = self._create_format('#333333', bold=True)  # 深灰列表标记
            self.formats['blockquote'] = self._create_format('#666666', italic=True)  # 灰色引用
            self.formats['horizontal_rule'] = self._create_format('#444444', bold=True)  # 深灰水平线
            self.formats['image'] = self._create_format('#6600CC')  # 紫色图片
        else:
            # 暗色主题的颜色
            self.formats['header'] = self._create_format('#6495ED', bold=True)  # 蓝色标题
            self.formats['emphasis'] = self._create_format('#E0E0E0', italic=True)  # 浅灰斜体
            self.formats['strong'] = self._create_format('#E0E0E0', bold=True)  # 浅灰粗体
            self.formats['code'] = self._create_format('#CE9178', bold=False)  # 橙色代码
            self.formats['link'] = self._create_format('#6A9955')  # 绿色链接
            self.formats['list'] = self._create_format('#B5CEA8', bold=True)  # 浅绿列表标记
            self.formats['blockquote'] = self._create_format('#9CDCFE', italic=True)  # 淡蓝引用
            self.formats['horizontal_rule'] = self._create_format('#569CD6', bold=True)  # 蓝色水平线
            self.formats['image'] = self._create_format('#C586C0')  # 粉色图片
    
    def highlightBlock(self, text):
        try:
            # 段落格式
            block_state = self.previousBlockState()
            
            # 标题格式 (# 标题)
            try:
                header_pattern = r'^(#{1,6})\s+(.+?)(?:\s+#+)?$'
                header_match = re.match(header_pattern, text)
                if header_match:
                    level = len(header_match.group(1))
                    header_text_start = header_match.start(2)
                    header_text_length = len(header_match.group(2))
                    # 使标题粗细与级别对应
                    header_format = self._create_format(
                        self.formats['header'].foreground().color().name(),
                        bold=True,
                        italic=False
                    )
                    # 根据标题级别设置字体大小 (可选)
                    font = QFont(header_format.font())
                    if level == 1:
                        font.setPointSize(font.pointSize() + 4)
                    elif level == 2:
                        font.setPointSize(font.pointSize() + 3)
                    elif level == 3:
                        font.setPointSize(font.pointSize() + 2)
                    elif level == 4:
                        font.setPointSize(font.pointSize() + 1)
                    header_format.setFont(font)
                    
                    # 高亮整行
                    self.setFormat(0, len(text), header_format)
            except Exception:
                pass

            # 代码块 (``` 或 ~~~)
            try:
                code_pattern = r'^(\s*)(```|~~~)(.*)$'
                code_match = re.match(code_pattern, text)
                
                # 如果是代码块开始或结束标记
                if code_match:
                    self.setFormat(code_match.start(2), len(code_match.group(2)), self.formats['code'])
                    if block_state != 1:  # 不在代码块内
                        self.setCurrentBlockState(1)  # 进入代码块
                    else:
                        self.setCurrentBlockState(0)  # 退出代码块
                    
                    # 高亮语言名称
                    if len(code_match.group(3)) > 0:
                        self.setFormat(code_match.start(3), len(code_match.group(3)), self.formats['code'])
                    
                # 如果处于代码块内部
                elif block_state == 1:
                    self.setFormat(0, len(text), self.formats['code'])
                    self.setCurrentBlockState(1)  # 保持在代码块中
            except Exception:
                pass
                
            # 如果不在代码块内，应用其他格式
            if self.currentBlockState() != 1:
                # 行内代码 (`代码`)
                try:
                    code_in_line = re.compile(r'`([^`]+)`')
                    for match in code_in_line.finditer(text):
                        start = match.start()
                        length = match.end() - start
                        self.setFormat(start, length, self.formats['code'])
                except Exception:
                    pass
                
                # 引用 (> 文本)
                try:
                    if text.startswith('>'):
                        self.setFormat(0, len(text), self.formats['blockquote'])
                except Exception:
                    pass
                
                # 强调 (*文本* 或 _文本_)
                try:
                    emphasis = re.compile(r'(\*|_)([^\*_]+)(\*|_)')
                    for match in emphasis.finditer(text):
                        if match.group(1) == match.group(3):  # 确保开始和结束标记匹配
                            start = match.start()
                            length = match.end() - start
                            self.setFormat(start, length, self.formats['emphasis'])
                except Exception:
                    pass
                
                # 粗体 (**文本** 或 __文本__)
                try:
                    strong = re.compile(r'(\*\*|__)([^\*_]+)(\*\*|__)')
                    for match in strong.finditer(text):
                        if match.group(1) == match.group(3):  # 确保开始和结束标记匹配
                            start = match.start()
                            length = match.end() - start
                            self.setFormat(start, length, self.formats['strong'])
                except Exception:
                    pass
                
                # 链接 [文本](链接)
                try:
                    link = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
                    for match in link.finditer(text):
                        start = match.start()
                        length = match.end() - start
                        self.setFormat(start, length, self.formats['link'])
                except Exception:
                    pass
                
                # 图片 ![文本](链接)
                try:
                    image = re.compile(r'!\[([^\]]+)\]\(([^)]+)\)')
                    for match in image.finditer(text):
                        start = match.start()
                        length = match.end() - start
                        self.setFormat(start, length, self.formats['image'])
                except Exception:
                    pass
                
                # 列表 (- 项目 或 * 项目 或 1. 项目)
                try:
                    list_pattern = re.compile(r'^\s*([\*\-\+]|\d+\.)\s')
                    match = list_pattern.search(text)
                    if match:
                        start = match.start(1)
                        length = match.end(1) - start
                        self.setFormat(start, length, self.formats['list'])
                except Exception:
                    pass
                
                # 水平线 (--- 或 *** 或 ___)
                try:
                    if re.match(r'^\s*([\*\-_])\s*(\1\s*){2,}$', text):
                        self.setFormat(0, len(text), self.formats['horizontal_rule'])
                except Exception:
                    pass
                    
        except Exception as e:
            # 如果出现任何错误，记录错误并避免崩溃
            log_highlight_error(f"Markdown语法高亮出错: {e}") 