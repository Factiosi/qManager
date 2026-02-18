from PySide6.QtWidgets import QFormLayout
from PySide6.QtCore import QTimer


class ExcelModeMixin:
    def update_excel_field_visibility(self):
        excel_mode = self.main_window.settings.get('excel_mode', 'logos')
        if excel_mode == 'sheets':
            if hasattr(self, 'excel_container'):
                self.excel_container.setVisible(False)
            if hasattr(self, 'excel_field'):
                self.excel_field.setVisible(False)
            if hasattr(self, 'form_layout') and hasattr(self, 'excel_form_row_index'):
                try:
                    item = self.form_layout.itemAt(self.excel_form_row_index, QFormLayout.LabelRole)
                    if item and item.widget():
                        item.widget().setVisible(False)
                except Exception:
                    pass
        else:
            if hasattr(self, 'excel_container'):
                self.excel_container.setVisible(True)
            if hasattr(self, 'excel_field'):
                self.excel_field.setVisible(True)
            if hasattr(self, 'form_layout') and hasattr(self, 'excel_form_row_index'):
                try:
                    item = self.form_layout.itemAt(self.excel_form_row_index, QFormLayout.LabelRole)
                    if item and item.widget():
                        item.widget().setVisible(True)
                except Exception:
                    pass
    
    def connect_settings_changes(self):
        if hasattr(self.main_window, 'settings_area'):
            try:
                self.main_window.settings_area.excel_mode_combo.currentTextChanged.connect(
                    lambda: self.update_excel_field_visibility()
                )
            except Exception:
                pass
    
    def setup_excel_field_visibility(self):
        QTimer.singleShot(200, lambda: self.update_excel_field_visibility())
        QTimer.singleShot(300, self.connect_settings_changes)
