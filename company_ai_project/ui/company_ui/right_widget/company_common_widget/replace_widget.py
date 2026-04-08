from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QProgressDialog, QMessageBox, QApplication
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from pyqt_common_widget.import_module import *
from pyqt_common_widget import sample_widget_template, color_variable
from company_ai_project.automate.company_automate import add_all_link, link_rewrite, overview
from company_ai_project.database.company_database import company_information, company_name_link
from company_ai_project.ui.company_ui.right_widget.company_common_widget import company_overview_widget, \
    company_link_widget, company_information_widget

import webbrowser
import urllib.parse


# Worker thread for background processing
class ReplaceWorker(QThread):
    finished = pyqtSignal(bool, str)  # success, message
    progress = pyqtSignal(str)  # progress message

    def __init__(self, company_data, add_all_links, overview_enabled):
        super().__init__()
        self.company_data = company_data
        self.add_all_links = add_all_links
        self.overview_enabled = overview_enabled

    def run(self):
        try:
            if self.add_all_links:
                self.progress.emit("Adding all links...")
                add_all_link.process_company(company=self.company_data, replace=True)

            if self.overview_enabled:
                self.progress.emit("Updating overview...")
                overview.set_overview(company=self.company_data, replace=True)

            self.progress.emit("Complete!")
            self.finished.emit(True, "Data replaced successfully!")
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")


# PDF Viewer Widget
class replace_common(QWidget):
    def __init__(self, parent=None, commmon_widget=None, widget=None):
        super().__init__(parent)
        self.sample_widget_template = sample_widget_template.SAMPLE_WIDGET_TEMPLATE()
        self.color_variable = color_variable.COLOR_VARIABLE()
        self.commmon_widget = commmon_widget
        self.overview_widget = company_overview_widget.company_overview_widget(commmon_widget=self.commmon_widget)
        self.link_widget = company_link_widget.company_link_widget(commmon_widget=self.commmon_widget)
        self.information_widget = company_information_widget.company_information(commmon_widget=self.commmon_widget)
        self.company_data = None
        self.__widget = widget
        # Store buttons for style management
        self.navigation_buttons = []
        self.current_active_button = None

        # Background thread variables
        self.worker = None
        self.status_label = None  # Optional: add a status label to show progress

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.main_widget())
        self.setLayout(self.layout)

    def main_widget(self):
        '''
        :return: main widget
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget, set_spacing=5)

        vertical_layout.addWidget(self.replace_checkbox_widget())

        # Add a status label (optional)
        self.status_label = self.sample_widget_template.label(set_text="Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        vertical_layout.addWidget(self.status_label)

        self.replace_button = self.sample_widget_template.pushButton(set_text='Replace Data')
        self.replace_button.clicked.connect(self.replace_all_data_def)
        vertical_layout.addWidget(self.replace_button)

        return widget

    def replace_checkbox_widget(self):
        '''
        :return: checkbox widget
        '''
        widget = self.sample_widget_template.widget_def()
        horizontal_layout = self.sample_widget_template.horizontal_layout(parent_self=widget)

        self.add_all_link_checkbox = self.sample_widget_template.checkbox(set_text="Add all links", set_checked=True)
        horizontal_layout.addWidget(self.add_all_link_checkbox)

        self.overview_checkbox = self.sample_widget_template.checkbox(set_text="Overview", set_checked=True)
        horizontal_layout.addWidget(self.overview_checkbox)

        return widget

    def replace_all_data_def(self):
        '''
        Handle replace all data button click with background processing
        UI remains fully interactive during operation
        '''
        reply = QMessageBox.question(self, 'Confirm Replace',
                                     f'Are you sure you want to replace ALL data for this company?\n\nThis action cannot be undone.\n\nYou can continue using the UI while processing happens in the background.',
                                     QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            print("Replace all data button clicked - Starting background process")
            self.company_data = self.__widget.company_data

            # Disable the button during operation
            self.replace_button.setEnabled(False)
            self.replace_button.setText("Processing...")

            # Disable checkboxes during operation
            self.add_all_link_checkbox.setEnabled(False)
            self.overview_checkbox.setEnabled(False)

            # Update status
            if self.status_label:
                self.status_label.setText("Processing in background... You can continue using the UI")
                self.status_label.setStyleSheet("color: green;")

            # Create and start background thread
            self.worker = ReplaceWorker(
                company_data=self.company_data,
                add_all_links=self.add_all_link_checkbox.isChecked(),
                overview_enabled=self.overview_checkbox.isChecked()
            )

            # Connect signals
            self.worker.finished.connect(self.on_replace_finished)
            self.worker.progress.connect(self.on_replace_progress)

            # Start the worker thread (UI remains fully interactive)
            self.worker.start()

            # Optional: Show a non-modal notification instead of blocking dialog
            # Comment this out if you don't want any dialog at all
            self.show_non_blocking_notification()

        else:
            print("Replace operation cancelled")

    def show_non_blocking_notification(self):
        '''
        Show a non-blocking notification (optional)
        '''
        # Create a temporary status bar message or tooltip
        # This won't block UI interaction
        if self.status_label:
            self.status_label.setText("Background processing started... Check status label for updates")

        # Or use a non-modal message box that doesn't block
        # msg = QMessageBox(self)
        # msg.setWindowTitle("Processing")
        # msg.setText("Data replacement started in background.\nYou can continue using the application.")
        # msg.setModal(False)
        # msg.show()

    def on_replace_progress(self, message):
        '''
        Update status with current operation progress
        :param message: progress message to display
        '''
        if self.status_label:
            self.status_label.setText(f"Status: {message}")
            # Force update
            QApplication.processEvents()
        print(f"Progress: {message}")

    def on_replace_finished(self, success, message):
        '''
        Handle completion of replace operation
        :param success: boolean indicating if operation succeeded
        :param message: result message
        '''
        # Re-enable the UI controls
        self.replace_button.setEnabled(True)
        self.replace_button.setText("Replace Data")
        self.add_all_link_checkbox.setEnabled(True)
        self.overview_checkbox.setEnabled(True)

        if success:
            # Update the UI with new data
            if self.status_label:
                self.status_label.setText("Ready")
                self.status_label.setStyleSheet("")

            self.__widget.update_ui(self.company_data)
            QMessageBox.information(self, 'Success', message)
            print("Data replaced successfully!")
        else:
            if self.status_label:
                self.status_label.setText(f"Error: {message}")
                self.status_label.setStyleSheet("color: red;")

            QMessageBox.critical(self, 'Error', f'Failed to replace data:\n{message}')
            print(f"Error during replace operation: {message}")

        # Clean up worker
        if self.worker:
            self.worker.deleteLater()
            self.worker = None

    def closeEvent(self, event):
        '''
        Clean up thread when widget is closed
        '''
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(self, 'Operation in Progress',
                                         'A replacement operation is still running. Do you want to stop it and close?',
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.worker.terminate()
                self.worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()