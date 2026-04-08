import json

from pyqt_common_widget.import_module import *
from pyqt_common_widget import sample_widget_template
from common_script import common
import webbrowser
import urllib.parse
from company_ai_project.database.exibition_database import exibition_db
from company_ai_project.database.company_database import company_information, company_name_link

_exibition_db = exibition_db.ExhibitorDB()
_company_name_link_db = company_name_link.CompanyNameLink()


# PDF Viewer Widget
class manual_widget(QWidget):
    def __init__(self, parent=None, commmon_widget=None, database='Company', widget=None):
        super().__init__(parent)
        self.sample_widget_template = sample_widget_template.SAMPLE_WIDGET_TEMPLATE()
        self.commmon_widget = commmon_widget
        self.database = database
        self.__widget = widget
        self.layout = self.sample_widget_template.vertical_layout(parent_self=self)
        self.layout.addWidget(self.main_widget())
        self.setLayout(self.layout)

    def main_widget(self):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget, set_spacing=15)

        vertical_layout.addItem(self.sample_widget_template.spaceItem())
        label = self.sample_widget_template.label(set_text='MANUAL',
                                                  set_alighment=self.sample_widget_template.center_alignment)
        vertical_layout.addWidget(label)

        vertical_layout.addWidget(self.company_name_widget())
        vertical_layout.addWidget(self.company_website_widget())

        create_button = self.sample_widget_template.pushButton(set_text='Create')
        create_button.clicked.connect(self.add_to_database_button_clicked)
        vertical_layout.addWidget(create_button)

        remove_button = self.sample_widget_template.pushButton(set_text='Remove')
        remove_button.clicked.connect(self.remove_to_database_button_clicked)
        vertical_layout.addWidget(remove_button)

        vertical_layout.addItem(self.sample_widget_template.spaceItem())

        return widget

    def company_name_widget(self):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        horizontal_layout = self.sample_widget_template.horizontal_layout(parent_self=widget, set_spacing=5)
        label = self.sample_widget_template.label(set_text='COMPANY NAME',
                                                  set_alighment=self.sample_widget_template.center_alignment)
        horizontal_layout.addWidget(label)

        self.company_name = self.sample_widget_template.line_edit()
        horizontal_layout.addWidget(self.company_name)

        search_company_button = self.sample_widget_template.pushButton(set_text='...')
        search_company_button.clicked.connect(self.search_company_in_browser)  # Connect the button
        horizontal_layout.addWidget(search_company_button)

        return widget

    def search_company_in_browser(self):
        '''
        Search the company name in Firefox
        :return:
        '''
        company_name = self.company_name.text()
        encoded_query = urllib.parse.quote(company_name)

        # Format the Google search URL
        search_url = f"https://www.google.com/search?q={encoded_query}"

        webbrowser.open(search_url)

    def on_go_website_clicked(self):
        """Handle Go button click - open the selected website"""
        website_url = self.company_website.text()

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

    def company_website_widget(self):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        horizontal_layout = self.sample_widget_template.horizontal_layout(parent_self=widget, set_spacing=5)
        label = self.sample_widget_template.label(set_text='COMPANY WEBSITE',
                                                  set_alighment=self.sample_widget_template.center_alignment)
        horizontal_layout.addWidget(label)

        # CHANGE THIS LINE - fix the spelling from "comapny_website" to "company_website"
        self.company_website = self.sample_widget_template.line_edit()  # Fixed spelling
        horizontal_layout.addWidget(self.company_website)  # Fixed spelling

        search_company_website_button = self.sample_widget_template.pushButton(set_text='...')
        search_company_website_button.clicked.connect(self.on_go_website_clicked)
        horizontal_layout.addWidget(search_company_website_button)

        return widget

    def update_ui(self, company_name='', website=''):
        '''

        :param company_name:
        :param website:
        :return:
        '''
        self.company_name.setText(company_name)
        self.company_website.setText(website)  # This is now correct

    def remove_to_database_button_clicked(self):
        '''
        Remove company from database with confirmation
        :return:
        '''
        company_name = self.company_name.text()
        website = self.company_website.text()

        if self.database == 'Company':
            print('this is company')
            company_data = _company_name_link_db.search_companies(company_name)
            print(company_data)

            if company_data:
                company_data = company_data[0]
                unique_name = company_data.get('unique_name')

                # Show confirmation dialog
                reply = QMessageBox.question(
                    self,
                    'Confirm Deletion',
                    f'Are you sure you want to delete "{company_name}" from the database?\n\n'
                    f'Unique Name: {unique_name}\n\n'
                    f'This action cannot be undone!',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No  # Default to No for safety
                )

                if reply == QMessageBox.Yes:
                    # User confirmed, proceed with deletion
                    try:
                        _company_name_link_db.delete_company(unique_name)
                        QMessageBox.information(
                            self,
                            'Success',
                            f'Company "{company_name}" has been successfully deleted from the database.'
                        )
                        print(f"Company {unique_name} deleted successfully")

                        # Optional: Clear the input fields after deletion
                        self.company_name.clear()
                        self.company_website.clear()

                        # Optional: Refresh the UI or database view if needed
                        self.__widget.on_refresh_clicked()

                        _exibition_db.insert_exhibitor(company_name=company_name,
                                                       company_website='',
                                                       replace=True)

                    except Exception as e:
                        QMessageBox.critical(
                            self,
                            'Error',
                            f'Failed to delete company:\n{str(e)}'
                        )
                        print(f"Error deleting company: {e}")
                else:
                    # User cancelled
                    print("Deletion cancelled by user")
                    QMessageBox.information(
                        self,
                        'Cancelled',
                        'Deletion was cancelled.'
                    )
            else:
                # No company found
                QMessageBox.warning(
                    self,
                    'Company Not Found',
                    f'No company named "{company_name}" was found in the database.'
                )
                print(f"Company {company_name} not found in database")

        else:
            print('this would be exhibition')

            # First, check if the exhibition exists
            exhibition_data = _exibition_db.search_exhibitors(company_name)

            if exhibition_data:
                # Show confirmation dialog for exhibition deletion
                reply = QMessageBox.question(
                    self,
                    'Confirm Exhibition Deletion',
                    f'Are you sure you want to delete exhibition "{company_name}" from the database?\n\n'
                    f'This action cannot be undone!\n\n'
                    f'Note: This will remove all exhibition records for "{company_name}".',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No  # Default to No for safety
                )

                if reply == QMessageBox.Yes:
                    # User confirmed, proceed with exhibition deletion
                    try:
                        _exibition_db.delete_exhibitor_by_name(company_name=company_name)
                        QMessageBox.information(
                            self,
                            'Success',
                            f'Exhibition "{company_name}" has been successfully deleted from the database.'
                        )
                        print(f"Exhibition {company_name} deleted successfully")

                        # Clear input fields after deletion
                        self.company_name.clear()
                        self.company_website.clear()

                        # Refresh the UI if needed
                        if hasattr(self, '__widget') and hasattr(self.__widget, 'on_refresh_clicked'):
                            self.__widget.on_refresh_clicked()

                    except Exception as e:
                        QMessageBox.critical(
                            self,
                            'Error',
                            f'Failed to delete exhibition:\n{str(e)}'
                        )
                        print(f"Error deleting exhibition: {e}")
                else:
                    # User cancelled
                    print("Exhibition deletion cancelled by user")
                    QMessageBox.information(
                        self,
                        'Cancelled',
                        'Exhibition deletion was cancelled.'
                    )
            else:
                # No exhibition found
                QMessageBox.warning(
                    self,
                    'Exhibition Not Found',
                    f'No exhibition named "{company_name}" was found in the database.'
                )
                print(f"Exhibition {company_name} not found in database")

    def add_to_database_button_clicked(self):
        '''

        :return:
        '''
        company_name = self.company_name.text()
        website = self.company_website.text()
        if self.database == 'Company':
            print('THIS IS COMPANY NAME: ', company_name)
            print('THIS IS COMPANY WEBSITE : ', website)
            company_data = _company_name_link_db.search_companies(company_name)
            print(company_data)
            if company_data:
                print('THIS IS UPDATING ')
                company_data = company_data[0]
                print(json.dumps(company_data, indent=4))

                # Add confirmation box here
                reply = QMessageBox.question(self, 'Confirm Update', f'Update {company_name}?',
                                             QMessageBox.Yes | QMessageBox.No)

                if reply == QMessageBox.Yes:
                    # Add confirmation for replace
                    replace_reply = QMessageBox.question(self, 'Confirm Replace',
                                                         f'Are you sure you want to replace the data for {company_name}?\n\nThis action cannot be undone.',
                                                         QMessageBox.Yes | QMessageBox.No)

                    if replace_reply == QMessageBox.Yes:
                        _company_name_link_db.update_company_by_unique_name(unique_name=company_data.get('unique_name'),
                                                                            company_name=company_name,
                                                                            website=website)
                        self.company_name.setText('')
                        self.company_website.setText('')
                        self.__widget.on_refresh_clicked()

                        get_company = _company_name_link_db.get_company(company_data.get('unique_name'))
                        if get_company:
                            self.__widget.company_common_class.replace_all()
                            print(get_company)

                        QMessageBox.information(self, 'Success', 'Updated successfully!')
                    else:
                        print("Replace operation cancelled")

            else:
                self.__widget.on_refresh_clicked()

        else:
            print(f'{company_name} - {website}')
            if company_name and website:
                exibitor_name = _exibition_db.search_exhibitors(company_name)
                if exibitor_name:
                    exibitor_name = exibitor_name[0]

                    # Simple confirmation
                    reply = QMessageBox.question(self, 'Confirm', f'Add {company_name} to database?',
                                                 QMessageBox.Yes | QMessageBox.No)

                    if reply == QMessageBox.Yes:
                        _exibition_db.insert_exhibitor(exhibitor_name=exibitor_name.get('exhibitor_name'),
                                                       company_name=company_name,
                                                       company_website=website,
                                                       company_data=exibitor_name.get('company_data'),
                                                       replace=True)
                        self.company_name.setText('')
                        self.company_website.setText('')
                        if self.__widget:
                            self.__widget.update_ui()
