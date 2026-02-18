"""
Кастомный чекбокс с иконкой check.svg
"""

from PySide6.QtWidgets import QCheckBox
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QPainter, QPixmap, QIcon, QColor
from PySide6.QtSvg import QSvgRenderer
import os
import src.ui_styles as ui_styles

class CustomCheckBox(QCheckBox):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.check_icon = None
        self.load_check_icon()

    def load_check_icon(self):
        try:
            current_file = os.path.abspath(__file__)
            project_root = os.path.dirname(os.path.dirname(current_file))
            icon_path = os.path.join(project_root, "src", "resources", "icons", "check.svg")

            if not os.path.exists(icon_path):
                return

            with open(icon_path, "rb") as f:
                svg_bytes = f.read()

            renderer = QSvgRenderer(svg_bytes)
            if not renderer.isValid():
                return

            icon_size = 18
            pixmap = QPixmap(icon_size, icon_size)
            pixmap.fill(Qt.transparent)

            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()

            # Перекрашиваем иконку в цвет текста текущей темы
            tinted = QPixmap(pixmap.size())
            tinted.fill(Qt.transparent)
            p = QPainter(tinted)
            p.drawPixmap(0, 0, pixmap)
            p.setCompositionMode(QPainter.CompositionMode_SourceIn)
            p.fillRect(tinted.rect(), QColor(ui_styles.get_colors()['text_color']))
            p.end()

            self.check_icon = QIcon(tinted)
        except Exception:
            self.check_icon = None

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.StyleChange:
            self.load_check_icon()
    
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
