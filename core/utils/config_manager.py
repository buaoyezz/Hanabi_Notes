import os
import json
from core.log.log_manager import log

class ConfigManager:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not ConfigManager._initialized:
            # 配置文件路径
            self.config_dir = os.path.join(os.path.expanduser('~'), '.imagine_snap', 'config')
            self.config_file = os.path.join(self.config_dir, 'settings.json')
            
            # 确保配置目录存在
            os.makedirs(self.config_dir, exist_ok=True)
            
            # 默认配置
            self.default_config = {
                'appearance': {
                    'font': 'Microsoft YaHei UI'
                }
            }
            
            # 当前配置
            self.config = self.load_config()
            
            ConfigManager._initialized = True
            log.info("配置管理器初始化完成")
    
    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                log.info("配置文件加载成功")
                return config
            else:
                # 如果配置文件不存在，创建默认配置
                self.save_config(self.default_config)
                log.info("创建默认配置文件")
                return self.default_config.copy()
        except Exception as e:
            log.error(f"加载配置文件出错: {str(e)}")
            return self.default_config.copy()
    
    def save_config(self, config=None):
        if config is not None:
            self.config = config
            
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            log.info("配置文件保存成功")
            return True
        except Exception as e:
            log.error(f"保存配置文件出错: {str(e)}")
            return False
    
    def get_config(self, section=None, key=None, default=None):
        try:
            if section is None:
                return self.config
            elif key is None:
                return self.config.get(section, {})
            else:
                return self.config.get(section, {}).get(key, default)
        except Exception as e:
            log.error(f"获取配置项出错: {str(e)}")
            return default
    
    def set_config(self, section, key, value):
        try:
            if section not in self.config:
                self.config[section] = {}
                
            self.config[section][key] = value
            self.save_config()
            return True
        except Exception as e:
            log.error(f"设置配置项出错: {str(e)}")
            return False

# 全局配置管理器实例
config_manager = ConfigManager() 