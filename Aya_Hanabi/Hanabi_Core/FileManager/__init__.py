# 文件管理模块
from .fileManager import FileManager
from .openFile import open_file
from .saveFile import saveFile
from .autoSave import AutoSave
from .autoBackup import AutoBackup
from .newFile import new_file
from .deleteFile import delete_file
from .closeFile import close_file
from .changeFile import change_file

# 兼容性导入，允许直接从模块导入函数
from .saveFile import saveFile as save_file 