from PySide6.QtWidgets import (QWidget, QApplication, QLabel, QPushButton, 
                             QHBoxLayout, QVBoxLayout, QRubberBand, QToolBar,
                             QSpinBox, QFontDialog, QColorDialog)
from PySide6.QtCore import Qt, QRect, QPoint, QSize, Signal, QTimer, QMetaObject, Slot
from PySide6.QtGui import (QColor, QPainter, QPixmap, QScreen, QImage, 
                          QPen, QCursor, QIcon, QKeySequence, QFont, QGuiApplication)
from core.log.log_manager import log
from core.utils.notif import show_info, show_error, Notification, NotificationType
from core.utils.config_manager import config_manager
from core.screenshot.screenshot_editor import ScreenshotEditor
from core.screenshot.screenshot_thread import ScreenshotThread
import win32gui
import win32con
import win32ui
import os
import threading
import time

class ScreenshotWindow(QWidget):
    screenshot_taken = Signal(QPixmap)  # 截图完成信号
    closed = Signal()  # 窗口关闭信号
    start_grab_signal = Signal()  # 开始抓取屏幕信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowState(Qt.WindowFullScreen)
        
        # 初始化属性
        self.original_pixmap = None
        self.current_pixmap = None
        self.begin = QPoint()
        self.end = QPoint()
        self.is_drawing = False
        self.editor = None
        self.edit_mode = False
        self.screenshot_thread = None
        
        # 连接信号
        self.start_grab_signal.connect(self._start_grab_thread)
        
        self.initUI()
        
    def initUI(self):
        # 设置窗口属性
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)
        
        # 创建工具栏
        self.toolbar = ScreenshotToolBar(self)
        self.toolbar.hide()
        
        # 创建橡皮筋选择框
        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)
        
        # 创建大小标签
        self.size_label = QLabel(self)
        self.size_label.setStyleSheet("""
            background-color: rgba(0, 0, 0, 0.6);
            color: white;
            padding: 2px 5px;
            border-radius: 3px;
        """)
        self.size_label.hide()
        
        # 创建等待提示
        self.wait_label = QLabel("正在准备截图...", self)
        self.wait_label.setStyleSheet("""
            background-color: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            font-size: 16px;
        """)
        self.wait_label.adjustSize()
        self.wait_label.move(
            (self.width() - self.wait_label.width()) // 2,
            (self.height() - self.wait_label.height()) // 2
        )
        self.wait_label.hide()
        
    def grab_screen(self):
        try:
            # 设置窗口大小和属性
            screen = QGuiApplication.primaryScreen()
            if not screen:
                log.error("无法获取主屏幕")
                return
                
            available_geometry = screen.availableGeometry()
            self.setGeometry(available_geometry)
            
            # 显示等待提示
            self.wait_label.move(
                (self.width() - self.wait_label.width()) // 2,
                (self.height() - self.wait_label.height()) // 2
            )
            self.wait_label.show()
            
            # 显示窗口
            self.show()
            self.activateWindow()  # 确保窗口激活
            
            # 使用信号在主线程中启动截图线程
            QMetaObject.invokeMethod(self, "_start_grab_thread", Qt.QueuedConnection)
            
            log.info("区域截图窗口已显示，等待截图...")
        except Exception as e:
            log.error(f"截取屏幕失败: {str(e)}")
            
    @Slot()
    def _start_grab_thread(self):
        try:
            # 在后台线程中获取截图
            if self.screenshot_thread and self.screenshot_thread.isRunning():
                self.screenshot_thread.wait()  # 等待之前的线程完成
            
            self.screenshot_thread = ScreenshotThread()
            self.screenshot_thread.finished.connect(self._on_screenshot_ready)
            self.screenshot_thread.start()
        except Exception as e:
            log.error(f"启动截图线程失败: {str(e)}")

    def _on_screenshot_ready(self, pixmap):
        try:
            # 保存截图
            self.original_pixmap = pixmap
            self.current_pixmap = pixmap.copy()
            
            # 隐藏等待提示
            self.wait_label.hide()
            
            # 激活窗口
            self.activateWindow()
            self.raise_()
            
            # 更新界面
            self.update()
            
            log.info("区域截图准备完成")
        except Exception as e:
            log.error(f"处理截图失败: {str(e)}")

    def paintEvent(self, event):
        try:
            # 如果截图尚未准备好，不进行绘制
            if not self.original_pixmap:
                return
                
            painter = QPainter(self)
            
            # 绘制半透明背景
            painter.drawPixmap(0, 0, self.original_pixmap)
            
            # 绘制半透明遮罩
            painter.fillRect(self.rect(), QColor(0, 0, 0, 100))
            
            # 如果有选区，则显示选区内容
            if self.is_drawing and self.begin != self.end:
                selection_rect = self.get_selection_rect()
                painter.drawPixmap(selection_rect, self.original_pixmap, selection_rect)
                
                # 绘制选区边框
                pen = QPen(QColor(0, 174, 255), 2)
                painter.setPen(pen)
                painter.drawRect(selection_rect)
        except Exception as e:
            log.error(f"绘制事件处理失败: {str(e)}")

    def update_size_label(self, rect):
        try:
            # 设置标签内容
            if rect.isValid() and rect.width() > 0 and rect.height() > 0:
                text = f"{rect.width()} × {rect.height()}"
                self.size_label.setText(text)
                
                # 调整标签位置
                label_x = rect.x()
                label_y = rect.y() - 25
                if label_y < 0:
                    label_y = rect.bottom() + 5
                
                self.size_label.move(label_x, label_y)
                self.size_label.adjustSize()
                self.size_label.show()
            else:
                self.size_label.hide()
        except Exception as e:
            log.error(f"更新尺寸标签失败: {str(e)}")

    def update_toolbar_position(self, rect):
        try:
            if rect.isValid() and rect.width() > 0 and rect.height() > 0:
                # 计算工具栏位置
                toolbar_x = rect.x()
                toolbar_y = rect.bottom() + 5
                
                # 确保工具栏不超出屏幕边界
                screen_rect = self.geometry()
                toolbar_width = self.toolbar.sizeHint().width()
                toolbar_height = self.toolbar.sizeHint().height()
                
                # 水平方向调整
                if toolbar_x + toolbar_width > screen_rect.width():
                    toolbar_x = screen_rect.width() - toolbar_width - 5
                
                # 垂直方向调整
                if toolbar_y + toolbar_height > screen_rect.height():
                    toolbar_y = rect.top() - toolbar_height - 5
                
                self.toolbar.move(toolbar_x, toolbar_y)
        except Exception as e:
            log.error(f"更新工具栏位置失败: {str(e)}")

    def get_selection_rect(self):
        return QRect(self.begin, self.end).normalized()

    def mousePressEvent(self, event):
        try:
            # 忽略右键
            if event.button() == Qt.RightButton:
                return
                
            if self.edit_mode:
                # 如果在编辑模式，传递给编辑器
                if self.editor:
                    self.editor.mousePressEvent(event)
                return
                
            # 开始选择区域
            self.begin = event.pos()
            self.end = self.begin
            self.is_drawing = True
            self.rubber_band.setGeometry(QRect(self.begin, self.begin))
            self.rubber_band.show()
            self.update_size_label(QRect(self.begin, self.begin))
            self.size_label.show()
            
            # 隐藏工具栏
            self.toolbar.hide()
            
            # 更新显示
            self.update()
            
        except Exception as e:
            log.error(f"鼠标按下事件处理失败: {str(e)}")
            
    def mouseMoveEvent(self, event):
        try:
            if self.edit_mode:
                # 如果在编辑模式，传递给编辑器
                if self.editor:
                    self.editor.mouseMoveEvent(event)
                return
                
            if self.is_drawing:
                # 更新选择区域
                self.end = event.pos()
                selection_rect = self.get_selection_rect()
                self.rubber_band.setGeometry(selection_rect)
                self.update_size_label(selection_rect)
                
                # 更新显示
                self.update()
                
        except Exception as e:
            log.error(f"鼠标移动事件处理失败: {str(e)}")
            
    def mouseReleaseEvent(self, event):
        try:
            # 忽略右键
            if event.button() == Qt.RightButton:
                return
                
            if self.edit_mode:
                # 如果在编辑模式，传递给编辑器
                if self.editor:
                    self.editor.mouseReleaseEvent(event)
                return
                
            if self.is_drawing:
                # 完成选择
                self.end = event.pos()
                selection_rect = self.get_selection_rect()
                
                # 确保选择区域有效
                if selection_rect.width() > 10 and selection_rect.height() > 10:
                    # 更新工具栏位置并显示
                    self.update_toolbar_position(selection_rect)
                    self.toolbar.update_for_capture_mode()
                    self.toolbar.show()
                
                self.is_drawing = False
                
                # 更新显示
                self.update()
                
        except Exception as e:
            log.error(f"鼠标释放事件处理失败: {str(e)}")

    def keyPressEvent(self, event):
        try:
            # ESC键退出
            if event.key() == Qt.Key_Escape:
                if self.edit_mode:
                    self.exit_edit_mode()
                else:
                    self.close()
                    
            # 回车键确认截图
            elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                if self.edit_mode:
                    self.finish_edit()
                else:
                    self.capture_current_selection()
        except Exception as e:
            log.error(f"键盘事件处理失败: {str(e)}")

    def capture_current_selection(self):
        try:
            # 获取选区
            rect = self.get_selection_rect()
            if not rect.isValid() or rect.width() <= 0 or rect.height() <= 0:
                log.warning("无效的选区")
                return
            
            # 从原始截图中裁剪选区
            cropped_pixmap = self.original_pixmap.copy(rect)
            
            # 进入编辑模式
            if config_manager.get_config('screenshot', 'edit_after_capture', True):
                self.enter_edit_mode(cropped_pixmap, rect)
                log.info(f"已捕获选区并进入编辑模式: {rect.width()}x{rect.height()}")
            else:
                # 直接发出截图完成信号
                self.screenshot_taken.emit(cropped_pixmap)
                # 关闭窗口
                self.close()
            
        except Exception as e:
            log.error(f"捕获选区失败: {str(e)}")

    def enter_edit_mode(self, pixmap, rect):
        try:
            from core.screenshot.screenshot_editor import ScreenshotEditor
            
            self.edit_mode = True
            self.rubber_band.hide()
            self.size_label.hide()
            
            # 创建编辑器
            self.editor = ScreenshotEditor(pixmap, self)
            self.editor.move(rect.topLeft())
            self.editor.show()
            
            # 更新工具栏
            self.toolbar.update_for_edit_mode()
            self.update_toolbar_position(rect)
            self.toolbar.show()
        except Exception as e:
            log.error(f"进入编辑模式失败: {str(e)}")

    def exit_edit_mode(self):
        try:
            self.edit_mode = False
            
            if self.editor:
                self.editor.hide()
                self.editor = None
                
            self.toolbar.update_for_capture_mode()
            self.update()
        except Exception as e:
            log.error(f"退出编辑模式失败: {str(e)}")

    def finish_edit(self):
        try:
            if self.editor:
                # 获取编辑后的图片
                edited_pixmap = self.editor.get_edited_pixmap()
                
                # 发出截图完成信号
                self.screenshot_taken.emit(edited_pixmap)
                
                # 退出编辑模式
                self.exit_edit_mode()
                
                # 关闭窗口
                self.close()
                
                log.info("编辑完成，已发送截图")
            else:
                log.warning("编辑器不存在，无法完成编辑")
                self.close()
                
        except Exception as e:
            log.error(f"完成编辑失败: {str(e)}")
            self.close()

    def closeEvent(self, event):
        try:
            # 停止截图线程
            if self.screenshot_thread and self.screenshot_thread.isRunning():
                self.screenshot_thread.terminate()
                self.screenshot_thread.wait(1000)  # 等待最多1秒
            
            # 清理编辑器
            if self.editor:
                self.editor.deleteLater()
                self.editor = None
            
            # 发出关闭信号
            self.closed.emit()
            
            # 接受关闭事件
            event.accept()
            
        except Exception as e:
            log.error(f"关闭截图窗口失败: {str(e)}")
            event.accept()  # 确保窗口关闭

class ScreenshotToolBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 创建工具按钮配置
        self.capture_buttons = [
            ("复制", "copy", self.copy_to_clipboard),
            ("保存", "save", self.save_screenshot),
            ("编辑", "edit", self.edit_screenshot),
            ("关闭", "close", self.close_screenshot)
        ]
        
        self.edit_buttons = [
            ("撤销", "undo", self.undo),
            ("重做", "redo", self.redo),
            (None, None, None),  # 分隔符
            ("文字", "text", lambda: self.set_tool("text")),
            ("画笔", "pen", lambda: self.set_tool("pen")),
            ("箭头", "arrow", lambda: self.set_tool("arrow")),
            ("马赛克", "mosaic", lambda: self.set_tool("mosaic")),
            (None, None, None),  # 分隔符
            ("颜色", "color", self.set_color),
            ("字体", "font", self.set_font),
            (None, None, None),  # 分隔符
            ("保存", "save", self.save_screenshot),
            ("完成", "check", self.finish_edit)
        ]
        
        self.current_buttons = self.capture_buttons
        self.create_buttons()
        
        # 设置工具栏样式
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 5px;
                border: 1px solid #DDDDDD;
            }
            QPushButton {
                border: none;
                border-radius: 3px;
                background: transparent;
                color: #666666;
                font-family: 'Material Icons';
                font-size: 18px;
                padding: 5px;
                min-width: 30px;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #F0F0F0;
            }
            QPushButton:pressed {
                background-color: #E0E0E0;
            }
            QSpinBox {
                border: 1px solid #DDDDDD;
                border-radius: 3px;
                padding: 2px;
            }
        """)
        
    def create_buttons(self):
        # 清除现有按钮
        for i in reversed(range(self.layout().count())): 
            self.layout().itemAt(i).widget().deleteLater()
        
        # 创建新按钮
        for text, icon_name, callback in self.current_buttons:
            if text is None:  # 添加分隔符
                self.layout().addSpacing(10)
                continue
                
            btn = QPushButton()
            btn.setToolTip(text)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(callback)
            
            # 设置图标
            try:
                from core.font.icon_map import ICON_MAP
                icon_text = ICON_MAP.get(icon_name, "")
                if icon_text:
                    btn.setText(icon_text)
            except Exception as e:
                log.error(f"加载图标失败: {str(e)}")
                btn.setText(text)
            
            self.layout().addWidget(btn)
            
        self.adjustSize()
        
    def update_for_edit_mode(self):
        self.current_buttons = self.edit_buttons
        self.create_buttons()
        
    def update_for_capture_mode(self):
        self.current_buttons = self.capture_buttons
        self.create_buttons()
        
    def copy_to_clipboard(self):
        if self.parent.editor:
            pixmap = self.parent.editor.get_edited_pixmap()
        else:
            rect = QRect(self.parent.begin, 
                        self.parent.end).normalized()
            if rect.width() > 0 and rect.height() > 0:
                pixmap = self.parent.original_pixmap.copy(rect)
            else:
                return
                
        QApplication.clipboard().setPixmap(pixmap)
        show_info("已复制到剪贴板")
        self.parent.close()
        
    def save_screenshot(self):
        try:
            log.info("手动保存截图")
            
            # 获取截图数据
            if self.parent.editor:
                pixmap = self.parent.editor.get_edited_pixmap()
                if pixmap.isNull():
                    log.error("获取编辑后的截图失败，返回空图像")
                    show_error("获取截图数据失败")
                    return
            else:
                rect = QRect(self.parent.begin, 
                            self.parent.end).normalized()
                if rect.width() > 0 and rect.height() > 0:
                    pixmap = self.parent.original_pixmap.copy(rect)
                else:
                    log.error("选区无效，无法保存截图")
                    show_error("请先选择一个有效的区域")
                    return
            
            # 使用截图管理器的保存功能            
            from core.screenshot.screenshot_manager import ScreenshotManager
            screenshot_manager = ScreenshotManager()
            screenshot_manager._save_screenshot(pixmap)
            
            # 关闭窗口
            log.info("截图已保存，关闭窗口")
            self.parent.close()
                
        except Exception as e:
            log.error(f"保存截图操作失败: {str(e)}")
            show_error(f"保存截图失败: {str(e)}")
            
    def edit_screenshot(self):
        try:
            log.info("点击了编辑按钮，准备捕获当前选区")
            self.parent.capture_current_selection()
        except Exception as e:
            log.error(f"编辑截图失败: {str(e)}")
            
    def close_screenshot(self):
        try:
            log.info("关闭截图窗口")
            self.parent.close()
        except Exception as e:
            log.error(f"关闭截图失败: {str(e)}")
        
    def set_tool(self, tool):
        if self.parent.editor:
            self.parent.editor.set_tool(tool)
            
    def set_color(self):
        if self.parent.editor:
            self.parent.editor.set_pen_color()
            
    def set_font(self):
        if self.parent.editor:
            self.parent.editor.set_font()
            
    def undo(self):
        if self.parent.editor:
            self.parent.editor.undo()
            
    def redo(self):
        if self.parent.editor:
            self.parent.editor.redo()
            
    def finish_edit(self):
        if self.parent.editor:
            pixmap = self.parent.editor.get_edited_pixmap()
            self.parent.screenshot_taken.emit(pixmap)
            self.parent.close() 