from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from core.log.log_manager import log
from core.utils.config_manager import config_manager, ConfigManager
from core.screenshot.screenshot_manager import screenshot_manager
import os

class WindowManager:
    _tray_icon = None
    
    @staticmethod
    def init():
        try:
            # 注册全局快捷键
            screenshot_manager.register_global_hotkeys()
            log.info("窗口管理器初始化完成")
        except Exception as e:
            log.error(f"窗口管理器初始化失败: {str(e)}")
    
    @staticmethod
    def cleanup():
        try:
            # 注销全局快捷键
            screenshot_manager.unregister_global_hotkeys()
            log.info("窗口管理器清理完成")
        except Exception as e:
            log.error(f"窗口管理器清理失败: {str(e)}")
    
    @staticmethod
    def handle_close_event(window, event):
        # 检查是否要最小化到托盘
        minimize_to_tray = config_manager.get_config('system', 'minimize_to_tray', True)
        
        if minimize_to_tray and WindowManager._tray_icon is None:
            # 第一次关闭窗口时创建托盘图标
            WindowManager._create_tray_icon(window)
            
        if minimize_to_tray and WindowManager._tray_icon is not None:
            # 最小化到托盘而不是关闭
            event.ignore()
            window.hide()
            
            # 显示托盘消息
            if not hasattr(window, '_has_shown_tray_message'):
                WindowManager._tray_icon.showMessage(
                    "Imagine Snap",
                    "应用程序已最小化到系统托盘",
                    QSystemTrayIcon.Information,
                    2000
                )
                window._has_shown_tray_message = True
                
            return
        
        # 正常关闭处理
        if window._closing:
            event.accept()
            return
            
        try:
            log.info("开始关闭应用程序")
            window._closing = True
            event.ignore()
            
            # 停止所有动画
            window.pages_manager.stop_animations()
            
            # 确保所有页面都停止扫描
            stacked_widget = window.pages_manager.get_stacked_widget()
            for i in range(stacked_widget.count()):
                page = stacked_widget.widget(i)
                if hasattr(page, 'safe_cleanup'):
                    page.safe_cleanup()
            
            # 延迟关闭
            window._cleanup_timer.start(1000)  # 给予1秒的清理时间
            
        except Exception as e:
            log.error(f"关闭应用程序时出错: {str(e)}")
            event.accept()

    @staticmethod
    def finish_close(window):
        try:
            # 强制清理所有页面的引用
            stacked_widget = window.pages_manager.get_stacked_widget()
            while stacked_widget.count() > 0:
                widget = stacked_widget.widget(0)
                stacked_widget.removeWidget(widget)
                if hasattr(widget, 'scanner'):
                    widget.scanner = None
                widget.deleteLater()
            
            # 删除托盘图标
            if WindowManager._tray_icon is not None:
                WindowManager._tray_icon.hide()
                WindowManager._tray_icon = None
                
            # 清理其他资源
            QApplication.processEvents()
            
            # 确保主窗口关闭
            window.close()
            
        except Exception as e:
            log.error(f"完成关闭时出错: {str(e)}")
            window.close()

    @staticmethod
    def switch_page(window, page_name):
        try:
            # 获取页面索引
            page_index = {
                "快速开始": 0,
                "关于": 1,
            }.get(page_name)
            
            if page_index is not None:
                # 切换到对应页面
                window.pages_manager.get_stacked_widget().setCurrentIndex(page_index)
                # 更新侧边栏选中状态
                if hasattr(window, 'sidebar'):
                    window.sidebar.select_item(page_name)
                log.info(f"切换到页面: {page_name}")
            else:
                log.error(f"未找到页面: {page_name}")
                
        except Exception as e:
            log.error(f"切换页面失败: {str(e)}")
            
    @staticmethod
    def _create_tray_icon(window):
        try:
            # 创建托盘图标
            tray_icon = QSystemTrayIcon(window)
            
            # 设置图标
            from core.utils.resource_manager import ResourceManager
            resource_manager = ResourceManager()
            
            # 使用白色图标 white_256
            icon_path = resource_manager.get_resource_path(os.path.join("resources", "white_256.png"))
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
                tray_icon.setIcon(icon)
                log.info(f"成功加载托盘图标: {icon_path}")
            else:
                # 如果白色图标不存在，尝试使用默认图标
                icon = resource_manager.get_icon("small_256")
                if icon:
                    tray_icon.setIcon(icon)
                    log.info("使用默认图标作为托盘图标")
                    
            # 创建右键菜单
            tray_menu = QMenu()
            
            # 恢复窗口动作
            show_action = QAction("显示主窗口", window)
            show_action.triggered.connect(lambda: WindowManager._show_main_window(window))
            tray_menu.addAction(show_action)
            
            # 添加分隔符
            tray_menu.addSeparator()
            
            # 全屏截图
            fullscreen_action = QAction("全屏截图", window)
            fullscreen_action.triggered.connect(lambda: WindowManager._trigger_screenshot(window, "fullscreen"))
            tray_menu.addAction(fullscreen_action)
            
            # 区域截图
            region_action = QAction("区域截图", window)
            region_action.triggered.connect(lambda: WindowManager._trigger_screenshot(window, "region"))
            tray_menu.addAction(region_action)
            
            # 窗口截图
            window_action = QAction("窗口截图", window)
            window_action.triggered.connect(lambda: WindowManager._trigger_screenshot(window, "window"))
            tray_menu.addAction(window_action)
            
            # 添加分隔符
            tray_menu.addSeparator()
            
            # 退出动作
            exit_action = QAction("退出", window)
            exit_action.triggered.connect(lambda: WindowManager._exit_application(window))
            tray_menu.addAction(exit_action)
            
            # 设置托盘图标菜单
            tray_icon.setContextMenu(tray_menu)
            
            # 单击托盘图标显示主窗口
            tray_icon.activated.connect(lambda reason: WindowManager._on_tray_activated(window, reason))
            
            # 显示托盘图标
            tray_icon.show()
            
            # 保存托盘图标引用
            WindowManager._tray_icon = tray_icon
            
            log.info("系统托盘图标创建成功")
            
        except Exception as e:
            log.error(f"创建系统托盘图标失败: {str(e)}")
    
    @staticmethod
    def _show_main_window(window):
        window.showNormal()
        window.activateWindow()
        log.info("从托盘恢复主窗口")
    
    @staticmethod
    def _exit_application(window):
        try:
            log.info("从托盘菜单退出应用程序")
            
            # 设置强制退出标志
            window._force_quit = True
            
            # 禁用最小化到托盘
            window._closing = True
            
            # 清理托盘图标
            if WindowManager._tray_icon:
                WindowManager._tray_icon.hide()
                WindowManager._tray_icon = None
            
            # 清理窗口管理器
            WindowManager.cleanup()
            
            # 关闭主窗口
            window.close()
            
            # 直接退出应用程序
            QApplication.quit()
            
        except Exception as e:
            log.error(f"从托盘菜单退出应用程序失败: {str(e)}")
            # 强制退出
            import sys
            sys.exit(0)
    
    @staticmethod
    def _on_tray_activated(window, reason):
        # 单击或双击显示主窗口
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            WindowManager._show_main_window(window)
    
    @staticmethod
    def _trigger_screenshot(window, mode):
        try:
            log.info(f"从托盘菜单触发{mode}截图")
            # 调用截图管理器进行截图
            from core.screenshot.screenshot_manager import ScreenshotManager
            
            # 检查是否自动保存
            config_manager = ConfigManager()
            auto_save = config_manager.get_config('screenshot', 'autosave', False)
            
            # 如果是快速截图，直接截图并保存
            if mode == "quick":
                screenshot_manager = ScreenshotManager()
                screenshot_manager.start_screenshot(mode)
            # 如果从托盘激活的是区域截图或窗口截图，自动开启
            elif mode in ["region", "window", "fullscreen"]:
                screenshot_manager = ScreenshotManager()
                screenshot_manager.start_screenshot(mode)
        except Exception as e:
            log.error(f"触发截图失败: {str(e)}") 