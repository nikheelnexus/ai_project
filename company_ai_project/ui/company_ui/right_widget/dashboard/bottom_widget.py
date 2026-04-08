from pyqt_common_widget.import_module import *
from pyqt_common_widget import sample_widget_template, color_variable

from pyqt_common_widget.import_module import *
from pyqt_common_widget import sample_widget_template
import json


# PDF Viewer Widget
class bottom_widget(QWidget):
    def __init__(self, parent=None, commmon_widget=None):
        super().__init__(parent)
        self.sample_widget_template = sample_widget_template.SAMPLE_WIDGET_TEMPLATE()
        self.color_variable = color_variable.COLOR_VARIABLE()
        self.commmon_widget = commmon_widget

        # Store buttons and track active button
        self.navigation_buttons = []
        self.current_active_button = None

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.main_widget())
        self.setLayout(self.layout)

    def get_status_data(self):
        '''

        :return:
        '''
        status_dic = {}
        status_dic['Recent Company'] = self.sample_widget_template.label(set_text='Recent Company')
        status_dic['Recent Company List '] = self.sample_widget_template.label(set_text='Recent Company List')
        status_dic['Recent Company Filter Link '] = self.sample_widget_template.label(
            set_text='Recent Company Filter Link')
        status_dic['Recent Company Overview '] = self.sample_widget_template.label(set_text='Recent Company Overview')
        status_dic['Recent Company Summery '] = self.sample_widget_template.label(set_text='Recent Company Summery')

        return status_dic

    def set_button_style(self, button, is_active=False):
        '''
        Set button style based on active state
        :param button: button widget
        :param is_active: boolean indicating if button is active
        '''
        if is_active:
            # Green style for active button
            button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 8px 15px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
        else:
            # Default style for inactive buttons
            button.setStyleSheet("""""")

    def on_navigation_button_clicked(self, button, index):
        '''
        Handle navigation button click
        :param button: clicked button
        :param index: index of the widget to show
        '''
        # Reset the previously active button
        if self.current_active_button and self.current_active_button != button:
            self.set_button_style(self.current_active_button, is_active=False)

        # Set the new active button
        self.current_active_button = button
        self.set_button_style(button, is_active=True)

        # Switch to the selected widget
        self.bottom_stake_widget.setCurrentIndex(index)

    def main_widget(self):
        '''
        Read from JSON file and create grid with 5 items per row
        :return:
        '''
        # Read from JSON file
        status_data = self.get_status_data()

        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget)

        vertical_layout.addWidget(self.top_button_list_widget())

        self.bottom_stake_widget = QStackedWidget()
        for status_label, status_value in status_data.items():
            self.bottom_stake_widget.addWidget(status_value)

        vertical_layout.addWidget(self.bottom_stake_widget)

        return widget

    def top_button_list_widget(self):
        '''
        Create a button with given name
        :return:
        '''
        status_data = self.get_status_data()

        # Main widget that will contain everything
        widget = self.sample_widget_template.widget_def()
        main_layout = self.sample_widget_template.vertical_layout(parent_self=widget)

        # Create scroll area
        scroll_widget = QScrollArea()
        scroll_widget.setWidgetResizable(True)
        scroll_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_widget.setMaximumHeight(50)  # You can adjust this height

        # Container widget for scroll area
        scroll_container = self.sample_widget_template.widget_def()
        horizontal_layout = self.sample_widget_template.horizontal_layout(parent_self=scroll_container, set_spacing=5)

        button_index = 0
        self.button_list = []  # Store buttons to keep reference

        for status_label, status_value in status_data.items():
            button = self.sample_widget_template.pushButton(set_text=status_label)

            # Connect button click to the new handler function
            button.clicked.connect(lambda checked, idx=button_index, btn=button:
                                   self.on_navigation_button_clicked(btn, idx))

            horizontal_layout.addWidget(button)
            self.button_list.append(button)
            self.navigation_buttons.append(button)
            button_index += 1

        # Add stretch to push buttons to left (optional)
        horizontal_layout.addStretch()

        # Set the container widget to scroll area
        scroll_widget.setWidget(scroll_container)

        # Add scroll widget to main layout
        main_layout.addWidget(scroll_widget)

        # Set the first button as active by default
        if self.navigation_buttons:
            self.current_active_button = self.navigation_buttons[0]
            self.set_button_style(self.current_active_button, is_active=True)

        return widget