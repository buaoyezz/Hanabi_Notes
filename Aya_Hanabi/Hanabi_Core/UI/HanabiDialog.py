import sys
import os
import json
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QApplication, QGraphicsDropShadowEffect,
                             QSpacerItem, QSizePolicy, QWidget, QComboBox)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize, Property, Signal, QRect
from PySide6.QtGui import QColor, QPainter, QPainterPath, QFont, QIcon, QPixmap
from Aya_Hanabi.Hanabi_Core.FontManager.fontManager import FontManager, IconProvider, ICONS

class HanabiDialog(QDialog):
    Ok_Result = 0
    Cancel_Result = 1
    Yes_Result = 2
    No_Result = 3
    
    def __init__(self, parent=None, title="对话框", width=400, height=250):
        super().__init__(parent)
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.result_value = self.Cancel_Result
        
        self.resize(width, height)
        
        IconProvider.init_font()
        
        self.theme_colors = self.get_theme_colors(parent)
        
        self.setup_ui(title)
        
        self.add_shadow_effect()
        
        self.setup_animations()
        
        self.dragging = False
        self.drag_position = None
    
    def get_theme_colors(self, parent):
        colors = {
            "primary": "#8B5CF6",
            "text": "#333333",
            "background": "#FFFFFF",
            "border": "#E5E7EB",
            "hover": "rgba(0, 0, 0, 0.05)",
            "is_dark": False,
            "font_family": "Microsoft YaHei"
        }
        
        if parent and hasattr(parent, 'themeManager') and parent.themeManager:
            theme_manager = parent.themeManager
            theme = getattr(theme_manager, 'current_theme', {})
            
            is_dark = False
            if hasattr(theme_manager, 'current_theme_name'):
                is_dark = theme_manager.current_theme_name in ["dark", "purple_dream", "green_theme"]
            
            colors["is_dark"] = is_dark
            
            if is_dark:
                colors["primary"] = theme.get("accent_color", "#8B5CF6")
                colors["text"] = theme.get("editor.text_color", "#E0E0E0")
                colors["background"] = theme.get("window.background", "#1E2128")
                colors["border"] = theme.get("window.border", "#333842")
                colors["hover"] = "rgba(255, 255, 255, 0.05)"
            else:
                colors["primary"] = theme.get("accent_color", "#6B9FFF")
                colors["text"] = theme.get("editor.text_color", "#333333")
                colors["background"] = theme.get("window.background", "#FFFFFF")
                colors["border"] = theme.get("window.border", "#E5E7EB")
                colors["hover"] = "rgba(0, 0, 0, 0.05)"
                
            if hasattr(parent, 'font_family'):
                colors["font_family"] = parent.font_family
        
        else:
            try:
                settings_dir = os.path.join(os.path.expanduser("~"), ".hanabi_notes")
                settings_file = os.path.join(settings_dir, "settings.json")
                
                if os.path.exists(settings_file):
                    with open(settings_file, 'r', encoding='utf-8') as f:
                        settings = json.load(f)
                    
                    theme_name = settings.get("appearance", {}).get("theme", "light")
                    colors["is_dark"] = theme_name in ["dark", "purple_dream", "green_theme"]
                    
                    if colors["is_dark"]:
                        colors["primary"] = "#8B5CF6"
                        colors["text"] = "#E0E0E0"
                        colors["background"] = "#1E2128"
                        colors["border"] = "#333842"
                        colors["hover"] = "rgba(255, 255, 255, 0.05)"
                        
                    if "editor" in settings and "font" in settings["editor"]:
                        font_settings = settings["editor"]["font"]
                        if "family" in font_settings:
                            colors["font_family"] = font_settings["family"]
            except Exception as e:
                print(f"读取主题设置时出错: {e}")
        
        return colors
    
    def setup_ui(self, title):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)
        
        bg_color = self.theme_colors["background"]
        text_color = self.theme_colors["text"]
        primary_color = self.theme_colors["primary"]
        border_color = self.theme_colors["border"]
        hover_color = self.theme_colors["hover"]
        font_family = self.theme_colors["font_family"]
        
        font = FontManager.get_font(font_family, 14)
        self.setFont(font)
        
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        self.title_label = QLabel(title)
        title_font = FontManager.get_font(font_family, 16, bold=True)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet(f"""
            color: {primary_color};
        """)
        title_layout.addWidget(self.title_label)
        
        title_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        self.close_button = QPushButton()
        icon_font = IconProvider.get_icon_font(16)
        self.close_button.setFont(icon_font)
        self.close_button.setText(IconProvider.get_icon("close"))
        self.close_button.setStyleSheet(f"""
            QPushButton {{
                border: none;
                color: {text_color};
                background-color: transparent;
            }}
            QPushButton:hover {{
                color: {primary_color};
            }}
            QPushButton:pressed {{
                color: {text_color};
            }}
        """)
        self.close_button.setFixedSize(30, 30)
        self.close_button.clicked.connect(self.reject)
        title_layout.addWidget(self.close_button)
        
        self.main_layout.addLayout(title_layout)
        
        self.separator = QLabel()
        self.separator.setFixedHeight(1)
        self.separator.setStyleSheet(f"background-color: {primary_color}; margin: 0px 0px;")
        self.main_layout.addWidget(self.separator)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 10, 0, 10)
        self.content_layout.setSpacing(15)
        
        self.content_widget.setStyleSheet(f"""
            color: {text_color};
            background-color: transparent;
        """)
        
        self.main_layout.addWidget(self.content_widget)
        
        self.button_layout = QHBoxLayout()
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.setSpacing(10)
        
        self.button_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        btn_font = FontManager.get_font(font_family, 14, bold=True)
        self.button_style = f"""
            QPushButton {{
                background-color: {primary_color};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {QColor(primary_color).lighter(115).name()};
            }}
            QPushButton:pressed {{
                background-color: {QColor(primary_color).darker(115).name()};
            }}
            QPushButton[flat="true"] {{
                background-color: transparent;
                color: {primary_color};
            }}
            QPushButton[flat="true"]:hover {{
                background-color: {hover_color};
            }}
            QPushButton[flat="true"]:pressed {{
                background-color: rgba(0, 0, 0, 0.1);
            }}
        """
        
        self.main_layout.addLayout(self.button_layout)
    
    def add_shadow_effect(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
    
    def setup_animations(self):
        self.opacity = 0.0
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(200)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self.scale_animation = QPropertyAnimation(self, b"geometry")
        self.scale_animation.setDuration(200)
        self.scale_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def add_ok_button(self, text="确定", icon_name=None):
        self.ok_button = QPushButton(text)
        self.ok_button.setFont(FontManager.get_font(self.theme_colors["font_family"], 14, bold=True))
        
        if icon_name and icon_name in ICONS:
            icon_font = IconProvider.get_icon_font(14)
            icon_text = IconProvider.get_icon(icon_name)
            button_text = f"{icon_text} {text}" if icon_text else text
            self.ok_button.setFont(icon_font)
            self.ok_button.setText(button_text)
            
        self.ok_button.setStyleSheet(self.button_style)
        self.ok_button.clicked.connect(self.handle_ok)
        self.button_layout.addWidget(self.ok_button)
    
    def add_cancel_button(self, text="取消", icon_name=None):
        self.cancel_button = QPushButton(text)
        self.cancel_button.setFont(FontManager.get_font(self.theme_colors["font_family"], 14))
        
        if icon_name and icon_name in ICONS:
            icon_font = IconProvider.get_icon_font(14)
            icon_text = IconProvider.get_icon(icon_name)
            button_text = f"{icon_text} {text}" if icon_text else text
            self.cancel_button.setFont(icon_font)
            self.cancel_button.setText(button_text)
            
        self.cancel_button.setProperty("flat", True)
        self.cancel_button.setStyleSheet(self.button_style)
        self.cancel_button.clicked.connect(self.handle_cancel)
        self.button_layout.addWidget(self.cancel_button)
    
    def handle_ok(self):
        self.result_value = self.Ok_Result
        self.accept()
    
    def handle_cancel(self):
        self.result_value = self.Cancel_Result
        self.reject()
    
    def get_result(self):
        return self.result_value
    
    def showEvent(self, event):
        super().showEvent(event)
        
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - self.height()) // 2
        else:
            desktop = QApplication.primaryScreen().availableGeometry()
            x = (desktop.width() - self.width()) // 2
            y = (desktop.height() - self.height()) // 2
        
        self.move(x, y)
        
        self.animation.start()
        
        start_rect = QRect(x + self.width() // 2 - 10, y + self.height() // 2 - 10, 20, 20)
        end_rect = QRect(x, y, self.width(), self.height())
        
        self.scale_animation.setStartValue(start_rect)
        self.scale_animation.setEndValue(end_rect)
        self.scale_animation.start()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 10, 10)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(self.theme_colors["background"]))
        painter.drawPath(path)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        self.dragging = False
        event.accept()

