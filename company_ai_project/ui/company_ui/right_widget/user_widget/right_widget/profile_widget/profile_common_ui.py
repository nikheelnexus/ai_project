import json
from PyQt5.QtCore import QTimer

from pyqt_common_widget.import_module import *
from pyqt_common_widget import sample_widget_template
from company_ai_project.ui.company_ui.right_widget.user_widget.right_widget.user_common_right_widget import \
    user_common_right_ui
from company_ai_project.database.user_database import user_comparable

from company_ai_project.database.company_database import company_information, company_name_link


# PDF Viewer Widget
class profile_common_ui(QWidget):
    def __init__(self, parent=None, commmon_widget=None):
        super().__init__(parent)
        self.commmon_widget = commmon_widget
        self.sample_widget_template = sample_widget_template.SAMPLE_WIDGET_TEMPLATE()
        self.company_name_link_db = company_name_link.CompanyNameLink()

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.main_widget())
        self.setLayout(self.layout)

    def main_widget(self):
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget, set_spacing=5)

        vertical_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        vertical_layout.addWidget(self.company_name_widget())
        vertical_layout.addWidget(self.first_name_widget())
        vertical_layout.addWidget(self.last_name_widget())
        vertical_layout.addWidget(self.full_name_widget())
        vertical_layout.addWidget(self.user_name_widget())
        vertical_layout.addWidget(self.company_website_widget())
        vertical_layout.addWidget(self.email_address_widget())

        vertical_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))



        return widget

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

        return widget

    def first_name_widget(self):
        '''
        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        horizontal_layout = self.sample_widget_template.horizontal_layout(parent_self=widget)

        first_name_label = self.sample_widget_template.label(set_text='First Name:')
        horizontal_layout.addWidget(first_name_label)

        self.first_name_line_edit = self.sample_widget_template.line_edit(set_text='')
        horizontal_layout.addWidget(self.first_name_line_edit)

        return widget

    def last_name_widget(self):
        '''
        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        horizontal_layout = self.sample_widget_template.horizontal_layout(parent_self=widget)

        last_name_label = self.sample_widget_template.label(set_text='Last Name:')
        horizontal_layout.addWidget(last_name_label)

        self.last_name_line_edit = self.sample_widget_template.line_edit(set_text='')
        horizontal_layout.addWidget(self.last_name_line_edit)

        return widget

    def full_name_widget(self):
        '''
        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        horizontal_layout = self.sample_widget_template.horizontal_layout(parent_self=widget)

        full_name_label = self.sample_widget_template.label(set_text='Full Name:')
        horizontal_layout.addWidget(full_name_label)

        self.full_name_line_edit = self.sample_widget_template.line_edit(set_text='')
        horizontal_layout.addWidget(self.full_name_line_edit)

        return widget

    def user_name_widget(self):
        '''
        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        horizontal_layout = self.sample_widget_template.horizontal_layout(parent_self=widget)

        user_name_label = self.sample_widget_template.label(set_text='User Name:')
        horizontal_layout.addWidget(user_name_label)

        self.user_name_line_edit = self.sample_widget_template.line_edit(set_text='')
        horizontal_layout.addWidget(self.user_name_line_edit)

        return widget

    def company_website_widget(self):
        '''
        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        horizontal_layout = self.sample_widget_template.horizontal_layout(parent_self=widget)

        company_website_label = self.sample_widget_template.label(set_text='Company Website:')
        horizontal_layout.addWidget(company_website_label)

        self.company_website_lineedit = self.sample_widget_template.line_edit(set_text='')
        horizontal_layout.addWidget(self.company_website_lineedit)

        return widget

    def email_address_widget(self):
        '''
        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        horizontal_layout = self.sample_widget_template.horizontal_layout(parent_self=widget)

        email_address_label = self.sample_widget_template.label(set_text='Email:')
        horizontal_layout.addWidget(email_address_label)

        self.email_address_line_edit = self.sample_widget_template.line_edit(set_text='')
        horizontal_layout.addWidget(self.email_address_line_edit)

        return widget



    def update_ui(self, user_data):
        '''

        :return:
        '''
        if not user_data:
            return
        website = user_data['website']
        user_company_data = self.company_name_link_db.search_companies(search_text=website)
        company_name = user_company_data[0]['company_name'] if user_company_data else ''

        full_name_split = user_data['full_name'].split(' ')
        first_name = full_name_split[0] if len(full_name_split) > 0 else ''
        last_name = full_name_split[1] if len(full_name_split) > 1 else ''
        self.first_name_line_edit.setText(first_name)
        self.last_name_line_edit.setText(last_name)
        self.full_name_line_edit.setText(user_data['full_name'])
        self.user_name_line_edit.setText(user_data['username'])
        self.company_name_line_edit.setText(company_name)
        self.company_website_lineedit.setText(website)
        self.email_address_line_edit.setText(user_data['email'])









