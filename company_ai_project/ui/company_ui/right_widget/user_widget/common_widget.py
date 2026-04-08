from pyqt_common_widget.import_module import *
from pyqt_common_widget import sample_widget_template
from company_ai_project.ui.company_ui.right_widget.user_widget.right_widget.company_list_widget import company_list_ui
from company_ai_project.ui.company_ui.right_widget.user_widget.right_widget.saved_company_widget import saved_company_ui
from company_ai_project.ui.company_ui.right_widget.user_widget.right_widget.profile_widget import profile_ui
from company_ai_project.database.user_database import user
from PyQt5.QtWidgets import QButtonGroup  # Add this import


# PDF Viewer Widget
class commonWidget(QWidget):
    def __init__(self, parent=None, commmon_widget=None, first_name='Nikheel', last_name='Patel'):
        super().__init__(parent)
        self.commmon_widget = commmon_widget
        self.sample_widget_template = sample_widget_template.SAMPLE_WIDGET_TEMPLATE()
        self.first_name = first_name
        self.last_name = last_name
        self.user_data = self.get_user_data()
        self.company_list_ui = company_list_ui.company_list_ui(commmon_widget=self)
        self.saved_company_ui = saved_company_ui.saved_company_ui(commmon_widget=self)
        self.profile_ui = profile_ui.profile_ui(commmon_widget=self)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.main_widget())
        self.setLayout(self.layout)

    def main_widget(self):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget)

        splitter = QSplitter()
        splitter.addWidget(self.left_widget())
        splitter.addWidget(self.right_widget())
        vertical_layout.addWidget(splitter)

        return widget

    def left_widget(self):
        '''
        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget, set_spacing=5)

        # Create buttons
        company_list_button = self.sample_widget_template.pushButton(set_text='Company list')
        saved_company_button = self.sample_widget_template.pushButton(set_text='Save Company')
        profile_button = self.sample_widget_template.pushButton(set_text='Profile')

        # Set default stylesheet
        default_style = """
            QPushButton {
                background-color: #f0f0f0;
                color: black;
                border: 1px solid #ccc;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """

        active_style = """
            QPushButton {
                background-color: green;
                color: white;
                border: 1px solid #006400;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #006400;
            }
        """

        # Apply default style to all buttons
        for button in [company_list_button, saved_company_button, profile_button]:
            button.setStyleSheet(default_style)

        # Store buttons as instance variables for access in other methods
        self.buttons = [company_list_button, saved_company_button, profile_button]
        self.default_style = default_style
        self.active_style = active_style

        # Connect buttons directly instead of using QButtonGroup
        company_list_button.clicked.connect(lambda: self.on_button_click(0, company_list_button))
        saved_company_button.clicked.connect(lambda: self.on_button_click(1, saved_company_button))
        profile_button.clicked.connect(lambda: self.on_button_click(2, profile_button))

        # Add buttons to layout
        vertical_layout.addWidget(company_list_button)
        vertical_layout.addWidget(saved_company_button)

        vertical_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        vertical_layout.addWidget(profile_button)

        # Optionally set first button as active by default
        company_list_button.setStyleSheet(active_style)

        return widget

    def on_button_click(self, index, clicked_button):
        '''
        Handle button clicks and update styles
        :param index: button index (0, 1, 2)
        :param clicked_button: the button that was clicked
        '''
        # Reset all buttons to default style
        for button in self.buttons:
            button.setStyleSheet(self.default_style)

        # Set clicked button to active style
        clicked_button.setStyleSheet(self.active_style)

        # Change the stacked widget index
        self.widget_change(index)

    def right_widget(self):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget)

        self.stake_widget = QStackedWidget()
        vertical_layout.addWidget(self.stake_widget)

        self.stake_widget.addWidget(self.company_list_ui)
        self.stake_widget.addWidget(self.saved_company_ui)
        self.stake_widget.addWidget(self.profile_ui)

        return widget

    def get_user_data(self):
        '''

        :return:
        '''
        user_db = user.UserDB()
        user_name = f"{self.first_name} {self.last_name}"
        user_data = user_db.search_users(user_name)
        return user_data

    def widget_change(self, value):
        '''

        :param value:
        :return:
        '''
        print(f"Changing to widget index: {value}")  # Add debug print
        self.stake_widget.setCurrentIndex(value)