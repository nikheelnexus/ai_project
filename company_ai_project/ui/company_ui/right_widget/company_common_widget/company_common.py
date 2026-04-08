from pyqt_common_widget.import_module import *
from pyqt_common_widget import sample_widget_template, color_variable
from company_ai_project.automate.company_automate import add_all_link, link_rewrite, overview
from company_ai_project.automate.company_automate import overview as auto_overview
from company_ai_project.database.company_database import company_information, company_name_link, link, overview
from company_ai_project.ui.company_ui.right_widget.company_common_widget import replace_widget

link_db = link.LinkTable()
filter_link_db = link.FilterLinkTable()
overview_db = overview.OverviewTable()

import webbrowser
import urllib.parse
from pyqt_common_widget.import_module import *
from pyqt_common_widget import sample_widget_template
from company_ai_project.ui.company_ui.right_widget.company_common_widget import company_overview_widget, \
    company_link_widget, company_information_widget


# PDF Viewer Widget
class company_common(QWidget):
    def __init__(self, parent=None, commmon_widget=None, widget=None, replace_widget_=False):
        super().__init__(parent)
        self.sample_widget_template = sample_widget_template.SAMPLE_WIDGET_TEMPLATE()
        self.color_variable = color_variable.COLOR_VARIABLE()
        self.commmon_widget = commmon_widget
        self.overview_widget = company_overview_widget.company_overview_widget(commmon_widget=self.commmon_widget)
        self.link_widget = company_link_widget.company_link_widget(commmon_widget=self.commmon_widget)
        self.information_widget = company_information_widget.company_information(commmon_widget=self.commmon_widget)
        self.replace_widget_class = replace_widget.replace_common(commmon_widget=self.commmon_widget, widget=self)
        self.replace_widget = replace_widget_
        self.company_data = None
        self.__widget = widget
        # Store buttons for style management
        self.navigation_buttons = []
        self.current_active_button = None

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.main_widget())
        self.setLayout(self.layout)

    def main_widget(self):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget, set_spacing=5)

        vertical_layout.addWidget(self.company_name_widget())
        vertical_layout.addWidget(self.company_website_widget())
        vertical_layout.addWidget(self.company_data_switch_widget())
        vertical_layout.addWidget(self.company_center_widget())
        if self.replace_widget:
            vertical_layout.addWidget(self.replace_widget_class)

        return widget

    def replace_all(self):
        '''

        :return:
        '''
        add_all_link.process_company(company=self.company_data, replace=True)
        auto_overview.set_overview(company=self.company_data, replace=True)
        self.update_ui(self.company_data)

    def replace_all_data_def(self):
        '''

        :return:
        '''
        reply = QMessageBox.question(self, 'Confirm Replace',
                                     f'Are you sure you want to replace ALL data for this company?\n\nThis action cannot be undone.',
                                     QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            print("Replace all data button clicked")
            print(self.company_data)
            self.replace_all()

            QMessageBox.information(self, 'Success', 'Data replaced successfully!')

        else:
            print("Replace operation cancelled")

    def company_name_widget(self):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        horizontal_layout = self.sample_widget_template.horizontal_layout(parent_self=widget)

        company_name_label = self.sample_widget_template.label(set_text='Company Name:')
        horizontal_layout.addWidget(company_name_label)

        self.company_name_line_edit = self.sample_widget_template.line_edit(set_text='')
        horizontal_layout.addWidget(self.company_name_line_edit)

        search_internet = self.sample_widget_template.pushButton(set_text='...')
        search_internet.clicked.connect(self.search_company_in_browser)  # Connect the button
        horizontal_layout.addWidget(search_internet)

        return widget

    def search_company_in_browser(self):
        '''
        Search the company name in Firefox
        :return:
        '''
        company_name = self.company_name_line_edit.text()
        encoded_query = urllib.parse.quote(company_name)

        # Format the Google search URL
        search_url = f"https://www.google.com/search?q={encoded_query}"

        webbrowser.open(search_url)

    def company_website_widget(self):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        horizontal_layout = self.sample_widget_template.horizontal_layout(parent_self=widget)

        company_website_label = self.sample_widget_template.label(set_text='Company Website:')
        horizontal_layout.addWidget(company_website_label)

        self.company_website_pushbutton = self.sample_widget_template.pushButton(set_text='')
        self.company_website_pushbutton.clicked.connect(self.on_go_website_clicked)  # Connect the button
        horizontal_layout.addWidget(self.company_website_pushbutton)

        return widget

    def on_go_website_clicked(self):
        """Handle Go button click - open the selected website"""
        website_url = self.company_website_pushbutton.text()

        if website_url:
            self.open_website(website_url)
        else:
            print("No website URL found for selected item")

    def open_website(self, url):
        """Open website in default browser"""
        try:
            # Ensure URL has http:// or https://
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            webbrowser.open(url)
            print(f"🌐 Opening website: {url}")

        except Exception as e:
            print(f"❌ Error opening website: {e}")

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
                    padding: 5px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
        else:
            # Default style for inactive buttons
            button.setStyleSheet('''''')

    def on_navigation_button_clicked(self, button, widget):
        '''
        Handle navigation button click
        :param button: clicked button
        :param widget: widget to show
        '''
        # Reset the previously active button
        if self.current_active_button and self.current_active_button != button:
            self.set_button_style(self.current_active_button, is_active=False)

        # Set the new active button
        self.current_active_button = button
        self.set_button_style(button, is_active=True)

        # Switch to the selected widget
        self.center_stake_widget.setCurrentWidget(widget)

    def company_data_switch_widget(self):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        horizontal_layout = self.sample_widget_template.horizontal_layout(parent_self=widget, set_spacing=5)

        company_overview_pushbutton = self.sample_widget_template.pushButton(set_text='Company Overview')
        company_overview_pushbutton.clicked.connect(
            lambda: self.on_navigation_button_clicked(company_overview_pushbutton, self.overview_widget))
        horizontal_layout.addWidget(company_overview_pushbutton)
        self.navigation_buttons.append(company_overview_pushbutton)

        links_pushbutton = self.sample_widget_template.pushButton(set_text='Links')
        links_pushbutton.clicked.connect(lambda: self.on_navigation_button_clicked(links_pushbutton, self.link_widget))
        horizontal_layout.addWidget(links_pushbutton)
        self.navigation_buttons.append(links_pushbutton)

        company_information_pushbutton = self.sample_widget_template.pushButton(set_text='Company Information')
        company_information_pushbutton.clicked.connect(
            lambda: self.on_navigation_button_clicked(company_information_pushbutton, self.information_widget))
        horizontal_layout.addWidget(company_information_pushbutton)
        self.navigation_buttons.append(company_information_pushbutton)

        # Set the first button as active by default
        if self.navigation_buttons:
            self.current_active_button = company_overview_pushbutton
            self.set_button_style(company_overview_pushbutton, is_active=True)

        return widget

    def company_center_widget(self):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget)

        self.center_stake_widget = QStackedWidget()
        vertical_layout.addWidget(self.center_stake_widget)

        self.center_stake_widget.addWidget(self.overview_widget)
        self.center_stake_widget.addWidget(self.link_widget)
        self.center_stake_widget.addWidget(self.information_widget)

        return widget

    def update_ui(self, company_data):
        '''

        :return:
        '''
        company_name = company_data.get('company_name', '')
        company_website = company_data.get('website', '')
        self.company_data = company_data
        self.company_name_line_edit.setText(company_name)
        self.company_website_pushbutton.setText(company_website)
        self.overview_widget.update_ui(company_data=company_data)
        self.link_widget.update_ui(company_data=company_data)
        self.information_widget.update_ui(company_data=company_data)

        all_link = link_db.get_links_by_unique_name(company_data['unique_name'])
        all_filter_link = filter_link_db.get_filter_links_by_unique_name(company_data['unique_name'])
        all_overview = overview_db.get_overview(unique_name=company_data['unique_name'])

        try:
            if not all_link or not all_filter_link:
                self.replace_widget_class.add_all_link_checkbox.setChecked(True)
            else:
                self.replace_widget_class.add_all_link_checkbox.setChecked(False)

            if not all_overview:
                self.replace_widget_class.overview_checkbox.setChecked(True)
            else:
                self.replace_widget_class.overview_checkbox.setChecked(False)
        except:
            pass

