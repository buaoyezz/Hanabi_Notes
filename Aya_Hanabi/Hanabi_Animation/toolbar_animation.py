from PySide6.QtCore import (QPropertyAnimation, QEasingCurve, QObject, 
                       Property, QTimer, QPoint, QParallelAnimationGroup, 
                       QSequentialAnimationGroup, Qt)
from PySide6.QtWidgets import QWidget

class ToolbarAnimation:
    
    @staticmethod
    def slide_horizontal(widget, start_width, end_width, duration=350, ease_type=QEasingCurve.OutCubic):
        animation = QPropertyAnimation(widget, b"minimumWidth")
        animation.setDuration(duration)
        animation.setStartValue(start_width)
        animation.setEndValue(end_width)
        animation.setEasingCurve(ease_type)
        
        max_width_animation = QPropertyAnimation(widget, b"maximumWidth")
        max_width_animation.setDuration(duration)
        max_width_animation.setStartValue(start_width)
        max_width_animation.setEndValue(end_width)
        max_width_animation.setEasingCurve(ease_type)
        
        group = QParallelAnimationGroup()
        group.addAnimation(animation)
        group.addAnimation(max_width_animation)
        
        return group
    
    @staticmethod
    def expand_sidebar(sidebar, collapsed_width=0, expanded_width=60, duration=350):
        curve = QEasingCurve(QEasingCurve.OutBack)
        curve.setOvershoot(1.02)
        
        animation = ToolbarAnimation.slide_horizontal(
            sidebar, 
            collapsed_width, 
            expanded_width, 
            duration,
            curve
        )
        
        # 不使用透明度动画，而是使用颜色变化来提示变化
        if hasattr(sidebar, 'actionBar') and sidebar.actionBar and False:  # 禁用此效果
            # 使用QTimer模拟视觉效果，避免使用透明度
            def highlight_effect():
                sidebar.actionBar.setStyleSheet("background-color: #0069a3;")
                QTimer.singleShot(300, lambda: sidebar.actionBar.setStyleSheet("background-color: #005780;"))
            
            # 延迟执行突出效果
            QTimer.singleShot(int(duration * 0.2), highlight_effect)
        
        # 如果有标签按钮，添加级联显示动画 - 不使用透明度
        if hasattr(sidebar, 'tabButtons') and sidebar.tabButtons and False:  # 禁用此效果
            for i, btn in enumerate(sidebar.tabButtons):
                # 创建延迟的级联动画 - 使用背景色代替透明度
                delay = i * int(duration * 0.08)
                
                def highlight_button(button=btn):
                    # 使用背景色变化替代透明度
                    current_style = button.styleSheet()
                    highlight_style = current_style.replace("background-color: transparent", 
                                                         "background-color: rgba(255, 255, 255, 0.2)")
                    button.setStyleSheet(highlight_style)
                    QTimer.singleShot(300, lambda: button.updateStyle())
                
                QTimer.singleShot(delay, highlight_button)
        
        return animation
    
    @staticmethod
    def collapse_sidebar(sidebar, collapsed_width=0, expanded_width=60, duration=300):
        curve = QEasingCurve(QEasingCurve.InOutQuad)
        
        animation = ToolbarAnimation.slide_horizontal(
            sidebar, 
            expanded_width, 
            collapsed_width, 
            duration,
            curve
        )
        
        return animation

class SidebarActionManager:
    
    def __init__(self, sidebar):
        self.sidebar = sidebar
        self.current_animation = None
        self.hover_timer = QTimer()
        self.hover_timer.setSingleShot(True)
        self.hover_timer.timeout.connect(self.handle_hover_timeout)
        
        self.is_expanded = True
        self.hover_active = False
        
        self.collapsed_width = 0
        self.expanded_width = 60
        self.expand_duration = 350
        self.collapse_duration = 300
        self.hover_delay = 300
        self.auto_collapse_delay = 2000
    
    def configure(self, collapsed_width=0, expanded_width=60, 
                expand_duration=350, collapse_duration=300,
                hover_delay=300, auto_collapse_delay=2000):
        self.collapsed_width = collapsed_width
        self.expanded_width = expanded_width
        self.expand_duration = expand_duration
        self.collapse_duration = collapse_duration
        self.hover_delay = hover_delay
        self.auto_collapse_delay = auto_collapse_delay
    
    def expand(self):
        if not self.is_expanded:
            if self.current_animation and self.current_animation.state() == QPropertyAnimation.Running:
                self.current_animation.stop()
            
            self.sidebar.setAttribute(Qt.WA_OpaquePaintEvent, True)
            self.sidebar.setAttribute(Qt.WA_TranslucentBackground, False)
            
            self.original_style = self.sidebar.styleSheet()
            
            self.sidebar.setFixedWidth(self.collapsed_width)
            self.current_animation = ToolbarAnimation.expand_sidebar(
                self.sidebar,
                self.collapsed_width,
                self.expanded_width,
                self.expand_duration
            )
            
            self.current_animation.finished.connect(self.on_expand_finished)
            self.current_animation.start()
    
    def collapse(self):
        if self.is_expanded and not self.hover_active:
            if self.current_animation and self.current_animation.state() == QPropertyAnimation.Running:
                self.current_animation.stop()
            
            self.sidebar.setAttribute(Qt.WA_OpaquePaintEvent, True)
            self.sidebar.setAttribute(Qt.WA_TranslucentBackground, False)
            
            if not hasattr(self, 'original_style'):
                self.original_style = self.sidebar.styleSheet()
            
            self.current_animation = ToolbarAnimation.collapse_sidebar(
                self.sidebar,
                self.collapsed_width,
                self.expanded_width,
                self.collapse_duration
            )
            
            self.current_animation.finished.connect(self.on_collapse_finished)
            self.current_animation.start()
    
    def on_expand_finished(self):
        self.is_expanded = True
        self.sidebar.setFixedWidth(self.expanded_width)
        
        if hasattr(self.sidebar, "refreshBackground"):
            self.sidebar.refreshBackground()
        elif hasattr(self, 'original_style'):
            self.sidebar.setStyleSheet(self.original_style)
    
    def on_collapse_finished(self):
        self.is_expanded = False
        self.sidebar.setFixedWidth(self.collapsed_width)
        
        if hasattr(self, 'original_style'):
            self.sidebar.setStyleSheet(self.original_style)
    
    def handle_mouse_enter(self):
        self.hover_active = True
        if hasattr(self, 'auto_collapse_timer') and self.auto_collapse_timer.isActive():
            self.auto_collapse_timer.stop()
        
        if not self.is_expanded:
            self.hover_timer.start(self.hover_delay)
    
    def handle_mouse_leave(self):
        self.hover_active = False
        if self.hover_timer.isActive():
            self.hover_timer.stop()
        
        if self.is_expanded:
            if not hasattr(self, 'auto_collapse_timer'):
                self.auto_collapse_timer = QTimer()
                self.auto_collapse_timer.setSingleShot(True)
                self.auto_collapse_timer.timeout.connect(self.collapse)
            
            self.auto_collapse_timer.start(self.auto_collapse_delay)
    
    def handle_hover_timeout(self):
        if self.hover_active and not self.is_expanded:
            self.expand()
