#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

# 获取项目根目录
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

# 导入消息框模块
from PySide6.QtWidgets import QApplication
from Aya_Hanabi.Hanabi_Core.UI.messageBox import (
    AndroidStyleMessageBox, 
    information, 
    warning, 
    critical, 
    question, 
    success
)

def main():
    """测试Android风格消息框的各种类型和功能"""
    app = QApplication(sys.argv)
    
    print("==================================================")
    print("        Android风格消息框测试工具                  ")
    print("==================================================")
    
    while True:
        print("\n选择要测试的消息框类型:")
        print("1. 信息提示 (Information)")
        print("2. 警告提示 (Warning)")
        print("3. 错误提示 (Error)")
        print("4. 问题询问 (Yes/No)")
        print("5. 问题询问 (Yes/No/Cancel)")
        print("6. 成功提示 (Success)")
        print("7. 自定义消息框")
        print("0. 退出测试")
        
        choice = input("\n请输入选择 (0-7): ")
        
        if choice == "0":
            break
        elif choice == "1":
            result = information(None, "信息提示", "这是一个信息消息框\n用于显示一般性的提示信息")
            print(f"返回结果: {result}")
        elif choice == "2":
            result = warning(None, "警告提示", "这是一个警告消息框\n用于警告用户注意某些潜在问题")
            print(f"返回结果: {result}")
        elif choice == "3":
            result = critical(None, "错误提示", "这是一个错误消息框\n用于通知用户发生了严重错误")
            print(f"返回结果: {result}")
        elif choice == "4":
            result = question(None, "确认操作", "确定要执行此操作吗？\n此操作可能需要一些时间完成。")
            if result == AndroidStyleMessageBox.Yes_Result:
                print("用户选择: 是")
            else:
                print("用户选择: 否")
        elif choice == "5":
            result = question(None, "保存更改", "是否保存更改？\n选择"否"将丢弃所有更改。", 
                            AndroidStyleMessageBox.YesNoCancel)
            if result == AndroidStyleMessageBox.Yes_Result:
                print("用户选择: 是")
            elif result == AndroidStyleMessageBox.No_Result:
                print("用户选择: 否")
            else:
                print("用户选择: 取消")
        elif choice == "6":
            result = success(None, "操作成功", "操作已成功完成！\n所有更改已保存。")
            print(f"返回结果: {result}")
        elif choice == "7":
            title = input("输入标题: ")
            message = input("输入内容: ")
            print("选择消息框类型:")
            print("1. 信息 2. 警告 3. 错误 4. 问题 5. 成功")
            type_choice = int(input("选择 (1-5): ")) - 1
            print("选择按钮类型:")
            print("1. 确定 2. 确定/取消 3. 是/否 4. 是/否/取消")
            button_choice = int(input("选择 (1-4): ")) - 1
            
            dialog = AndroidStyleMessageBox(
                None, 
                title, 
                message,
                type_choice,
                button_choice
            )
            result = dialog.exec_()
            print(f"对话框返回值: {result}")
            print(f"结果值: {dialog.get_result()}")
        else:
            print("无效的选择，请重试")
    
    print("\n测试完成!")

if __name__ == "__main__":
    main() 