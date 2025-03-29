from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton
from Aya_Hanabi.Hanabi_Core.FontManager.fontManager import IconProvider

class IconButton(QPushButton):
    def __init__(self, iconName, size=14, parent=None):
        super().__init__(parent)
        self.setText(iconName)
        self.setFont(IconProvider.get_icon_font(size))
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("border: none; background: transparent;")
        
    def updateStyle(self, icon_color="#333333", hover_bg="rgba(0, 0, 0, 0.05)", active=False, active_color="#6b9fff"):
        color = active_color if active else icon_color
        
        self.setStyleSheet(f"""
            QPushButton {{
                color: {color};
                background-color: transparent;
                border: none;
                border-radius: 8px;
                padding: 4px;
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
            }}
        """) 