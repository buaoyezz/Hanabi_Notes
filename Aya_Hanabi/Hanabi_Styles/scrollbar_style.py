class ScrollBarStyle:
    @staticmethod
    def get_style(base_color="#005780", handle_color="rgba(255, 255, 255, 0.3)"):
        f = f"""
            QScrollBar:vertical {{
                border: none;
                background: {base_color};
                width: 8px;
                margin: 0px 0px 0px 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {handle_color};
                min-height: 20px;
                border-radius: 4px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
            QScrollBar:horizontal {{
                border: none;
                background: {base_color};
                height: 8px;
                margin: 0px 0px 0px 0px;
            }}
            QScrollBar::handle:horizontal {{
                background: {handle_color};
                min-width: 20px;
                border-radius: 4px;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}
        """
        return f
        
    @staticmethod
    def apply_to(scrollbar, base_color="#005780", handle_color="rgba(255, 255, 255, 0.3)"):
        """
        将滚动条样式应用到指定的滚动条对象
        
        参数:
        - scrollbar: 需要应用样式的滚动条对象
        - base_color: 滚动条背景色
        - handle_color: 滚动条滑块颜色
        """
        style = ScrollBarStyle.get_style(base_color, handle_color)
        scrollbar.setStyleSheet(style) 