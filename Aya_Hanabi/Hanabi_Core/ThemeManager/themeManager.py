import os
import json
from PySide6.QtGui import QColor

# 不要再问我为什么不写注释了，不想写
class Theme:
    def __init__(self, name, data=None):
        self.name = name
        self.data = data or {}
        
    def get(self, key, default=None):
        parts = key.split('.')
        value = self.data
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
        return value
    
    def should_preserve_font_size(self):
        return self.get('editor.preserve_font_size', False)

class ThemeManager:
    def __init__(self):
        self.themes = {}
        self.current_theme = None
        self.current_theme_name = "dark"  # 默认主题
        self.default_theme_name = "dark"
        self._initialize_default_themes()
        
    def _initialize_default_themes(self):
        # 暗色主题
        dark_theme = {
            "name": "dark",
            "display_name": "暗色主题",
            "window": {
                "background": "#1e2128",
                "border": "#2a2e36",
                "radius": "10px"
            },
            "title_bar": {
                "background": "#1e2128",
                "text_color": "white",
                "icon_bg": "#303540",
                "icon_color": "#6b9fff"
            },
            "editor": {
                "background": "#1e2128",
                "text_color": "#e0e0e0",
                "selection_color": "#404eff",
                "cursor_color": "white",
                "line_height": "1.5",
                "border_color": "#1e2128",
                "preserve_font_size": True
            },
            "scrollbar": {
                "background": "transparent",
                "handle_color": "rgba(255, 255, 255, 0.3)",
                "handle_hover_color": "rgba(255, 255, 255, 0.5)",
                "width": "6px",
                "radius": "3px"
            },
            "status_bar": {
                "background": "#1a1d23",
                "text_color": "white",
                "icon_color": "rgba(255, 255, 255, 0.7)",
                "active_icon_color": "#6b9fff",
                "hover_bg": "rgba(255, 255, 255, 0.1)",
                "line_count_bg": "rgba(0, 0, 0, 0.2)"
            },
            "sidebar": {
                "background": "#252932",
                "text_color": "white",
                "active_tab_bg": "#2f3440",
                "hover_tab_bg": "rgba(255, 255, 255, 0.08)",
                "icon_color": "rgba(255, 255, 255, 0.7)"
            },
            "preview": {
                "background": "#1e2128",
                "text_color": "#e0e0e0",
                "heading_color": "#ffffff",
                "link_color": "#58a6ff",
                "code_bg": "rgba(110, 118, 129, 0.4)",
                "blockquote_color": "#8b949e",
                "blockquote_border": "#3b434b",
                "table_border": "#30363d"
            },
            "highlight": {
                "line_color": "rgba(107, 159, 255, 60)",
                "flash_color": "rgba(107, 159, 255, 120)"
            }
        }
        
        # 只添加暗色主题
        self.add_theme(Theme("dark", dark_theme))
        
        # 设置默认主题
        self.set_theme(self.default_theme_name)
    
    def add_theme(self, theme):
        self.themes[theme.name] = theme
    
    def get_theme(self, name):
        return self.themes.get(name)
    
    def set_theme(self, name):
        print(f"设置主题: {name}")
        if name in self.themes:
            self.current_theme = self.themes[name]
            self.current_theme_name = name  # 添加一个属性存储当前主题名称
            
            # 确保主题对象有name属性
            if not hasattr(self.current_theme, 'name'):
                setattr(self.current_theme, 'name', name)
            else:
                self.current_theme.name = name
                
            print(f"当前主题设置为: {name}, 主题对象名称为: {self.current_theme.name}")
            return True
            
        # 如果找不到指定主题，使用默认主题
        print(f"主题 {name} 不存在，尝试使用默认主题")
        if name != self.default_theme_name and self.default_theme_name in self.themes:
            return self.set_theme(self.default_theme_name)
            
        print(f"主题 {name} 不存在且默认主题也不可用")
        return False
    
    def get_all_themes(self):
        return [(theme.name, theme.data.get("display_name", theme.name)) for theme in self.themes.values()]
    
    def save_theme(self, theme):
        themes_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'custom_themes')
        os.makedirs(themes_dir, exist_ok=True)
        
        file_path = os.path.join(themes_dir, f"{theme.name}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(theme.data, f, ensure_ascii=False, indent=2)
    
    def load_themes_from_directory(self, directory=None):
        if directory is None:
            directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'custom_themes')
        
        if not os.path.exists(directory):
            return
        
        for filename in os.listdir(directory):
            if filename.endswith('.json'):
                file_path = os.path.join(directory, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        theme_data = json.load(f)
                        theme_name = os.path.splitext(filename)[0]
                        theme = Theme(theme_name, theme_data)
                        self.add_theme(theme)
                except Exception as e:
                    print(f"加载主题文件 {filename} 时出错: {str(e)}")
    
    def create_custom_theme(self, base_theme_name, custom_data, new_name):
        base_theme = self.get_theme(base_theme_name)
        if not base_theme:
            return None
        
        # 复制基础主题数据
        new_data = dict(base_theme.data)
        
        # 更新自定义数据
        def update_dict(target, source):
            for key, value in source.items():
                if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                    update_dict(target[key], value)
                else:
                    target[key] = value
        
        update_dict(new_data, custom_data)
        new_data["name"] = new_name
        
        # 创建并添加新主题
        new_theme = Theme(new_name, new_data)
        self.add_theme(new_theme)
        return new_theme
    
    def get_window_style(self):
        """获取主窗口样式"""
        if not self.current_theme:
            return ""
        
        # 特殊处理亮色主题
        if hasattr(self.current_theme, 'name') and self.current_theme.name == "light":
            bg = "#f5f5f5"  # 确保亮色主题窗口使用浅色背景
            print(f"窗口样式使用亮色背景: {bg}")
        else:
            bg = self.current_theme.get("window.background", "#1e2128")
            
        radius = self.current_theme.get("window.radius", "10px")
        
        return f"""
            #mainWindow {{
                background-color: {bg};
                border-radius: {radius};
                border: none;
            }}
        """
    
    def get_title_bar_style(self):
        if not self.current_theme:
            return ""
        
        bg = self.current_theme.get("title_bar.background", "#1e2128")
        text_color = self.current_theme.get("title_bar.text_color", "white")
        icon_bg = self.current_theme.get("title_bar.icon_bg", "#303540")
        icon_color = self.current_theme.get("title_bar.icon_color", "#6b9fff")
        
        return f"""
            background-color: {bg}; 
            border-top-left-radius: 10px; 
            border-top-right-radius: 10px;
            color: {text_color};
        """, f"""
            background-color: {icon_bg}; 
            border-radius: 14px;
        """, f"""
            color: {icon_color}; 
            font-weight: bold; 
            font-size: 18px;
        """
    
    def get_editor_style(self, font_size=15):
        if not self.current_theme:
            return ""
        
        bg = self.current_theme.get("editor.background", "#1e2128")
        text_color = self.current_theme.get("editor.text_color", "#e0e0e0")
        selection_color = self.current_theme.get("editor.selection_color", "#404eff")
        line_height = self.current_theme.get("editor.line_height", "1.5")
        
        return f"""
            QPlainTextEdit {{
                border: none;
                color: {text_color};
                background-color: {bg};
                selection-background-color: {selection_color};
                font-size: {font_size}px;
                line-height: {line_height};
            }}
        """
    
    def get_scrollbar_style(self):
        if not self.current_theme:
            return ""
        
        # 获取当前主题名
        theme_name = self.current_theme.name if hasattr(self.current_theme, 'name') else ""
        
        # 亮色主题特殊处理
        if theme_name == "light":
            bg = "transparent"
            handle_color = "rgba(0, 0, 0, 0.15)"
            handle_hover = "rgba(0, 0, 0, 0.25)"
        else:
            bg = self.current_theme.get("scrollbar.background", "transparent")
            handle_color = self.current_theme.get("scrollbar.handle_color", "rgba(255, 255, 255, 0.3)")
            handle_hover = self.current_theme.get("scrollbar.handle_hover_color", "rgba(255, 255, 255, 0.5)")
        
        width = self.current_theme.get("scrollbar.width", "6px")
        radius = self.current_theme.get("scrollbar.radius", "3px")
        
        return f"""
            QScrollBar:vertical {{
                background: {bg};
                width: {width};
                margin: 0px;
                border-radius: {radius};
            }}
            QScrollBar::handle:vertical {{
                background-color: {handle_color};
                min-height: 30px;
                border-radius: {radius};
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {handle_hover};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """
    
    def get_status_bar_style(self):
        if not self.current_theme:
            return ("background-color: #1a1d23; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px;",
                   "color: rgba(255, 255, 255, 0.7); hover { background-color: rgba(255, 255, 255, 0.1); border-radius: 8px; }",
                   "color: #6b9fff; hover { background-color: rgba(255, 255, 255, 0.1); border-radius: 8px; }")
        
        # 获取样式属性
        bg = self.current_theme.get("status_bar.background", "#1a1d23")
        text_color = self.current_theme.get("status_bar.text_color", "white")
        icon_color = self.current_theme.get("status_bar.icon_color", "rgba(255, 255, 255, 0.7)")
        active_icon = self.current_theme.get("status_bar.active_icon_color", "#6b9fff")
        hover_bg = self.current_theme.get("status_bar.hover_bg", "rgba(255, 255, 255, 0.1)")
        line_count_bg = self.current_theme.get("status_bar.line_count_bg", "rgba(0, 0, 0, 0.2)")
        
        # 优先使用主题中定义的完整样式
        status_style = self.current_theme.get("status_bar.style")
        if not status_style:
            # 如果没有定义完整样式，则使用单独的属性生成样式
            status_style = f"""
                background-color: {bg}; 
                border-bottom-left-radius: 10px; 
                border-bottom-right-radius: 10px;
                color: {text_color};
            """
        
        # 优先使用主题中定义的图标样式
        icon_style = self.current_theme.get("status_bar.icon")
        if not icon_style:
            # 如果没有定义图标样式，则使用单独的属性生成样式
            icon_style = f"""
                color: {icon_color}; 
                background-color: transparent;
                border: none;
                border-radius: 8px;
                padding: 4px;
            """
            icon_style += f"""
                :hover {{
                    background-color: {hover_bg};
                }}
            """
        
        # 优先使用主题中定义的活动图标样式
        active_icon_style = self.current_theme.get("status_bar.active_icon")
        if not active_icon_style:
            # 如果没有定义活动图标样式，则使用单独的属性生成样式
            active_icon_style = f"""
                color: {active_icon}; 
                background-color: transparent;
                border: none;
                border-radius: 8px;
                padding: 4px;
            """
            active_icon_style += f"""
                :hover {{
                    background-color: {hover_bg};
                }}
            """
        
        return (status_style, icon_style, active_icon_style)
    
    def get_sidebar_style(self):
        if not self.current_theme:
            return (
                "background-color: #1a1d23; color: #e0e5ec;",
                "background-color: #2f3440;",
                "background-color: rgba(255, 255, 255, 0.02);",  # 降低默认透明度
                "color: rgba(224, 229, 236, 0.7);"
            )
        
        # 优先使用主题中定义的侧边栏样式
        sidebar_style = self.current_theme.get("sidebar.style")
        if not sidebar_style:
            # 如果没有定义侧边栏样式，则使用单独的属性生成样式
            bg = self.current_theme.get("sidebar.background", "#1a1d23")
            text_color = self.current_theme.get("sidebar.text_color", "#e0e5ec")
            border_color = self.current_theme.get("sidebar.border_color", "#2d2d2d")
            sidebar_style = f"""
                background-color: {bg};
                color: {text_color};
                border-right: 1px solid {border_color};
            """
        
        # 活动标签页样式
        active_tab_bg = self.current_theme.get("sidebar.active_tab_bg", "#2f3440")
        active_tab_style = f"background-color: {active_tab_bg};"
        
        # 悬停标签页样式 - 非常低的透明度
        hover_tab_bg = self.current_theme.get("sidebar.hover_tab_bg", "rgba(255, 255, 255, 0.02)")
        
        # 确保hover_tab_bg的透明度很低
        if "rgba(" in hover_tab_bg:
            parts = hover_tab_bg.replace("rgba(", "").replace(")", "").split(",")
            if len(parts) == 4:
                r, g, b = parts[0].strip(), parts[1].strip(), parts[2].strip()
                alpha = float(parts[3].strip())
                if alpha > 0.05:  # 如果透明度大于0.05，降低到0.02
                    hover_tab_bg = f"rgba({r}, {g}, {b}, 0.02)"
        
        hover_tab_style = f"background-color: {hover_tab_bg};"
        
        # 图标颜色样式
        icon_color = self.current_theme.get("sidebar.icon_color", "rgba(224, 229, 236, 0.7)")
        icon_style = f"color: {icon_color};"
        
        return (sidebar_style, active_tab_style, hover_tab_style, icon_style)
    
    def get_preview_styles(self):
        if not self.current_theme:
            return ""
        
        # 特殊处理亮色主题
        if hasattr(self.current_theme, 'name') and self.current_theme.name == "light":
            bg = "#ffffff"  # 亮色主题使用白色背景
            text_color = "#333333"
            heading_color = "#000000"
            link_color = "#0066cc"
            code_bg = "rgba(0, 0, 0, 0.05)"
            blockquote_color = "#666666"
            blockquote_border = "#cccccc"
            table_border = "#dddddd"
            
            preview_style = f"""
                background-color: {bg}; 
                border: none;
                color: {text_color};
            """
            
            html_style = f"""
                <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    line-height: 1.6;
                    color: {text_color};
                    background-color: {bg};
                    margin: 0;
                    padding: 0 10px;
                }}
                h1, h2, h3, h4, h5, h6 {{
                    color: {heading_color};
                    margin-top: 24px;
                    margin-bottom: 16px;
                    font-weight: 600;
                }}
                h1 {{ font-size: 2em; border-bottom: 1px solid {table_border}; padding-bottom: 0.3em; }}
                h2 {{ font-size: 1.5em; border-bottom: 1px solid {table_border}; padding-bottom: 0.3em; }}
                a {{ color: {link_color}; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
                code {{
                    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
                    padding: 0.2em 0.4em;
                    background-color: {code_bg};
                    border-radius: 3px;
                }}
                pre {{
                    background-color: #f5f5f5;
                    border-radius: 6px;
                    padding: 16px;
                    overflow: auto;
                }}
                pre code {{
                    background-color: transparent;
                    padding: 0;
                }}
                blockquote {{
                    color: {blockquote_color};
                    border-left: 3px solid {blockquote_border};
                    padding-left: 16px;
                    margin-left: 0;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 16px 0;
                }}
                table th, table td {{
                    border: 1px solid {table_border};
                    padding: 6px 13px;
                }}
                table th {{
                    background-color: #f5f5f5;
                }}
                hr {{
                    border: 1px solid {table_border};
                }}
                </style>
            """
            
            print(f"应用亮色主题预览样式")
            return preview_style, html_style
        else:
            bg = self.current_theme.get("preview.background", "#1e2128")
            text_color = self.current_theme.get("preview.text_color", "#e0e0e0")
            heading_color = self.current_theme.get("preview.heading_color", "#ffffff")
            link_color = self.current_theme.get("preview.link_color", "#58a6ff")
            code_bg = self.current_theme.get("preview.code_bg", "rgba(110, 118, 129, 0.4)")
            blockquote_color = self.current_theme.get("preview.blockquote_color", "#8b949e")
            blockquote_border = self.current_theme.get("preview.blockquote_border", "#3b434b")
            table_border = self.current_theme.get("preview.table_border", "#30363d")
            
            return f"""
                background-color: {bg}; 
                border: none;
                color: {text_color};
            """, f"""
                <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    line-height: 1.6;
                    color: {text_color};
                    background-color: {bg};
                    margin: 0;
                    padding: 0 10px;
                }}
                h1, h2, h3, h4, h5, h6 {{
                    color: {heading_color};
                    margin-top: 24px;
                    margin-bottom: 16px;
                    font-weight: 600;
                }}
                h1 {{ font-size: 2em; border-bottom: 1px solid {table_border}; padding-bottom: 0.3em; }}
                h2 {{ font-size: 1.5em; border-bottom: 1px solid {table_border}; padding-bottom: 0.3em; }}
                a {{ color: {link_color}; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
                code {{
                    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
                    padding: 0.2em 0.4em;
                    background-color: {code_bg};
                    border-radius: 3px;
                }}
                pre {{
                    background-color: #161b22;
                    border-radius: 6px;
                    padding: 16px;
                    overflow: auto;
                }}
                pre code {{
                    background-color: transparent;
                    padding: 0;
                }}
                blockquote {{
                    color: {blockquote_color};
                    border-left: 3px solid {blockquote_border};
                    padding-left: 16px;
                    margin-left: 0;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 16px 0;
                }}
                table th, table td {{
                    border: 1px solid {table_border};
                    padding: 6px 13px;
                }}
                table th {{
                    background-color: #161b22;
                }}
                hr {{
                    border: 1px solid {table_border};
                }}
                </style>
            """
    
    def get_highlight_colors(self):
        if not self.current_theme:
            return (QColor(107, 159, 255, 60), QColor(107, 159, 255, 120))
        
        line_color_str = self.current_theme.get("highlight.line_color", "rgba(107, 159, 255, 60)")
        flash_color_str = self.current_theme.get("highlight.flash_color", "rgba(107, 159, 255, 120)")
            
        def parse_rgba(rgba_str):
            if rgba_str.startswith("rgba(") and rgba_str.endswith(")"):
                values = rgba_str[5:-1].split(",")
                if len(values) == 4:
                    r = int(values[0].strip())
                    g = int(values[1].strip())
                    b = int(values[2].strip())
                    a = int(float(values[3].strip()) * 255)
                    return QColor(r, g, b, a)
            return QColor(107, 159, 255, 60)  # 默认值
        
        line_color = parse_rgba(line_color_str)
        flash_color = parse_rgba(flash_color_str)
        
        return line_color, flash_color

    def get_editor_font_settings(self):
        """获取编辑器字体设置"""
        if not self.current_theme:
            return {
                "preserve_font_size": False
            }
            
        preserve_font_size = self.current_theme.should_preserve_font_size()
            
        return {
            "preserve_font_size": preserve_font_size
        }
