import os
import re
import sys
from pathlib import Path

def replace_qmessagebox_with_hanabiMessageBox(file_path):
    """
    替换指定文件中的QMessageBox为HanabiMessageBox
    """
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查文件是否已包含HanabiMessageBox导入
        if 'from Aya_Hanabi.Hanabi_Core.UI.messageBox import HanabiMessageBox' in content:
            print(f"文件 {file_path} 已经导入了HanabiMessageBox")
            return False
        
        # 替换QMessageBox导入
        import_pattern = r'(from PySide6.QtWidgets import .*?)(QMessageBox|QApplication|QDialog)(.*?)'
        if re.search(import_pattern, content):
            content = re.sub(import_pattern, r'from Aya_Hanabi.Hanabi_Core.UI.messageBox import HanabiMessageBox, information, warning, critical, question, success\1\2', content)
        else:
            # 如果没有找到合适的import行，添加新的import语句
            import_line = 'from Aya_Hanabi.Hanabi_Core.UI.messageBox import HanabiMessageBox, information, warning, critical, question, success\n'
            if 'import ' in content:
                # 在最后一个import语句后添加
                import_indices = [m.start() for m in re.finditer(r'^import .*?$', content, re.MULTILINE)]
                last_import_index = import_indices[-1] if import_indices else 0
                last_import_line_end = content.find('\n', last_import_index) + 1
                content = content[:last_import_line_end] + import_line + content[last_import_line_end:]
            else:
                # 在文件开头添加
                content = import_line + content
        
        # 替换基本方法 QMessageBox.information -> information 等
        content = re.sub(r'QMessageBox\.information\((.*?),\s*"([^"]+)"\s*,\s*"([^"]+)"\)', r'information(\1, "\2", "\3")', content)
        content = re.sub(r'QMessageBox\.warning\((.*?),\s*"([^"]+)"\s*,\s*"([^"]+)"\)', r'warning(\1, "\2", "\3")', content)
        content = re.sub(r'QMessageBox\.critical\((.*?),\s*"([^"]+)"\s*,\s*"([^"]+)"\)', r'critical(\1, "\2", "\3")', content)
        content = re.sub(r'QMessageBox\.question\((.*?),\s*"([^"]+)"\s*,\s*"([^"]+)"\)', r'question(\1, "\2", "\3")', content)
        
        # 替换带按钮参数的question
        question_pattern = r'QMessageBox\.question\((.*?),\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*QMessageBox\.StandardButton\.([^,\)]+)(?:\s*\|\s*QMessageBox\.StandardButton\.([^,\)]+))?\)'
        if re.search(question_pattern, content):
            for match in re.finditer(question_pattern, content):
                obj, title, text, btn1, btn2 = match.groups()
                
                # 根据按钮类型选择对应的HanabiMessageBox按钮类型
                if btn1 == 'Yes' and btn2 == 'No':
                    button_type = 'HanabiMessageBox.YesNo'
                elif btn1 == 'Yes' and btn2 == 'Cancel':
                    button_type = 'HanabiMessageBox.YesNoCancel'
                elif btn1 == 'Ok' and btn2 == 'Cancel':
                    button_type = 'HanabiMessageBox.OkCancel'
                else:
                    button_type = 'HanabiMessageBox.Ok'
                
                # 进行替换
                old = match.group(0)
                new = f'question({obj}, "{title}", "{text}", {button_type})'
                content = content.replace(old, new)
        
        # 替换返回值判断
        content = re.sub(r'QMessageBox\.Yes', r'HanabiMessageBox.Yes_Result', content)
        content = re.sub(r'QMessageBox\.No', r'HanabiMessageBox.No_Result', content)
        content = re.sub(r'QMessageBox\.Ok', r'HanabiMessageBox.Ok_Result', content)
        content = re.sub(r'QMessageBox\.Cancel', r'HanabiMessageBox.Cancel_Result', content)
        
        # 替换StandardButton枚举
        content = re.sub(r'QMessageBox\.StandardButton\.Save', r'HanabiMessageBox.Yes_Result', content)
        content = re.sub(r'QMessageBox\.StandardButton\.Discard', r'HanabiMessageBox.No_Result', content)
        content = re.sub(r'QMessageBox\.StandardButton\.Cancel', r'HanabiMessageBox.Cancel_Result', content)
        
        # 保存修改后的文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"已完成文件 {file_path} 的消息框替换")
        return True
    except Exception as e:
        print(f"替换消息框时出错: {e}")
        return False

def batch_replace_in_directory(directory):
    """
    批量替换目录中所有.py文件的QMessageBox为HanabiMessageBox
    """
    count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if replace_qmessagebox_with_hanabiMessageBox(file_path):
                    count += 1
    
    print(f"批量替换完成，共处理了 {count} 个文件")

if __name__ == "__main__":
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 获取项目根目录 (假设是再往上两级)
    project_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    # 在根目录下的所有Python文件中执行替换
    batch_replace_in_directory(project_dir) 