import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer
from company_ai_project.ui.company_ui import qdarktheme, common_widget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Company Window")
        self.setGeometry(100, 100, 1800, 900)

        self.central_widget = QWidget()
        self.layout = QVBoxLayout(self.central_widget)
        self.commonWidget = common_widget.commonWidget()
        self.layout.addWidget(self.commonWidget)
        self.setCentralWidget(self.central_widget)

        # Maximize the window
        self.showMaximized()

        # Set up timer to print every minute without blocking GUI
        self.counter = 1
        self.timer = QTimer()
        self.timer.timeout.connect(self.print_every_minute)
        self.timer.start(600)  # 60000 ms = 1 minute

    def print_every_minute(self):
        #print(f"Message {self.counter}: Hello! This prints every minute.")
        self.counter += 1



if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarktheme.load_stylesheet(custom_colors={"primary": "#D0BCFF"}))
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())