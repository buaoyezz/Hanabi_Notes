import sys
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QApplication, QGraphicsDropShadowEffect,
                             QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize, Property, Signal, QRect, QPoint
from PySide6.QtGui import QColor, QPainter, QPainterPath, QFont, QIcon, QCursor
from Aya_Hanabi.Hanabi_Core.FontManager.fontManager import FontManager, IconProvider, ICONS

class HanabiMessageBox(QDialog):
    # 按钮类型
    Ok = 0
    OkCancel = 1
    YesNo = 2
    YesNoCancel = 3
    
    # 消息类型
    Information = 0
    Warning = 1
    Error = 2
    Question = 3
    Success = 4
    
    # 返回结果
    Ok_Result = 0
    Cancel_Result = 1
    Yes_Result = 2
    No_Result = 3
    
    def __init__(self, parent=None, title="消息", text="", message_type=Information, 
                 button_type=Ok, width=400, height=200):
        super().__init__(parent)
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.result_value = self.Cancel_Result
        
        self.default_width = width
        self.default_height = height
        
        self.resize(width, height)
        
        IconProvider.init_font()
        
        self.font_family = self.get_font_family(parent)
        
        # 颜色配置 - 将从主题中加载
        self.theme_colors = self.get_theme_colors(parent)
        
        self.color_scheme = {
            self.Information: {"icon": "info", "color": QColor(33, 150, 243)},
            self.Warning: {"icon": "warning", "color": QColor(255, 152, 0)},
            self.Error: {"icon": "error", "color": QColor(244, 67, 54)},
            self.Question: {"icon": "help", "color": QColor(156, 39, 176)},
            self.Success: {"icon": "check_circle", "color": QColor(76, 175, 80)}
        }
        
        self.setup_ui(title, text, message_type, button_type)
        
        self.add_shadow_effect()
        
        self.setup_animations()
        
        # 初始化拖动状态变量
        self.dragging = False
        self.drag_position = None
    
    def get_theme_colors(self, parent):
        """从父窗口或应用程序设置中获取主题颜色"""
        # 默认颜色配置
        theme_colors = {
            "background": "#ffffff",
            "text": "#212121",
            "secondary_text": "#757575",
            "dialog_background": "#ffffff",
            "dialog_text": "#212121",
            "dialog_border": "#e0e0e0"
        }
        
        # 尝试从父窗口获取主题
        if parent and hasattr(parent, 'themeManager') and parent.themeManager:
            if hasattr(parent.themeManager, 'current_theme'):
                # 获取当前主题颜色
                theme = parent.themeManager.current_theme
                is_dark = False
                
                if hasattr(parent.themeManager, 'current_theme_name'):
                    is_dark = parent.themeManager.current_theme_name in ["dark", "purple_dream", "green_theme"]
                
                if is_dark:
                    # 暗色主题
                    theme_colors = {
                        "background": theme.get("editor.bg_color", "#1e1e1e"),
                        "text": theme.get("editor.text_color", "#f3f3f3"),
                        "secondary_text": theme.get("editor.comment_color", "#a0a0a0"),
                        "dialog_background": theme.get("app.bg_color", "#2d2d30"),
                        "dialog_text": theme.get("app.text_color", "#f3f3f3"),
                        "dialog_border": theme.get("app.border_color", "#3f3f46")
                    }
                else:
                    # 亮色主题
                    theme_colors = {
                        "background": theme.get("editor.bg_color", "#ffffff"),
                        "text": theme.get("editor.text_color", "#212121"),
                        "secondary_text": theme.get("editor.comment_color", "#757575"),
                        "dialog_background": theme.get("app.bg_color", "#ffffff"),
                        "dialog_text": theme.get("app.text_color", "#212121"),
                        "dialog_border": theme.get("app.border_color", "#e0e0e0")
                    }
        
        return theme_colors
    
    def get_font_family(self, parent):
        font_family = "Microsoft YaHei"
        
        if parent and hasattr(parent, 'font_family'):
            font_family = parent.font_family
        else:
            try:
                import os
                import json
                settings_dir = os.path.join(os.path.expanduser("~"), ".hanabi_notes")
                settings_file = os.path.join(settings_dir, "settings.json")
                
                if os.path.exists(settings_file):
                    with open(settings_file, 'r', encoding='utf-8') as f:
                        settings = json.load(f)
                    
                    if "editor" in settings and "font" in settings["editor"]:
                        font_settings = settings["editor"]["font"]
                        if "family" in font_settings:
                            font_family = font_settings["family"]
            except Exception as e:
                print(f"读取字体设置时出错: {e}")
        
        return font_family
    
    def setup_ui(self, title, text, message_type, button_type):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        font = FontManager.get_font(self.font_family, 14)
        self.setFont(font)
        
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        if message_type in self.color_scheme and "icon" in self.color_scheme[message_type]:
            icon_name = self.color_scheme[message_type]["icon"]
            if IconProvider.get_icon(icon_name):
                icon_label = QLabel()
                icon_font = IconProvider.get_icon_font(18)
                icon_label.setFont(icon_font)
                icon_label.setText(IconProvider.get_icon(icon_name))
                icon_label.setStyleSheet(f"""
                    color: {self.color_scheme[message_type]['color'].name()};
                    margin-right: 8px;
                """)
                title_layout.addWidget(icon_label)
        
        self.title_label = QLabel(title)
        title_font = FontManager.get_font(self.font_family, 16, bold=True)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet(f"""
            color: {self.color_scheme[message_type]['color'].name()};
        """)
        title_layout.addWidget(self.title_label)
        
        title_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        self.close_button = QPushButton()
        icon_font = IconProvider.get_icon_font(16)
        self.close_button.setFont(icon_font)
        self.close_button.setText(IconProvider.get_icon("close"))
        self.close_button.setStyleSheet(f"""
            QPushButton {{
                border: none;
                color: {self.theme_colors['secondary_text']};
                background-color: transparent;
            }}
            QPushButton:hover {{
                color: {self.theme_colors['text']};
            }}
            QPushButton:pressed {{
                color: {self.theme_colors['secondary_text']};
            }}
        """)
        self.close_button.setFixedSize(30, 30)
        self.close_button.clicked.connect(self.reject)
        title_layout.addWidget(self.close_button)
        
        main_layout.addLayout(title_layout)
        
        self.separator = QLabel()
        self.separator.setFixedHeight(1)
        self.separator.setStyleSheet(f"background-color: {self.color_scheme[message_type]['color'].name()}; margin: 0px 0px;")
        main_layout.addWidget(self.separator)
        
        self.text_label = QLabel(text)
        content_font = FontManager.get_font(self.font_family, 14)
        self.text_label.setFont(content_font)
        self.text_label.setWordWrap(True)
        self.text_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.text_label.setStyleSheet(f"""
            color: {self.theme_colors['text']};
            margin: 10px 5px;
        """)
        main_layout.addWidget(self.text_label)
        
        main_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)
        
        button_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        btn_font = FontManager.get_font(self.font_family, 14, bold=True)
        
        self.button_style = f"""
            QPushButton {{
                background-color: {self.color_scheme[message_type]['color'].name()};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.color_scheme[message_type]['color'].lighter(110).name()};
            }}
            QPushButton:pressed {{
                background-color: {self.color_scheme[message_type]['color'].darker(110).name()};
            }}
            QPushButton[flat="true"] {{
                background-color: transparent;
                color: {self.color_scheme[message_type]['color'].name()};
            }}
            QPushButton[flat="true"]:hover {{
                background-color: rgba(0, 0, 0, 0.05);
            }}
            QPushButton[flat="true"]:pressed {{
                background-color: rgba(0, 0, 0, 0.1);
            }}
        """
        
        if button_type == self.OkCancel:
            self.cancel_button = QPushButton("取消")
            self.cancel_button.setProperty("flat", True)
            self.cancel_button.setStyleSheet(self.button_style)
            self.cancel_button.clicked.connect(self.handle_cancel)
            button_layout.addWidget(self.cancel_button)
            
            self.ok_button = QPushButton("确定")
            self.ok_button.setStyleSheet(self.button_style)
            self.ok_button.clicked.connect(self.handle_ok)
            button_layout.addWidget(self.ok_button)
            
        elif button_type == self.YesNo:
            self.no_button = QPushButton("否")
            self.no_button.setProperty("flat", True)
            self.no_button.setStyleSheet(self.button_style)
            self.no_button.clicked.connect(self.handle_no)
            button_layout.addWidget(self.no_button)
            
            self.yes_button = QPushButton("是")
            self.yes_button.setStyleSheet(self.button_style)
            self.yes_button.clicked.connect(self.handle_yes)
            button_layout.addWidget(self.yes_button)
            
        elif button_type == self.YesNoCancel:
            self.cancel_button = QPushButton("取消")
            self.cancel_button.setProperty("flat", True)
            self.cancel_button.setStyleSheet(self.button_style)
            self.cancel_button.clicked.connect(self.handle_cancel)
            button_layout.addWidget(self.cancel_button)
            
            self.no_button = QPushButton("否")
            self.no_button.setProperty("flat", True)
            self.no_button.setStyleSheet(self.button_style)
            self.no_button.clicked.connect(self.handle_no)
            button_layout.addWidget(self.no_button)
            
            self.yes_button = QPushButton("是")
            self.yes_button.setStyleSheet(self.button_style)
            self.yes_button.clicked.connect(self.handle_yes)
            button_layout.addWidget(self.yes_button)
            
        else:  # Ok (默认)
            self.ok_button = QPushButton("确定")
            self.ok_button.setStyleSheet(self.button_style)
            self.ok_button.clicked.connect(self.handle_ok)
            button_layout.addWidget(self.ok_button)
        
        main_layout.addLayout(button_layout)
    
    def add_shadow_effect(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
    
    def setup_animations(self):
        self.opacity = 0.0
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(200)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self.scale_animation = QPropertyAnimation(self, b"geometry")
        self.scale_animation.setDuration(200)
        self.scale_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def showEvent(self, event):
        super().showEvent(event)
        
        # 计算对话框在屏幕上的位置
        center_point = QPoint()
        
        # 优先使用父窗口中心点
        if self.parent():
            parent_rect = self.parent().geometry()
            center_point = parent_rect.center()
        else:
            # 如果没有父窗口，则使用当前屏幕的中心点
            center_point = QCursor.pos()
            # 如果鼠标位置不可靠，则使用屏幕中心
            if center_point.x() == 0 and center_point.y() == 0:
                screen = QApplication.primaryScreen().geometry()
                center_point = screen.center()
        
        # 根据对话框大小计算左上角位置
        x = center_point.x() - self.width() // 2
        y = center_point.y() - self.height() // 2
        
        # 确保对话框在屏幕内
        screen = QApplication.primaryScreen().geometry()
        if x < screen.left():
            x = screen.left() + 10
        elif x + self.width() > screen.right():
            x = screen.right() - self.width() - 10
            
        if y < screen.top():
            y = screen.top() + 10
        elif y + self.height() > screen.bottom():
            y = screen.bottom() - self.height() - 10
        
        self.move(x, y)
        
        # 启动动画
        self.animation.start()
        
        start_rect = QRect(center_point.x() - 10, center_point.y() - 10, 20, 20)
        end_rect = QRect(x, y, self.width(), self.height())
        
        self.scale_animation.setStartValue(start_rect)
        self.scale_animation.setEndValue(end_rect)
        self.scale_animation.start()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 10, 10)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(self.theme_colors['dialog_background']))
        painter.drawPath(path)
    
    # 添加鼠标事件处理以支持拖动
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 检查鼠标是否点击了对话框的标题区域（上边缘30像素范围）
            if event.position().y() <= 30:
                self.dragging = True
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
        
        super().mouseReleaseEvent(event)
    
    def handle_ok(self):
        self.result_value = self.Ok_Result
        self.accept()
    
    def handle_cancel(self):
        self.result_value = self.Cancel_Result
        self.reject()
    
    def handle_yes(self):
        self.result_value = self.Yes_Result
        self.accept()
    
    def handle_no(self):
        self.result_value = self.No_Result
        self.reject()
    
    def get_result(self):
        return self.result_value

