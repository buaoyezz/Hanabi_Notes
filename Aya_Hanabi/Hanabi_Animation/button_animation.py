from PySide6.QtCore import QObject, Qt, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QColor, QPalette

class ButtonHoverAnimation(QObject):
    def __init__(self, button, parent=None):
        super().__init__(parent)
        self.button = button
        self.is_hovered = False
        self.animation = None
        self.disable_transparency = True
        self._hover_scale = 1.0
        self._hover_opacity = 1.0  # 将初始不透明度设为1.0，确保按钮默认状态足够清晰
        self._background_opacity = 0.0
        
        self.button.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self.button.setAttribute(Qt.WA_TranslucentBackground, False)
        
        self.original_style = self.button.styleSheet()
        
        current_font = button.font()
        self.original_font_size = current_font.pixelSize()
        if self.original_font_size <= 0:
            self.original_font_size = current_font.pointSize()
            if self.original_font_size <= 0:
                self.original_font_size = 18
        
        self.scale_animation = QPropertyAnimation(self, b"hover_scale")
        self.scale_animation.setDuration(150)
        self.scale_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self.opacity_animation = QPropertyAnimation(button, b"windowOpacity")
        self.opacity_animation.setDuration(200)
        self.opacity_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        self.bg_animation = QPropertyAnimation(self, b"background_opacity")
        self.bg_animation.setDuration(200)
        self.bg_animation.setEasingCurve(QEasingCurve.OutQuad)
        
        self.button.installEventFilter(self)
    
    # 添加属性存取器方法
    def get_hover_scale(self):
        return self._hover_scale
        
    def set_hover_scale(self, scale):
        self._hover_scale = scale
        # 当比例变化时可以更新按钮样式，例如字体大小
        # 但这里简单起见，不做任何操作
    
    # 将hover_scale定义为Qt属性
    hover_scale = Property(float, get_hover_scale, set_hover_scale)
    
    def get_background_opacity(self):
        return self._background_opacity
        
    def set_background_opacity(self, opacity):
        self._background_opacity = opacity
        # 当背景透明度变化时可以更新按钮样式
        # 但这里简单起见，不做任何操作
    
    # 将background_opacity定义为Qt属性
    background_opacity = Property(float, get_background_opacity, set_background_opacity)
    
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
        
        # 使用start_leave_animation方法处理离开动画
        self.start_leave_animation()
        
        # 设置按钮不透明度为1.0，确保可见性
        self.button.setWindowOpacity(1.0)
        
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
    
    def start_leave_animation(self):
        self.scale_animation.stop()
        self.opacity_animation.stop()
        self.bg_animation.stop()
        
        self.scale_animation.setStartValue(self._hover_scale)
        self.scale_animation.setEndValue(1.0)
        
        self.opacity_animation.setStartValue(self._hover_opacity)
        
        if hasattr(self.button, 'isActive') and self.button.isActive:
            self.opacity_animation.setEndValue(1.0)
        else:
            self.opacity_animation.setEndValue(1.0)  # 将鼠标离开后的不透明度设为1.0，不再使按钮变暗
        
        self.bg_animation.setStartValue(self._background_opacity)
        self.bg_animation.setEndValue(0.0)
        
        self.scale_animation.start()
        self.opacity_animation.start()
        self.bg_animation.start() 