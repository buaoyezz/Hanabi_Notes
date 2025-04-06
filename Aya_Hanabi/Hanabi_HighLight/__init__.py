import sys
import os
import re
import json
from PySide6.QtGui import QColor, QFont, QTextCharFormat, QSyntaxHighlighter

# 导入设置函数
try:
    from Aya_Hanabi.Hanabi_Page.SettingsPages import get_setting
except ImportError:
    # 如果无法导入，创建一个临时的默认函数
    def get_setting(section, group=None, key=None, default=None):
        return default

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
        elif file_type.lower() == 'json':
            from .JSON.json_highlighter import JSONHighlighter
            return JSONHighlighter(document, is_light_theme)
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

# 根据文件扩展名获取文件类型
def get_type_by_extension(file_path):
    if not file_path:
        return 'text'
    
    ext = os.path.splitext(file_path)[1].lower()
    ext_map = {
        # 编程语言
        '.py': 'python',
        '.pyw': 'python',
        '.pyi': 'python',
        '.pyx': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript', 
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'cpp',
        '.h': 'cpp',
        '.cs': 'csharp',
        '.go': 'go',
        '.rb': 'ruby',
        '.php': 'php',
        '.rs': 'rust',
        
        # 标记语言
        '.md': 'markdown',
        '.mdown': 'markdown',
        '.mkdn': 'markdown',
        '.mkd': 'markdown',
        '.mdwn': 'markdown',
        '.mdtxt': 'markdown',
        '.markdown': 'markdown',
        '.html': 'html',
        '.htm': 'html',
        '.xml': 'xml',
        '.svg': 'xml',
        
        # 样式表
        '.css': 'css',
        '.scss': 'css',
        '.less': 'css',
        
        # 数据格式
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.toml': 'toml',
        '.ini': 'ini',
        '.conf': 'ini',
        
        # 文本文件
        '.txt': 'text',
        '.log': 'text',
        '.csv': 'text',
        '.sql': 'sql'
    }
    return ext_map.get(ext, 'text')

