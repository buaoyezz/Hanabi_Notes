import datetime
from Aya_Hanabi.Hanabi_Core.UI.messageBox import HanabiMessageBox, question, information

def close_file(self, filePath):
    """
    关闭指定文件
    
    Args:
        self: HanabiNotesApp实例
        filePath: 要关闭的文件路径
    """
    print(f"关闭文件：{filePath}")
    
    # 检查是否只有一个标签页，如果是则不允许关闭
    if len(self.sidebar.tabs) <= 1:
        print("这是最后一个标签页，不允许关闭")
        information(self, "操作提示", "至少需要保留一个标签页")
        return
    
    editorIndex = -1
    fileIndex = -1
    isVirtual = not filePath  # 标记是否为虚拟标签页
    
    # 处理虚拟标签页（无文件路径）的情况
    if isVirtual:
        print("正在关闭虚拟标签页")
        for i, tab_btn in enumerate(self.sidebar.tabs):
            if tab_btn.filePath is None:
                # 找到与当前活动标签页匹配的虚拟标签页
                if i == self.sidebar.current_tab_index:
                    for j, file_info in enumerate(self.openFiles):
                        if file_info.get('index') == i and file_info.get('filePath') is None:
                            editorIndex = file_info.get('editorIndex')
                            fileIndex = j
                            print(f"找到要关闭的虚拟标签页索引：{i}，编辑器索引：{editorIndex}")
                            break
                    break
    else:
        # 处理有文件路径的标签页
        for i, file_info in enumerate(self.openFiles):
            if file_info.get('filePath') == filePath:
                editorIndex = file_info.get('editorIndex')
                fileIndex = i
                print(f"找到要关闭的文件索引：{i}，编辑器索引：{editorIndex}")
                break
    
    if editorIndex >= 0 and fileIndex >= 0:
        # 检查文件是否被修改
        modified = False
        if hasattr(self, 'isTextModified'):
            try:
                modified = self.isTextModified(filePath)
                print(f"文件是否被修改: {modified}")
            except Exception as e:
                print(f"检查文件修改状态时出错: {e}")
        
        # 如果文件被修改，提示用户保存
        if modified:
            fileName = "未命名"
            # 尝试获取文件名
            for tab_btn in self.sidebar.tabs:
                if (isVirtual and tab_btn.filePath is None) or (not isVirtual and tab_btn.filePath == filePath):
                    fileName = tab_btn.fileName
                    break
            
            result = question(self, "保存文件", f"文件 {fileName} 已修改，是否保存？", 
                           HanabiMessageBox.YesNoCancel)
            
            if result == HanabiMessageBox.Yes_Result:
                # 保存文件
                if hasattr(self, 'saveFile'):
                    self.saveFile(filePath)
            elif result == HanabiMessageBox.Cancel_Result:
                # 取消关闭操作
                print("用户取消了关闭操作")
                return
            # 如果选择"No"，则不保存继续关闭
        
        # 从记录中移除文件信息
        self.openFiles.pop(fileIndex)
        
        # 记录关闭前的编辑器堆栈索引
        closed_stack_index = self.editorsStack.currentIndex()
        
        # 跟踪已关闭的编辑器
        if 0 <= editorIndex < len(self.editors):
            editor_info = {
                'editorIndex': editorIndex,
                'filePath': filePath,
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.closedEditors.append(editor_info)
            print(f"添加到已关闭编辑器列表：{editor_info}")
        
        # 更新剩余标签页的索引
        for i, tab_btn in enumerate(self.sidebar.tabs):
            for file_info in self.openFiles:
                if (tab_btn.filePath is None and file_info.get('filePath') is None) or \
                   (tab_btn.filePath == file_info.get('filePath')):
                    file_info['index'] = i
                    break
        
        print(f"关闭文件成功，剩余文件数量：{len(self.openFiles)}，已关闭编辑器数量：{len(self.closedEditors)}")
        
        # 如果没有剩余文件，创建一个新的空白标签页
        if len(self.openFiles) == 0:
            print("没有剩余文件，创建新的空白标签页")
            self.newFile()
        elif closed_stack_index == self.editorsStack.currentIndex():
            # 如果当前显示的是被关闭的编辑器，切换到其他编辑器
            print("当前编辑器被关闭，切换到其他编辑器")
            if len(self.openFiles) > 0:
                # 尝试切换到第一个可用的标签页
                first_file = self.openFiles[0]
                first_index = first_file.get('index')
                if 0 <= first_index < len(self.sidebar.tabs):
                    self.sidebar.activateTab(first_index, True)
        
        # 强制处理事件以确保UI更新
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents() 