from PySide6.QtWidgets import QApplication

def new_file(self):
    """
    创建一个新的未命名文件
    
    Args:
        self: HanabiNotesApp实例
    """
    print("创建新的未命名标签页")
    index = self.sidebar.addTab("未命名")
    editorIndex = self.createNewEditor()
    
    # 设置初始内容（如果需要）
    if 0 <= editorIndex < len(self.editors):
        editor = self.editors[editorIndex]
        # 确保编辑器为空并获得焦点
        editor.clear()
        editor.setFocus()
        
    # 记录新标签页信息，特别标记为虚拟标签页（无文件路径）
    self.openFiles.append({
        'index': index,
        'editorIndex': editorIndex,
        'filePath': None,
        'title': "未命名",
        'isVirtual': True  # 标记为虚拟标签页
    })
    
    # 更新当前文件信息
    self.currentFilePath = None
    self.currentTitle = "未命名"
    
    # 更新窗口标题和状态栏
    self.setWindowTitle("Hanabi Notes - 未命名")
    self.updateLineCount(self.editors[editorIndex])
    
    # 确保将主题样式应用到新创建的编辑器区域
    if hasattr(self, 'editorsStack') and self.editorsStack.count() > 0:
        stackWidget = self.editorsStack.widget(editorIndex)
        if stackWidget and hasattr(self, 'themeManager') and self.themeManager:
            print("为新标签页应用主题样式")
            # 检查堆栈控件的子控件
            for i in range(stackWidget.count()):
                container = stackWidget.widget(i)
                if container:
                    self.updateEditorContainerStyle(container)
            
            # 确保编辑器样式更新
            if 0 <= editorIndex < len(self.editors):
                fontSize = 15
                if hasattr(self, 'statusBarWidget') and hasattr(self.statusBarWidget, 'currentFontSize'):
                    fontSize = self.statusBarWidget.currentFontSize
                self.updateEditorStyle(self.editors[editorIndex], fontSize)
    
    print(f"新建虚拟标签页完成，索引: {index}, 编辑器索引: {editorIndex}")
    
    # 强制处理事件以确保UI更新
    QApplication.processEvents() 