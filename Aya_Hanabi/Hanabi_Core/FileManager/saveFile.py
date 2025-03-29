import os
import sys
import time
import shutil
import codecs
from pathlib import Path
from Aya_Hanabi.Hanabi_Core.UI.messageBox import HanabiMessageBox, information, warning, critical, question, success
from PySide6.QtWidgets import QFileDialog, QApplication, QDialog, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QPushButton, QWidget
from Aya_Hanabi.Hanabi_Core.UI.HanabiDialog import EncodingSelectionDialog

def get_encoding_name_to_python(encoding_name):
    """将UI显示的编码名称转换为Python的编码名称"""
    encoding_map = {
        "UTF-8": "utf-8",
        "ANSI": "cp1252",  # Windows下的ANSI通常是cp1252
        "UTF-16 LE": "utf-16-le",
        "UTF-16 BE": "utf-16-be",
        "UTF-8 BOM": "utf-8-sig",
        "GB18030": "gb18030"
    }
    return encoding_map.get(encoding_name, "utf-8")

def saveFile(self, savePath=None, encoding=None):
    start_time = time.time()
    
    if not hasattr(self, 'currentEditor') or self.currentEditor is None:
        print("没有可保存的编辑器内容")
        return False

    content = self.currentEditor.toPlainText()
    content_size = len(content)
    
    if content_size == 0:
        user_choice = question(
            self, "保存空文件", "当前文件内容为空，确定要保存空文件吗？", HanabiMessageBox.YesNo)
        if user_choice == HanabiMessageBox.No_Result:
            return False
    
    if savePath is None:
        savePath = self.currentFilePath
    
    if not savePath:
        fileTypeExtMap = {
            'python': '.py',
            'markdown': '.md',
            'html': '.html',
            'javascript': '.js',
            'json': '.json',
            'text': '.txt',
            'xml': '.xml',
            'yaml': '.yaml',
            'ini': '.ini',
            'toml': '.toml',
            'c': '.c',
            'cpp': '.cpp',
            'java': '.java',
            'cs': '.cs',
            'go': '.go',
            'rust': '.rs',
            'php': '.php',
            'sql': '.sql',
            'css': '.css',
            'bash': '.sh',
            'ruby': '.rb',
            'perl': '.pl',
            'typescript': '.ts'
        }
        
        defaultExt = fileTypeExtMap.get(self.currentFileType, '.txt')
        defaultFilter = f"当前类型 (*{defaultExt})"
        
        filters = (
            "所有文件 (*);;文本文件 (*.txt);;Python (*.py);;Markdown (*.md);;HTML (*.html);;CSS (*.css);;"
            "JavaScript (*.js);;TypeScript (*.ts);;JSON (*.json);;XML (*.xml);;YAML (*.yaml, *.yml);;"
            "INI (*.ini);;TOML (*.toml);;C/C++ (*.c *.cpp *.h *.hpp);;Java (*.java);;C# (*.cs);;"
            "Go (*.go);;Rust (*.rs);;PHP (*.php);;SQL (*.sql);;Bash (*.sh);;Ruby (*.rb);;Perl (*.pl)"
        )
        
        defaultFileName = ""
        currentEditorIndex = self.editorsStack.currentIndex()
        isVirtualTab = True
        
        if hasattr(self, 'openFiles') and self.openFiles:
            for fileInfo in self.openFiles:
                if fileInfo.get('editorIndex') == currentEditorIndex:
                    isVirtualTab = fileInfo.get('isVirtual', True)
                    
                    if not isVirtualTab and fileInfo.get('title'):
                        fileName = fileInfo.get('title')
                        
                        if not os.path.splitext(fileName)[1] and defaultExt:
                            fileName = f"{fileName}{defaultExt}"
                        
                        defaultFileName = fileName
                    break
        
        initialPath = self.lastDirectory or os.path.expanduser("~")
        if defaultFileName:
            initialPath = os.path.join(initialPath, defaultFileName)
        
        print(f"保存对话框默认文件名: {defaultFileName}")
        
        savePath, selectedFilter = QFileDialog.getSaveFileName(
            self, 
            "保存文件", 
            initialPath, 
            filters,
            defaultFilter
        )
    
    if savePath:
        # 如果没有提供编码，弹出编码选择对话框
        if encoding is None:
            # 获取当前使用的编码或默认编码
            current_encoding = getattr(self, 'last_used_encoding', "UTF-8")
            
            # 创建并显示自定义编码选择对话框
            encoding_dialog = EncodingSelectionDialog(self, current_encoding)
            if encoding_dialog.exec_() == QDialog.Accepted:
                selected_encoding_name = encoding_dialog.get_selected_encoding()
                encoding = get_encoding_name_to_python(selected_encoding_name)
                
                # 保存编码选择供下次使用
                self.last_used_encoding = selected_encoding_name
            else:
                return False  # 用户取消了编码选择
        
        try:
            self.lastDirectory = os.path.dirname(savePath)
            
            save_dir = os.path.dirname(savePath)
            if save_dir and not os.path.exists(save_dir):
                try:
                    os.makedirs(save_dir)
                    print(f"创建目录: {save_dir}")
                except Exception as e:
                    print(f"创建目录失败: {e}")
                    warning(self, "保存警告", f"无法创建目录 {save_dir}，将尝试保存到当前位置。")
            
            should_backup = False
            if hasattr(self, 'autoBackupManager') and self.autoBackupManager and os.path.exists(savePath):
                file_size = os.path.getsize(savePath)
                if file_size > 10240:
                    should_backup = True
                else:
                    try:
                        with open(savePath, 'r', encoding='utf-8') as f:
                            old_content = f.read()
                        if abs(len(old_content) - content_size) / max(1, len(old_content)) > 0.2:
                            should_backup = True
                    except:
                        should_backup = True
                
                if should_backup:
                    self.autoBackupManager.create_backup(savePath)
                    print(f"已创建文件备份: {savePath}")
            
            temp_path = f"{savePath}.temp"
            
            encoding_used = encoding
            try:
                with open(temp_path, 'w', encoding=encoding) as f:
                    f.write(content)
            except UnicodeEncodeError:
                error_msg = f"使用 {encoding} 编码保存文件失败，是否尝试使用其他编码？"
                retry_choice = question(
                    self, "编码错误", error_msg, HanabiMessageBox.YesNo)
                
                if retry_choice == HanabiMessageBox.Yes_Result:
                    # 递归调用但不指定路径以避免再次弹出文件选择对话框
                    return self.saveFile(savePath, None)
                else:
                    return False
            
            if os.path.exists(savePath):
                try:
                    os.remove(savePath)
                except Exception as e:
                    print(f"删除原文件时出错: {e}")
            
            try:
                os.rename(temp_path, savePath)
            except Exception as e:
                print(f"重命名临时文件失败，尝试直接复制: {e}")
                shutil.copy2(temp_path, savePath)
                try:
                    os.remove(temp_path)
                except:
                    pass
            
            self.currentFilePath = savePath
            fileName = os.path.basename(savePath)
            fileTitle = os.path.splitext(fileName)[0]
            
            suffix = os.path.splitext(fileName)[1].lower()
            file_type_map = {
                '.py': 'python',
                '.txt': 'text',
                '.md': 'markdown',
                '.html': 'html',
                '.htm': 'html',
                '.css': 'css',
                '.js': 'javascript',
                '.ts': 'typescript',
                '.json': 'json',
                '.xml': 'xml',
                '.yaml': 'yaml',
                '.yml': 'yaml',
                '.ini': 'ini',
                '.toml': 'toml',
                '.c': 'c',
                '.cpp': 'cpp',
                '.h': 'c',
                '.hpp': 'cpp',
                '.java': 'java',
                '.cs': 'cs',
                '.go': 'go',
                '.rs': 'rust',
                '.php': 'php',
                '.sql': 'sql',
                '.sh': 'bash',
                '.rb': 'ruby',
                '.pl': 'perl'
            }
            self.currentFileType = file_type_map.get(suffix, 'text')
            
            self.setWindowTitle(f"{fileName} - Hanabi Notes")
            if hasattr(self, 'updateWindowTitle'):
                self.updateWindowTitle()
            
            currentEditorIndex = self.editorsStack.currentIndex()
            for fileData in self.openFiles:
                if fileData.get('editorIndex') == currentEditorIndex:
                    fileData['isModified'] = False
                    fileData['isVirtual'] = False
                    fileData['filePath'] = savePath
                    fileData['title'] = fileTitle
                    fileData['last_save_time'] = time.time()
                    fileData['encoding'] = encoding_used  # 保存使用的编码
                    break
            
            if hasattr(self, 'sidebar') and hasattr(self.sidebar, 'updateTabName'):
                activeTabIndex = self.sidebar.activeTabIndex if hasattr(self.sidebar, 'activeTabIndex') else -1
                if activeTabIndex >= 0:
                    self.sidebar.updateTabName(activeTabIndex, fileTitle, savePath)
            
            if hasattr(self, 'autoSaveManager') and self.autoSaveManager:
                self.autoSaveManager.file_saved(savePath)
            
            if hasattr(self, 'addToRecentFiles'):
                self.addToRecentFiles(savePath)
            
            if hasattr(self, 'getFileInfo') and hasattr(self, 'updateFileInfo'):
                fileInfo = self.getFileInfo(savePath)
                self.updateFileInfo(fileInfo)
            
            if hasattr(self, 'highlightMode') and self.highlightMode and hasattr(self, 'applyHighlighter'):
                self.applyHighlighter(self.currentEditor)
            
            elapsed_time = time.time() - start_time
            save_speed = content_size / (elapsed_time + 0.001)
            print(f"文件已保存: {savePath}")
            print(f"保存性能: {elapsed_time:.3f}秒, {save_speed:.1f} 字符/秒, 使用编码: {encoding_used}")
            
            message = f"文件已保存: {fileName}\n大小: {content_size/1024:.1f} KB\n编码: {encoding_used}"
            information(self, "保存成功", message)
            
            return True
        except Exception as e:
            if hasattr(self, 'logError'):
                self.logError(f"保存文件出错: {str(e)}")
            else:
                print(f"保存文件出错: {str(e)}")
                import traceback
                traceback.print_exc()
            
            error_message = f"无法保存文件: {str(e)}\n路径: {savePath}"
            critical(self, "保存失败", error_message)
            return False
    return False