from PySide6.QtWidgets import QComboBox, QLabel
from PySide6.QtCore import Qt, QEvent

class WhiteComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)  # 允许获取焦点
        
        # 延迟导入FontManager和FontPagesManager
        from core.font.font_manager import FontManager
        from core.font.font_pages_manager import FontPagesManager
        self.font_manager = FontManager()
        self.font_pages_manager = FontPagesManager()
        
        # 创建下拉箭头图标
        self.arrow_label = QLabel(self)
        self.arrow_label.setText(self.font_pages_manager.get_icon_text('expand_more'))
        self.font_manager.apply_icon_font(self.arrow_label, 20)  # 使用FontManager应用图标字体
        self.arrow_label.setStyleSheet("color: #757575;")
        
        self.setup_ui()
        
        # 确保事件过滤器正确安装
        self.installEventFilter(self)
        
    def setup_ui(self):
        # 应用字体
        self.font_pages_manager.apply_normal_style(self)
        
        # 设置基础样式
        self.setStyleSheet("""
            QComboBox {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 5px 30px 5px 10px;
                background: white;
                min-height: 20px;
            }
            QComboBox:hover {
                border-color: #2196F3;
            }
            QComboBox:focus {
                border-color: #2196F3;
                border-width: 2px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                background: white;
                selection-background-color: #F5F5F5;
            }
        """)
        
        # 调整箭头标签位置
        self.arrow_label.setFixedSize(20, 20)
        self.arrow_label.move(self.width() - 28, (self.height() - 20) // 2)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 当控件大小改变时，重新调整箭头位置
        self.arrow_label.move(self.width() - 28, (self.height() - 20) // 2)
        
    def showPopup(self):
        # 在显示下拉框前，确保箭头图标字体正确
        self.font_manager.apply_icon_font(self.arrow_label, 20)
        super().showPopup()
        
    def hidePopup(self):
        # 确保下拉框正常隐藏
        super().hidePopup()
        
    def eventFilter(self, obj, event):
        # 处理鼠标点击事件，确保下拉框可以正常展开
        if obj == self and event.type() == QEvent.MouseButtonPress:
            # 确保点击事件能够正常触发下拉框的展开和收起
            return False  # 不拦截事件，让事件继续传递
        
        # 处理焦点事件
        if obj == self and event.type() == QEvent.FocusIn:
            # 当获得焦点时，更新样式
            self.setStyleSheet("""
                QComboBox {
                    border: 2px solid #2196F3;
                    border-radius: 4px;
                    padding: 5px 30px 5px 10px;
                    background: white;
                    min-height: 20px;
                }
                QComboBox::drop-down {
                    border: none;
                }
                QComboBox::down-arrow {
                    image: none;
                }
                QComboBox QAbstractItemView {
                    border: 1px solid #E0E0E0;
                    border-radius: 4px;
                    background: white;
                    selection-background-color: #F5F5F5;
                }
            """)
            # 确保箭头图标字体正确
            self.font_manager.apply_icon_font(self.arrow_label, 20)
            return False
        
        # 处理失去焦点事件
        if obj == self and event.type() == QEvent.FocusOut:
            # 恢复默认样式
            self.setStyleSheet("""
                QComboBox {
                    border: 1px solid #E0E0E0;
                    border-radius: 4px;
                    padding: 5px 30px 5px 10px;
                    background: white;
                    min-height: 20px;
                }
                QComboBox:hover {
                    border-color: #2196F3;
                }
                QComboBox::drop-down {
                    border: none;
                }
                QComboBox::down-arrow {
                    image: none;
                }
                QComboBox QAbstractItemView {
                    border: 1px solid #E0E0E0;
                    border-radius: 4px;
                    background: white;
                    selection-background-color: #F5F5F5;
                }
            """)
            return False
        
        # 处理基本事件
        return super().eventFilter(obj, event)