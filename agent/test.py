import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPlainTextEdit,
                             QVBoxLayout, QWidget, QPushButton, QColorDialog,
                             QHBoxLayout, QLabel, QGroupBox)
from PyQt5.QtGui import QTextCharFormat, QColor, QTextCursor, QFont
from PyQt5.QtCore import Qt


class AdvancedColorTextEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced Text Color Editor")
        self.setGeometry(100, 100, 900, 600)

        self.current_color = QColor(0, 0, 0)
        self.current_bg_color = QColor(255, 255, 255)

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Text editor
        self.text_edit = QPlainTextEdit()
        self.text_edit.setPlainText(
            "Welcome to Advanced Text Color Editor!\n\n"
            "Instructions:\n"
            "1. Select text you want to color\n"
            "2. Choose foreground/background colors\n"
            "3. Click apply buttons\n"
            "4. Use shortcuts: Ctrl+Shift+F for foreground, Ctrl+Shift+B for background"
        )
        main_layout.addWidget(self.text_edit)

        # Color control group
        color_group = QGroupBox("Color Controls")
        color_layout = QHBoxLayout()

        # Foreground color
        fg_layout = QVBoxLayout()
        fg_layout.addWidget(QLabel("Text Color:"))

        self.fg_color_btn = QPushButton()
        self.fg_color_btn.setFixedSize(40, 40)
        self.update_fg_preview()
        self.fg_color_btn.clicked.connect(self.choose_fg_color)
        fg_layout.addWidget(self.fg_color_btn)

        self.apply_fg_btn = QPushButton("Apply Text Color")
        self.apply_fg_btn.clicked.connect(self.apply_fg_color)
        self.apply_fg_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; }")
        fg_layout.addWidget(self.apply_fg_btn)
        color_layout.addLayout(fg_layout)

        # Background color
        bg_layout = QVBoxLayout()
        bg_layout.addWidget(QLabel("Background Color:"))

        self.bg_color_btn = QPushButton()
        self.bg_color_btn.setFixedSize(40, 40)
        self.update_bg_preview()
        self.bg_color_btn.clicked.connect(self.choose_bg_color)
        bg_layout.addWidget(self.bg_color_btn)

        self.apply_bg_btn = QPushButton("Apply Background")
        self.apply_bg_btn.clicked.connect(self.apply_bg_color)
        self.apply_bg_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; }")
        bg_layout.addWidget(self.apply_bg_btn)
        color_layout.addLayout(bg_layout)

        # Reset button
        reset_layout = QVBoxLayout()
        reset_layout.addWidget(QLabel("Reset:"))

        self.reset_btn = QPushButton("Reset Formatting")
        self.reset_btn.clicked.connect(self.reset_formatting)
        self.reset_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
        reset_layout.addWidget(self.reset_btn)
        color_layout.addLayout(reset_layout)

        color_group.setLayout(color_layout)
        main_layout.addWidget(color_group)

        # Status area
        self.status_label = QPlainTextEdit()
        self.status_label.setMaximumHeight(80)
        self.status_label.setPlainText("Status: Ready - Select text and choose colors")
        self.status_label.setReadOnly(True)
        main_layout.addWidget(self.status_label)

    def choose_fg_color(self):
        color = QColorDialog.getColor(self.current_color, self, "Choose Text Color")
        if color.isValid():
            self.current_color = color
            self.update_fg_preview()
            self.update_status(f"Selected text color: {color.name()}")

    def choose_bg_color(self):
        color = QColorDialog.getColor(self.current_bg_color, self, "Choose Background Color")
        if color.isValid():
            self.current_bg_color = color
            self.update_bg_preview()
            self.update_status(f"Selected background color: {color.name()}")

    def update_fg_preview(self):
        self.fg_color_btn.setStyleSheet(
            f"QPushButton {{ background-color: {self.current_color.name()}; border: 2px solid black; }}"
        )

    def update_bg_preview(self):
        self.bg_color_btn.setStyleSheet(
            f"QPushButton {{ background-color: {self.current_bg_color.name()}; border: 2px solid black; }}"
        )

    def apply_fg_color(self):
        cursor = self.text_edit.textCursor()
        if not cursor.hasSelection():
            self.update_status("No text selected for foreground color!")
            return

        text_format = QTextCharFormat()
        text_format.setForeground(self.current_color)
        cursor.mergeCharFormat(text_format)
        self.update_status(f"Applied text color: {self.current_color.name()}")

    def apply_bg_color(self):
        cursor = self.text_edit.textCursor()
        if not cursor.hasSelection():
            self.update_status("No text selected for background color!")
            return

        text_format = QTextCharFormat()
        text_format.setBackground(self.current_bg_color)
        cursor.mergeCharFormat(text_format)
        self.update_status(f"Applied background color: {self.current_bg_color.name()}")

    def reset_formatting(self):
        cursor = self.text_edit.textCursor()
        if not cursor.hasSelection():
            self.update_status("No text selected to reset!")
            return

        # Create default format
        default_format = QTextCharFormat()
        default_format.setForeground(QColor(0, 0, 0))
        default_format.setBackground(QColor(255, 255, 255, 0))  # Transparent

        cursor.mergeCharFormat(default_format)
        self.update_status("Reset text formatting to default")

    def update_status(self, message):
        self.status_label.setPlainText(f"Status: {message}")

    def keyPressEvent(self, event):
        # Keyboard shortcuts
        if event.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
            if event.key() == Qt.Key_F:
                self.apply_fg_color()
            elif event.key() == Qt.Key_B:
                self.apply_bg_color()
        else:
            super().keyPressEvent(event)


def main():
    app = QApplication(sys.argv)
    editor = AdvancedColorTextEditor()
    editor.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()