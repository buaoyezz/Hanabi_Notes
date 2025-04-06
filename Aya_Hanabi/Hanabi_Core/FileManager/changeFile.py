import os
from PySide6.QtWidgets import QApplication

def change_file(self, filePath, fileName):
    """
    切换到指定文件
    
    Args:
        self: HanabiNotesApp实例
        filePath: 文件路径
        fileName: 文件名
    """
    print(f"切换到文件：{fileName}，路径：{filePath}")
    
    # 更新当前文件信息 - 必须保证filePath不会被错误设为None
    self.currentFilePath = filePath  # 确保明确设置为传入的文件路径
    self.currentTitle = fileName
    
    # 更新窗口标题
    self.setWindowTitle(f"Hanabi Notes - {fileName}")
    
    # 获取当前活动标签索引
    try:
        current_tab_index = self.sidebar.current_tab_index
        if current_tab_index is None:  # 如果为None，设为0
            current_tab_index = 0
    except Exception as e:
        print(f"获取活动标签索引时出错: {e}")
        current_tab_index = 0  # 默认值
    
    print(f"当前活动标签索引: {current_tab_index}")
    
    # 查找对应的编辑器索引
    editorIndex = -1
    fileInfo = None
    
    # 首先尝试通过文件路径查找（如果提供了路径）
    if filePath is not None:
        for info in self.openFiles:
            if info.get('filePath') == filePath:
                fileInfo = info
                editorIndex = info.get('editorIndex')
                print(f"通过文件路径找到编辑器索引: {editorIndex}")
                break
    
    # 如果通过路径没找到，则尝试通过标签索引查找
    if editorIndex == -1:
        for info in self.openFiles:
            if info.get('index') == current_tab_index:
                fileInfo = info
                editorIndex = info.get('editorIndex')
                print(f"通过活动标签索引 {current_tab_index} 找到编辑器索引: {editorIndex}")
                break
    
    # 如果仍未找到，可能是新打开的虚拟标签页或文件
    if editorIndex == -1:
        print(f"未找到对应编辑器，创建新的编辑器")
        
        # 创建新的编辑器
        newEditorIndex = self.createNewEditor()
        
        # 如果有文件路径，尝试加载文件内容
        if filePath:
            try:
                with open(filePath, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                if 0 <= newEditorIndex < len(self.editors):
                    self.editors[newEditorIndex].setPlainText(content)
                    print(f"从文件加载内容，长度：{len(content)}")
            except Exception as e:
                print(f"加载文件内容时出错：{e}")
        
        # 记录文件信息
        fileInfo = {
            'index': current_tab_index,
            'editorIndex': newEditorIndex,
            'filePath': filePath,
            'title': fileName
        }
        if filePath is None:
            fileInfo['isVirtual'] = True  # 标记为虚拟标签页
        
        self.openFiles.append(fileInfo)
        
        print(f"创建新编辑器成功，索引：{newEditorIndex}, 虚拟标签: {filePath is None}")
        
        # 更新行数统计
        if 0 <= newEditorIndex < len(self.editors):
            self.updateLineCount(self.editors[newEditorIndex])
        
        # 确保当前编辑器引用更新
        self.currentEditor = self.editors[newEditorIndex]
        print(f"已设置当前编辑器为: {newEditorIndex}, 当前文件路径: {filePath}")
        
        return
    
    # 切换到对应的编辑器
    if 0 <= editorIndex < len(self.editors):
        editor = self.editors[editorIndex]
        self.editorsStack.setCurrentIndex(editorIndex)
        # 重要：更新当前编辑器引用
        self.currentEditor = editor
        print(f"切换到编辑器索引: {editorIndex}")
        
        # 明确更新当前文件路径，确保它与fileInfo一致
        if fileInfo:
            self.currentFilePath = fileInfo.get('filePath')
            print(f"确认当前文件路径: {self.currentFilePath}")
        
        # 更新行数计数
        self.updateLineCount(editor)
        
        # 先确定文件类型，再应用高亮
        if fileInfo and fileInfo.get('filePath'):
            from Aya_Hanabi.Hanabi_HighLight import detect_file_type
            self.currentFileType = detect_file_type(fileInfo.get('filePath'))
        else:
            self.currentFileType = "text"  # 默认为普通文本
            
        print(f"已切换到编辑器索引：{editorIndex}，文件类型：{self.currentFileType}")
        
        # 应用高亮 - 移到文件类型确定后
        if hasattr(self, 'highlightMode') and self.highlightMode:
            # 直接传递当前文件类型，确保高亮使用正确的类型
            self.applyHighlighter(editor, self.currentFileType)
    else:
        print(f"未找到对应编辑器，创建新的编辑器")
        
        # 创建新的编辑器
        newEditorIndex = self.createNewEditor()
        
        # 如果有文件路径，尝试加载文件内容
        if filePath:
            try:
                with open(filePath, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                if 0 <= newEditorIndex < len(self.editors):
                    self.editors[newEditorIndex].setPlainText(content)
                    print(f"从文件加载内容，长度：{len(content)}")
            except Exception as e:
                print(f"加载文件内容时出错：{e}")
        
        # 记录文件信息
        fileInfo = {
            'index': current_tab_index,
            'editorIndex': newEditorIndex,
            'filePath': filePath,
            'title': fileName
        }
        if filePath is None:
            fileInfo['isVirtual'] = True  # 标记为虚拟标签页
        
        self.openFiles.append(fileInfo)
        
        # 确保当前编辑器引用更新
        self.currentEditor = self.editors[newEditorIndex]
        print(f"已设置当前编辑器为: {newEditorIndex}, 当前文件路径: {filePath}")
        
        print(f"创建新编辑器成功，索引：{newEditorIndex}, 虚拟标签: {filePath is None}")
        
        # 更新行数统计
        if 0 <= newEditorIndex < len(self.editors):
            self.updateLineCount(self.editors[newEditorIndex]) 