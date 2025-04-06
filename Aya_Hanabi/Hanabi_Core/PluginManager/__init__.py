"""
Hanabi Notes 插件系统
用于管理和加载各种功能扩展
"""

from .pluginCore import (
    HanabiPlugin, PluginMetadata, PluginHooks, FileHandler,
    PluginError, PluginLoadError, PluginInitError, PluginVersionError
)
from .pluginManager import PluginManager

__all__ = [
    'HanabiPlugin', 'PluginMetadata', 'PluginHooks', 'FileHandler',
    'PluginError', 'PluginLoadError', 'PluginInitError', 'PluginVersionError',
    'PluginManager'
] 