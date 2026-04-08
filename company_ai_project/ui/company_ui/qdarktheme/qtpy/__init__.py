"""Package applying Qt compat of PyQt6, PySide6, PyQt5 and PySide2."""
from company_ai_project_old.ui.company_ui.qdarktheme.qtpy.qt_compat import QtImportError
from company_ai_project_old.ui.company_ui.qdarktheme.qtpy.qt_version import __version__

try:
    from company_ai_project_old.ui.company_ui.qdarktheme.qtpy import QtCore, QtGui, QtSvg, QtWidgets
except ImportError:
    from company_ai_project_old.ui.company_ui.qdarktheme._util import get_logger as __get_logger

    __logger = __get_logger(__name__)
    __logger.warning("Failed to import QtCore, QtGui, QtSvg and QtWidgets.")
