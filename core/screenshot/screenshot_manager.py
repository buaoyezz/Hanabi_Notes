from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, QTimer, QMetaObject, Qt, Slot
from PySide6.QtGui import QPixmap, QKeySequence, QGuiApplication, QScreen
from core.log.log_manager import log
from core.utils.config_manager import config_manager
from core.utils.notif import Notification, NotificationType
from core.screenshot.screenshot_window import ScreenshotWindow
import keyboard
import win32gui
import win32con
import win32ui
import win32api
from ctypes import windll
from PIL import Image, ImageGrab
import os
import time

class ScreenshotManager(QObject):
    screenshot_taken = Signal(QPixmap)  # 截图完成信号
    start_screenshot_signal = Signal(str)  # 开始截图信号，用于在主线程中执行
    
    _instance = None
    _hotkeys = {}  # 存储注册的快捷键
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ScreenshotManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            super().__init__()
            self.screenshot_window = None
            self.initialized = True
            self._hotkeys = {}
            self._taking_screenshot = False  # 防止重复触发
            
            # 连接信号到槽函数，确保在主线程中执行
            self.start_screenshot_signal.connect(self._execute_screenshot)
            
            log.info("截图管理器初始化完成")
    
    def start_screenshot(self, mode="region"):
        """开始截图"""
        # 防止重复触发
        if self._taking_screenshot:
            log.info("正在截图中，忽略此次请求")
            # 如果上次截图已超过10秒，则强制重置状态
            self._force_reset_if_stuck()
            return
            
        try:
            # 强制重置之前的状态
            self.cancel_screenshot()
            
            self._taking_screenshot = True
            self._last_action_time = time.time()  # 记录开始时间
            log.info(f"开始截图，模式: {mode}")
            
            # 使用信号在主线程中执行截图操作
            self.start_screenshot_signal.emit(mode)
            
        except Exception as e:
            log.error(f"截图失败: {str(e)}")
            self._reset_screenshot_state()  # 确保出错时也重置状态
            
    def _force_reset_if_stuck(self):
        """检查是否卡住，如果卡住则强制重置"""
        if self._taking_screenshot:
            # 获取上次操作时间
            import time
            current_time = time.time()
            last_action_time = getattr(self, '_last_action_time', 0)
            
            # 如果超过10秒没有活动，认为是卡住了
            if current_time - last_action_time > 10 or last_action_time == 0:
                log.warning("检测到截图状态卡住，强制重置")
                self._reset_screenshot_state()
                
                # 尝试关闭截图窗口
                try:
                    if self.screenshot_window:
                        self.screenshot_window.close()
                        self.screenshot_window = None
                except:
                    pass
            
    def _reset_screenshot_state(self):
        """重置截图状态"""
        try:
            log.info("重置截图状态")
            self._taking_screenshot = False
            
            # 清理截图窗口
            if self.screenshot_window:
                try:
                    self.screenshot_window.close()
                    self.screenshot_window = None
                except:
                    pass
            
            # 记录最后操作时间
            import time
            self._last_action_time = time.time()
            
        except Exception as e:
            log.error(f"重置截图状态失败: {str(e)}")
            # 强制重置基本状态
            self._taking_screenshot = False
            self.screenshot_window = None
    
    def _take_region_screenshot(self):
        """区域截图"""
        try:
            # 先截取全屏作为背景
            screen_pixmap = self._grab_full_screen()
            if not screen_pixmap:
                log.error("获取全屏截图失败")
                self._reset_screenshot_state()
                return
                
            # 创建截图窗口
            if self.screenshot_window is None:
                from core.screenshot.screenshot_window import ScreenshotWindow
                self.screenshot_window = ScreenshotWindow()
                self.screenshot_window.screenshot_taken.connect(self._on_screenshot_taken)
                
                # 连接关闭信号，确保状态重置
                self.screenshot_window.closed.connect(self._reset_screenshot_state)
            
            # 配置并显示截图窗口，直接调用不使用QTimer
            self.screenshot_window.grab_screen()
            
        except Exception as e:
            log.error(f"区域截图失败: {str(e)}")
            self._reset_screenshot_state()
            
    def _check_screenshot_progress(self):
        """检查截图进度，如果超时则重置状态"""
        self._force_reset_if_stuck()
        
    def cancel_screenshot(self):
        """强制取消截图"""
        log.info("强制取消截图")
        
        # 关闭截图窗口
        try:
            if self.screenshot_window:
                self.screenshot_window.close()
                self.screenshot_window = None
        except:
            pass
            
        # 重置状态
        self._reset_screenshot_state()
        
        # 显示通知
        try:
            notification = Notification(
                text="已强制取消截图操作",
                title="截图已取消",
                type=NotificationType.INFO
            )
            notification.show_notification()
        except Exception as e:
            log.error(f"显示取消通知失败: {str(e)}")
            
    def _grab_full_screen(self):
        """获取全屏截图"""
        try:
            # 获取主屏幕
            screen = QGuiApplication.primaryScreen()
            if not screen:
                log.error("无法获取主屏幕")
                return None
                
            # 截取全屏
            pixmap = screen.grabWindow(0)
            log.info(f"获取全屏截图成功: {pixmap.width()}x{pixmap.height()}")
            return pixmap
            
        except Exception as e:
            log.error(f"获取全屏截图失败: {str(e)}")
            return None
    
    def _take_fullscreen_screenshot(self):
        """全屏截图"""
        try:
            pixmap = self._grab_full_screen()
            if pixmap:
                # 直接保存全屏截图
                self._on_screenshot_taken(pixmap, auto_save=True)
                log.info("完成全屏截图")
            
        except Exception as e:
            log.error(f"全屏截图失败: {str(e)}")
    
    def _take_window_screenshot(self):
        """窗口截图"""
        try:
            # 获取前台窗口句柄
            hwnd = win32gui.GetForegroundWindow()
            if hwnd == 0:
                log.error("无法获取前台窗口")
                return self._take_fullscreen_screenshot()  # 失败时切换到全屏截图
                
            # 确保不是自己的窗口
            window_title = win32gui.GetWindowText(hwnd)
            if "Imagine Snap" in window_title:
                log.info("前台窗口是截图工具自身，切换到全屏截图")
                return self._take_fullscreen_screenshot()
                
            # 获取窗口大小
            try:
                left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                width = right - left
                height = bottom - top
                
                if width <= 0 or height <= 0:
                    log.error(f"窗口尺寸无效: {width}x{height}")
                    return self._take_fullscreen_screenshot()
                    
                log.info(f"窗口尺寸: {width}x{height}, 位置: ({left}, {top})")
            except Exception as e:
                log.error(f"获取窗口尺寸失败: {str(e)}")
                return self._take_fullscreen_screenshot()
                
            # 使用Win32 API截取窗口
            # 创建设备上下文
            hwndDC = win32gui.GetWindowDC(hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()
            
            # 创建位图对象
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)
            
            # 截取窗口内容
            result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)  # 使用PW_RENDERFULLCONTENT
            
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
            win32gui.ReleaseDC(hwnd, hwndDC)
            win32gui.DeleteObject(saveBitMap.GetHandle())
            
            if result == 1 and not pixmap.isNull():
                log.info(f"窗口截图成功: {pixmap.width()}x{pixmap.height()}")
                # 直接保存窗口截图
                self._on_screenshot_taken(pixmap, auto_save=True)
            else:
                log.error(f"窗口截图失败，结果: {result}, 尝试使用备选方法")
                # 备选方法：使用PIL的ImageGrab
                try:
                    pil_img = ImageGrab.grab((left, top, right, bottom))
                    buffer = BytesIO()
                    pil_img.save(buffer, format='PNG')
                    buffer.seek(0)
                    pixmap = QPixmap()
                    pixmap.loadFromData(buffer.getvalue())
                    
                    if not pixmap.isNull():
                        log.info(f"备选方法窗口截图成功: {pixmap.width()}x{pixmap.height()}")
                        # 直接保存窗口截图
                        self._on_screenshot_taken(pixmap, auto_save=True)
                    else:
                        log.error("备选方法窗口截图失败")
                        self._take_fullscreen_screenshot()
                except Exception as e:
                    log.error(f"备选方法窗口截图失败: {str(e)}")
                    self._take_fullscreen_screenshot()
            
        except Exception as e:
            log.error(f"窗口截图失败: {str(e)}")
            # 如果窗口截图失败，回退到全屏截图
            self._take_fullscreen_screenshot()
    
    def _on_screenshot_taken(self, pixmap, auto_save=False):
        try:
            # 发出截图完成信号
            self.screenshot_taken.emit(pixmap)
            
            # 保存截图 - 简化逻辑，确保所有截图都保存
            self._save_screenshot(pixmap)
                
            # 重置截图状态
            self._reset_screenshot_state()
                
        except Exception as e:
            log.error(f"处理截图失败: {str(e)}")
            self._reset_screenshot_state()  # 确保出错时也重置状态
    
    def _save_screenshot(self, pixmap):
        try:
            # 获取保存路径和格式
            save_path = config_manager.get_config(
                'screenshot', 
                'save_path', 
                os.path.join(os.path.expanduser('~'), 'Pictures')
            )
            
            # 转换格式名称为正确的扩展名
            format_map = {
                "PNG": "png",
                "JPG": "jpg", 
                "JPEG": "jpg",
                "BMP": "bmp",
                "GIF": "gif"
            }
            
            format_str = config_manager.get_config('screenshot', 'format', "PNG").upper()
            format_ext = format_map.get(format_str, "png")
            
            # 生成文件名
            from datetime import datetime
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_ext}"
            filepath = os.path.join(save_path, filename)
            
            # 确保目录存在
            os.makedirs(save_path, exist_ok=True)
            
            # 保存截图
            if pixmap.save(filepath, format_str):
                log.info(f"截图已保存至: {filepath}")
                # 显示通知
                self._show_save_notification(filepath)
            else:
                log.error(f"保存截图失败，格式: {format_str}")
                
        except Exception as e:
            log.error(f"保存截图失败: {str(e)}")
            
    def _show_save_notification(self, filepath):
        try:
            # 创建并显示通知
            notification = Notification(
                text=f"保存路径: {filepath}",
                title="截图已保存",
                type=NotificationType.INFO,
                duration=3000
            )
            notification.show_notification()
        except Exception as e:
            # 如果通知失败，记录错误但不中断程序
            log.error(f"显示保存通知失败: {str(e)}")
            
    def _parse_shortcut(self, shortcut):
        # 替换修饰键
        shortcut = shortcut.lower()
        shortcut = shortcut.replace("ctrl", "control")
        # 不需要替换+号，不然会导致快捷键解析错误
        return shortcut
            
    def register_global_hotkeys(self):
        try:
            # 获取快捷键设置
            shortcuts = {
                'fullscreen': config_manager.get_config('shortcuts', 'fullscreen', "ctrl+alt+f"),
                'region': config_manager.get_config('shortcuts', 'region', "ctrl+alt+a"),
                'window': config_manager.get_config('shortcuts', 'window', "ctrl+alt+w"),
                'quick': config_manager.get_config('shortcuts', 'quick', "ctrl+alt+s"),
                'cancel': "ctrl+alt+c"  # 新增：取消截图快捷键
            }
            
            # 注销之前的快捷键
            self.unregister_global_hotkeys()
            
            # 注册新的快捷键
            for mode, shortcut in shortcuts.items():
                if shortcut:
                    kb_shortcut = self._parse_shortcut(shortcut)
                    try:
                        if mode == 'cancel':
                            keyboard.add_hotkey(kb_shortcut, self.cancel_screenshot)
                        else:
                            # 直接调用截图函数，不使用QTimer
                            keyboard.add_hotkey(kb_shortcut, lambda m=mode: self.start_screenshot(m))
                        self._hotkeys[mode] = kb_shortcut
                        log.info(f"已注册{mode}快捷键: {kb_shortcut}")
                    except Exception as e:
                        log.error(f"注册{mode}快捷键失败: {str(e)}")
            
            log.info("已注册全局快捷键")
            
        except Exception as e:
            log.error(f"注册全局快捷键失败: {str(e)}")
            
    def unregister_global_hotkeys(self):
        try:
            for mode, shortcut in self._hotkeys.items():
                try:
                    keyboard.remove_hotkey(shortcut)
                    log.info(f"已注销{mode}截图快捷键: {shortcut}")
                except:
                    pass
            self._hotkeys.clear()
            log.info("已注销全局快捷键")
            
        except Exception as e:
            log.error(f"注销全局快捷键失败: {str(e)}")
            
    @Slot(str)
    def _execute_screenshot(self, mode):
        try:
            if mode == "region":
                self._take_region_screenshot()
            elif mode == "fullscreen":
                self._take_fullscreen_screenshot()
            elif mode == "window":
                self._take_window_screenshot()
            elif mode == "quick":
                # 快速截图：直接截取全屏并保存，不需要编辑
                pixmap = self._grab_full_screen()
                if pixmap:
                    self._on_screenshot_taken(pixmap, auto_save=True)
                    self._reset_screenshot_state()  # 重置状态
            else:
                log.error(f"未知的截图模式: {mode}")
                self._reset_screenshot_state()
        except Exception as e:
            log.error(f"执行截图操作失败: {str(e)}")
            self._reset_screenshot_state()

# 创建单例实例
screenshot_manager = ScreenshotManager() 