import json
from PyQt5.QtCore import QTimer

from pyqt_common_widget.import_module import *
from pyqt_common_widget import sample_widget_template
from company_ai_project.ui.company_ui.right_widget.user_widget.right_widget.user_common_right_widget import \
    user_common_right_ui
from company_ai_project.database.user_database import user_comparable
from company_ai_project.database.company_database import company_information, company_name_link
from company_ai_project.ui.company_ui.right_widget.user_widget.right_widget.profile_widget import profile_common_ui
from company_ai_project.ui.company_ui.right_widget.company_common_widget import company_common


# PDF Viewer Widget
class profile_ui(QWidget):
    def __init__(self, parent=None, commmon_widget=None):
        super().__init__(parent)
        self.commmon_widget = commmon_widget
        self.sample_widget_template = sample_widget_template.SAMPLE_WIDGET_TEMPLATE()
        self.user_common_right_ui = user_common_right_ui.user_common_right_ui(commmon_widget=self.commmon_widget)
        self.company_information_db = company_information.CompanyInformationTable()
        self.company_name_link_db = company_name_link.CompanyNameLink()
        self.comparable_db = user_comparable.UserComparableDB()
        self.profile_common_ui = profile_common_ui.profile_common_ui(commmon_widget=self.commmon_widget)
        self.company_common_class = company_common.company_common(commmon_widget=self.commmon_widget)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.main_widget())
        self.setLayout(self.layout)
        self.update_ui()

    def main_widget(self):
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget)

        tab_widget = QTabWidget()
        vertical_layout.addWidget(tab_widget)
        tab_widget.addTab(self.profile_common_ui, "Profile Information")
        tab_widget.addTab(self.company_common_class, "Company Information")

        return widget


    def update_ui(self):
        '''

        :return:
        '''
        user_data = self.commmon_widget.user_data
        if not user_data:
            return

        user_data = user_data[0]
        website = user_data['website']
        self.profile_common_ui.update_ui(user_data=user_data)
        user_company_data = self.company_name_link_db.search_companies(search_text=website)
        if user_company_data:
            user_company_data = user_company_data[0]
            self.company_common_class.update_ui(company_data=user_company_data)
