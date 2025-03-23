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
    _default_font_family = "Consolas"
    _default_font_size = 15
    
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
    
    @classmethod
    def init_font(cls):
        if cls._font_id is None:
            cls._font_id = QFontDatabase.addApplicationFont(ICON_FONT_PATH)
            if cls._font_id == -1:
                print("无法加载Material图标字体")
                return False
        return True
    
    @classmethod
    def get_icon_font(cls, size=12):
        if cls.init_font():
            font_family = QFontDatabase.applicationFontFamilies(cls._font_id)[0]
            font = QFont(font_family)
            font.setPixelSize(size)
            return font
        return QFont()
    
    @classmethod
    def get_icon(cls, name):
        return ICON_MAP.get(name, "")
    
    @classmethod
    def get_all_icon_names(cls):
        # 返回所有可用图标名称列表
        return list(ICON_MAP.keys())

ICONS = {
    "close": ICON_MAP.get("close", "x"),
    "minimize": ICON_MAP.get("remove", "-"),
    "maximize": ICON_MAP.get("crop_square", "□"),
    "restore": ICON_MAP.get("filter_none", "⧉"),
    "circle": ICON_MAP.get("radio_button_unchecked", "○"),
    "code": ICON_MAP.get("code", "</>"),
    "settings": ICON_MAP.get("settings", "⚙"),
    "save": ICON_MAP.get("save", "💾"),
    "folder": ICON_MAP.get("folder", "📁"),
    "file": ICON_MAP.get("description", "📄"),
    "search": ICON_MAP.get("search", "🔍"),
    "font": ICON_MAP.get("text_format", "T"),
    "bold": ICON_MAP.get("format_bold", "B"),
    "italic": ICON_MAP.get("format_italic", "I"),
    "underline": ICON_MAP.get("format_underlined", "U"),
    "text_color": ICON_MAP.get("format_color_text", "A"),
    "background_color": ICON_MAP.get("format_color_fill", "BG"),
    "align_left": ICON_MAP.get("format_align_left", "⟸"),
    "align_center": ICON_MAP.get("format_align_center", "⟺"),
    "align_right": ICON_MAP.get("format_align_right", "⟹"),
    "size_up": ICON_MAP.get("text_increase", "A+"),
    "size_down": ICON_MAP.get("text_decrease", "A-"),
}
