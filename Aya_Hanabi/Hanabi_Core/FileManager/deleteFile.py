import os
from Aya_Hanabi.Hanabi_Core.UI.messageBox import HanabiMessageBox, information, warning, critical, question, success

def delete_file(self):
    """
    删除当前活动标签页对应的文件
    
    Args:
        self: HanabiNotesApp实例
    """
    activeInfo = self.sidebar.getActiveTabInfo()
    if not activeInfo or not activeInfo.get('filePath'):
        information(self, "删除文件", "没有打开的文件可以删除。")
        return
    
    filePath = activeInfo.get('filePath')
    fileName = activeInfo.get('fileName')
    
    reply = question(
        self, "删除文件", f"确定要删除文件 {fileName} 吗？此操作不可恢复。", HanabiMessageBox.YesNo)
    
    if reply == HanabiMessageBox.Yes_Result:
        try:
            # 使用FileManager来删除文件
            success = self.fileManager.deleteFile(filePath, self)
            if success:
                self.sidebar.closeTab(self.sidebar.activeTabIndex)
                information(self, "删除成功", "文件已成功删除。")
        except Exception as e:
            warning(self, "删除失败", f"无法删除文件: {str(e)}")
    
    # 移除不必要的字体大小重置，避免可能的错误
    # self.changeFontSize(self.statusBarWidget.currentFontSize) 