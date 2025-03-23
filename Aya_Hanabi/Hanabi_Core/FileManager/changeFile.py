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
    
    # 更新当前文件信息
    self.currentFilePath = filePath
    self.currentTitle = fileName
    
    # 更新窗口标题
    self.setWindowTitle(f"Hanabi Notes - {fileName}")
    
    # 获取当前活动标签索引
    try:
        activeTabIndex = self.sidebar.activeTabIndex
        if activeTabIndex is None:  # 如果为None，设为0
            activeTabIndex = 0
    except Exception as e:
        print(f"获取活动标签索引时出错: {e}")
        activeTabIndex = 0  # 默认值
    
    print(f"当前活动标签索引: {activeTabIndex}")
    
    # 查找对应的编辑器索引
    editorIndex = -1
    fileInfo = None
    
    # 直接通过活动标签索引查找对应的文件信息
    for info in self.openFiles:
        if info.get('index') == activeTabIndex:
            fileInfo = info
            editorIndex = info.get('editorIndex')
            print(f"通过活动标签索引 {activeTabIndex} 找到编辑器索引: {editorIndex}")
            break
    
    # 如果通过标签索引没找到，但有文件路径，尝试通过文件路径查找
    if editorIndex == -1 and filePath is not None:
        for info in self.openFiles:
            if info.get('filePath') == filePath:
                fileInfo = info
                editorIndex = info.get('editorIndex')
                print(f"通过文件路径找到编辑器索引: {editorIndex}")
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
            'index': activeTabIndex,
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
        
        return
    
    # 切换到对应的编辑器
    if 0 <= editorIndex < len(self.editors):
        editor = self.editors[editorIndex]
        self.editorsStack.setCurrentIndex(editorIndex)
        print(f"切换到编辑器索引: {editorIndex}")
        
        # 更新行数计数
        self.updateLineCount(editor)
        
        # 应用高亮
        if hasattr(self, 'highlightMode') and self.highlightMode:
            self.applyHighlighter(editor)
        
        # 确定文件类型
        if fileInfo and fileInfo.get('filePath'):
            from Aya_Hanabi.Hanabi_HighLight import detect_file_type
            self.currentFileType = detect_file_type(fileInfo.get('filePath'))
        else:
            self.currentFileType = "text"  # 默认为普通文本
        
        print(f"已切换到编辑器索引：{editorIndex}，文件类型：{self.currentFileType}")
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
            'index': activeTabIndex,
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