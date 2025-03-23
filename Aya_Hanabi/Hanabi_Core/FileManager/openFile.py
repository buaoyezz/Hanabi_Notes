import os
from PySide6.QtWidgets import QFileDialog, QMessageBox, QApplication

def open_file(self):
    """
    打开文件的功能实现
    
    self: HanabiNotesApp实例
    """
    filePath, title, content = self.fileManager.openFile(self)
    if filePath:
        # 检查文件是否已经打开
        for i, file_info in enumerate(self.openFiles):
            if file_info.get('filePath') == filePath:
                editorIndex = file_info.get('editorIndex')
                print(f"文件已经打开，重新激活标签页: {i}，编辑器索引: {editorIndex}")
                
                # 确保编辑器内容是最新的
                if 0 <= editorIndex < len(self.editors):
                    try:
                        with open(filePath, 'r', encoding='utf-8') as file:
                            fresh_content = file.read()
                        self.editors[editorIndex].setPlainText(fresh_content)
                        print(f"更新已打开文件的内容，长度: {len(fresh_content)}")
                    except Exception as e:
                        print(f"更新已打开文件内容时出错: {e}")
                
                # 激活对应的标签页并立即返回
                self.sidebar.activateTab(file_info.get('index'), True)
                return
        
        # 文件尚未打开，创建新标签页
        index = self.sidebar.addTab(title, filePath)
        editorIndex = self.createNewEditor()
        
        # 设置编辑器内容
        if 0 <= editorIndex < len(self.editors):
            self.editors[editorIndex].setPlainText(content)
            print(f"新文件加载到编辑器，内容长度: {len(content)}")
        
        # 记录文件信息
        self.openFiles.append({
            'index': index,
            'editorIndex': editorIndex,
            'filePath': filePath,
            'title': title
        })
        
        # 更新当前文件信息
        self.currentFilePath = filePath
        self.currentTitle = title
        
        # 获取文件类型
        from Aya_Hanabi.Hanabi_HighLight import detect_file_type
        self.currentFileType = detect_file_type(filePath)
        print(f"打开文件类型: {self.currentFileType}")
        
        # 激活对应的标签页
        if self.sidebar.activeTabIndex != index:
            self.sidebar.activateTab(index, True)
        
        # 更新窗口标题
        self.setWindowTitle(f"Hanabi Notes - {title}")
        
        # 应用高亮
        if 0 <= editorIndex < len(self.editors) and hasattr(self, 'highlightMode') and self.highlightMode:
            self.applyHighlighter(self.editors[editorIndex])
