import os
import sys
from PySide6.QtGui import QFont, QFontDatabase

BASE_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
FONTS_PATH = os.path.join(BASE_PATH, "Hanabi", "Fonts")
ICON_FONT_PATH = os.path.join(FONTS_PATH, "MaterialIcons-Regular.ttf")

sys.path.append(BASE_PATH)
try:
    from Hanabi.Fonts.icon_map import ICON_MAP
except ImportError:
    print("警告: 无法导入图标映射文件")
    ICON_MAP = {}

class FontManager:
    _custom_fonts = {}
    _default_font_family = "Microsoft YaHei UI"
    _default_font_size = 15
    _fallback_fonts = ["Microsoft YaHei", "Microsoft YaHei UI", "Segoe UI", "SimHei", "SimSun"]
    
    @classmethod
    def init(cls):
        # 加载自定义字体
        fonts_loaded = cls.load_custom_fonts()
        return fonts_loaded
    
    @classmethod
    def load_custom_fonts(cls):
        # 加载自定义字体目录中的所有字体
        fonts_loaded = 0
        
        if os.path.exists(FONTS_PATH):
            for file in os.listdir(FONTS_PATH):
                if file.lower().endswith(('.ttf', '.otf')):
                    font_path = os.path.join(FONTS_PATH, file)
                    font_id = QFontDatabase.addApplicationFont(font_path)
                    if font_id != -1:
                        font_families = QFontDatabase.applicationFontFamilies(font_id)
                        for family in font_families:
                            cls._custom_fonts[family] = font_id
                        fonts_loaded += 1
                    else:
                        print(f"无法加载字体: {file}")
        
        return fonts_loaded > 0
    
    @classmethod
    def get_system_fonts(cls):
        # 获取系统中所有可用字体列表
        return QFontDatabase.families()
    
    @classmethod
    def get_custom_fonts(cls):
        # 获取已加载的自定义字体列表
        return list(cls._custom_fonts.keys())
    
    @classmethod
    def get_ui_font(cls, size=None):
        """获取UI界面字体"""
        if size is None:
            size = cls._default_font_size
        
        # 尝试使用微软雅黑UI或其他适合UI的字体
        for font_family in cls._fallback_fonts:
            if font_family in QFontDatabase.families():
                return QFont(font_family, size)
        
        # 如果都不可用，使用系统默认字体
        return QFont(cls._default_font_family, size)
    
    @classmethod
    def get_font(cls, family=None, size=None, bold=False, italic=False):
        # 创建指定属性的QFont对象
        if family is None:
            family = cls._default_font_family
        
        if size is None:
            size = cls._default_font_size
            
        font = QFont(family, size)
        font.setBold(bold)
        font.setItalic(italic)
        
        return font
    
    @classmethod
    def set_default_font(cls, family, size):
        cls._default_font_family = family
        cls._default_font_size = size

class IconProvider:
    _font_id = None
    _icon_size = 18  # 默认图标大小
    
    @classmethod
    def init_font(cls):
        if cls._font_id is None:
            if not os.path.exists(ICON_FONT_PATH):
                print(f"Material图标字体文件不存在: {ICON_FONT_PATH}")
                return False
                
            cls._font_id = QFontDatabase.addApplicationFont(ICON_FONT_PATH)
            if cls._font_id == -1:
                print("无法加载Material图标字体")
                return False
                
            if not QFontDatabase.applicationFontFamilies(cls._font_id):
                print("加载的字体没有可用的字体族")
                return False
                
        return True
    
    @classmethod
    def ensure_font_loaded(cls):
        """确保Material图标字体已加载，如果未加载则尝试加载"""
        if cls._font_id is None or cls._font_id == -1:
            print("Material图标字体未加载，尝试加载...")
            return cls.init_font()
        
        # 验证字体是否可用
        font_families = QFontDatabase.applicationFontFamilies(cls._font_id)
        if not font_families:
            print("Material图标字体不可用，尝试重新加载...")
            # 移除旧字体（如果存在）
            if cls._font_id != -1:
                QFontDatabase.removeApplicationFont(cls._font_id)
                cls._font_id = None
            # 重新加载
            return cls.init_font()
            
        return True
    
    @classmethod
    def get_icon_font(cls, size=None):
        if size is None:
            size = cls._icon_size
            
        # 确保字体已加载
        cls.ensure_font_loaded()
        
        if cls._font_id != -1 and cls._font_id is not None:
            font_families = QFontDatabase.applicationFontFamilies(cls._font_id)
            if font_families:
                font_family = font_families[0]
                font = QFont(font_family)
                font.setPixelSize(size)
                return font
        
        # 如果字体仍然不可用，返回备用字体
        print("警告：Material图标字体不可用，使用备用字体")
        fallback_font = QFont()
        fallback_font.setPixelSize(size)
        return fallback_font
    
    @classmethod
    def get_icon(cls, name):
        # 确保字体已加载
        cls.ensure_font_loaded()
        return ICON_MAP.get(name, "")
    
    @classmethod
    def get_all_icon_names(cls):
        # 返回所有可用图标名称列表
        return list(ICON_MAP.keys())
    
    @classmethod
    def set_default_icon_size(cls, size):
        cls._icon_size = size

# 扩展更多常用图标
ICONS = {
    # 基本界面图标
    "close": ICON_MAP.get("close", "x"),
    "minimize": ICON_MAP.get("remove", "-"),
    "maximize": ICON_MAP.get("fullscreen", "□"),
    "restore": ICON_MAP.get("fullscreen_exit", "⧉"),
    
    # 常用动作图标
    "save": ICON_MAP.get("save", "💾"),
    "refresh": ICON_MAP.get("refresh", "↻"),
    "home": ICON_MAP.get("home", "🏠"),
    "share": ICON_MAP.get("share", "↗"),
    "download": ICON_MAP.get("download", "↓"),
    "upload": ICON_MAP.get("upload", "↑"),
    "delete": ICON_MAP.get("delete", "🗑"),
    "edit": ICON_MAP.get("edit", "✎"),
    "settings": ICON_MAP.get("settings", "⚙"),
    "menu": ICON_MAP.get("menu", "☰"),
    "more_vert": ICON_MAP.get("more_vert", "⋮"),
    "more_horiz": ICON_MAP.get("more_horiz", "⋯"),
    
    # 导航图标
    "arrow_back": ICON_MAP.get("arrow_back", "←"),
    "arrow_forward": ICON_MAP.get("arrow_forward", "→"),
    "arrow_upward": ICON_MAP.get("arrow_upward", "↑"),
    "arrow_downward": ICON_MAP.get("arrow_downward", "↓"),
    "chevron_left": ICON_MAP.get("chevron_left", "<"),
    "chevron_right": ICON_MAP.get("chevron_right", ">"),
    "expand_more": ICON_MAP.get("expand_more", "▼"),
    "expand_less": ICON_MAP.get("expand_less", "▲"),
    
    # 文件相关图标
    "folder": ICON_MAP.get("folder", "📁"),
    "folder_open": ICON_MAP.get("folder_open", "📂"),
    "file": ICON_MAP.get("description", "📄"),
    "create_new_folder": ICON_MAP.get("create_new_folder", ""),
    "attachment": ICON_MAP.get("attachment", "📎"),
    
    # 文本编辑图标
    "undo": ICON_MAP.get("undo", "↩"),
    "redo": ICON_MAP.get("redo", "↪"),
    "content_cut": ICON_MAP.get("content_cut", "✂"),
    "content_copy": ICON_MAP.get("content_copy", "📋"),
    "content_paste": ICON_MAP.get("content_paste", "📊"),
    "search": ICON_MAP.get("search", "🔍"),
    
    # 设置面板相关图标
    "info": ICON_MAP.get("info", "ℹ"),
    "help": ICON_MAP.get("help", "?"),
    "palette": ICON_MAP.get("palette", "🎨"),
    "brush": ICON_MAP.get("brush", "🖌"),
    "color_lens": ICON_MAP.get("color_lens", "🎭"),
    "tune": ICON_MAP.get("tune", "⚙"),
    "build": ICON_MAP.get("build", "🔧"),
    "account_circle": ICON_MAP.get("account_circle", "👤"),
    "person": ICON_MAP.get("person", "👤"),
    "people": ICON_MAP.get("people", "👥"),
    "extension": ICON_MAP.get("extension", "🧩"),
    "dashboard": ICON_MAP.get("dashboard", "📊"),
    "code": ICON_MAP.get("code", "</>"),
    "format_size": ICON_MAP.get("format_size", "A"),
    "format_color_text": ICON_MAP.get("format_color_text", "A"),
    "format_align_left": ICON_MAP.get("format_align_left", "☰"),
    "text_format": ICON_MAP.get("text_format", "A"),
    "visibility": ICON_MAP.get("visibility", "👁"),
    "visibility_off": ICON_MAP.get("visibility_off", "👁‍🗨"),
    "language": ICON_MAP.get("language", "🌐"),
    "translate": ICON_MAP.get("translate", "🌍"),
    "bookmark": ICON_MAP.get("bookmark", "🔖"),
    "bookmark_border": ICON_MAP.get("bookmark_border", "🔖"),
    "notifications": ICON_MAP.get("notifications", "🔔"),
    "notifications_none": ICON_MAP.get("notifications_none", "🔕"),
    "security": ICON_MAP.get("security", "🔒"),
    "verified_user": ICON_MAP.get("verified_user", "✓"),
    "cloud": ICON_MAP.get("cloud", "☁"),
    "cloud_download": ICON_MAP.get("cloud_download", "☁↓"),
    "cloud_upload": ICON_MAP.get("cloud_upload", "☁↑"),
    "laptop": ICON_MAP.get("laptop", "💻"),
    "desktop_windows": ICON_MAP.get("desktop_windows", "🖥")
    }