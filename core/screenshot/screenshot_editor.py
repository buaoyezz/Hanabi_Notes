from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QColorDialog, QSpinBox, QFontDialog)
from PySide6.QtCore import Qt, QPoint, QRect, QSize
from PySide6.QtGui import (QPainter, QPen, QColor, QPixmap, QPainterPath,
                          QFont, QFontMetrics)
from core.log.log_manager import log
from core.font.font_manager import FontManager
import math

class ScreenshotEditor(QWidget):
    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.original_pixmap = pixmap
        self.current_pixmap = pixmap.copy()
        self.undo_stack = []
        self.redo_stack = []
        self.current_tool = None
        self.drawing = False
        self.last_point = None
        self.font_manager = FontManager()
        self.setup_ui()
        
    def setup_ui(self):
        # 设置编辑器大小
        self.setFixedSize(self.original_pixmap.size())
        
        # 初始化工具属性
        self.pen_color = QColor("#FF0000")  # 默认红色
        self.pen_width = 2
        self.font = self.font_manager._create_optimized_font()  # 使用字体管理器创建字体
        self.font.setPointSize(12)  # 设置字体大小
        self.mosaic_size = 10
        
        # 保存当前状态
        self._save_state()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.current_pixmap)
        
        # 如果正在绘制，显示预览
        if self.drawing and self.last_point:
            painter.setPen(QPen(self.pen_color, self.pen_width))
            
            if self.current_tool == "pen":
                painter.drawLine(self.last_point, event.pos())
            elif self.current_tool == "arrow":
                self._draw_arrow(painter, self.last_point, event.pos())
                
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.last_point = event.pos()
            
            if self.current_tool == "text":
                self._add_text(event.pos())
            elif self.current_tool == "mosaic":
                self._apply_mosaic(event.pos())
                
    def mouseMoveEvent(self, event):
        if self.drawing and self.last_point:
            if self.current_tool in ["pen", "arrow"]:
                self.update()  # 触发重绘以显示预览
            elif self.current_tool == "mosaic":
                self._apply_mosaic(event.pos())
                
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing:
            if self.current_tool in ["pen", "arrow"]:
                # 在pixmap上绘制
                painter = QPainter(self.current_pixmap)
                painter.setPen(QPen(self.pen_color, self.pen_width))
                
                if self.current_tool == "pen":
                    painter.drawLine(self.last_point, event.pos())
                elif self.current_tool == "arrow":
                    self._draw_arrow(painter, self.last_point, event.pos())
                    
                painter.end()
                
                # 保存状态
                self._save_state()
                
            self.drawing = False
            self.last_point = None
            self.update()
            
    def _draw_arrow(self, painter, start, end):
        # 计算箭头方向
        angle = math.atan2(end.y() - start.y(), end.x() - start.x())
        
        # 箭头大小
        arrow_size = self.pen_width * 4
        
        # 绘制直线
        painter.drawLine(start, end)
        
        # 绘制箭头
        arrow_p1 = QPoint(
            int(end.x() - arrow_size * math.cos(angle - math.pi/6)),
            int(end.y() - arrow_size * math.sin(angle - math.pi/6))
        )
        arrow_p2 = QPoint(
            int(end.x() - arrow_size * math.cos(angle + math.pi/6)),
            int(end.y() - arrow_size * math.sin(angle + math.pi/6))
        )
        
        arrow_head = QPainterPath()
        arrow_head.moveTo(end)
        arrow_head.lineTo(arrow_p1)
        arrow_head.lineTo(arrow_p2)
        arrow_head.lineTo(end)
        
        painter.fillPath(arrow_head, self.pen_color)
        
    def _add_text(self, pos):
        from PySide6.QtWidgets import QInputDialog
        
        text, ok = QInputDialog.getText(self, "添加文字", "请输入文字:")
        if ok and text:
            painter = QPainter(self.current_pixmap)
            painter.setFont(self.font)
            painter.setPen(self.pen_color)
            
            # 计算文字大小
            metrics = QFontMetrics(self.font)
            rect = metrics.boundingRect(text)
            
            # 调整位置，使文字不超出边界
            x = min(pos.x(), self.width() - rect.width())
            y = min(pos.y(), self.height() - rect.height())
            x = max(x, 0)
            y = max(y + metrics.ascent(), metrics.ascent())  # 考虑基线
            
            try:
                painter.drawText(x, y, text)
                log.info(f"成功添加文字: {text}")
            except Exception as e:
                log.error(f"绘制文字失败: {str(e)}")
            finally:
                painter.end()
            
            # 保存状态
            self._save_state()
            self.update()
            
    def _apply_mosaic(self, pos):
        # 计算马赛克区域
        x = pos.x() - self.mosaic_size // 2
        y = pos.y() - self.mosaic_size // 2
        rect = QRect(x, y, self.mosaic_size, self.mosaic_size)
        
        # 确保区域在图片范围内
        rect = rect.intersected(self.current_pixmap.rect())
        
        if not rect.isEmpty():
            # 获取区域图像
            region = self.current_pixmap.copy(rect)
            
            # 缩小后放大以产生马赛克效果
            scaled = region.scaled(1, 1, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            mosaic = scaled.scaled(rect.size(), Qt.IgnoreAspectRatio, Qt.FastTransformation)
            
            # 将马赛克效果应用到图片
            painter = QPainter(self.current_pixmap)
            painter.drawPixmap(rect, mosaic)
            painter.end()
            
            self.update()
            
    def _save_state(self):
        self.undo_stack.append(self.current_pixmap.copy())
        self.redo_stack.clear()
        
    def undo(self):
        if len(self.undo_stack) > 1:  # 保留第一个状态
            self.redo_stack.append(self.current_pixmap.copy())
            self.current_pixmap = self.undo_stack.pop()
            self.update()
            
    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(self.current_pixmap.copy())
            self.current_pixmap = self.redo_stack.pop()
            self.update()
            
    def set_tool(self, tool):
        self.current_tool = tool
        
    def set_pen_color(self):
        color = QColorDialog.getColor(self.pen_color, self)
        if color.isValid():
            self.pen_color = color
            
    def set_pen_width(self, width):
        self.pen_width = width
        
    def set_font(self):
        font, ok = QFontDialog.getFont(self.font, self)
        if ok:
            self.font = font
            
    def set_mosaic_size(self, size):
        self.mosaic_size = size
        
    def get_edited_pixmap(self):
        return self.current_pixmap.copy() 