# auto detect file type
def detect_file_type(file_path):
    if not file_path:
        log_highlight_error("文件路径为空，返回text类型")
        return 'text'
        
    # 获取编辑器设置
    try:
        # 获取设置
        settings_dir = os.path.join(os.path.expanduser("~"), ".hanabi_notes")
        settings_file = os.path.join(settings_dir, "settings.json")
        
        if os.path.exists(settings_file):
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                smart_detection = settings.get("editor", {}).get("editing", {}).get("smart_file_detection", False)
                
                # 如果未启用智能检测，仅使用文件后缀判断
                if not smart_detection:
                    return get_type_by_extension(file_path)
        else:
            # 如果设置文件不存在，默认启用智能检测
            smart_detection = True
    except:
        # 如果获取设置失败，仅使用文件后缀判断
        return get_type_by_extension(file_path)
    
    log_highlight_error(f"开始检测文件类型: {file_path}")
    
    # 检查文件是否为.txt文件，如果是，我们将强制执行内容检测
    is_txt_file = os.path.splitext(file_path)[1].lower() == '.txt'
    
    # 导入配置功能
    try:
        try:
            from Aya_Hanabi.Hanabi_Page.SettingsPages import get_setting
        except ImportError:
            try:
                from Aya_Hanabi.Hanabi_Page.SettingsPages import get_setting
            except ImportError:
                # 如果无法导入，创建一个临时的默认函数
                def get_setting(section, group=None, key=None, default=None):
                    return default
        
        # 获取检测优先级配置 - 默认为根据内容检测
        extension_first = get_setting('editor', 'editing', 'extension_first', False)
        
        # 对于.txt文件，除非禁用了智能检测，否则始终执行内容检测
        if is_txt_file and smart_detection:
            extension_first = False
            log_highlight_error("检测到.txt文件，强制执行内容检测")
        
        # 确定扩展名（后面无论如何都要用到）
        ext = ""
        try:
            ext = os.path.splitext(file_path)[1].lower()
        except Exception as e:
            log_highlight_error(f"获取文件扩展名失败: {e}")
        
        # 根据优先级配置决定检测顺序
        if extension_first:
            # 优先扩展名检测
            log_highlight_error("优先使用扩展名检测")
            
            # 如果是明确的Python文件扩展名，直接返回python类型
            if ext == '.py':
                log_highlight_error(f"直接通过.py扩展名判断为Python文件")
                return 'python'
                
            # 检查文件名是否包含python关键字
            filename = os.path.basename(file_path).lower()
            if 'python' in filename or 'py' in filename.split('.')[0]:
                log_highlight_error(f"文件名包含python相关字符，判断为Python文件")
                return 'python'
                
            # 通过扩展名映射表判断
            # 扩展名映射表
            ext_map = {
                'python': ['.py', '.pyw', '.pyc', '.pyo', '.pyd', '.pyi'],
                'markdown': ['.md', '.markdown', '.mdown', '.mkdn', '.mkd', '.mdwn', '.mdtxt', '.mdtext', '.rmd'],
                'javascript': ['.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs'],
                'json': ['.json', '.jsonc', '.json5'],
                'html': ['.html', '.htm', '.xml', '.xhtml', '.svg'],
                'css': ['.css', '.scss', '.less', '.sass', '.styl'],
                'java': ['.java', '.class', '.jar'],
                'cpp': ['.cpp', '.c', '.h', '.hpp', '.cc', '.cxx'],
                'csharp': ['.cs', '.csx'],
                'go': ['.go'],
                'php': ['.php', '.phtml', '.php3', '.php4', '.php5'],
                'ruby': ['.rb', '.rbw'],
                'swift': ['.swift'],
                'rust': ['.rs', '.rlib'],
                'sql': ['.sql'],
                'yaml': ['.yml', '.yaml'],
                'toml': ['.toml'],
                'ini': ['.ini', '.cfg', '.conf']
            }
            
            # 通过扩展名查找文件类型
            for type_name, extensions in ext_map.items():
                if ext in extensions:
                    log_highlight_error(f"通过扩展名判断文件类型: {type_name}")
                    return type_name
        
        # 无论扩展名优先与否，都要尝试进行内容检测（扩展名优先只是先检查扩展名）
        # 内容检测 - 更准确但相对较慢
        if get_setting('editor', 'editing', 'smart_file_detection', True) or (is_txt_file and smart_detection):  # 修改逻辑，对.txt文件强制检测
            log_highlight_error("尝试通过文件内容检测文件类型")
            content = ""
            encodings = ['utf-8', 'gbk']
            
            # 尝试不同编码读取文件
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read(2048)  # 增加读取字节数以提高准确性
                    break  # 如果成功读取则跳出循环
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    log_highlight_error(f"读取文件内容失败: {e}")
                    break
                    
            content = content.strip()
            
            # 文件类型检测规则
            type_patterns = [
                # JSON文件检测 - 优先检测
                {
                    'type': 'json',
                    'check': lambda c: check_is_json(c, file_path)
                },
                # XML/HTML文件检测
                {
                    'type': 'html',
                    'check': lambda c: check_is_html_xml(c, file_path)
                },
                # Python文件检测
                {
                    'type': 'python',
                    'check': lambda c: bool(re.search(r'^(import\s+\w+|from\s+\w+\s+import|def\s+\w+\s*\(|class\s+\w+\s*[:\(]|#.*python|#.*coding:|#.*-\*-\s*coding:\s*|if\s+__name__\s*==\s*[\'"]__main__[\'"]|try:\s*$|except\s+\w+\s*:\s*$|@\w+(\.\w+)*(\(.*\))?$)', c, re.MULTILINE) or 
                                      any(keyword in c.lower() for keyword in ['def ', 'class ', 'import ', 'while ', 'for ', 'if ', 'elif ', 'else:', 'try:', 'except:', 'finally:', 'with ', 'yield ', 'return ', 'print(', 'assert ', 'global ', 'lambda ']))
                },
                # JavaScript文件检测
                {
                    'type': 'javascript',
                    'check': lambda c: check_is_javascript(c, file_path)
                },
                # CSS文件检测
                {
                    'type': 'css',
                    'check': lambda c: check_is_css(c, file_path)
                },
                # Markdown文件检测
                {
                    'type': 'markdown',
                    'check': lambda c: check_is_markdown(c, file_path)
                }
            ]
            
            # 检测文件类型
            for pattern in type_patterns:
                try:
                    if pattern['check'](content):
                        log_highlight_error(f"检测到{pattern['type']}文件格式")
                        return pattern['type']
                except Exception as e:
                    log_highlight_error(f"检测{pattern['type']}格式时出错: {e}")
                    continue
        
        # 如果不是扩展名优先，并且内容检测失败，这里再进行扩展名检测
        if not extension_first:
            log_highlight_error("内容检测失败，尝试通过扩展名判断")
            # 扩展名映射表
            ext_map = {
                'python': ['.py', '.pyw', '.pyc', '.pyo', '.pyd', '.pyi'],
                'markdown': ['.md', '.markdown', '.mdown', '.mkdn', '.mkd', '.mdwn', '.mdtxt', '.mdtext', '.rmd'],
                'javascript': ['.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs'],
                'json': ['.json', '.jsonc', '.json5'],
                'html': ['.html', '.htm', '.xml', '.xhtml', '.svg'],
                'css': ['.css', '.scss', '.less', '.sass', '.styl'],
                'java': ['.java', '.class', '.jar'],
                'cpp': ['.cpp', '.c', '.h', '.hpp', '.cc', '.cxx'],
                'csharp': ['.cs', '.csx'],
                'go': ['.go'],
                'php': ['.php', '.phtml', '.php3', '.php4', '.php5'],
                'ruby': ['.rb', '.rbw'],
                'swift': ['.swift'],
                'rust': ['.rs', '.rlib'],
                'sql': ['.sql'],
                'yaml': ['.yml', '.yaml'],
                'toml': ['.toml'],
                'ini': ['.ini', '.cfg', '.conf']
            }
            
            # 通过扩展名查找文件类型
            for type_name, extensions in ext_map.items():
                if ext in extensions:
                    log_highlight_error(f"通过扩展名判断文件类型: {type_name}")
                    return type_name
    except Exception as e:
        log_highlight_error(f"智能检测失败: {e}")
    
    # 为.txt文件添加二次内容检测
    try:
        if os.path.splitext(file_path)[1].lower() == '.txt' and get_setting('editor', 'editing', 'smart_file_detection', True):
            log_highlight_error("对.txt文件进行最终内容检测")
            # 读取文件内容
            content = ""
            encodings = ['utf-8', 'gbk']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read(4096)  # 读取更多内容进行检测
                    break
                except Exception:
                    continue
                    
            content = content.strip()
            if content:
                # 尝试一些更宽松的模式匹配
                if '{' in content and '}' in content and (':' in content) and ('"' in content):
                    log_highlight_error("内容疑似JSON，返回json类型")
                    return 'json'
                elif '<' in content and '>' in content and ('</' in content):
                    log_highlight_error("内容疑似HTML/XML，返回html类型")
                    return 'html'
                elif '#' in content[:500] and ('```' in content or '*' in content or '-' in content[:500]):
                    log_highlight_error("内容疑似Markdown，返回markdown类型")
                    return 'markdown'
                elif ('function' in content or 'var ' in content or 'let ' in content or 'const ' in content 
                      or 'import ' in content or 'export ' in content or 'class ' in content and '{' in content):
                    log_highlight_error("内容疑似JavaScript，返回javascript类型")
                    return 'javascript'
                elif ('def ' in content or 'class ' in content or 'import ' in content 
                      or 'print(' in content or 'if __name__' in content):
                    log_highlight_error("内容疑似Python，返回python类型")
                    return 'python'
                elif ('#include' in content or 'int main' in content or 'public class' in content 
                      or 'namespace' in content or 'using namespace' in content):
                    log_highlight_error("内容疑似C/C++/Java，返回cpp类型")
                    return 'cpp'
    except Exception as e:
        log_highlight_error(f".txt文件二次检测失败: {e}")
    
    # 如果所有检测都失败，返回默认类型
    return 'text'

