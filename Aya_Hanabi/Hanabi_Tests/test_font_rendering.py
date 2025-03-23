import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

class FontTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("字体渲染测试")
        self.setMinimumSize(600, 400)
        
        # 创建中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        
        # 测试的字体列表
        self.test_fonts = [
            "STHupo",  # 华文琥珀
            "华文琥珀",
            "SimHei",  # 黑体
            "Microsoft YaHei",  # 微软雅黑
            "Consolas",
            "Arial"
        ]
        
        # 测试文本
        self.test_text = "AaBbCcXxYyZz 1234567890 花火笔记，随你四季"
        
        # 为每种字体创建标签
        for font_name in self.test_fonts:
            # 标题标签
            title_label = QLabel(f"字体测试: {font_name}")
            layout.addWidget(title_label)
            
            # 普通方式设置字体
            normal_label = QLabel(self.test_text)
            font = QFont(font_name, 14)
            normal_label.setFont(font)
            layout.addWidget(normal_label)
            
            # 样式表方式设置字体
            css_label = QLabel(self.test_text)
            css_label.setStyleSheet(f"""
                font-family: "{font_name}";
                font-size: 14pt;
            """)
            layout.addWidget(css_label)
            
            # 两种方式结合
            combined_label = QLabel(self.test_text)
            combined_label.setFont(font)
            combined_label.setStyleSheet(f"""
                font-family: "{font_name}";
                font-size: 14pt;
            """)
            layout.addWidget(combined_label)
            
            # 分隔线
            separator = QLabel()
            separator.setStyleSheet("background-color: #333; min-height: 1px;")
            layout.addWidget(separator)
        
        # 刷新按钮
        refresh_button = QPushButton("强制刷新")
        refresh_button.clicked.connect(self.force_refresh)
        layout.addWidget(refresh_button)
    
    def force_refresh(self):
        """强制刷新所有标签"""
        for i in range(self.centralWidget().layout().count()):
            widget = self.centralWidget().layout().itemAt(i).widget()
            if isinstance(widget, QLabel) and widget.text() == self.test_text:
                current_text = widget.text()
                widget.setText("")
                widget.setText(current_text)
                widget.update()
                widget.repaint()
        
        # 强制处理事件
        QApplication.processEvents()
        print("已强制刷新所有字体标签")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FontTestWindow()
    window.show()
    sys.exit(app.exec()) 