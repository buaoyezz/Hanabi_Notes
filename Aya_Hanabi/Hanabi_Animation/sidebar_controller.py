from PySide6.QtCore import QObject, QTimer, QPoint, QRect, QEasingCurve
from PySide6.QtGui import QCursor
from .animation_manager import AnimationManager, AnimationConfig

class SidebarController(QObject):
    def __init__(self, sidebar, parent=None):
        super().__init__(parent)
        self.sidebar = sidebar
        self.animation_manager = AnimationManager(self)
        
        # 启用硬件加速
        self.animation_manager.set_hardware_acceleration(True)
        
        # 状态管理
        self.is_expanded = True
        self.hover_active = False
        self.is_animating = False
        
        # 配置参数
        self.collapsed_width = 0
        self.expanded_width = 60
        self.hover_delay = 100
        self.auto_collapse_delay = 3000
        
        # 定时器
        self.hover_timer = QTimer(self)
        self.hover_timer.setSingleShot(True)
        self.hover_timer.timeout.connect(self.handle_hover_timeout)
        
        self.auto_collapse_timer = QTimer(self)
        self.auto_collapse_timer.setSingleShot(True)
        self.auto_collapse_timer.timeout.connect(self.collapse)
        
        # 初始化动画
        self._setup_animations()
        
    def _setup_animations(self):
        # 创建展开动画
        expand_anim = self.animation_manager.create_animation(
            self.sidebar, b"geometry",
            None, None,  # 值会在运行时设置
            duration=AnimationConfig.SIDEBAR_EXPAND['duration'],
            easing=AnimationConfig.SIDEBAR_EXPAND['easing'],
            cache_key="sidebar_expand"
        )
        expand_anim.finished.connect(self._on_expand_finished)
        self.animation_manager.register_animation("expand", expand_anim)
        
        # 创建收起动画
        collapse_anim = self.animation_manager.create_animation(
            self.sidebar, b"geometry",
            None, None,  # 值会在运行时设置
            duration=AnimationConfig.SIDEBAR_COLLAPSE['duration'],
            easing=AnimationConfig.SIDEBAR_COLLAPSE['easing'],
            cache_key="sidebar_collapse"
        )
        collapse_anim.finished.connect(self._on_collapse_finished)
        self.animation_manager.register_animation("collapse", collapse_anim)
        
    def configure(self, collapsed_width=0, expanded_width=60,
                hover_delay=100, auto_collapse_delay=3000):
        self.collapsed_width = collapsed_width
        self.expanded_width = expanded_width
        self.hover_delay = hover_delay
        self.auto_collapse_delay = auto_collapse_delay
        
    def expand(self):
        if not self.is_expanded and not self.is_animating:
            self.is_animating = True
            
            # 停止所有正在运行的动画
            self.animation_manager.stop_all_animations()
            
            # 准备动画
            current_rect = self.sidebar.geometry()
            target_rect = current_rect.adjusted(0, 0, 
                                             self.expanded_width - current_rect.width(), 0)
            
            # 获取展开动画
            anim = self.animation_manager.get_animation("expand")
            anim.setStartValue(current_rect)
            anim.setEndValue(target_rect)
            
            # 设置初始宽度并启动动画
            self.sidebar.setFixedWidth(1)
            anim.start()
            
    def collapse(self):
        if self.is_expanded and not self.is_animating and not self.hover_active:
            # 检查鼠标是否在侧边栏区域
            if self._is_mouse_over_sidebar():
                return
                
            self.is_animating = True
            
            # 停止所有正在运行的动画
            self.animation_manager.stop_all_animations()
            
            # 准备动画
            current_rect = self.sidebar.geometry()
            target_rect = current_rect.adjusted(0, 0,
                                             self.collapsed_width - current_rect.width(), 0)
            
            # 获取收起动画
            anim = self.animation_manager.get_animation("collapse")
            anim.setStartValue(current_rect)
            anim.setEndValue(target_rect)
            
            # 启动动画
            anim.start()
            
    def _on_expand_finished(self):
        self.is_expanded = True
        self.is_animating = False
        self.sidebar.setFixedWidth(self.expanded_width)
        
    def _on_collapse_finished(self):
        self.is_expanded = False
        self.is_animating = False
        self.sidebar.setFixedWidth(self.collapsed_width)
        
    def handle_mouse_enter(self):
        self.hover_active = True
        self.auto_collapse_timer.stop()
        
        if not self.is_expanded and not self.is_animating:
            self.hover_timer.start(self.hover_delay)
            
    def handle_mouse_leave(self):
        self.hover_active = False
        self.hover_timer.stop()
        
        if self.is_expanded and not self.is_animating:
            self.auto_collapse_timer.start(self.auto_collapse_delay)
            
    def handle_hover_timeout(self):
        if self.hover_active and not self.is_expanded and not self.is_animating:
            self.expand()
            
    def _is_mouse_over_sidebar(self):
        global_pos = QCursor.pos()
        sidebar_global_pos = self.sidebar.mapToGlobal(QPoint(0, 0))
        sidebar_global_rect = QRect(sidebar_global_pos, self.sidebar.size())
        return sidebar_global_rect.contains(global_pos)
        
    def cleanup(self):
        # 清理资源
        self.animation_manager.stop_all_animations()
        self.animation_manager.clear_cache()
        self.hover_timer.stop()
        self.auto_collapse_timer.stop() 