import os
import time
from PySide6.QtWidgets import QFileDialog, QMessageBox, QApplication, QWidget
from Aya_Hanabi.Hanabi_Core.UI.messageBox import HanabiMessageBox, information, warning, critical, question, success

# 添加一个标志位来跟踪是否已经在处理文件打开操作
_file_open_in_progress = False
_last_open_time = 0  # 记录上次打开文件的时间

def open_file(self):
    """
    打开文件的功能实现，支持多种文件类型，并优化性能
    
    self: HanabiNotesApp实例或其父窗口
    """
    global _file_open_in_progress, _last_open_time
    
    # 增加时间防抖，避免短时间内多次触发
    current_time = time.time()
    if current_time - _last_open_time < 1.0:  # 1秒内不允许重复打开
        print(f"防抖：上次打开才过去 {current_time - _last_open_time:.2f} 秒，忽略此次调用")
        return None, None, None
    
    # 防止重复打开（递归调用或多次调用）
    if _file_open_in_progress:
        print("已有文件打开操作正在进行中，忽略此次调用")
        return None, None, None
    
    # 设置标志位，防止重入
    _file_open_in_progress = True
    _last_open_time = current_time
    
    try:
        # 检查是否是主应用实例，而不是侧边栏或其他组件
        is_main_app = hasattr(self, 'openFiles') and hasattr(self, 'editors')
        
        # 如果不是主应用实例，尝试找到主窗口
        if not is_main_app:
            print("调用者不是HanabiNotesApp实例，尝试查找主窗口")
            # 找到主窗口的几种方法
            main_app = None
            
            # 方法1：通过parent()方法向上查找
            parent = self
            for _ in range(5):  # 最多向上查找5层，避免无限循环
                if not parent:
                    break
                    
                if hasattr(parent, 'openFiles') and hasattr(parent, 'editors'):
                    main_app = parent
                    print(f"通过parent()找到主窗口: {main_app}")
                    break
                    
                if hasattr(parent, 'parent'):
                    parent = parent.parent()
                else:
                    break
            
            # 方法2：如果方法1没找到，尝试window()方法
            if not main_app and hasattr(self, 'window'):
                window = self.window()
                if hasattr(window, 'openFiles') and hasattr(window, 'editors'):
                    main_app = window
                    print(f"通过window()找到主窗口: {main_app}")
            
            # 方法3：查看顶层窗口
            if not main_app:
                for widget in QApplication.topLevelWidgets():
                    if hasattr(widget, 'openFiles') and hasattr(widget, 'editors'):
                        main_app = widget
                        print(f"通过topLevelWidgets找到主窗口: {main_app}")
                        break
            
            # 如果找到主窗口，则将调用转发给主窗口
            if main_app:
                print(f"找到有效的主窗口，将调用转发到主窗口")
                # 临时重置标志位，因为我们会递归调用open_file
                _file_open_in_progress = False
                _last_open_time = 0  # 重置时间戳允许主窗口打开
                result = open_file(main_app)
                # 递归调用后重新设置标志位，继续防止重入
                _file_open_in_progress = True
                return result
            
            # 找不到主窗口，显示错误并返回
            print("无法找到有效的主窗口，无法打开文件")
            warning(self, "操作错误", "无法打开文件：应用程序状态异常")
            return None, None, None
        
        # 正常的文件打开流程（此时self应该是主应用实例）
        # 扩展支持的文件类型
        file_filters = "所有文件 (*);;文本文件 (*.txt);;Python (*.py);;Markdown (*.md);;HTML (*.html);;JavaScript (*.js);;JSON (*.json);;XML (*.xml);;YAML (*.yaml *.yml);;CSS (*.css);;C/C++ (*.c *.cpp *.h *.hpp);;Java (*.java);;C# (*.cs);;Go (*.go);;Rust (*.rs);;PHP (*.php);;SQL (*.sql)"
        
        # 记住上次打开的目录
        initial_dir = self.lastDirectory if hasattr(self, 'lastDirectory') and self.lastDirectory else os.path.expanduser("~")
        
        try:
            # 使用QFileDialog打开文件选择对话框
            filePath, _ = QFileDialog.getOpenFileName(
                self,
                "打开文件",
                initial_dir,
                file_filters
            )
            
            if not filePath:
                print("用户取消了文件选择")
                return None, None, None
            
            # 更新最后打开的目录
            self.lastDirectory = os.path.dirname(filePath)
            
            # 获取文件基本信息
            fileName = os.path.basename(filePath)
            title = os.path.splitext(fileName)[0]
            
            # 检查文件是否已经打开
            for i, file_info in enumerate(self.openFiles):
                if file_info.get('filePath') == filePath:
                    editorIndex = file_info.get('editorIndex')
                    print(f"文件已经打开，重新激活标签页: {i}，编辑器索引: {editorIndex}")
                    
                    # 性能优化：仅在文件被修改时重新加载内容
                    if os.path.exists(filePath):
                        file_mtime = os.path.getmtime(filePath)
                        last_load_time = file_info.get('last_load_time', 0)
                        
                        if file_mtime > last_load_time:
                            # 文件被修改，需要重新加载
                            try:
                                with open(filePath, 'r', encoding='utf-8') as file:
                                    fresh_content = file.read()
                                self.editors[editorIndex].setPlainText(fresh_content)
                                file_info['last_load_time'] = file_mtime  # 更新加载时间
                                print(f"文件已修改，更新内容，长度: {len(fresh_content)}")
                            except UnicodeDecodeError:
                                # 尝试使用其他编码
                                try:
                                    with open(filePath, 'r', encoding='gbk') as file:
                                        fresh_content = file.read()
                                    self.editors[editorIndex].setPlainText(fresh_content)
                                    file_info['last_load_time'] = file_mtime
                                    print(f"使用GBK编码读取文件")
                                except Exception as e:
                                    print(f"读取文件内容时出错: {e}")
                                    warning(self, "读取错误", f"无法读取文件内容: {str(e)}")
                                    return None, None, None
                            except Exception as e:
                                print(f"更新已打开文件内容时出错: {e}")
                                warning(self, "读取错误", f"无法读取文件内容: {str(e)}")
                                return None, None, None
                        else:
                            print("文件未修改，使用当前内容")
                    
                    # 激活对应的标签页并立即返回
                    self.sidebar.activateTab(file_info.get('index'), True)
                    return filePath, title, self.editors[editorIndex].toPlainText()
            
            # 文件尚未打开，读取文件内容
            content = ""
            try:
                # 性能优化：使用with语句确保文件正确关闭
                with open(filePath, 'r', encoding='utf-8') as file:
                    content = file.read()
            except UnicodeDecodeError:
                # 尝试使用其他编码
                try:
                    with open(filePath, 'r', encoding='gbk') as file:
                        content = file.read()
                    print(f"使用GBK编码读取文件")
                except Exception as e:
                    print(f"读取文件内容时出错: {e}")
                    warning(self, "读取错误", f"无法读取文件内容: {str(e)}")
                    return None, None, None
            except Exception as e:
                print(f"读取文件内容时出错: {e}")
                warning(self, "读取错误", f"无法读取文件内容: {str(e)}")
                return None, None, None
                    
            # 文件尚未打开，创建新标签页
            index = self.sidebar.addTab(title, filePath)
            editorIndex = self.createNewEditor()
            
            # 设置编辑器内容
            if 0 <= editorIndex < len(self.editors):
                self.editors[editorIndex].setPlainText(content)
                print(f"新文件加载到编辑器，内容长度: {len(content)}")
            
            # 记录文件信息
            current_time = os.path.getmtime(filePath) if os.path.exists(filePath) else 0
            self.openFiles.append({
                'index': index,
                'editorIndex': editorIndex,
                'filePath': filePath,
                'title': title,
                'last_load_time': current_time  # 记录加载时间用于后续检查文件是否更新
            })
            
            # 更新当前文件信息
            self.currentFilePath = filePath
            self.currentTitle = title
            
            # 获取文件类型
            from Aya_Hanabi.Hanabi_HighLight import detect_file_type
            self.currentFileType = detect_file_type(filePath)
            print(f"打开文件类型: {self.currentFileType}")
            
            # 激活对应的标签页
            if self.sidebar.current_tab_index != index:
                self.sidebar.activateTab(index, True)
            
            # 更新窗口标题
            self.setWindowTitle(f"Hanabi Notes - {title}")
            
            # 应用高亮
            if 0 <= editorIndex < len(self.editors) and hasattr(self, 'highlightMode') and self.highlightMode:
                self.applyHighlighter(self.editors[editorIndex], self.currentFileType)
            
            return filePath, title, content
        
        except Exception as e:
            print(f"打开文件时出错: {e}")
            import traceback
            traceback.print_exc()
            warning(self, "打开错误", f"无法打开文件: {str(e)}")
            return None, None, None
    finally:
        # 最后重置标志位，无论成功或失败
        _file_open_in_progress = False
