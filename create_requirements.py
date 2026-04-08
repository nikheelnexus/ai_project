import os
import sys

# Set environment variables BEFORE importing PyQt
os.environ['QT_QPA_PLATFORM'] = 'windows'

from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt5.QtCore import Qt

app = QApplication(sys.argv)
window = QMainWindow()
window.setWindowTitle("Test")
window.setGeometry(100, 100, 400, 200)

label = QLabel("Working!", window)
label.setAlignment(Qt.AlignCenter)
window.setCentralWidget(label)

window.show()
sys.exit(app.exec_())