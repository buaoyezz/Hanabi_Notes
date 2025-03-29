import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QComboBox, QVBoxLayout, QWidget, QLabel, QRadioButton
from Aya_Hanabi.Hanabi_Core.ThemeManager.themeManager import ThemeManager
from Aya_Hanabi.Hanabi_Page.SettingsPages import OfficeStyleSettingsDialog

class TestComboBox(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ComboBox测试")
        layout = QVBoxLayout(self)
        
        # 测试普通ComboBox
        layout.addWidget(QLabel("测试普通ComboBox:"))
        simple_combo = QComboBox()
        simple_combo.addItem("测试项1")
        simple_combo.addItem("测试项2")
        simple_combo.addItem("测试项3")
        layout.addWidget(simple_combo)
        
        # 测试带userData的ComboBox
        layout.addWidget(QLabel("测试带userData的ComboBox:"))
        data_combo = QComboBox()
        data_combo.addItem("显示名1", "data1")
        data_combo.addItem("显示名2", "data2")
        data_combo.addItem("显示名3", "data3")
        layout.addWidget(data_combo)

class TestRadioButtons(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("单选按钮测试")
        layout = QVBoxLayout(self)
        
        # 添加说明
        layout.addWidget(QLabel("单选按钮测试:"))
        
        # 创建几个单选按钮
        for i in range(1, 5):
            radio = QRadioButton(f"测试选项 {i}")
            radio.setStyleSheet("""
                QRadioButton {
                    color: #333333;
                    font-size: 14px;
                    padding: 5px;
                }
                QRadioButton::indicator {
                    width: 15px;
                    height: 15px;
                }
            """)
            layout.addWidget(radio)
            
            # 默认选中第一个
            if i == 1:
                radio.setChecked(True)

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("主题测试")
        self.resize(1000, 800)
        
        # 创建主题管理器
        self.themeManager = ThemeManager()
        self.themeManager.load_themes_from_directory()
        
        # 打印所有主题
        print("加载的主题:")
        for theme_name, display_name in self.themeManager.get_all_themes():
            print(f"  - {theme_name}: {display_name}")
        
        # 测试ComboBox
        self.combo_test = TestComboBox()
        self.combo_test.show()
        
        # 测试单选按钮
        self.radio_test = TestRadioButtons()
        self.radio_test.show()
        
        # 打开设置对话框
        self.openSettings()
        
    def openSettings(self):
        dialog = OfficeStyleSettingsDialog(self)
        # 连接信号
        dialog.themeChanged.connect(self.onThemeChanged)
        dialog.exec()
    
    def onThemeChanged(self, theme_name):
        print(f"主题已更改为: {theme_name}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec()) 