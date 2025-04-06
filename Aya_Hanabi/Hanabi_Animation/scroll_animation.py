from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QObject, Property, QTimer, QPoint, QParallelAnimationGroup, QSequentialAnimationGroup, QAbstractAnimation, QRect
from PySide6.QtWidgets import QScrollBar, QScrollArea
from PySide6.QtGui import QColor

class ScrollFadeAnimation(QObject):
    def __init__(self, widget, parent=None):
        super().__init__(parent)
        self.widget = widget
        self._opacity = 0.0
        
        self.animation = QPropertyAnimation(self, b"opacity")
        self.animation.setDuration(350)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.start_hide_animation)
        
    def get_opacity(self):
        return self._opacity
        
    def set_opacity(self, opacity):
        if self._opacity != opacity:
            self._opacity = opacity
            self.update_style()
            
    opacity = Property(float, get_opacity, set_opacity)
    
    def update_style(self):
        from Aya_Hanabi.Hanabi_Styles.scrollbar_style import ScrollBarStyle
        # 确保滚动条始终有一定的可见度，最小不透明度为0.3
        opacity = max(0.3, self._opacity)
        handle_color = f"rgba(255, 255, 255, {opacity})"
        
        # 直接应用滚动条样式，使用 get_style 方法获取样式表字符串
        style = ScrollBarStyle.get_style(base_color="transparent", handle_color=handle_color)
        self.widget.verticalScrollBar().setStyleSheet(style)
    
    def start_show_animation(self):
        self.hide_timer.stop()
        self.animation.setStartValue(self._opacity)
        self.animation.setEndValue(0.4)
        
        curve = QEasingCurve(QEasingCurve.OutCubic)
        self.animation.setEasingCurve(curve)
        
        self.animation.start()
        
    def start_hide_animation(self):
        self.animation.setStartValue(self._opacity)
        self.animation.setEndValue(0.1)
        
        curve = QEasingCurve(QEasingCurve.InOutQuad)
        self.animation.setEasingCurve(curve)
        
        self.animation.start()
    
    def show_temporarily(self):
        self.start_show_animation()
        self.hide_timer.start(1800)
        
    def cleanup(self):
        if self.animation.state() == QAbstractAnimation.Running:
            self.animation.stop()
        
        if self.hide_timer.isActive():
            self.hide_timer.stop()

class ScrollAnimation:
    @staticmethod
    def smooth_scroll_to(scroll_area, target_widget, duration=350):
        target_pos = target_widget.mapTo(scroll_area.viewport(), QPoint(0, 0))
        
        scroll_animation = QPropertyAnimation(scroll_area.verticalScrollBar(), b"value")
        scroll_animation.setDuration(duration)
        
        curve = QEasingCurve(QEasingCurve.OutCubic)
        scroll_animation.setEasingCurve(curve)
        
        scroll_bar = scroll_area.verticalScrollBar()
        scroll_animation.setStartValue(scroll_bar.value())
        
        target_value = target_pos.y() - (scroll_area.viewport().height() - target_widget.height()) / 2
        target_value = max(0, min(target_value, scroll_bar.maximum()))
        
        scroll_animation.setEndValue(target_value)
        scroll_animation.start()
        
        return scroll_animation
    
    @staticmethod
    def elastic_scroll_to(scroll_area, target_widget, duration=450):
        target_pos = target_widget.mapTo(scroll_area.viewport(), QPoint(0, 0))
        
        scroll_animation = QPropertyAnimation(scroll_area.verticalScrollBar(), b"value")
        scroll_animation.setDuration(duration)
        
        curve = QEasingCurve(QEasingCurve.OutBack)
        curve.setOvershoot(1.02)
        scroll_animation.setEasingCurve(curve)
        
        scroll_bar = scroll_area.verticalScrollBar()
        scroll_animation.setStartValue(scroll_bar.value())
        
        target_value = target_pos.y() - (scroll_area.viewport().height() - target_widget.height()) / 2
        target_value = max(0, min(target_value, scroll_bar.maximum()))
        
        scroll_animation.setEndValue(target_value)
        scroll_animation.start()
        
        return scroll_animation
    
    @staticmethod
    def setup_advanced_scrolling(scroll_area):
        scroll_helper = SmoothScrollHelper(scroll_area)
        return scroll_helper

