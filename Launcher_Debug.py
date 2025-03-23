import sys
import os
import traceback
import psutil
import platform
import threading
import GPUtil
from datetime import datetime

os.environ["QT_ENABLE_SHARED_MEMORY"] = "0"
os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=1"

try:
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"操作系统: {platform.system()} {platform.version()}")
    print(f"Python版本: {sys.version}")
    print(f"CPU信息:")
    print(f"  - 核心数: {psutil.cpu_count()}")
    print(f"  - 物理核心数: {psutil.cpu_count(logical=False)}")
    print(f"  - CPU使用率: {psutil.cpu_percent()}%")
    
    print(f"\n内存信息:")
    print(f"  - 总内存: {psutil.virtual_memory().total / 1024 / 1024 / 1024:.1f} GB")
    print(f"  - 可用内存: {psutil.virtual_memory().available / 1024 / 1024 / 1024:.1f} GB")
    print(f"  - 内存使用率: {psutil.virtual_memory().percent}%")
    print(f"  - 当前进程内存: {psutil.Process().memory_info().rss / 1024 / 1024:.1f} MB")
    
    print(f"\n磁盘信息:")
    disk = psutil.disk_usage('/')
    print(f"  - 总空间: {disk.total / 1024 / 1024 / 1024:.1f} GB")
    print(f"  - 可用空间: {disk.free / 1024 / 1024 / 1024:.1f} GB")
    print(f"  - 使用率: {disk.percent}%")
    
    try:
        gpus = GPUtil.getGPUs()
        if gpus:
            print(f"\nGPU信息:")
            for gpu in gpus:
                print(f"  - GPU型号: {gpu.name}")
                print(f"  - 显存总量: {gpu.memoryTotal} MB")
                print(f"  - 显存使用: {gpu.memoryUsed} MB")
                print(f"  - GPU使用率: {gpu.load*100}%")
    except:
        print("\nGPU信息获取失败")
    
    print(f"\n其他信息:")
    print(f"  - 活跃线程数: {threading.active_count()}")
    print(f"  - 进程PID: {os.getpid()}")
    print(f"  - 当前工作目录: {os.getcwd()}")
    
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtWidgets import QApplication
    from Hanabi_Notes import HanabiNotesApp

    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = HanabiNotesApp()
    window.show()
    
    exit_code = app.exec()
    sys.exit(exit_code)

except Exception as e:
    print(f"错误类型: {type(e).__name__}")
    print(f"错误信息: {str(e)}")
    print("完整堆栈跟踪:")
    traceback.print_exc()
    try:
        with open("error_log.txt", "w") as f:
            f.write(f"错误类型: {type(e).__name__}\n")
            f.write(f"错误信息: {str(e)}\n")
            traceback.print_exc(file=f)
    except Exception as log_error:
        print(f"写入日志文件时发生错误: {log_error}")