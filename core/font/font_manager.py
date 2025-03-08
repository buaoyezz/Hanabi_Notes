from PySide6.QtGui import QFont, QFontDatabase, QColor
from PySide6.QtWidgets import QWidget, QApplication, QLabel, QPushButton, QComboBox
from PySide6.QtCore import Qt, QThread, Signal
import platform
import re
import os
import sys
from core.log.log_manager import log
from .icon_map import ICON_MAP
from core.thread.thread_manager import thread_manager
from core.ui.white_combox import WhiteComboBox

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        # Anti Packaged
        base_path = sys._MEIPASS
    else:
        # Dev
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class FontLoaderThread(QThread):
    finished = Signal(dict)  # 修改为返回字典，包含更多信息
    progress = Signal(str, int)  # 添加进度百分比
    
    def __init__(self, fonts_to_load):
        super().__init__()
        self.fonts_to_load = fonts_to_load
        
    def run(self):
        font_db = QFontDatabase()
        loaded_fonts = {}
        total = len(self.fonts_to_load)
        
        def load_single_font(font_path, font_name):
            try:
                if os.path.exists(font_path):
                    font_id = font_db.addApplicationFont(font_path)
                    if font_id >= 0:
                        return {
                            'success': True,
                            'name': font_name,
                            'id': font_id,
                            'families': font_db.applicationFontFamilies(font_id)
                        }
                return {'success': False, 'name': font_name, 'error': '字体文件不存在'}
            except Exception as e:
                return {'success': False, 'name': font_name, 'error': str(e)}

        # 创建任务列表
        tasks = {}
        for i, (font_path, font_name) in enumerate(self.fonts_to_load):
            task_id = f"font_load_{font_name}_{i}"
            future = thread_manager.submit_task(
                task_id,
                load_single_font,
                font_path,
                font_name
            )
            tasks[task_id] = (future, font_name)
            self.progress.emit(f"提交字体加载任务: {font_name}", int((i + 1) * 50 / total))

        # 收集结果
        for i, (task_id, (future, font_name)) in enumerate(tasks.items()):
            try:
                result = future.result(timeout=3)  # 3秒超时
                loaded_fonts[font_name] = result
                self.progress.emit(
                    f"完成字体加载: {font_name}", 
                    int(50 + (i + 1) * 50 / total)
                )
            except Exception as e:
                loaded_fonts[font_name] = {
                    'success': False,
                    'name': font_name,
                    'error': f'加载超时: {str(e)}'
                }
                
        self.finished.emit(loaded_fonts)

