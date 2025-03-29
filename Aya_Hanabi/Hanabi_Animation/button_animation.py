from PySide6.QtCore import QObject, Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPalette

class ButtonHoverAnimation(QObject):
    def __init__(self, button):
        super().__init__()
        self.button = button
        self.is_hovered = False
        self.animation = None
        self.disable_transparency = True
        
        self.button.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self.button.setAttribute(Qt.WA_TranslucentBackground, False)
        
        self.original_style = self.button.styleSheet()
    
    def enterEvent(self):
        self.is_hovered = True
        
        if self.animation and self.animation.state() == QPropertyAnimation.Running:
            self.animation.stop()
        
        # 检查是否为暗色主题按钮，如果是，使用较弱的hover效果
        is_dark_theme = False
        themeManager = None
        
        if hasattr(self.button, 'parent') and self.button.parent():
            parent = self.button.parent()
            while parent:
                if hasattr(parent, 'themeManager'):
                    themeManager = parent.themeManager
                    if hasattr(themeManager, 'current_theme_name'):
                        theme_name = themeManager.current_theme_name
                        is_dark_theme = theme_name in ["dark", "purple_dream", "green_theme"]
                    break
                parent = parent.parent()
                
        self.button.updateStyle(True, themeManager)
    
    def leaveEvent(self):
        self.is_hovered = False
        
        if self.animation and self.animation.state() == QPropertyAnimation.Running:
            self.animation.stop()
        
        # 检查是否为暗色主题按钮
        themeManager = None
        if hasattr(self.button, 'parent') and self.button.parent():
            parent = self.button.parent()
            while parent:
                if hasattr(parent, 'themeManager'):
                    themeManager = parent.themeManager
                    break
                parent = parent.parent()
                
        self.button.updateStyle(False, themeManager) 