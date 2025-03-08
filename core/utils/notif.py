"""
HOW TO USE

# 完整通知
notification = Notification(
    title="自定义标题",
    text="这是通知内容",
    type=NotificationType.TIPS,
    duration=3000
)
notification.show_notification()

# 快速通知
show_info("这是一条提示信息")
show_warning("这是一条警告信息")
show_error("这是一条错误信息")

"""
from PySide6.QtWidgets import (
    QWidget, 
    QLabel, 
    QVBoxLayout, 
    QHBoxLayout, 
    QApplication, 
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import (
    Qt, 
    QTimer, 
    QPoint,
    Signal
)
from PySide6.QtGui import QColor
from core.animations.animation_manager import NotificationAnimation
from core.font.font_pages_manager import FontPagesManager
from core.font.font_manager import FontManager
from core.log.log_manager import log
from enum import Enum, auto

class NotificationType:
    INFO = "Tips"
    TIPS = "提示"
    WARNING = "警告"
    WARN = "Warn"
    ERROR = "错误"
    FAILED = "失败"

# 通知样式映射
NOTIFICATION_STYLES = {
    NotificationType.INFO: ("#1A73E8", "rgba(26, 115, 232, 0.05)", "rgba(26, 115, 232, 0.1)"),
    NotificationType.TIPS: ("#1A73E8", "rgba(26, 115, 232, 0.05)", "rgba(26, 115, 232, 0.1)"),
    NotificationType.WARNING: ("#F9A825", "rgba(249, 168, 37, 0.05)", "rgba(249, 168, 37, 0.1)"),
    NotificationType.WARN: ("#F9A825", "rgba(249, 168, 37, 0.05)", "rgba(249, 168, 37, 0.1)"),
    NotificationType.ERROR: ("#D93025", "rgba(217, 48, 37, 0.05)", "rgba(217, 48, 37, 0.1)"),
    NotificationType.FAILED: ("#D93025", "rgba(217, 48, 37, 0.05)", "rgba(217, 48, 37, 0.1)")
}

# 图标映射
NOTIFICATION_ICONS = {
    NotificationType.INFO: 'info',
    NotificationType.TIPS: 'info',
    NotificationType.WARNING: 'warning',
    NotificationType.WARN: 'warning',
    NotificationType.ERROR: 'error',
    NotificationType.FAILED: 'error'
}

class Notification(QWidget):
    # 类级别的通知队列管理
    active_notifications = []
    animation_finished = Signal()
    
    def __init__(self, text="", title=None, type=NotificationType.TIPS, duration=8000, parent=None):
        super().__init__(parent)
        
        # 创建动画控制器
        self.animation = NotificationAnimation(self)
        # 将动画控制器的animation_finished信号连接到本类的animation_finished信号
        self.animation.animation_finished.connect(self.animation_finished)
        
        # 设置窗口属性
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.Tool | 
            Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # 保存参数
        self.text = text
        self.title = title
        self.notification_type = type
        self.duration = duration
        
        # 保存类型和获取对应的图标
        self.icon_name = NOTIFICATION_ICONS.get(type, 'info')
        
        # 初始化字体管理器
        self.font_manager = FontManager()
        self.font_pages_manager = FontPagesManager()
        
        # 初始化UI
        self._init_ui()
        
        # 创建定时器
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.on_timeout)
        
    def _init_ui(self):
        # 获取通知样式
        text_color, bg_color, hover_color = NOTIFICATION_STYLES.get(
            self.notification_type, 
            NOTIFICATION_STYLES[NotificationType.TIPS]
        )
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        
        # 创建标题和内容标签
        title = self.title if self.title else self.notification_type
        
        # 创建水平布局用于图标和标题
        title_layout = QHBoxLayout()
        title_layout.setSpacing(8)
        
        # 添加图标标签
        self.icon_label = QLabel()
        self.font_manager.apply_icon_font(self.icon_label, 20)
        
        # 设置图标
        self.icon_label.setText(self.font_manager.get_icon_text(self.icon_name))
        self.icon_label.setStyleSheet(f"color: {text_color};")
        
        self.title_label = QLabel(title)
        self.text_label = QLabel(self.text)
        self.text_label.setWordWrap(True)
        
        # 使用字体管理器，调整字体粗细
        self.font_pages_manager.apply_subtitle_style(self.title_label)
        self.title_label.setStyleSheet(f"color: {text_color}; font-weight: 500;")
        
        self.font_pages_manager.apply_normal_style(self.text_label)
        self.text_label.setStyleSheet("color: #333333;")
        
        # 添加图标和标题到水平布局
        title_layout.addWidget(self.icon_label)
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()

        # 创建水平布局用于图标和内容
        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(12, 10, 12, 10)

        # 创建左侧颜色条
        color_bar = QWidget()
        color_bar.setFixedWidth(4)
        color_bar.setStyleSheet(f"""
            background-color: {text_color};
            border-radius: 2px;
        """)
        
        # 创建内容区域
        content_widget = QWidget()
        content_widget_layout = QVBoxLayout(content_widget)
        content_widget_layout.setContentsMargins(0, 0, 0, 0)
        content_widget_layout.setSpacing(4)
        content_widget_layout.addLayout(title_layout) 
        content_widget_layout.addWidget(self.text_label)
        
        # 添加到水平布局
        content_layout.addWidget(color_bar)
        content_layout.addWidget(content_widget, 1)
        
        # 将水平布局添加到主布局
        layout.addLayout(content_layout)
        
        # 设置样式
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border-radius: 12px;
                border: 1px solid rgba(0, 0, 0, 0.08);
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
        """)
        
        # 设置固定宽度和最大高度
        self.setFixedWidth(360)
        self.setMaximumHeight(150)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
    def show_notification(self):
        # 调整大小以适应内容
        self.adjustSize()
        
        # 获取屏幕尺寸
        screen = QApplication.primaryScreen().availableGeometry()
        
        # 计算基础位置
        margin = 20
        start_x = screen.right() - self.width() - margin
        
        # 修改这里：只考虑当前活动的通知数量
        total_height = self.height() + margin
        active_count = len([n for n in Notification.active_notifications if n.isVisible()])
        offset = active_count * total_height
        
        start_y = screen.top() + offset + total_height
        end_y = screen.top() + offset + margin
        
        # 将自己添加到活动通知列表
        Notification.active_notifications.append(self)
        
        # 开始显示动画
        self.animation.show_animation(
            QPoint(start_x, start_y),
            QPoint(start_x, end_y)
        )
        
        # 开始计时
        self.timer.start(self.duration)
        
    def on_timeout(self):
        # 获取当前位置
        current_pos = self.pos()
        end_pos = current_pos + QPoint(self.width() + 20, 0)
        
        # 开始隐藏动画
        self.animation.hide_animation(current_pos, end_pos)
        
        # 从活动通知列表中移除自己
        if self in Notification.active_notifications:
            Notification.active_notifications.remove(self)
            
        # 调整其他通知的位置
        self._adjust_notifications()
        
    def _adjust_notifications(self):
        # 获取屏幕尺寸
        screen = QApplication.primaryScreen().availableGeometry()
        margin = 20
        
        # 重新计算每个通知的位置
        for i, notif in enumerate(n for n in Notification.active_notifications if n.isVisible() and n != self):
            target_y = screen.top() + margin + i * (notif.height() + margin)
            if notif.y() != target_y:
                notif.animation.show_animation(
                    notif.pos(),
                    QPoint(notif.x(), target_y)
                )

def show_info(text, duration=3000):
    notification = Notification(text=text, type=NotificationType.INFO, duration=duration)
    notification.show_notification()
    
def show_warning(text, duration=3000):
    notification = Notification(text=text, type=NotificationType.WARNING, duration=duration)
    notification.show_notification()
    
def show_error(text, duration=3000):
    notification = Notification(text=text, type=NotificationType.ERROR, duration=duration)
    notification.show_notification()
