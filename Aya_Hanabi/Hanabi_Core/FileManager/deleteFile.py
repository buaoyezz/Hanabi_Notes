import os
from PySide6.QtWidgets import QMessageBox

def delete_file(self):
    """
    删除当前活动标签页对应的文件
    
    Args:
        self: HanabiNotesApp实例
    """
    activeInfo = self.sidebar.getActiveTabInfo()
    if not activeInfo or not activeInfo.get('filePath'):
        QMessageBox.information(self, "删除文件", "没有打开的文件可以删除。")
        return
    
    filePath = activeInfo.get('filePath')
    fileName = activeInfo.get('fileName')
    
    reply = QMessageBox.question(
        self, "删除文件", 
        f"确定要删除文件 {fileName} 吗？此操作不可恢复。",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
    )
    
    if reply == QMessageBox.Yes:
        try:
            # 使用FileManager来删除文件
            success = self.fileManager.deleteFile(filePath, self)
            if success:
                self.sidebar.closeTab(self.sidebar.activeTabIndex)
                QMessageBox.information(self, "删除成功", "文件已成功删除。")
        except Exception as e:
            QMessageBox.warning(self, "删除失败", f"无法删除文件: {str(e)}")
    
    self.changeFontSize(self.statusBarWidget.currentFontSize) 