def information(parent, title, text):
    dialog = HanabiMessageBox(parent, title, text, HanabiMessageBox.Information)
    dialog.exec_()
    return dialog.get_result()

def warning(parent, title, text):
    dialog = HanabiMessageBox(parent, title, text, HanabiMessageBox.Warning)
    dialog.exec_()
    return dialog.get_result()

def critical(parent, title, text):
    dialog = HanabiMessageBox(parent, title, text, HanabiMessageBox.Error)
    dialog.exec_()
    return dialog.get_result()

def question(parent, title, text, buttons=HanabiMessageBox.YesNo):
    dialog = HanabiMessageBox(parent, title, text, HanabiMessageBox.Question, buttons)
    dialog.exec_()
    return dialog.get_result()

def success(parent, title, text):
    dialog = HanabiMessageBox(parent, title, text, HanabiMessageBox.Success)
    dialog.exec_()
    return dialog.get_result()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    information(None, "信息提示", "这是一个信息消息框\n用于显示一般性的提示信息")
    
    warning(None, "警告提示", "这是一个警告消息框\n用于警告用户注意某些潜在问题")
    
    critical(None, "错误提示", "这是一个错误消息框\n用于通知用户发生了严重错误")
    
    result = question(None, "确认操作", "确定要执行此操作吗？\n此操作可能需要一些时间完成。")
    print(f"用户选择: {'是' if result == HanabiMessageBox.Yes_Result else '否'}")
    
    result = question(None, "保存更改", "是否保存更改？\n选择<否>将丢弃所有更改。", HanabiMessageBox.YesNoCancel)
    if result == HanabiMessageBox.Yes_Result:
        print("用户选择: 是")
    elif result == HanabiMessageBox.No_Result:
        print("用户选择: 否")
    else:
        print("用户选择: 取消")
    
    success(None, "操作成功", "操作已成功完成！\n所有更改已保存。")
    
    dialog = HanabiMessageBox(None, "确定/取消", "这是一个带有确定和取消按钮的消息框", HanabiMessageBox.Information, HanabiMessageBox.OkCancel)
    dialog.exec_()
    
    print("所有测试完成!")
    
    sys.exit(0)