def check_is_json(content, file_path):
    """增强的JSON检测函数"""
    try:
        log_highlight_error(f"开始JSON检测: {file_path}")
        
        # 基本特征检查
        has_json_start = content.strip().startswith(('{', '['))
        has_json_structure = '{"' in content[:100] or '[{' in content[:100] or '":{' in content[:100] or '":' in content[:100]
        
        log_highlight_error(f"JSON特征检查: 起始符号匹配={has_json_start}, 结构匹配={has_json_structure}")
        
        # 强烈的JSON指示器 - 如果这些模式出现很多次，很可能是JSON
        if content.count('":"') > 3 or content.count('": "') > 3:
            log_highlight_error("检测到大量JSON键值对模式")
            return True
            
        # 检查是否包含常见JSON配置键
        common_json_keys = ['"version":', '"name":', '"description":', '"dependencies":', '"settings":', '"author":', 
                            '"config":', '"options":', '"properties":', '"type":', '"required":', '"items":']
        key_matches = [key for key in common_json_keys if key in content]
        if key_matches:
            log_highlight_error(f"匹配到JSON常见键: {key_matches}")
            return True
        
        # 尝试严格解析
        try:
            import json
            # 移除可能干扰JSON解析的注释行
            lines = content.split('\n')
            cleaned_lines = []
            for line in lines:
                # 跳过注释行
                if line.strip().startswith('//') or line.strip().startswith('#'):
                    continue
                # 移除行内注释
                comment_pos = line.find('//')
                if comment_pos >= 0:
                    line = line[:comment_pos]
                cleaned_lines.append(line)
            
            cleaned_content = '\n'.join(cleaned_lines)
            
            json.loads(cleaned_content)
            log_highlight_error("JSON解析成功")
            return True
        except Exception as e:
            log_highlight_error(f"JSON严格解析失败: {str(e)}")
            
            # 宽松检查 - 检查JSON的基本结构特征
            if (has_json_start and 
                (('{' in content[:50] and '}' in content[-50:]) or 
                 ('[' in content[:50] and ']' in content[-50:]))):
                log_highlight_error("JSON宽松解析成功")
                return True
                
            # 检查不太可能是其他格式的情况
            if not re.search(r'(import\s+|def\s+|class\s+|function\s+|<html|<body|\bif\s+|while\s+|for\s+)', content, re.IGNORECASE):
                # 如果文件名暗示是JSON
                if 'json' in file_path.lower() or 'config' in file_path.lower() or 'settings' in file_path.lower():
                    log_highlight_error("可能是JSON配置文件")
                    return True
        
        log_highlight_error("不是JSON文件")
        return False
    except Exception as e:
        log_highlight_error(f"JSON检测出错: {e}")
        return False

