from PySide6.QtCore import QObject, QPropertyAnimation, QEasingCurve, QPoint, Qt, Property, Signal
from PySide6.QtWidgets import QWidget
from core.log.log_manager import log

class BasicAnimation(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._opacity = 0.0
        
        # 创建透明度动画
        self.opacity_animation = QPropertyAnimation(self, b"opacity")
        self.opacity_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.opacity_animation.setDuration(200)  # 缩短动画时间
        self.opacity_animation.valueChanged.connect(self._update_opacity)
        
    def _update_opacity(self, value):
        if self.parent():
            self.parent().setWindowOpacity(value)
    
    def _get_opacity(self):
        return self._opacity
        
    def _set_opacity(self, opacity):
        self._opacity = opacity
        
    opacity = Property(float, _get_opacity, _set_opacity)
    
    def fade_in(self):
        if not self.parent():
            return
            
        self.opacity_animation.setStartValue(0.0)
        self.opacity_animation.setEndValue(1.0)
        self.opacity_animation.start()
        
    def fade_out(self):
        if not self.parent():
            return
            
        self.opacity_animation.setStartValue(1.0)
        self.opacity_animation.setEndValue(0.0)
        self.opacity_animation.finished.connect(self.parent().hide)
        self.opacity_animation.start()

class MessageBoxAnimation(BasicAnimation):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 创建位置动画
        self.pos_animation = QPropertyAnimation(parent, b"pos")
        self.pos_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.pos_animation.setDuration(200)  # 缩短动画时间
        
    def show_with_animation(self):
        if not self.parent():
            return
            
        # 获取屏幕中心位置
        screen = self.parent().screen().availableGeometry()
        center = screen.center() - self.parent().rect().center()
        
        # 设置起始位置（稍微向上）
        start_pos = center + QPoint(0, 30)  # 减小偏移距离
        
        # 设置动画
        self.pos_animation.setStartValue(start_pos)
        self.pos_animation.setEndValue(center)
        
        # 开始动画
        self.parent().move(start_pos)
        self.parent().show()
        self.pos_animation.start()
        self.fade_in()
        
    def hide_with_animation(self):
        if not self.parent():
            return
            
        current_pos = self.parent().pos()
        end_pos = current_pos + QPoint(0, 30)  # 减小偏移距离
        
        # 设置动画
        self.pos_animation.setStartValue(current_pos)
        self.pos_animation.setEndValue(end_pos)
        
        # 开始动画
        self.pos_animation.start()
        self.fade_out()

class NotificationAnimation(BasicAnimation):
    animation_finished = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 创建位置动画
        self.pos_animation = QPropertyAnimation(parent, b"pos")
        self.pos_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.pos_animation.setDuration(200)  # 缩短动画时间
        self.pos_animation.finished.connect(self.animation_finished)
        
    def show_animation(self, start_pos, end_pos):
        if not self.parent():
            return
            
        # 设置动画
        self.pos_animation.setStartValue(start_pos)
        self.pos_animation.setEndValue(end_pos)
        
        # 开始动画
        self.parent().move(start_pos)
        self.parent().show()
        self.pos_animation.start()
        self.fade_in()
        
    def hide_animation(self, start_pos, end_pos):
        if not self.parent():
            return
            
        # 设置动画
        self.pos_animation.setStartValue(start_pos)
        self.pos_animation.setEndValue(end_pos)
        
        # 开始动画
        self.pos_animation.start()
        self.fade_out() 