"""
文件格式转换插件
支持将 Markdown 转换为 HTML，以及其他格式转换
"""

import os
import re
import logging
from Aya_Hanabi.Hanabi_Core.PluginManager import (
    HanabiPlugin, PluginMetadata, PluginHooks, FileHandler
)

# 导入可能缺失的库
try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    logging.warning("markdown 库未安装，部分功能将不可用")


class MarkdownToHtmlHandler(FileHandler):
    """Markdown 转 HTML 处理器"""
    
    def __init__(self):
        super().__init__(extensions=['.md', '.markdown'])
        self.css = """
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            padding: 20px;
            max-width: 900px;
            margin: 0 auto;
            color: #333;
        }
        a {
            color: #0366d6;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        h1, h2, h3, h4, h5, h6 {
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
            line-height: 1.25;
        }
        h1 {
            font-size: 2em;
            border-bottom: 1px solid #eaecef;
            padding-bottom: .3em;
        }
        h2 {
            font-size: 1.5em;
            border-bottom: 1px solid #eaecef;
            padding-bottom: .3em;
        }
        code {
            font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
            background-color: rgba(27, 31, 35, .05);
            padding: .2em .4em;
            border-radius: 3px;
            font-size: 85%;
        }
        pre {
            background-color: #f6f8fa;
            border-radius: 3px;
            padding: 16px;
            overflow: auto;
        }
        pre code {
            background-color: transparent;
            padding: 0;
        }
        blockquote {
            padding: 0 1em;
            color: #6a737d;
            border-left: .25em solid #dfe2e5;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin-bottom: 16px;
        }
        table th, table td {
            border: 1px solid #dfe2e5;
            padding: 6px 13px;
        }
        table tr {
            background-color: #fff;
        }
        table tr:nth-child(2n) {
            background-color: #f6f8fa;
        }
        img {
            max-width: 100%;
        }
        """
    
    def md_to_html(self, content, css=True, standalone=True):
        """将Markdown转换为HTML
        
        Args:
            content: Markdown内容
            css: 是否包含CSS
            standalone: 是否生成完整HTML
            
        Returns:
            str: HTML内容
        """
        if not MARKDOWN_AVAILABLE:
            return "<p>无法转换 Markdown: 未安装 markdown 库</p>"
        
        # 转换Markdown为HTML
        html_content = markdown.markdown(
            content,
            extensions=['tables', 'fenced_code', 'codehilite']
        )
        
        if standalone:
            # 添加HTML头和尾
            html = "<!DOCTYPE html>\n<html>\n<head>\n"
            html += '<meta charset="utf-8">\n'
            html += '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            
            # 提取标题
            title = "Markdown转换"
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if title_match:
                title = title_match.group(1)
            
            html += f'<title>{title}</title>\n'
            
            # 添加样式
            if css:
                html += f'<style>\n{self.css}\n</style>\n'
            
            html += '</head>\n<body>\n'
            html += html_content
            html += '\n</body>\n</html>'
            
            return html
        else:
            return html_content
    
    def save_file(self, file_path, content):
        """保存HTML文件
        
        Args:
            file_path: Markdown文件路径
            content: Markdown内容
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 转换为HTML
            html_content = self.md_to_html(content)
            
            # 生成HTML文件路径
            html_path = os.path.splitext(file_path)[0] + '.html'
            
            # 保存HTML文件
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return True
        except Exception as e:
            logging.error(f"转换Markdown为HTML失败: {e}")
            return False


class FormatConverterPlugin(HanabiPlugin):
    """文件格式转换插件"""
    
    def __init__(self, app_instance=None):
        super().__init__(app_instance)
        
        # 设置插件元数据
        self.metadata = PluginMetadata(
            name="格式转换工具",
            version="1.0.0",
            description="支持各种文件格式的转换，包括Markdown到HTML等",
            author="Hanabi Team",
            min_app_version="1.0.0"
        )
        
        # 文件处理器
        self.md_handler = MarkdownToHtmlHandler()
    
    def initialize(self) -> bool:
        """初始化插件"""
        print("格式转换插件初始化中...")
        
        # 检查依赖
        if not MARKDOWN_AVAILABLE:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self.app,
                "插件警告",
                "未安装markdown库，部分功能将不可用。\n请使用pip install markdown安装。"
            )
        
        # 注册钩子
        self.register_hook(PluginHooks.FILE_SAVED, self.on_file_saved)
        
        # 添加菜单动作
        self.add_menu_action({
            'text': 'Markdown转HTML',
            'callback': self.convert_current_to_html,
            'menu': 'plugins'
        })
        
        self.add_menu_action({
            'text': 'HTML预览',
            'callback': self.preview_as_html,
            'menu': 'plugins'
        })
        
        print("格式转换插件初始化完成")
        return super().initialize()
    
    def on_file_saved(self, file_path):
        """文件保存时的处理"""
        # 根据设置决定是否自动转换
        auto_convert = self.get_setting('auto_convert', False)
        
        if auto_convert and self.md_handler.can_handle(file_path):
            try:
                # 读取文件内容
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 转换并保存
                self.md_handler.save_file(file_path, content)
                
                print(f"已自动将 {file_path} 转换为HTML")
            except Exception as e:
                logging.error(f"自动转换失败: {e}")
    
    def convert_current_to_html(self):
        """将当前编辑的文件转换为HTML"""
        try:
            # 获取当前文件
            if not self.app or not hasattr(self.app, 'currentFilePath') or not self.app.currentFilePath:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self.app,
                    "转换失败",
                    "没有打开的文件，请先保存文件。"
                )
                return
            
            # 检查文件类型
            if not self.md_handler.can_handle(self.app.currentFilePath):
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self.app,
                    "转换失败",
                    "当前文件不是Markdown格式，无法转换。"
                )
                return
            
            # 获取当前内容
            if hasattr(self.app, 'currentEditor') and self.app.currentEditor:
                content = self.app.currentEditor.toPlainText()
                
                # 保存为HTML
                html_path = os.path.splitext(self.app.currentFilePath)[0] + '.html'
                html_content = self.md_handler.md_to_html(content)
                
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(
                    self.app,
                    "转换成功",
                    f"文件已转换并保存为:\n{html_path}"
                )
            else:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self.app,
                    "转换失败",
                    "无法获取当前编辑器内容。"
                )
        except Exception as e:
            logging.error(f"转换失败: {e}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self.app,
                "转换失败",
                f"转换过程中出错: {str(e)}"
            )
    
    def preview_as_html(self):
        """预览当前内容为HTML"""
        try:
            # 获取当前内容
            if hasattr(self.app, 'currentEditor') and self.app.currentEditor:
                content = self.app.currentEditor.toPlainText()
                
                # 转换为HTML
                html_content = self.md_handler.md_to_html(content)
                
                # 创建临时文件
                import tempfile
                with tempfile.NamedTemporaryFile(
                    suffix='.html', delete=False, mode='w', encoding='utf-8'
                ) as f:
                    f.write(html_content)
                    temp_path = f.name
                
                # 打开浏览器预览
                import webbrowser
                webbrowser.open(f'file://{temp_path}')
            else:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self.app,
                    "预览失败",
                    "无法获取当前编辑器内容。"
                )
        except Exception as e:
            logging.error(f"预览失败: {e}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self.app,
                "预览失败",
                f"预览过程中出错: {str(e)}"
            )
    
    def create_settings_widget(self):
        """创建插件设置界面"""
        try:
            from PySide6.QtWidgets import QWidget, QVBoxLayout, QCheckBox, QLabel
            
            widget = QWidget()
            layout = QVBoxLayout(widget)
            
            # 标题
            title = QLabel("<h3>格式转换设置</h3>")
            layout.addWidget(title)
            
            # 自动转换设置
            auto_convert = QCheckBox("保存Markdown文件时自动转换为HTML")
            auto_convert.setChecked(self.get_setting('auto_convert', False))
            auto_convert.toggled.connect(lambda state: self.set_setting('auto_convert', state))
            
            layout.addWidget(auto_convert)
            layout.addStretch()
            
            return widget
        except Exception as e:
            logging.error(f"创建设置界面失败: {e}")
            return None


# 导出插件类，使插件管理器能够识别
__plugin_class__ = FormatConverterPlugin 