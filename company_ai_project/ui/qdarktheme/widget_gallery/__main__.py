"""Module allowing for `python -m qdarktheme.widget_gallery`."""
import sys

from company_ai_project_old.ui.company_ui import qdarktheme
from company_ai_project_old.ui.company_ui.qdarktheme.qtpy.QtWidgets import QApplication
from company_ai_project_old.ui.company_ui.qdarktheme.widget_gallery.main_window import WidgetGallery

if __name__ == "__main__":
    qdarktheme.enable_hi_dpi()
    app = QApplication(sys.argv)
    qdarktheme.setup_theme("auto")
    win = WidgetGallery()
    win.show()
    app.exec()
