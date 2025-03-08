from PySide6.QtCore import QThread, Signal, QMetaObject, Qt, Slot
from PySide6.QtGui import QPixmap, QGuiApplication, QScreen, QPainter
from core.log.log_manager import log
import time
import win32gui
import win32con
import win32ui
from ctypes import windll
from PIL import Image, ImageGrab

class ScreenshotThread(QThread):
    finished = Signal(QPixmap)
    
    def run(self):
        try:
            # 给系统更多时间切换窗口
            time.sleep(0.5)  # 增加延迟时间，确保窗口完全显示
            
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
        
        # 如果超时，发送空截图信号
        if not hasattr(self, '_screenshot_completed'):
            log.error("截图超时")
            self.finished.emit(QPixmap())
    
    @Slot()
    def _grab_screenshot(self):
        try:
            # 尝试使用多种方法获取屏幕截图
            pixmap = self._grab_using_qt()
            
            # 如果Qt方法失败，尝试使用Win32 API
            if pixmap.isNull():
                log.warning("Qt截图方法失败，尝试使用Win32 API")
                pixmap = self._grab_using_win32()
            
            # 如果Win32 API也失败，尝试使用PIL
            if pixmap.isNull():
                log.warning("Win32 API截图方法失败，尝试使用PIL")
                pixmap = self._grab_using_pil()
            
            # 发送结果
            self.finished.emit(pixmap)
            
            # 标记截图已完成
            self._screenshot_completed = True
            
        except Exception as e:
            log.error(f"获取截图失败: {str(e)}")
            self.finished.emit(QPixmap())
            self._screenshot_completed = True
    
    def _grab_using_qt(self):
        """使用Qt方法获取屏幕截图"""
        try:
            # 获取全屏截图
            screens = QGuiApplication.screens()
            if not screens:
                log.error("无法获取屏幕")
                return QPixmap()
            
            # 计算所有屏幕的总区域
            total_rect = screens[0].geometry()
            for screen in screens[1:]:
                total_rect = total_rect.united(screen.geometry())
            
            # 创建足够大的pixmap
            result_pixmap = QPixmap(total_rect.width(), total_rect.height())
            result_pixmap.fill(Qt.transparent)
            
            # 绘制每个屏幕的内容
            painter = QPainter(result_pixmap)
            
            for screen in screens:
                # 获取屏幕截图
                screen_pixmap = screen.grabWindow(0)
                # 计算相对位置
                screen_rect = screen.geometry()
                # 绘制到结果pixmap上
                painter.drawPixmap(screen_rect.x() - total_rect.x(), 
                                  screen_rect.y() - total_rect.y(), 
                                  screen_pixmap)
            
            painter.end()
            
            return result_pixmap
            
        except Exception as e:
            log.error(f"Qt截图方法失败: {str(e)}")
            return QPixmap()
    
    def _grab_using_win32(self):
        """使用Win32 API获取屏幕截图"""
        try:
            # 获取屏幕DC
            hdc = win32gui.GetDC(0)
            # 创建兼容DC
            mfcDC = win32ui.CreateDCFromHandle(hdc)
            saveDC = mfcDC.CreateCompatibleDC()
            
            # 获取屏幕尺寸
            import win32api
            width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
            height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
            left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
            top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
            
            # 创建位图
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)
            
            # 复制屏幕内容到位图
            saveDC.BitBlt((0, 0), (width, height), mfcDC, (left, top), win32con.SRCCOPY)
            
            # 转换为PIL图像
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)
            img = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1)
                
            # 转换为QPixmap
            from io import BytesIO
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            pixmap = QPixmap()
            pixmap.loadFromData(buffer.getvalue())
            
            # 清理资源
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(0, hdc)
            win32gui.DeleteObject(saveBitMap.GetHandle())
            
            return pixmap
            
        except Exception as e:
            log.error(f"Win32 API截图方法失败: {str(e)}")
            return QPixmap()
    
    def _grab_using_pil(self):
        """使用PIL获取屏幕截图"""
        try:
            # 使用PIL的ImageGrab
            img = ImageGrab.grab()
            
            # 转换为QPixmap
            from io import BytesIO
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            pixmap = QPixmap()
            pixmap.loadFromData(buffer.getvalue())
            
            return pixmap
            
        except Exception as e:
            log.error(f"PIL截图方法失败: {str(e)}")
            return QPixmap() 