class EncodingSelectionDialog(HanabiDialog):
    def __init__(self, parent=None, current_encoding="UTF-8"):
        super().__init__(parent, "选择文件编码", width=320, height=180)
        
        self.encodings = [
            "UTF-8", 
            "ANSI",
            "UTF-16 LE", 
            "UTF-16 BE",
            "UTF-8 BOM",
            "GB18030"
        ]
        
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, 0, 0, 0)
        
        text_color = self.theme_colors["text"]
        border_color = self.theme_colors["border"]
        hover_color = self.theme_colors["hover"]
        bg_color = self.theme_colors["background"]
        is_dark = self.theme_colors["is_dark"]
        font_family = self.theme_colors["font_family"]
        
        encoding_label = QLabel("编码:")
        encoding_label.setFont(FontManager.get_font(font_family, 14))
        encoding_label.setStyleSheet(f"color: {text_color};")
        row_layout.addWidget(encoding_label)
        
        combo_style = f"""
            QComboBox {{
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 5px 10px;
                background-color: {QColor(bg_color).lighter(115).name() if is_dark else bg_color};
                color: {text_color};
                min-width: 180px;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: right center;
                width: 20px;
                border-left: none;
            }}
            QComboBox QAbstractItemView {{
                border: 1px solid {border_color};
                border-radius: 4px;
                background-color: {bg_color};
                color: {text_color};
                selection-background-color: {hover_color};
            }}
        """
        
        self.encoding_combo = QComboBox()
        self.encoding_combo.setFont(FontManager.get_font(font_family, 14))
        self.encoding_combo.addItems(self.encodings)
        self.encoding_combo.setStyleSheet(combo_style)
        
        try:
            index = self.encodings.index(current_encoding)
            self.encoding_combo.setCurrentIndex(index)
        except ValueError:
            self.encoding_combo.setCurrentIndex(0)
            
        row_layout.addWidget(self.encoding_combo)
        
        self.content_layout.addLayout(row_layout)
        self.content_layout.addStretch(1)
        
        self.add_cancel_button("取消")
        self.add_ok_button("保存", "save")
    
    def get_selected_encoding(self):
        return self.encoding_combo.currentText()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    FontManager.init()
    
    dialog = EncodingSelectionDialog(None, "UTF-8")
    if dialog.exec_() == QDialog.Accepted:
        print(f"选择的编码: {dialog.get_selected_encoding()}")
    
    sys.exit(0)
