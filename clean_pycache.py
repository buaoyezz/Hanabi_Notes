import os
import shutil

def clean_pycache(root_dir='.'):
    """
    递归删除所有__pycache__目录和.pyc文件
    """
    # 计数器
    removed_dirs = 0
    removed_files = 0
    
    # 遍历目录
    for root, dirs, files in os.walk(root_dir, topdown=False):
        # 删除__pycache__目录
        for dir_name in dirs:
            if dir_name == "__pycache__":
                dir_path = os.path.join(root, dir_name)
                try:
                    shutil.rmtree(dir_path)
                    removed_dirs += 1
                    print(f"已删除: {dir_path}")
                except Exception as e:
                    print(f"删除失败 {dir_path}: {e}")
        
        # 删除.pyc文件
        for file_name in files:
            if file_name.endswith(".pyc"):
                file_path = os.path.join(root, file_name)
                try:
                    os.remove(file_path)
                    removed_files += 1
                    print(f"已删除: {file_path}")
                except Exception as e:
                    print(f"删除失败 {file_path}: {e}")
    
    print(f"\n清理完成! 已删除 {removed_dirs} 个__pycache__目录和 {removed_files} 个.pyc文件")

if __name__ == "__main__":
    clean_pycache() 