class SmoothScrollHelper(QObject):
    def __init__(self, scroll_area, parent=None):
        super().__init__(parent)
        self.scroll_area = scroll_area
        self._velocity = 0
        self._active_animation = None
        
        self.deceleration_timer = QTimer()
        self.deceleration_timer.setInterval(16)
        self.deceleration_timer.timeout.connect(self.update_scroll)
        
        self.scroll_area.viewport().installEventFilter(self)
    
    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        from PySide6.QtGui import QWheelEvent
        
        if obj is self.scroll_area.viewport() and event.type() == QEvent.Wheel:
            wheel_event = event
            
            delta = wheel_event.angleDelta().y()
            
            self._velocity += delta * 0.2
            
            max_speed = 200
            self._velocity = max(-max_speed, min(self._velocity, max_speed))
            
            if not self.deceleration_timer.isActive():
                self.deceleration_timer.start()
            
            return True
            
        return super().eventFilter(obj, event)
    
    def update_scroll(self):
        scrollbar = self.scroll_area.verticalScrollBar()
        
        scrollbar.setValue(scrollbar.value() - int(self._velocity))
        
        self._velocity *= 0.95
        
        if abs(self._velocity) < 0.1:
            self._velocity = 0
            self.deceleration_timer.stop()

class SidebarAnimation:
    @staticmethod
    def slide(sidebar, expanded=True, duration=450):
        animation = QPropertyAnimation(sidebar, b"geometry")
        animation.setDuration(duration)
        
        if expanded:
            curve = QEasingCurve(QEasingCurve.OutBack)
            curve.setOvershoot(1.02)
        else:
            curve = QEasingCurve(QEasingCurve.InOutQuint)
            
        animation.setEasingCurve(curve)
        
        current_rect = sidebar.geometry()
        
        if expanded:
            target_width = sidebar.expandedWidth
        else:
            target_width = sidebar.collapsedWidth
        
        target_rect = current_rect.adjusted(0, 0, target_width - current_rect.width(), 0)
        
        animation.setStartValue(current_rect)
        animation.setEndValue(target_rect)
        
        return animation

    @staticmethod
    def advanced_slide(sidebar, expanded=True, duration=450):
        animation_group = QParallelAnimationGroup()
        
        geo_anim = SidebarAnimation.slide(sidebar, expanded, duration)
        animation_group.addAnimation(geo_anim)
        
        if hasattr(sidebar, 'tabButtons') and sidebar.tabButtons and duration > 10:
            for i, btn in enumerate(sidebar.tabButtons):
                fade_anim = QPropertyAnimation(btn, b"windowOpacity")
                fade_anim.setDuration(duration * 0.8)
                
                if expanded:
                    fade_anim.setStartValue(0.4)
                    fade_anim.setEndValue(1.0)
                    fade_anim.setEasingCurve(QEasingCurve.OutCubic)
                else:
                    fade_anim.setStartValue(1.0)
                    fade_anim.setEndValue(0.4)
                    fade_anim.setEasingCurve(QEasingCurve.InCubic)
                
                animation_group.addAnimation(fade_anim)
                
                if i > 0 and duration > 200:
                    delay_ms = i * int(duration * 0.08)
                    QTimer.singleShot(delay_ms, lambda btn=btn, start=0.4, end=1.0 if expanded else 0.4: 
                                      SidebarAnimation._start_delayed_fade(btn, start, end, duration * 0.8))
        
        return animation_group
    
    @staticmethod
    def _start_delayed_fade(widget, start_value, end_value, duration):
        actual_duration = max(50, duration)
        
        fade = QPropertyAnimation(widget, b"windowOpacity")
        fade.setDuration(actual_duration)
        fade.setStartValue(start_value)
        fade.setEndValue(end_value)
        fade.setEasingCurve(QEasingCurve.OutCubic)
        fade.start()

