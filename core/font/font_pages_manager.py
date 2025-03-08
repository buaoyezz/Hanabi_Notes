# 字体管理器 -Pages

from PySide6.QtGui import QFont, QFontDatabase, QAction
from PySide6.QtWidgets import QWidget, QApplication, QLabel, QPushButton
from PySide6.QtCore import Qt
import platform
from core.log.log_manager import log
import os
import sys
from core.thread.thread_manager import thread_manager

def resource_path(relative_path):
    base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class FontPagesManager:
    FONT_CONFIGS = {
        'default': {
            'primary': 'Microsoft YaHei UI',
            'secondary': 'Segoe UI',
            'icon': 'Material Icons'
        }
    }
    
    FONT_FILES = {
        'Material Icons': 'MaterialIcons-Regular.ttf'
    }

    def __init__(self):
        self.fonts = {}
        self._init_font_paths()
        self._load_fonts()
        self._setup_font_objects()
        # 延迟导入FontManager
        from core.font.font_manager import FontManager
        self.font_manager = FontManager()

    def _init_font_paths(self):
        self.font_paths = {}
        for font_name, file_name in self.FONT_FILES.items():
            folder = 'icons' if 'Material' in font_name else 'font'
            path = os.path.join("core", "font", folder, file_name)
            if hasattr(sys, '_MEIPASS'):
                path = os.path.join(sys._MEIPASS, path)
            else:
                path = os.path.join(os.path.abspath("."), path)
            self.font_paths[font_name] = path

    def _load_fonts(self):
        font_db = QFontDatabase()
        # 只加载Material Icons字体
        for font_name, path in self.font_paths.items():
            try:
                if os.path.exists(path):
                    font_id = font_db.addApplicationFont(path)
                    if font_id >= 0:
                        log.info(f"字体加载成功: {font_name}")
                    else:
                        log.error(f"字体加载失败: {font_name}")
                else:
                    log.error(f"字体文件不存在: {path}")
            except Exception as e:
                log.error(f"加载字体出错 {font_name}: {str(e)}")

    def _setup_font_objects(self):
        fonts = self.FONT_CONFIGS['default']
        
        self.title_font = self._create_font([fonts['primary'], fonts['secondary']], 24, QFont.Weight.Bold)
        self.subtitle_font = self._create_font([fonts['primary'], fonts['secondary']], 16, QFont.Weight.Medium)
        self.normal_font = self._create_font([fonts['primary'], fonts['secondary']], 14)
        self.button_font = self._create_font([fonts['primary'], fonts['secondary']], 14, QFont.Weight.Medium)
        self.icon_font = self._create_font([fonts['icon']], 24)

    def _create_font(self, families, size, weight=QFont.Weight.Normal, letter_spacing=0.5):
        font = QFont()
        font.setFamilies(families)
        font.setPixelSize(size)
        font.setWeight(weight)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, letter_spacing)
        return font

    def setFont(self, font_name, size=14, is_bold=False):
        font = QFont(font_name)
        font.setPixelSize(size)
        if is_bold:
            font.setBold(True)
        return font

    def apply_font(self, widget, font_type="normal"):
        if not isinstance(widget, (QWidget, QLabel)):
            return

        font_map = {
            "title": self.title_font,
            "normal": self.normal_font
        }
        widget.setFont(font_map.get(font_type, self.normal_font))

    def apply_icon_font(self, widget, size=24):
        if isinstance(widget, QLabel):
            widget.setStyleSheet("color: #666666; background-color: transparent;")
            widget.setAttribute(Qt.WA_TranslucentBackground)
            font = self.font_manager.create_icon_font(size)
            widget.setFont(font)

    def get_icon_text(self, icon_name):
        return self.font_manager.get_icon_text(icon_name)

    def apply_title_style(self, widget):
        if isinstance(widget, QLabel):
            widget.setStyleSheet("color: #333333; background-color: transparent;")
            widget.setAttribute(Qt.WA_TranslucentBackground)
        # 使用当前字体
        current_font = self.font_manager.current_font
        font = self.setFont(current_font, size=24, is_bold=True)
        widget.setFont(font)
        
    def apply_subtitle_style(self, widget):
        if isinstance(widget, QLabel):
            widget.setStyleSheet("color: #666666; background-color: transparent;")
            widget.setAttribute(Qt.WA_TranslucentBackground)
        # 使用当前字体
        current_font = self.font_manager.current_font
        font = self.setFont(current_font, size=16)
        widget.setFont(font)
        
    def apply_normal_style(self, widget):
        if isinstance(widget, QLabel):
            widget.setStyleSheet("""
                QLabel {
                    color: #333333;
                    background-color: transparent;
                }
            """)
            widget.setAttribute(Qt.WA_TranslucentBackground)
        # 使用当前字体
        current_font = self.font_manager.current_font
        font = self.setFont(current_font, size=14)
        widget.setFont(font)
        
    def apply_small_style(self, widget):
        if isinstance(widget, QLabel):
            widget.setStyleSheet("""
                QLabel {
                    color: #666666;
                    background-color: transparent;
                }
            """)
            widget.setAttribute(Qt.WA_TranslucentBackground)
        # 使用当前字体
        current_font = self.font_manager.current_font
        font = self.setFont(current_font, size=13)
        widget.setFont(font)
        
    def apply_button_style(self, widget):
        if isinstance(widget, QPushButton):
            widget.setFont(self.button_font)