def check_is_html_xml(content, file_path):
    """增强的HTML/XML检测函数"""
    try:
        log_highlight_error(f"开始HTML/XML检测: {file_path}")
        
        # 基本标签检查
        basic_tags = ['<?xml', '<!DOCTYPE', '<html', '<!--', '<head', '<body', '<div', '<span', '<p>', '<a ', '<img ', '<script', '<style', '<table', '<form']
        for tag in basic_tags:
            if tag in content[:500]:
                log_highlight_error(f"检测到HTML/XML标签: {tag}")
                return True
        
        # 检查XML声明
        if re.search(r'<\?xml\s+version=["\']\d+\.\d+["\']', content):
            log_highlight_error("检测到XML声明")
            return True
            
        # 检查常见HTML模式
        html_patterns = [
            r'<\w+\s+[^>]*>.*?</\w+>',  # 完整标签对
            r'<meta\s+[^>]*>',           # meta标签
            r'<link\s+[^>]*>',           # link标签
            r'<(br|hr|img|input)[^>]*>', # 自闭合标签
            r'class=["\'][^"\']*["\']',  # class属性
            r'id=["\'][^"\']*["\']',     # id属性
            r'style=["\'][^"\']*["\']'   # style属性
        ]
        
        for pattern in html_patterns:
            if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                log_highlight_error(f"匹配到HTML模式: {pattern}")
                return True
                
        # 检查文件名特征
        if any(ext in file_path.lower() for ext in ['.html', '.htm', '.xml', '.xhtml', '.svg', '.jsp', '.asp', '.php']):
            log_highlight_error("文件名暗示是HTML/XML文件")
            
            # 额外的快速检查，只要有一些标签特征即可确认
            if '<' in content and '>' in content and re.search(r'</\w+>', content):
                log_highlight_error("检测到基本HTML结构特征")
                return True
                
        log_highlight_error("不是HTML/XML文件")
        return False
    except Exception as e:
        log_highlight_error(f"HTML/XML检测出错: {e}")
        return False