class ButtonHoverAnimation(QObject):
    def __init__(self, button, parent=None):
        super().__init__(parent)
        self.button = button
        self._hover_scale = 1.0
        self._hover_opacity = 1.0
        self._background_opacity = 0.0
        
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
        
    def get_hover_scale(self):
        return self._hover_scale
        
    def set_hover_scale(self, scale):
        if self._hover_scale != scale:
            self._hover_scale = scale
            self.update_style()
            
    hover_scale = Property(float, get_hover_scale, set_hover_scale)
    
    def get_hover_opacity(self):
        return self._hover_opacity
        
    def set_hover_opacity(self, opacity):
        if self._hover_opacity != opacity:
            self._hover_opacity = opacity
            self.update_style()
            
    hover_opacity = Property(float, get_hover_opacity, set_hover_opacity)
    
    def get_background_opacity(self):
        return self._background_opacity
        
    def set_background_opacity(self, opacity):
        if self._background_opacity != opacity:
            self._background_opacity = opacity
            self.update_style()
            
    background_opacity = Property(float, get_background_opacity, set_background_opacity)
    
    def update_style(self):
        # 检查是否为暗色主题按钮
        is_dark_theme = False
        if hasattr(self.button, 'parent') and self.button.parent():
            parent = self.button.parent()
            while parent:
                if hasattr(parent, 'themeManager') and parent.themeManager:
                    if hasattr(parent.themeManager, 'current_theme_name'):
                        theme_name = parent.themeManager.current_theme_name
                        is_dark_theme = theme_name in ["dark", "purple_dream", "green_theme"]
                    break
                parent = parent.parent()
        
        # 根据主题类型使用不同的透明度处理
        bg_opacity = self._background_opacity
        if is_dark_theme:
            # 暗色主题时降低动画效果透明度
            bg_opacity = bg_opacity * 0.05
            bg_color = f"rgba(255, 255, 255, {bg_opacity})"
        else:
            bg_color = f"rgba(255, 255, 255, {bg_opacity * 0.15})"
        
        text_opacity = min(1.0, self._hover_opacity)
        text_color = f"rgba(255, 255, 255, {text_opacity})"
        
        border_radius = min(self.button.width(), self.button.height()) // 2
        
        # 保存基本样式设置，确保背景色正确
        if not hasattr(self, '_original_style'):
            # 保存原始样式，避免每次重设
            original_style = self.button.styleSheet()
            
            # 只保留非QPushButton的样式内容和背景设置
            style_parts = []
            is_button_block = False
            background_set = False
            
            for line in original_style.split('\n'):
                if line.strip().startswith('QPushButton {'):
                    is_button_block = True
                    continue
                elif is_button_block and line.strip() == '}':
                    is_button_block = False
                    continue
                elif is_button_block:
                    if line.strip().startswith('background-color:'):
                        background_set = True
                    continue
                
                style_parts.append(line)
            
            self._original_style = '\n'.join(style_parts)
            
            # 记录是否需要设置背景色
            self._needs_background = not background_set
        
        # 构建更新的样式
        button_style = f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                border: none;
                border-radius: {border_radius}px;
                padding: 0px;
            }}
        """
        
        # 合并样式
        self.button.setStyleSheet(button_style + self._original_style)
        
        if hasattr(self.button, 'font'):
            current_font = self.button.font()
            
            if hasattr(self.button, 'isActive') and self.button.isActive:
                pass
            else:
                if hasattr(self, 'original_font_size'):
                    scaled_size = int(self.original_font_size * self._hover_scale)
                    if current_font.pixelSize() != scaled_size:
                        current_font.setPixelSize(scaled_size)
                        self.button.setFont(current_font)
                else:
                    self.original_font_size = current_font.pixelSize()
                    if self.original_font_size <= 0:
                        self.original_font_size = current_font.pointSize()
                        if self.original_font_size <= 0:
                            self.original_font_size = 18
    
    def eventFilter(self, watched, event):
        from PySide6.QtCore import QEvent
        
        if watched == self.button:
            if event.type() == QEvent.Enter:
                self.start_hover_animation()
                return False
            elif event.type() == QEvent.Leave:
                self.start_leave_animation()
                return False
        
        return super().eventFilter(watched, event)
    
    def start_hover_animation(self):
        self.scale_animation.stop()
        self.opacity_animation.stop()
        self.bg_animation.stop()
        
        self.scale_animation.setStartValue(self._hover_scale)
        self.scale_animation.setEndValue(1.03)
        
        self.opacity_animation.setStartValue(self._hover_opacity)
        self.opacity_animation.setEndValue(1.0)
        
        self.bg_animation.setStartValue(self._background_opacity)
        self.bg_animation.setEndValue(1.0)
        
        self.scale_animation.start()
        self.opacity_animation.start()
        self.bg_animation.start()
    
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
            self.opacity_animation.setEndValue(0.8)
        
        self.bg_animation.setStartValue(self._background_opacity)
        self.bg_animation.setEndValue(0.0)
        
        self.scale_animation.start()
        self.opacity_animation.start()
        self.bg_animation.start()

class ParallelAnimation:
    @staticmethod
    def create(animations, duration=None):
        group = QParallelAnimationGroup()
        
        for anim in animations:
            if duration is not None and hasattr(anim, 'setDuration'):
                anim.setDuration(duration)
            group.addAnimation(anim)
        
        return group
    
    @staticmethod
    def sequence(animations, duration=None):
        group = QSequentialAnimationGroup()
        
        for anim in animations:
            if duration is not None and hasattr(anim, 'setDuration'):
                anim.setDuration(duration)
            group.addAnimation(anim)
        
        return group 