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
        
        if not self.disable_transparency:
            self.animation = QPropertyAnimation(self.button, b"windowOpacity")
            self.animation.setDuration(200)
            self.animation.setStartValue(self.button.windowOpacity())
            self.animation.setEndValue(1.0)
            self.animation.setEasingCurve(QEasingCurve.OutCubic)
            self.animation.start()
        else:
            current_color = self.button.palette().color(QPalette.Button)
            target_color = QColor(0, 103, 163)
            
            updated_style = self.button.styleSheet().replace(
                "background-color: #005780", 
                "background-color: #0067a3"
            )
            self.button.setStyleSheet(updated_style)
            
            self.button.updateStyle(True)
    
    def leaveEvent(self):
        self.is_hovered = False
        
        if self.animation and self.animation.state() == QPropertyAnimation.Running:
            self.animation.stop()
        
        if not self.disable_transparency:
            self.animation = QPropertyAnimation(self.button, b"windowOpacity")
            self.animation.setDuration(300)
            self.animation.setStartValue(self.button.windowOpacity())
            self.animation.setEndValue(0.8)
            self.animation.setEasingCurve(QEasingCurve.OutCubic)
            self.animation.start()
        else:
            current_color = self.button.palette().color(QPalette.Button)
            target_color = QColor(0, 87, 128)
            
            updated_style = self.button.styleSheet().replace(
                "background-color: #0067a3", 
                "background-color: #005780"
            )
            self.button.setStyleSheet(updated_style)
            
            self.button.updateStyle(False) 