def check_is_javascript(content, file_path):
    """增强的JavaScript检测函数"""
    try:
        log_highlight_error(f"开始JavaScript检测: {file_path}")
        
        # 检查常见JavaScript关键字
        js_keywords = ['const ', 'let ', 'var ', 'function ', 'class ', 'import ', 'export ', '=>', 'document.', 
                       'window.', 'console.log', 'this.', 'new ', 'return ', 'async ', 'await ', 'try {', 'catch', 
                       'if (', 'else {', 'for (', 'while (', 'switch (', 'Promise', '.then(', '.catch(']
        
        keyword_matches = [kw for kw in js_keywords if kw in content]
        if len(keyword_matches) >= 3:  # 如果匹配3个以上的关键字，很可能是JS
            log_highlight_error(f"检测到多个JavaScript关键字: {keyword_matches}")
            return True
        
        # 检查函数定义和变量声明
        js_patterns = [
            r'function\s+\w+\s*\([^)]*\)\s*{',           # 函数定义
            r'const\s+\w+\s*=',                          # const变量
            r'let\s+\w+\s*=',                            # let变量
            r'var\s+\w+\s*=',                            # var变量
            r'class\s+\w+\s*{',                          # 类定义
            r'export\s+(default\s+)?(function|class|const|let|var)',  # export语句
            r'import\s+.*\s+from\s+[\'"]',               # import语句
            r'document\.getElementById\(',                # DOM操作
            r'window\.(addEventListener|onload)',         # 窗口事件
            r'\$\(.*\)\..*\(',                           # jQuery代码
            r'new\s+(Array|Object|Date|Map|Set|Promise)' # 常见对象实例化
        ]
        
        for pattern in js_patterns:
            if re.search(pattern, content, re.MULTILINE):
                log_highlight_error(f"匹配到JavaScript模式: {pattern}")
                return True
        
        # 检查是否是TypeScript
        ts_patterns = [
            r':\s*(string|number|boolean|any|void|null|undefined)',  # 类型注解
            r'interface\s+\w+\s*{',                                 # 接口定义
            r'<.*>.*\(',                                            # 泛型
            r'@\w+',                                                # 装饰器
        ]
        
        for pattern in ts_patterns:
            if re.search(pattern, content, re.MULTILINE):
                log_highlight_error(f"匹配到TypeScript模式: {pattern}")
                return True
        
        # 检查文件名
        if any(ext in file_path.lower() for ext in ['.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs']):
            # 基本检查 - 不是其他明显的类型就当作JS处理
            if '{' in content and '}' in content and (
                'function' in content or 'var' in content or 'const' in content or 'let' in content):
                log_highlight_error("文件名暗示是JavaScript且包含基本JS特征")
                return True
        
        log_highlight_error("不是JavaScript文件")
        return False
    except Exception as e:
        log_highlight_error(f"JavaScript检测出错: {e}")
        return False

def check_is_css(content, file_path):
    """增强的CSS检测函数"""
    try:
        log_highlight_error(f"开始CSS检测: {file_path}")
        
        # 检查特征性CSS选择器和属性
        css_selectors = ['body {', 'div {', '.class {', '#id {', '* {', ':hover', ':before', ':after', 
                         '@media', '@import', '@keyframes', '@font-face']
        
        selector_matches = [sel for sel in css_selectors if sel in content]
        if selector_matches:
            log_highlight_error(f"检测到CSS选择器: {selector_matches}")
            return True
        
        # 检查CSS属性定义
        css_properties = ['margin:', 'padding:', 'color:', 'background:', 'font-size:', 'width:', 'height:', 
                          'display:', 'position:', 'border:', 'text-align:', 'flex:', 'grid:']
                          
        property_matches = [prop for prop in css_properties if prop in content]
        if len(property_matches) >= 5:  # 如果匹配5个以上的属性，很可能是CSS
            log_highlight_error(f"检测到多个CSS属性: {property_matches}")
            return True
        
        # 正则表达式检测
        css_patterns = [
            r'[.#]?[\w-]+\s*{[^}]*}',                   # 基本CSS规则块
            r'@media\s+[^{]*{',                         # 媒体查询
            r'@keyframes\s+\w+\s*{',                    # 关键帧动画
            r'@import\s+url\([^)]+\);',                 # 导入语句
            r'[\w-]+\s*:\s*[\w-]+\s*;',                 # 属性定义
            r'(px|em|rem|%|vh|vw|deg|rgba?|hsla?)',     # 单位和颜色函数
            r'#[0-9a-fA-F]{3,8}',                       # 十六进制颜色
        ]
        
        for pattern in css_patterns:
            if re.search(pattern, content, re.MULTILINE):
                log_highlight_error(f"匹配到CSS模式: {pattern}")
                return True
        
        # 检查是否是SASS/SCSS/LESS
        preprocessor_patterns = [
            r'\$\w+\s*:',          # SASS变量
            r'@\w+\s*:',           # LESS变量
            r'@mixin\s+\w+',       # SASS混合
            r'@include\s+\w+',     # SASS包含
            r'@extend\s+\w+',      # SASS扩展
            r'&:',                 # 嵌套选择器
            r'\w+\([^)]*\)\s*{',   # 混合调用
        ]
        
        for pattern in preprocessor_patterns:
            if re.search(pattern, content, re.MULTILINE):
                log_highlight_error(f"匹配到CSS预处理器模式: {pattern}")
                return True
        
        # 检查文件名
        if any(ext in file_path.lower() for ext in ['.css', '.scss', '.sass', '.less']):
            # 基本检查
            if '{' in content and '}' in content and (':' in content) and (';' in content):
                log_highlight_error("文件名暗示是CSS且包含基本CSS特征")
                return True
        
        log_highlight_error("不是CSS文件")
        return False
    except Exception as e:
        log_highlight_error(f"CSS检测出错: {e}")
        return False

