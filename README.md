# Hanabi Notes

Hanabi Notes是一个现代化笔记应用程序，提供流畅的编辑体验和美观的界面设计。

## 功能特点

- 现代化UI设计，带有圆角和优雅的动画效果
- 可切换的侧边栏，便于组织和管理笔记
- 代码实时高亮功能[目前只支持Python、MarkDown]
- 多种功能按钮：
  - 导入/导出笔记
  - 创建/删除笔记
  - 切换主题
  - 调整字体大小
- 独立的项目列表和文档大纲视图

## 编译方案

+ 安装Python 3.12.x [本项目使用3.12.6]

+ 安装依赖

+ `Hanabi_Notes.py`是主文件，运行使用

+ `Debug`的py也可以启动并且可以带上错误日志

  

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行应用

```bash
python Hanabi_Notes.py
```

## 新增功能

### 侧边栏

- 侧边栏顶部设有快捷操作按钮：导入、导出、新建和删除
- 支持无限Tab多开



### 字体调整

- 使用底部状态栏的字体大小按钮可快速调整编辑器字体大小
- 支持多种预设字体大小，满足不同阅读偏好

## 快捷栏

- 高亮模式:快速切换
- 侧边栏切换:超强Tab多开支持
- 文件技术:自动保存

## 技术栈

- Python 3.12.x
- PySide6 (Qt for Python)
- Material Design Icons
- Markdown解析器 