from .themeManager import ThemeManager, Theme
from .themeDialog import ThemeSettingsDialog

__all__ = ['ThemeManager', 'Theme', 'ThemeSettingsDialog']

class ThemeManager:
    def __init__(self):
        self.current_theme = None
        self.current_theme_name = "dark"  # 默认主题名称
        self.themes = {}
        
    def set_theme(self, theme_name):
        """设置当前主题"""
        if theme_name in self.themes:
            theme = self.themes[theme_name]
            self.current_theme = theme
            self.current_theme_name = theme_name
            
            # 确保Theme对象有name属性
            if hasattr(theme, 'name'):
                if theme.name != theme_name:
                    theme.name = theme_name
            else:
                # 给主题对象添加name属性
                try:
                    setattr(theme, 'name', theme_name)
                except AttributeError:
                    # 如果是字典，直接赋值
                    if isinstance(theme, dict):
                        theme['name'] = theme_name
            
            return True
        return False
    
    def add_theme(self, theme):
        """添加新主题到主题列表中"""
        if hasattr(theme, 'name'):
            self.themes[theme.name] = theme
        elif isinstance(theme, dict) and 'name' in theme:
            self.themes[theme['name']] = theme
        
    def get_window_style(self):
        """获取窗口样式"""
        if not self.current_theme:
            return ""
        
        # 处理Theme对象或字典
        bg_color = "#1e2128"  # 默认背景色
        border_color = "#2a2e36"  # 默认边框色
        border_radius = "10px"  # 默认圆角
        
        if hasattr(self.current_theme, 'get'):
            # 如果是Theme对象并有get方法
            bg_color = self.current_theme.get("window.background", bg_color)
            border_color = self.current_theme.get("window.border", border_color)
            border_radius = self.current_theme.get("window.radius", border_radius)
        elif hasattr(self.current_theme, 'data') and isinstance(self.current_theme.data, dict):
            # 如果是Theme对象有data属性
            if 'window' in self.current_theme.data:
                window = self.current_theme.data['window']
                bg_color = window.get('background', bg_color)
                border_color = window.get('border', border_color)
                border_radius = window.get('radius', border_radius)
        elif isinstance(self.current_theme, dict):
            # 如果是字典
            if 'window' in self.current_theme:
                window = self.current_theme['window']
                bg_color = window.get('background', bg_color)
                border_color = window.get('border', border_color)
                border_radius = window.get('radius', border_radius)
                
        return f"""
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: {border_radius};
        """
        
    def get_editor_style(self, font_size=15):
        """获取编辑器样式"""
        if not self.current_theme:
            return ""
        style = self.current_theme.get("editor.style", "")
        return style.replace("{font_size}", str(font_size))
        
    def get_scrollbar_style(self):
        """获取滚动条样式"""
        if not self.current_theme:
            return ""
        return self.current_theme.get("scrollbar.style", "")
        
    def get_highlight_colors(self):
        """获取高亮颜色"""
        if not self.current_theme:
            from PySide6.QtGui import QColor
            return QColor(107, 159, 255, 60), QColor(107, 159, 255, 120)
        
        from PySide6.QtGui import QColor
        line_color_str = self.current_theme.get("highlight.line_color", "rgba(107, 159, 255, 60)")
        flash_color_str = self.current_theme.get("highlight.flash_color", "rgba(107, 159, 255, 120)")
        
        # 解析颜色字符串
        def parse_color(color_str):
            if color_str.startswith("rgba("):
                parts = color_str.strip("rgba()").split(",")
                return QColor(int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3]))
            elif color_str.startswith("rgb("):
                parts = color_str.strip("rgb()").split(",")
                return QColor(int(parts[0]), int(parts[1]), int(parts[2]))
            else:
                return QColor(color_str)
        
        return parse_color(line_color_str), parse_color(flash_color_str)
        
    def get_preview_styles(self):
        """获取预览样式"""
        if not self.current_theme:
            return "", ""
        
        preview_style = self.current_theme.get("preview.style", """
            background-color: #1e2128; 
            border: none;
            color: #e0e0e0;
        """)
        
        html_style = self.current_theme.get("preview.html_style", """
            <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                line-height: 1.6;
                color: #e0e0e0;
                background-color: #1e2128;
                margin: 0;
                padding: 0 10px;
            }
            h1, h2, h3, h4, h5, h6 {
                color: #e0e5ec;
                margin-top: 24px;
                margin-bottom: 16px;
                font-weight: 600;
            }
            h1 { font-size: 2em; border-bottom: 1px solid #30363d; padding-bottom: 0.3em; }
            h2 { font-size: 1.5em; border-bottom: 1px solid #30363d; padding-bottom: 0.3em; }
            a { color: #58a6ff; text-decoration: none; }
            a:hover { text-decoration: underline; }
            code {
                font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
                padding: 0.2em 0.4em;
                background-color: rgba(110, 118, 129, 0.4);
                border-radius: 3px;
            }
            pre {
                background-color: #161b22;
                border-radius: 6px;
                padding: 16px;
                overflow: auto;
            }
            pre code {
                background-color: transparent;
                padding: 0;
            }
            blockquote {
                color: #8b949e;
                border-left: 3px solid #3b434b;
                padding-left: 16px;
                margin-left: 0;
            }
            table {
                border-collapse: collapse;
                width: 100%;
                margin: 16px 0;
            }
            table th, table td {
                border: 1px solid #30363d;
                padding: 6px 13px;
            }
            table th {
                background-color: #161b22;
            }
            hr {
                border: 1px solid #30363d;
            }
            </style>
        """)
        
        return preview_style, html_style
        
    def get_title_bar_style(self):
        """获取标题栏样式"""
        if not self.current_theme:
            return ("background-color: #1e2128; border-top-left-radius: 10px; border-top-right-radius: 10px;",
                    "background-color: #303540; border-radius: 14px;",
                    "color: #6b9fff; font-weight: bold; font-size: 18px;")
        
        # 获取主题中定义的颜色
        bg_color = self.current_theme.get("title_bar.background", "#1e2128")
        icon_bg_color = self.current_theme.get("title_bar.icon_bg", "#303540")
        icon_color = self.current_theme.get("title_bar.icon_color", "#6b9fff")
        text_color = self.current_theme.get("title_bar.text_color", "#e0e5ec")
        
        # 构建完整的样式字符串
        title_style = f"""
            background-color: {bg_color}; 
            border-top-left-radius: 10px; 
            border-top-right-radius: 10px;
            border: none;
            color: {text_color};
        """
        
        icon_bg_style = f"""
            background-color: {icon_bg_color}; 
            border-radius: 14px;
        """
        
        icon_label_style = f"""
            color: {icon_color}; 
            font-weight: bold; 
            font-size: 18px;
        """
        
        return title_style, icon_bg_style, icon_label_style
        
    def get_status_bar_style(self):
        """获取状态栏样式"""
        if not self.current_theme:
            return ("background-color: #1a1d23; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px;",
                    "color: rgba(255, 255, 255, 0.7); hover { background-color: rgba(255, 255, 255, 0.1); border-radius: 8px; }",
                    "color: #6b9fff; hover { background-color: rgba(255, 255, 255, 0.1); border-radius: 8px; }")
        
        status_style = self.current_theme.get("status_bar.style", "background-color: #1a1d23; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px;")
        icon_style = self.current_theme.get("status_bar.icon", "color: rgba(255, 255, 255, 0.7); hover { background-color: rgba(255, 255, 255, 0.1); border-radius: 8px; }")
        active_icon_style = self.current_theme.get("status_bar.active_icon", "color: #6b9fff; hover { background-color: rgba(255, 255, 255, 0.1); border-radius: 8px; }")
        
        return status_style, icon_style, active_icon_style
        
    def load_themes_from_directory(self, directory=None):
        """从目录加载主题"""
        import os
        import json
        
        if directory is None:
            # 使用默认目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            directory = os.path.join(current_dir, "themes")
        
        # 确保目录存在
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        # 加载内置主题 - 只加载dark主题
        self.themes = {
            "dark": self._get_dark_theme()
        }
        
        # 加载自定义主题
        custom_themes_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "custom_themes")
        if os.path.exists(custom_themes_dir):
            for filename in os.listdir(custom_themes_dir):
                if filename.endswith(".json"):
                    try:
                        with open(os.path.join(custom_themes_dir, filename), 'r', encoding='utf-8') as f:
                            theme_data = json.load(f)
                            theme_name = os.path.splitext(filename)[0]
                            # 确保主题数据有名称属性
                            if 'name' not in theme_data:
                                theme_data['name'] = theme_name
                            # 创建主题对象
                            from .themeManager import Theme
                            theme = Theme(theme_name, theme_data)
                            self.add_theme(theme)
                            print(f"成功加载自定义主题: {theme_name}")
                    except Exception as e:
                        print(f"加载主题 {filename} 时出错: {e}")
        
        # 设置默认主题
        self.set_theme("dark")
    
    def get_all_themes(self):
        """获取所有主题的列表，返回(theme_name, display_name)的元组列表"""
        result = []
        for name, theme in self.themes.items():
            display_name = name
            if isinstance(theme, dict):
                display_name = theme.get("display_name", name)
            elif hasattr(theme, 'get'):
                display_name = theme.get("display_name", name)
            elif hasattr(theme, 'data') and isinstance(theme.data, dict):
                display_name = theme.data.get("display_name", name)
            result.append((name, display_name))
        return result
    
    def create_custom_theme(self, base_theme_name, custom_data, new_theme_name):
        """基于现有主题创建自定义主题"""
        try:
            if base_theme_name not in self.themes:
                return None
            
            # 获取基础主题
            base_theme = self.themes[base_theme_name]
            
            # 创建新主题数据
            new_theme_data = {}
            
            # 如果基础主题是字典，直接复制
            if isinstance(base_theme, dict):
                import copy
                new_theme_data = copy.deepcopy(base_theme)
            else:
                # 如果是Theme对象，获取其数据
                new_theme_data = base_theme.data.copy() if hasattr(base_theme, 'data') else {}
            
            # 更新自定义属性
            new_theme_data.update(custom_data)
            
            # 添加主题名称
            new_theme_data["name"] = new_theme_name
            
            # 创建新主题对象
            from .themeManager import Theme
            new_theme = Theme(new_theme_name, new_theme_data)
            
            # 添加到主题列表
            self.themes[new_theme_name] = new_theme
            
            return new_theme
        except Exception as e:
            print(f"创建自定义主题时出错: {e}")
            return None
    
    def save_theme(self, theme):
        """保存主题到文件"""
        try:
            import os
            import json
            
            # 确保主题目录存在
            current_dir = os.path.dirname(os.path.abspath(__file__))
            custom_themes_dir = os.path.join(current_dir, "themes", "custom_themes")
            os.makedirs(custom_themes_dir, exist_ok=True)
            
            # 获取主题数据
            theme_name = theme.name if hasattr(theme, 'name') else theme.get('name', 'custom')
            
            # 获取主题数据
            if hasattr(theme, 'data'):
                theme_data = theme.data
            else:
                theme_data = theme
            
            # 保存到文件
            file_path = os.path.join(custom_themes_dir, f"{theme_name}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(theme_data, f, ensure_ascii=False, indent=2)
                
            return True
        except Exception as e:
            print(f"保存主题时出错: {e}")
            return False
    
    def _get_dark_theme(self):
        """获取暗色主题"""
        return {
            "window.style": """
                QWidget#mainWindow {
                    background-color: #1e2128;
                    color: #e0e0e0;
                    border: none;
                    border-radius: 10px;
                }
            """,
            "editor.style": """
                QPlainTextEdit {
                    border: none;
                    color: #e0e0e0;
                    background-color: #1e2128;
                    selection-background-color: #404eff;
                    font-size: {font_size}px;
                    line-height: 1.5;
                }
            """,
            "scrollbar.style": """
                QScrollBar:vertical {
                    background: transparent;
                    width: 6px;
                    margin: 0px;
                    border-radius: 3px;
                }
                QScrollBar::handle:vertical {
                    background-color: rgba(255, 255, 255, 0.3);
                    min-height: 30px;
                    border-radius: 3px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: rgba(255, 255, 255, 0.5);
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0px;
                }
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                    background: none;
                }
            """,
            "highlight.line_color": "rgba(107, 159, 255, 0.6)",
            "highlight.flash_color": "rgba(107, 159, 255, 0.12)",
            
            # 标题栏样式
            "title_bar.background": "#1e2128",
            "title_bar.text_color": "#e0e5ec",
            "title_bar.icon_bg": "#303540",
            "title_bar.icon_color": "#6b9fff",
            "title_bar.controls_color": "rgba(224, 229, 236, 0.8)",
            "title_bar.controls_hover": "rgba(224, 229, 236, 1.0)",
            "title_bar.button_hover_bg": "rgba(255, 255, 255, 0.1)",
            "title_bar.close_color": "rgba(224, 229, 236, 0.8)",
            "title_bar.close_hover": "#e81123",
            
            # 状态栏样式
            "status_bar.style": "background-color: #1a1d23; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px;",
            "status_bar.icon": "color: rgba(224, 229, 236, 0.7); hover { background-color: rgba(255, 255, 255, 0.1); border-radius: 8px; }",
            "status_bar.active_icon": "color: #6b9fff; hover { background-color: rgba(255, 255, 255, 0.1); border-radius: 8px; }",
            "status_bar.text_color": "#e0e5ec",
            
            # 侧边栏样式
            "sidebar.background": "#1a1d23",
            "sidebar.text_color": "#e0e5ec",
            "sidebar.active_tab_bg": "#2f3440",
            "sidebar.hover_tab_bg": "rgba(255, 255, 255, 0.1)",
            "sidebar.icon_color": "rgba(224, 229, 236, 0.7)",
            "sidebar.border_color": "#2d2d2d",
        }

# 从旧版保持兼容
from .themeDialog import ThemeSettingsDialog 