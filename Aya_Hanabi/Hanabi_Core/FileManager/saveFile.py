import os
from PySide6.QtWidgets import QMessageBox

def save_file(self):
    """
    保存文件的功能实现
    
    self: HanabiNotesApp实例
    """
    if self.sidebar.activeTabIndex < 0:
        return
    
    activeInfo = self.sidebar.getActiveTabInfo()
    if not activeInfo:
        return
    
    currentEditorIndex = -1
    filePath = activeInfo.get('filePath')
    
    if filePath:
        for file_info in self.openFiles:
            if file_info.get('filePath') == filePath:
                currentEditorIndex = file_info.get('editorIndex')
                break
    else:
        for file_info in self.openFiles:
            if file_info.get('index') == self.sidebar.activeTabIndex:
                currentEditorIndex = file_info.get('editorIndex')
                break
    
    if currentEditorIndex < 0 or currentEditorIndex >= len(self.editors):
        return
    
    content = self.editors[currentEditorIndex].toPlainText()
    filePath = self.fileManager.saveFile(content, activeInfo['fileName'], self)
    
    if filePath:
        self.sidebar.updateTabName(self.sidebar.activeTabIndex, os.path.splitext(os.path.basename(filePath))[0], filePath)
        
        oldFilePath = activeInfo.get('filePath')
        fileName = os.path.splitext(os.path.basename(filePath))[0]
        
        for file_info in self.openFiles:
            if oldFilePath is None:
                if file_info.get('index') == self.sidebar.activeTabIndex:
                    file_info['filePath'] = filePath
                    file_info['title'] = fileName
                    break
            elif file_info.get('filePath') == oldFilePath:
                file_info['filePath'] = filePath
                file_info['title'] = fileName
                break
        
        self.currentFilePath = filePath
        self.currentTitle = fileName
        
        self.setWindowTitle(f"Hanabi Notes - {self.currentTitle}")
