import os
import time
import datetime
from PySide6.QtCore import QTimer

class AutoSave:
    def __init__(self, parent=None, interval=120):
        """
        初始化自动保存功能
        
        parent: HanabiNotesApp实例
        interval: 自动保存间隔（秒）
        """
        self.parent = parent
        self.interval = interval
        self.lastSaveTime = {}  # 记录每个文件最后保存时间
        self.enabled = True
        self.timer = None
        
    def start(self):
        """启动自动保存定时器"""
        if not self.timer:
            self.timer = QTimer(self.parent)
            self.timer.timeout.connect(self.check_files)
            self.timer.start(10000)  # 每10秒检查一次
            print(f"自动保存功能已启用，检查间隔：10秒，保存间隔：{self.interval}秒")
    
    def stop(self):
        """停止自动保存定时器"""
        if self.timer:
            self.timer.stop()
            self.timer = None
            print("自动保存功能已禁用")
    
    def toggle(self):
        """切换自动保存状态"""
        self.enabled = not self.enabled
        if self.enabled:
            self.start()
        else:
            self.stop()
        return self.enabled
    
    def set_interval(self, seconds):
        """设置自动保存间隔"""
        self.interval = seconds
        print(f"自动保存间隔已设置为 {seconds} 秒")
    
    def check_files(self):
        """检查并保存需要自动保存的文件"""
        if not self.enabled or not self.parent:
            return
        
        current_time = time.time()
        
        # 检查所有打开的文件
        for file_info in self.parent.openFiles:
            file_path = file_info.get('filePath')
            editor_index = file_info.get('editorIndex')
            
            # 跳过未保存过的文件（没有文件路径）
            if not file_path:
                continue
                
            # 检查是否需要保存
            last_save = self.lastSaveTime.get(file_path, 0)
            if current_time - last_save >= self.interval:
                if 0 <= editor_index < len(self.parent.editors):
                    try:
                        editor = self.parent.editors[editor_index]
                        content = editor.toPlainText()
                        
                        # 直接写入文件而不显示对话框
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                            
                        # 更新最后保存时间
                        self.lastSaveTime[file_path] = current_time
                        
                        # 获取当前时间
                        now = datetime.datetime.now().strftime("%H:%M:%S")
                        print(f"[{now}] 已自动保存文件: {os.path.basename(file_path)}")
                    except Exception as e:
                        print(f"自动保存文件时出错: {e}")
    
    def file_saved(self, file_path):
        """手动保存文件后更新时间记录"""
        if file_path:
            self.lastSaveTime[file_path] = time.time()
