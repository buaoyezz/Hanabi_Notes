from PySide6.QtCore import QThread, Signal, QMetaObject, Qt, Slot
from PySide6.QtGui import QPixmap, QGuiApplication
from core.log.log_manager import log
import time

class ScreenshotThread(QThread):
    finished = Signal(QPixmap)
    
    def run(self):
        try:
            # 给系统一点时间切换窗口
            time.sleep(0.2)
            
            # 使用QMetaObject.invokeMethod确保在主线程中获取截图
            QMetaObject.invokeMethod(self, "_grab_screenshot", Qt.QueuedConnection)
            
            # 等待截图完成
            self.wait_for_screenshot()
            
        except Exception as e:
            log.error(f"后台截图线程失败: {str(e)}")
    
    def wait_for_screenshot(self):
        # 简单的等待实现，实际应用中可以使用更复杂的同步机制
        timeout = 5  # 5秒超时
        start_time = time.time()
        while not hasattr(self, '_screenshot_completed') and time.time() - start_time < timeout:
            time.sleep(0.1)
    
    @Slot()
    def _grab_screenshot(self):
        try:
            # 获取全屏截图
            screen = QGuiApplication.primaryScreen()
            if not screen:
                log.error("无法获取主屏幕")
                return
                
            pixmap = screen.grabWindow(0)
            self.finished.emit(pixmap)
            
            # 标记截图已完成
            self._screenshot_completed = True
            
        except Exception as e:
            log.error(f"获取截图失败: {str(e)}")
            self._screenshot_completed = True 