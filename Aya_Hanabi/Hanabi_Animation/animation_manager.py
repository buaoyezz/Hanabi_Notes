from PySide6.QtCore import (QObject, QPropertyAnimation, QParallelAnimationGroup,
                           QSequentialAnimationGroup, QEasingCurve, Qt, QTimer)
from PySide6.QtWidgets import QWidget

class AnimationManager(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._animations = {}
        self._states = {}
        self._cached_animations = {}
        self._active_animations = set()
        
        # 性能优化设置
        self._use_hardware_acceleration = True
        
    def create_animation(self, target, property_name, start_value, end_value, 
                        duration=300, easing=QEasingCurve.OutCubic, cache_key=None):
        # 如果有缓存的动画，优先使用缓存
        if cache_key and cache_key in self._cached_animations:
            anim = self._cached_animations[cache_key]
            anim.setStartValue(start_value)
            anim.setEndValue(end_value)
            return anim
            
        # 创建新动画
        anim = QPropertyAnimation(target, property_name)
        anim.setDuration(duration)
        anim.setEasingCurve(easing)
        anim.setStartValue(start_value)
        anim.setEndValue(end_value)
        
        # 启用硬件加速
        if self._use_hardware_acceleration and hasattr(target, 'setGraphicsEffect'):
            target.setAttribute(Qt.WA_TranslucentBackground, False)
            target.setAttribute(Qt.WA_OpaquePaintEvent, True)
        
        # 添加动画状态管理
        anim.finished.connect(lambda: self._on_animation_finished(anim))
        anim.stateChanged.connect(lambda state: self._on_animation_state_changed(anim, state))
        
        # 缓存动画以供复用
        if cache_key:
            self._cached_animations[cache_key] = anim
            
        return anim
        
    def create_parallel_group(self, animations):
        group = QParallelAnimationGroup()
        for anim in animations:
            group.addAnimation(anim)
        return group
        
    def create_sequential_group(self, animations):
        group = QSequentialAnimationGroup()
        for anim in animations:
            group.addAnimation(anim)
        return group
        
    def _on_animation_finished(self, animation):
        if animation in self._active_animations:
            self._active_animations.remove(animation)
            
    def _on_animation_state_changed(self, animation, state):
        if state == QPropertyAnimation.Running:
            self._active_animations.add(animation)
        elif state == QPropertyAnimation.Stopped:
            if animation in self._active_animations:
                self._active_animations.remove(animation)
                
    def stop_all_animations(self):
        for anim in list(self._active_animations):
            anim.stop()
        self._active_animations.clear()
        
    def pause_all_animations(self):
        for anim in self._active_animations:
            anim.pause()
            
    def resume_all_animations(self):
        for anim in self._active_animations:
            anim.resume()
            
    def set_hardware_acceleration(self, enabled):
        self._use_hardware_acceleration = enabled
        
    def register_animation(self, name, animation):
        self._animations[name] = animation
        
    def get_animation(self, name):
        return self._animations.get(name)
        
    def set_state(self, name, value):
        self._states[name] = value
        
    def get_state(self, name):
        return self._states.get(name)
        
    def clear_cache(self):
        self.stop_all_animations()
        self._cached_animations.clear()
        
    @staticmethod
    def get_easing_curve(curve_type, overshoot=None):
        curve = QEasingCurve(curve_type)
        if overshoot is not None and curve_type in [QEasingCurve.OutBack, QEasingCurve.InOutBack]:
            curve.setOvershoot(overshoot)
        return curve

# 预定义的动画配置
class AnimationConfig:
    # 侧边栏动画
    SIDEBAR_EXPAND = {
        'duration': 180,  # 进一步减少持续时间
        'easing': QEasingCurve.OutCubic,  # 使用更流畅的曲线
        'overshoot': 1.01  # 减少回弹
    }
    
    SIDEBAR_COLLAPSE = {
        'duration': 150,  # 进一步减少持续时间
        'easing': QEasingCurve.InOutQuad
    }
    
    # 滚动条动画
    SCROLLBAR_FADE = {
        'duration': 150,
        'easing': QEasingCurve.OutCubic
    }
    
    # 按钮动画
    BUTTON_HOVER = {
        'duration': 100,
        'easing': QEasingCurve.OutCubic
    }
    
    # 标签动画
    TAB_SWITCH = {
        'duration': 150,
        'easing': QEasingCurve.OutCubic
    } 