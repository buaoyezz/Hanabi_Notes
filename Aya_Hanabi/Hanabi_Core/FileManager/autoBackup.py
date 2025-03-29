import os
import time
import datetime
import shutil
import json
import traceback

class AutoBackup:
    def __init__(self, parent=None, backup_path=None, max_backups=10):
        """
        初始化自动备份功能
        
        parent: HanabiNotesApp实例
        backup_path: 备份文件保存路径，默认为用户文档下的Hanabi_Backups文件夹
        max_backups: 每个文件保留的最大备份数量
        """
        self.parent = parent
        
        # 设置备份路径
        if backup_path:
            self.backup_path = backup_path
        else:
            self.backup_path = os.path.join(os.path.expanduser("~"), "Documents", "Hanabi_Backups")
        
        # 创建备份目录
        if not os.path.exists(self.backup_path):
            try:
                os.makedirs(self.backup_path)
                print(f"已创建备份目录: {self.backup_path}")
            except Exception as e:
                print(f"创建备份目录失败: {e}")
                # 如果无法创建，则使用程序目录
                self.backup_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Backups")
                if not os.path.exists(self.backup_path):
                    os.makedirs(self.backup_path)
        
        self.max_backups = max_backups
        self.backup_index = {}  # 记录每个文件的备份索引
        self.backup_history = {}  # 记录每个文件的备份历史
        
        # 加载备份历史记录
        self.load_backup_history()
        
        print(f"自动备份功能已初始化，备份路径: {self.backup_path}")
    
    def load_backup_history(self):
        """加载备份历史记录"""
        history_file = os.path.join(self.backup_path, "backup_history.json")
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.backup_history = data.get('history', {})
                    self.backup_index = data.get('index', {})
                print(f"已加载备份历史记录，共 {len(self.backup_history)} 个文件")
            except Exception as e:
                print(f"加载备份历史记录失败: {e}")
    
    def save_backup_history(self):
        """保存备份历史记录"""
        history_file = os.path.join(self.backup_path, "backup_history.json")
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'history': self.backup_history,
                    'index': self.backup_index
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存备份历史记录失败: {e}")
    
    def create_backup(self, file_path, content=None):
        """
        创建文件备份
        
        file_path: 要备份的文件路径
        content: 文件内容，如果为None则从文件读取
        """
        if not file_path:
            return False
        
        try:
            # 获取文件名和备份文件名
            filename = os.path.basename(file_path)
            file_dir = os.path.dirname(file_path)
            
            # 创建一个唯一的备份文件名
            backup_index = self.backup_index.get(file_path, 0) + 1
            self.backup_index[file_path] = backup_index
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{os.path.splitext(filename)[0]}_{timestamp}_{backup_index}{os.path.splitext(filename)[1]}.bak"
            
            # 确保文件夹结构
            relative_dir = os.path.relpath(file_dir, os.path.dirname(os.path.dirname(file_path)))
            backup_dir = os.path.join(self.backup_path, relative_dir)
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # 保存备份
            if content is not None:
                # 如果提供了内容，直接写入备份文件
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                # 否则复制原文件
                shutil.copy2(file_path, backup_path)
            
            # 更新备份历史
            if file_path not in self.backup_history:
                self.backup_history[file_path] = []
            
            self.backup_history[file_path].append({
                'backup_path': backup_path,
                'timestamp': timestamp,
                'index': backup_index
            })
            
            # 保留最新的N个备份
            if len(self.backup_history[file_path]) > self.max_backups:
                oldest_backup = self.backup_history[file_path].pop(0)
                if os.path.exists(oldest_backup['backup_path']):
                    os.remove(oldest_backup['backup_path'])
            
            # 保存备份历史
            self.save_backup_history()
            
            print(f"已创建备份: {backup_path}")
            return True
        except Exception as e:
            print(f"创建备份失败: {e}")
            traceback.print_exc()
            return False
    
    def backup_all_open_files(self):
        """备份所有打开的文件"""
        if not self.parent or not hasattr(self.parent, 'openFiles'):
            return
        
        for file_info in self.parent.openFiles:
            file_path = file_info.get('filePath')
            if not file_path:
                continue
                
            editor_index = file_info.get('editorIndex')
            if 0 <= editor_index < len(self.parent.editors):
                try:
                    editor = self.parent.editors[editor_index]
                    content = editor.toPlainText()
                    self.create_backup(file_path, content)
                except Exception as e:
                    print(f"备份文件 {file_path} 时出错: {e}")
    
    def get_backups_for_file(self, file_path):
        """获取指定文件的所有备份"""
        return self.backup_history.get(file_path, [])
    
    def restore_backup(self, backup_path, target_path=None):
        """
        恢复备份
        
        backup_path: 备份文件路径
        target_path: 恢复的目标路径，如果为None则恢复到原文件
        """
        if not os.path.exists(backup_path):
            print(f"备份文件不存在: {backup_path}")
            return False
        
        try:
            # 如果没有指定目标路径，则尝试从历史记录中找到原始文件路径
            if not target_path:
                for file_path, backups in self.backup_history.items():
                    for backup in backups:
                        if backup['backup_path'] == backup_path:
                            target_path = file_path
                            break
                    if target_path:
                        break
            
            if not target_path:
                print("无法确定恢复目标路径")
                return False
            
            # 如果目标文件存在，先创建备份
            if os.path.exists(target_path):
                self.create_backup(target_path)
            
            # 恢复备份
            with open(backup_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"已恢复备份: {backup_path} -> {target_path}")
            return True
        except Exception as e:
            print(f"恢复备份失败: {e}")
            traceback.print_exc()
            return False 