class FontManager:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FontManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not FontManager._initialized:
            super().__init__()
            self.current_font = None
            self.system_fonts = []
            self.icon_font_id = -1
            self.font_db = QFontDatabase()  # 初始化字体数据库
            self._init_system_fonts()
            self._init_icon_font()
            FontManager._initialized = True
            
    def _init_system_fonts(self):
        """初始化系统字体"""
        try:
            # 使用已初始化的font_db
            self.system_fonts = self.font_db.families()
            
            # 设置默认字体
            if platform.system() == 'Windows':
                default_fonts = ['Microsoft YaHei UI', 'Microsoft YaHei', 'SimHei', 'Arial']
            else:
                default_fonts = ['Noto Sans CJK SC', 'WenQuanYi Micro Hei', 'Arial']
                
            # 选择第一个可用的默认字体
            for font in default_fonts:
                if font in self.system_fonts:
                    self.current_font = font
                    log.info(f"使用默认字体: {font}")
                    break
                    
            # 如果没有找到默认字体，使用系统默认
            if not self.current_font:
                self.current_font = QApplication.font().family()
                log.info(f"使用系统默认字体: {self.current_font}")
                
        except Exception as e:
            log.error(f"初始化系统字体失败: {str(e)}")
            self.current_font = QApplication.font().family()
            
    def _init_icon_font(self):
        """初始化图标字体"""
        try:
            # 加载Material Icons字体
            icon_font_path = resource_path(os.path.join("core", "font", "icons", "MaterialIcons-Regular.ttf"))
            if os.path.exists(icon_font_path):
                font_id = self.font_db.addApplicationFont(icon_font_path)
                if font_id >= 0:
                    self.material_font = "Material Icons"
                    log.info("Material Icons字体加载成功")
                else:
                    self.material_font = None
                    log.error("Material Icons字体加载失败")
            else:
                self.material_font = None
                log.error("Material Icons字体文件不存在")
        except Exception as e:
            self.material_font = None
            log.error(f"初始化图标字体失败: {str(e)}")
    
    def _is_chinese_font(self, font_name):
        # 检查字体是否支持中文字符
        writing_systems = self.font_db.writingSystems(font_name)
        return QFontDatabase.WritingSystem.SimplifiedChinese in writing_systems
    
    def get_system_fonts(self):
        return self.system_fonts
    
    def set_current_font(self, font_name):
        if font_name in self.system_fonts:
            # 保存旧字体名称
            old_font = self.current_font
            
            # 设置新字体
            self.current_font = font_name
            log.info(f"设置当前字体为: {font_name}")
            
            # 如果字体没有变化,不需要更新
            if old_font == font_name:
                return True
            
            # 更新配置
            try:
                from core.utils.config_manager import config_manager
                config_manager.set_config('appearance', 'font', font_name)
                log.info(f"FontManager: 更新配置中的字体为: {font_name}")
            except Exception as e:
                log.error(f"更新字体配置出错: {str(e)}")
                
            # 更新应用程序字体
            app = QApplication.instance()
            if app:
                # 创建新字体并应用到应用程序
                font = self._create_optimized_font()
                app.setFont(font)
                
                # 保存使用Material Icons字体的控件列表
                material_icon_widgets = []
                
                # 强制所有窗口和控件更新
                for widget in app.allWidgets():
                    try:
                        # 检查是否是Material Icons控件
                        if hasattr(widget, "font") and widget.font().family() == self.material_font:
                            material_icon_widgets.append((widget, widget.font().pixelSize()))
                            continue
                            
                        # 尝试更新控件
                        if hasattr(widget, "setFont"):
                            # 根据控件类型应用不同的字体
                            if isinstance(widget, QLabel):
                                # 标签使用当前字体
                                label_font = QFont(font_name)
                                label_font.setPixelSize(widget.font().pixelSize())
                                widget.setFont(label_font)
                            else:
                                # 其他控件使用应用程序字体
                                widget.setFont(font)
                        
                        # 强制更新
                        widget.update()
                    except Exception as e:
                        # 忽略更新错误
                        pass
                
                # 恢复Material Icons字体
                for widget, size in material_icon_widgets:
                    try:
                        self.apply_icon_font(widget, size)
                    except:
                        pass
                
                log.info(f"已全局应用字体: {font_name}")
            return True
        return False
    
    def create_font_combobox(self, parent=None):
        combo = WhiteComboBox(parent)
        combo.addItems(self.system_fonts)
        combo.setCurrentText(self.current_font)
        
        # 断开默认连接，改为自定义处理
        try:
            combo.currentTextChanged.disconnect()
        except:
            pass
            
        combo.currentTextChanged.connect(self.set_current_font)
        return combo
    
    def _create_optimized_font(self, is_bold=False):
        """创建优化的字体实例"""
        try:
            font = QFont(self.current_font)
            font.setStyleStrategy(QFont.PreferAntialias)  # 启用抗锯齿
            if is_bold:
                font.setBold(True)
            return font
        except Exception as e:
            log.error(f"创建字体实例失败: {str(e)}")
            return QFont()
            
    def create_icon_font(self, size=24):
        if self.material_font:
            font = QFont(self.material_font)
        else:
            font = QFont()
        font.setPixelSize(size)
        return font

    def get_icon_text(self, icon_name):
        return ICON_MAP.get(icon_name, '')

    def apply_font(self, widget):
        """应用字体到控件"""
        try:
            if not widget:
                return
                
            # 创建字体实例
            font = self._create_optimized_font()
            
            # 根据控件类型调整字体
            if isinstance(widget, QPushButton):
                font.setPointSize(9)
            elif isinstance(widget, QLabel):
                font.setPointSize(10)
            elif isinstance(widget, QComboBox):
                font.setPointSize(9)
            else:
                font.setPointSize(9)
                
            # 应用字体
            widget.setFont(font)
            
        except Exception as e:
            log.error(f"应用字体失败: {str(e)}")

    def apply_icon_font(self, widget, size=24):
        if isinstance(widget, (QWidget, QLabel)):
            # 确保Material Icons字体已加载
            if not self.material_font:
                log.warning("Material Icons字体未加载，无法应用")
                return
                
            # 创建图标字体
            icon_font = self.create_icon_font(size)
            
            # 应用字体
            widget.setFont(icon_font)
            
            # 如果是标签，设置透明背景
            if isinstance(widget, QLabel):
                widget.setStyleSheet("color: #666666; background-color: transparent;")
                widget.setAttribute(Qt.WA_TranslucentBackground)
                
            log.debug(f"已应用Material Icons字体到控件: {widget.__class__.__name__}")
        else:
            raise TypeError("不支持的类型,只能应用到QWidget或QLabel ")

    def _get_background_color(self, widget):
        # QApplication 默认使用亮色主题
        if isinstance(widget, QApplication):
            return True
        
        # 获取背景色
        bg_color = widget.palette().color(widget.backgroundRole())
        
        # 背景透明时的处理
        if bg_color.alpha() == 0:
            parent = widget
            while parent:
                style = parent.styleSheet()
                if "background-color:" in style:
                    color_match = re.search(r'background-color:\s*(.*?)(;|$)', style)
                    if color_match:
                        color_str = color_match.group(1).strip().lower()
                        
                        # 处理颜色关键字
                        color_keywords = {
                            'white': True,
                            'black': False,
                            'transparent': True  # 透明默认当作亮色处理
                        }
                        if color_str in color_keywords:
                            return color_keywords[color_str]
                        
                        # 处理 rgb/rgba 格式
                        if color_str.startswith('rgb'):
                            rgb_match = re.search(r'(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', color_str)
                            if rgb_match:
                                r, g, b = map(int, rgb_match.groups())
                                return (r * 299 + g * 587 + b * 114) / 1000 > 128
                                
                        # 处理十六进制格式
                        if color_str.startswith('#'):
                            r = int(color_str[1:3], 16) if len(color_str) >= 3 else 255
                            g = int(color_str[3:5], 16) if len(color_str) >= 5 else 255
                            b = int(color_str[5:7], 16) if len(color_str) >= 7 else 255
                            return (r * 299 + g * 587 + b * 114) / 1000 > 128
                            
                parent = parent.parentWidget()
                
            return True  # 找不到背景色时默认为亮色
            
        # 计算亮度 (使用感知亮度公式)
        return (bg_color.red() * 299 + bg_color.green() * 587 + bg_color.blue() * 114) / 1000 > 128

    def reapply_icon_fonts(self):
        """重新应用所有Material Icons字体到使用它的控件"""
        if not self.material_font:
            log.warning("Material Icons字体未加载，无法重新应用")
            return False
            
        app = QApplication.instance()
        if not app:
            return False
            
        count = 0
        # 查找所有使用Material Icons字体的控件
        for widget in app.allWidgets():
            try:
                # 检查是否是图标控件
                is_icon_widget = False
                
                # 方法1：检查字体族名
                if hasattr(widget, "font") and widget.font().family() == self.material_font:
                    is_icon_widget = True
                
                # 方法2：检查控件文本是否是图标字符
                if isinstance(widget, QLabel) and len(widget.text()) == 1:
                    # 检查文本是否在图标映射中
                    for icon_name, icon_char in ICON_MAP.items():
                        if widget.text() == icon_char:
                            is_icon_widget = True
                            break
                
                if is_icon_widget:
                    # 重新应用图标字体
                    size = widget.font().pixelSize() if widget.font().pixelSize() > 0 else 24
                    self.apply_icon_font(widget, size)
                    count += 1
            except Exception as e:
                log.error(f"重新应用图标字体失败: {str(e)}")
                
        log.info(f"已重新应用Material Icons字体到 {count} 个控件")
        return True

