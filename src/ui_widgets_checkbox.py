"""
Кастомный чекбокс с иконкой check.svg
"""

from PySide6.QtWidgets import QCheckBox, QStyle
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPixmap, QIcon
from PySide6.QtSvg import QSvgRenderer
import os

class CustomCheckBox(QCheckBox):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.check_icon = None
        self.load_check_icon()
        
    def load_check_icon(self):
        """Загружает иконку check.svg"""
        try:
            current_file = os.path.abspath(__file__)
            project_root = os.path.dirname(os.path.dirname(current_file))
            icon_path = os.path.join(project_root, "src", "resources", "icons", "check.svg")
            
            if os.path.exists(icon_path):
                renderer = QSvgRenderer(icon_path)
                
                if renderer.isValid():
                    icon_size = 18
                    pixmap = QPixmap(icon_size, icon_size)
                    pixmap.fill(Qt.transparent)
                    
                    painter = QPainter(pixmap)
                    renderer.render(painter)
                    painter.end()
                    
                    self.check_icon = QIcon(pixmap)
        except Exception:
            self.check_icon = None
    
    def paintEvent(self, event):
        """Отрисовка с иконкой"""
        if self.isChecked() and self.check_icon:
            super().paintEvent(event)
            
            # Проверяем, что виджет готов к рисованию
            if self.width() <= 0 or self.height() <= 0:
                return
            
            painter = QPainter()
            if not painter.begin(self):
                return
            
            try:
                painter.setRenderHint(QPainter.Antialiasing)
                
                icon_size = 18
                x = 1
                y = (self.height() - icon_size) // 2
                
                self.check_icon.paint(painter, x, y, icon_size, icon_size)
            finally:
                painter.end()
        else:
            super().paintEvent(event)
