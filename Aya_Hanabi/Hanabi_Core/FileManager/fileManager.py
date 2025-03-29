import os
import json
from PySide6.QtCore import QObject, Signal, QSettings
from PySide6.QtWidgets import QFileDialog, QMessageBox
from Aya_Hanabi.Hanabi_Core.UI.messageBox import HanabiMessageBox, information, warning, critical, question, success

class FileManager(QObject):
    # 文件内容加载信号
    fileLoaded = Signal(str, str)  # 标题, 内容
    fileSaved = Signal(str, str)   # 文件路径, 状态消息
    fileDeleted = Signal(str)      # 文件路径
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lastOpenDir = ""
        self.lastSaveDir = ""
        
        # 加载上次使用的目录
        self.settings = QSettings("HanabiNotes", "FileManager")
        self.lastOpenDir = self.settings.value("lastOpenDir", "")
        self.lastSaveDir = self.settings.value("lastSaveDir", "")
    
    def openFile(self, parent=None, title="打开文件", fileTypes="Markdown文件 (*.md *.markdown);;所有文件 (*)"):
            
        # 如果上次打开的目录不存在，则使用当前目录
        startDir = self.lastOpenDir if os.path.exists(self.lastOpenDir) else ""
        
        filePath, _ = QFileDialog.getOpenFileName(
            parent, title, startDir, fileTypes
        )
        
        if not filePath:
            return None, None, None
        
        # 保存最后打开的目录
        self.lastOpenDir = os.path.dirname(filePath)
        self.settings.setValue("lastOpenDir", self.lastOpenDir)
        
        try:
            with open(filePath, 'r', encoding='utf-8') as file:
                content = file.read()
                
            # 获取文件名作为标题
            filename = os.path.basename(filePath)
            title = os.path.splitext(filename)[0]
            
            return filePath, title, content
        except Exception as e:
            if parent:
                warning(parent, "打开失败", f"无法打开文件: {str(e)}")
            return None, None, None
    
    def saveFile(self, content, defaultName="未命名", parent=None, title="保存文件", fileTypes="Markdown文件 (*.md);;所有文件 (*)"):
        
        # 如果上次保存的目录不存在，则使用当前目录
        startDir = self.lastSaveDir if os.path.exists(self.lastSaveDir) else ""
        startPath = os.path.join(startDir, f"{defaultName}.md")
        
        filePath, _ = QFileDialog.getSaveFileName(
            parent, title, startPath, fileTypes
        )
        
        if not filePath:
            return None
        
        # 保存最后保存的目录
        self.lastSaveDir = os.path.dirname(filePath)
        self.settings.setValue("lastSaveDir", self.lastSaveDir)
        
        try:
            with open(filePath, 'w', encoding='utf-8') as file:
                file.write(content)
            
            return filePath
        except Exception as e:
            if parent:
                warning(parent, "保存失败", f"无法保存文件: {str(e)}")
            return None
    
    def readFile(self, filePath):
        try:
            with open(filePath, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"读取文件失败: {str(e)}")
            return None
    
    def writeFile(self, filePath, content):
        try:
            with open(filePath, 'w', encoding='utf-8') as file:
                file.write(content)
            return True
        except Exception as e:
            print(f"写入文件失败: {str(e)}")
            return False

    def deleteFile(self, filePath, parent=None):
        """
        删除指定路径的文件
        
        Args:
            filePath: 要删除的文件路径
            parent: 父窗口，用于显示对话框
            
        Returns:
            bool: 删除是否成功
        """
        if not filePath or not os.path.exists(filePath):
            if parent:
                warning(parent, "删除失败", "文件不存在")
            return False
        
        try:
            os.remove(filePath)
            self.fileDeleted.emit(filePath)
            return True
        except Exception as e:
            if parent:
                warning(parent, "删除失败", f"无法删除文件: {str(e)}")
            return False 