def check_is_markdown(content, file_path):
    """增强的Markdown检测函数"""
    try:
        log_highlight_error(f"开始Markdown检测: {file_path}")
        
        # 检查常见Markdown语法
        md_features = [
            '# ',              # 一级标题
            '## ',             # 二级标题
            '### ',            # 三级标题
            '* ',              # 无序列表
            '- ',              # 无序列表
            '1. ',             # 有序列表
            '> ',              # 引用
            '```',             # 代码块
            '**',              # 粗体
            '*',               # 斜体
            '[',               # 链接开始
            '![',              # 图片开始
            '|---',            # 表格
            '---',             # 分隔线
        ]
        
        # 计算特征数量
        feature_matches = [feat for feat in md_features if feat in content]
        if len(feature_matches) >= 2:  # 如果匹配2个以上的特征，很可能是Markdown
            log_highlight_error(f"检测到多个Markdown特征: {feature_matches}")
            return True
        
        # 正则表达式检测
        md_patterns = [
            r'^#{1,6}\s+.+$',                   # 标题
            r'^\s*[-*+]\s+.+$',                 # 无序列表项
            r'^\s*\d+\.\s+.+$',                 # 有序列表项
            r'^\s*>\s+.+$',                     # 引用
            r'^\s*```[^`]*```',                 # 代码块
            r'\[.+\]\(.+\)',                    # 链接
            r'!\[.+\]\(.+\)',                   # 图片
            r'\*\*.+\*\*',                      # 粗体
            r'__.+__',                          # 粗体
            r'\*.+\*',                          # 斜体
            r'_.+_',                            # 斜体
            r'^\s*[-*_]{3,}\s*$',               # 分隔线
            r'^\s*\|.+\|.+\|',                  # 表格行
            r'^\s*\|[-:]+\|[-:]+\|',            # 表格分隔行
        ]
        
        md_pattern_count = 0
        for pattern in md_patterns:
            if re.search(pattern, content, re.MULTILINE):
                md_pattern_count += 1
                if md_pattern_count >= 2:  # 如果匹配2个以上的模式，很可能是Markdown
                    log_highlight_error("检测到多个Markdown模式")
                    return True
        
        # 检查是否存在前置YAML元数据（常见于静态站点生成器中的Markdown）
        if re.search(r'^---\s*$.*?^---\s*$', content, re.MULTILINE | re.DOTALL):
            log_highlight_error("检测到Markdown前置元数据")
            return True
        
        # 检查文件名
        if any(ext in file_path.lower() for ext in ['.md', '.markdown', '.mdown', '.mkdn', '.mdwn']):
            log_highlight_error("文件名暗示是Markdown文件")
            # 基本特征检查 - 不是特别像其他类型的文本通常就是Markdown
            if '#' in content and not ('{' in content[:100] and '}' in content[:500]):
                if not re.search(r'<(html|body|div|script)\s*>', content, re.IGNORECASE):
                    log_highlight_error("文件名是Markdown且内容不像HTML/JS/JSON")
                    return True
        
        log_highlight_error("不是Markdown文件")
        return False
    except Exception as e:
        log_highlight_error(f"Markdown检测出错: {e}")
        return False
