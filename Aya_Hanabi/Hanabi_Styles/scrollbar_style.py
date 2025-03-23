class ScrollBarStyle:
    @staticmethod
    def get_style(base_color="#005780", handle_color="rgba(255, 255, 255, 0.3)"):
        """返回滚动条样式"""
        return f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            
            QScrollBar:vertical {{
                background-color: {base_color};
                width: 6px;
                margin: 0px;
                border-radius: 3px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {handle_color};
                min-height: 30px;
                border-radius: 3px;
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """ 