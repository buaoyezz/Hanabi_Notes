import time
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QFont, QTextCursor, QColor, QPalette, QFontMetrics

class EditorWidget(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 基本设置
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.setTabStopDistance(QFontMetrics(self.font()).horizontalAdvance(' ') * 4)
        
        # 性能优化：设置文档最大块计数，防止文档过大影响性能
        self.document().setMaximumBlockCount(1000000)  # 设置最大块计数
        
        # 设置自定义的垂直滚动条策略，减少不必要的刷新
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 防抖定时器 - 用于处理连续输入时的延迟更新
        self.updateTimer = QTimer(self)
        self.updateTimer.setSingleShot(True)
        self.updateTimer.timeout.connect(self.delayedUpdate)
        
        # 上次修改时间 - 用于性能监控
        self.lastModifiedTime = 0
        
        # 性能优化：设置视口更新模式，减少重绘次数
        self.setViewportUpdateMode(QPlainTextEdit.ViewportUpdateMode.MinimalViewportUpdate)
        
        # 缓存高亮器实例，避免重复创建
        self.highlighter = None
        
        # 当前文本内容的哈希，用于检测是否真的变化
        self.lastContentHash = None
        
        # 设置默认字体
        defaultFont = QFont("Consolas", 10)
        defaultFont.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(defaultFont)
        
        # 连接信号与槽
        self.textChanged.connect(self.onTextChangedDebounced)
        self.cursorPositionChanged.connect(self.onCursorPositionChangedDebounced)
    
    def onTextChangedDebounced(self):
        """
        文本变化的防抖处理
        防止连续输入时频繁触发更新
        """
        # 检查内容是否真的变化了
        currentContent = self.toPlainText()
        currentHash = hash(currentContent)
        
        if self.lastContentHash == currentHash:
            return  # 内容没有变化，不触发更新
        
        self.lastContentHash = currentHash
        self.lastModifiedTime = time.time()
        
        # 取消前一个定时器，设置新的延时更新
        self.updateTimer.stop()
        self.updateTimer.start(300)  # 300毫秒后触发更新
    
    def onCursorPositionChangedDebounced(self):
        """光标位置变化的防抖处理"""
        # 使用计时器延迟处理光标位置变化事件
        self.updateTimer.stop()
        self.updateTimer.start(100)  # 100毫秒后触发更新
    
    def delayedUpdate(self):
        """延迟更新处理函数"""
        try:
            # 更新行号显示
            if hasattr(self, 'lineNumberArea') and self.lineNumberArea:
                self.updateLineNumberAreaWidth(0)
            
            # 当前行高亮
            self.highlightCurrentLine()
            
            # 通知父组件文本已更改
            if hasattr(self.parent(), 'onEditorTextChanged'):
                self.parent().onEditorTextChanged()
        except Exception as e:
            print(f"编辑器延迟更新错误: {e}")
    
    def setSyntaxHighlightFromName(self, highlightName):
        """根据名称设置语法高亮"""
        from Aya_Hanabi.Hanabi_HighLight import get_highlighter
        
        try:
            # 如果已有高亮器，先移除它
            if self.highlighter:
                self.highlighter.setDocument(None)
            
            # 获取并应用新的高亮器
            self.highlighter = get_highlighter(highlightName)
            if self.highlighter:
                self.highlighter.setDocument(self.document())
                print(f"已设置{highlightName}语法高亮")
            else:
                print(f"未找到{highlightName}语法高亮器")
        except Exception as e:
            print(f"设置语法高亮时出错: {e}")
    
    def highlightCurrentLine(self):
        """高亮当前行"""
        try:
            extraSelections = []
            
            if not self.isReadOnly():
                selection = QTextEdit.ExtraSelection()
                lineColor = QColor(Qt.GlobalColor.darkBlue).darker(400)
                selection.format.setBackground(lineColor)
                selection.format.setProperty(QTextEdit.ExtraSelectionProperty.FullWidth, True)
                selection.cursor = self.textCursor()
                selection.cursor.clearSelection()
                extraSelections.append(selection)
            
            self.setExtraSelections(extraSelections)
        except Exception as e:
            print(f"高亮当前行时出错: {e}")
    
    def resizeEvent(self, event):
        """重写调整大小事件，优化处理"""
        super().resizeEvent(event)
        
        # 仅当有行号区域时更新
        if hasattr(self, 'lineNumberArea') and self.lineNumberArea:
            cr = self.contentsRect()
            self.lineNumberArea.setGeometry(
                cr.left(), cr.top(), 
                self.lineNumberAreaWidth(), cr.height()
            )
    
    def lineNumberAreaWidth(self):
        """计算行号区域的宽度，优化性能"""
        if not hasattr(self, 'showLineNumbers') or not self.showLineNumbers:
            return 0
            
        # 计算数字的位数
        digits = 1
        max_blocks = max(1, self.document().blockCount())
        while max_blocks >= 10:
            max_blocks //= 10
            digits += 1
            
        # 计算宽度（使用字体度量计算更准确）
        space = 10 + self.fontMetrics().horizontalAdvance('9') * digits
        
        return space
    
    def wheelEvent(self, event):
        """优化滚轮事件处理，减少不必要的渲染"""
        # 使用更大的滚动步长
        delta = event.angleDelta().y()
        if abs(delta) > 0:
            # 如果按住Ctrl键，改变字体大小
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                if delta > 0:
                    self.zoomIn(1)
                else:
                    self.zoomOut(1)
                event.accept()
                return
            
            # 普通滚动，使用更大的步长
            scrollLines = max(1, abs(delta) // 40)  # 自适应滚动行数
            if delta > 0:
                self.verticalScrollBar().setValue(
                    self.verticalScrollBar().value() - scrollLines
                )
            else:
                self.verticalScrollBar().setValue(
                    self.verticalScrollBar().value() + scrollLines
                )
            event.accept()
        else:
            super().wheelEvent(event) 