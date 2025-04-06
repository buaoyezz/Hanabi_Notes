
# -*- coding: utf-8 -*-

import os
import sys
import time

# 获取项目根目录
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)


from Aya_Hanabi.Hanabi_Core.UI.messageBoxReplacer import replace_qmessagebox_in_directory
from Aya_Hanabi.Hanabi_Core.UI.messageBox import AndroidStyleMessageBox, information, warning, critical, question, success

def main():
    print("=================================================")
    print("        Hanabi Notes - 消息框替换工具            ")
    print("=================================================")
    print("该工具将替换项目中所有的QMessageBox为新的Android风格消息框")
    print("这将使应用程序的消息框更加美观和现代化")
    print("\n警告: 建议在执行此操作前备份您的代码")
    
    confirm = input("\n确定要开始替换吗? (y/n): ")
    if confirm.lower() != 'y':
        print("操作已取消")
        return
    
    print("\n开始扫描项目文件...")
    start_time = time.time()
    
    try:
        result = replace_qmessagebox_in_directory(project_root)
        
        elapsed_time = time.time() - start_time
        
        print("\n=================================================")
        print(f"替换完成! 耗时: {elapsed_time:.2f} 秒")
        print(f"成功处理: {result['success']} 个文件")
        print(f"失败处理: {result['fail']} 个文件")
        print(f"已跳过: {result['skip']} 个文件 (不包含QMessageBox)")
        print("=================================================")
        
        if result['fail'] > 0:
            print("\n警告: 部分文件处理失败，请查看上面的错误信息")
        
        print("\n如需恢复原来的消息框，请还原您的代码备份")
        
    except Exception as e:
        print(f"\n错误: 替换过程中发生异常: {str(e)}")
        print("操作已中断，请还原您的代码备份")

if __name__ == "__main__":
    main() 