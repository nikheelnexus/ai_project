from pyqt_common_widget.import_module import *
from pyqt_common_widget import sample_widget_template, color_variable

from pyqt_common_widget.import_module import *
from pyqt_common_widget import sample_widget_template
from company_ai_project.database.company_database import company_name_link, link, overview
from company_ai_project.database.certification_database import certification_db
import json


get_all_companies = company_name_link.CompanyNameLink().get_all_companies()
link_db = link.LinkTable()
filter_link_db = link.FilterLinkTable()
overview_db = overview.OverviewTable()
summery_db = overview.SummaryTable()
certification_db = certification_db.CertificationDB()


# PDF Viewer Widget
class overall_status_widget(QWidget):
    def __init__(self, parent=None, commmon_widget=None):
        super().__init__(parent)
        self.sample_widget_template = sample_widget_template.SAMPLE_WIDGET_TEMPLATE()
        self.color_variable = color_variable.COLOR_VARIABLE()
        self.commmon_widget = commmon_widget
        self.total_company_link = 0
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.main_widget())
        self.setLayout(self.layout)

    def get_status_data(self):
        '''

        :return:
        '''
        all_link_list = []
        filter_link_list = []
        overview_link_list = []
        summery_link_list = []
        link_list, filter_link_list, overview_link_list, summery_link_list, certifiction_list = self.get_total_company_link()
        status_dic = {}
        status_dic['Total Company'] = len(get_all_companies)
        status_dic['Total Company Link '] = link_list
        status_dic['Total Company Filter Link '] = filter_link_list
        status_dic['Total Company Overview '] = overview_link_list
        status_dic['Total Company Summery '] = summery_link_list
        status_dic['Total Certification '] = certifiction_list


        return status_dic

    def main_widget(self):
        '''
        Read from JSON file and create grid with 5 items per row
        :return:
        '''
        # Read from JSON file
        status_data = self.get_status_data()

        widget = self.sample_widget_template.widget_def()
        grid_layout = self.sample_widget_template.grid_layout(parent_self=widget, set_spacing=5)

        # Set 5 columns per row
        columns_per_row = 5
        row = 0
        col = 0

        for status_label, status_value in status_data.items():
            status_widget = self.common_widget(status_label, status_value)
            grid_layout.addWidget(status_widget, row, col)

            col += 1
            if col >= columns_per_row:
                col = 0
                row += 1

        return widget

    def common_widget(self, staus_label, status_value):
        '''

        :return:
        '''
        font = QFont()
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget)
        font.setPointSize(20)
        label = self.sample_widget_template.label(set_text=staus_label, set_alighment=self.sample_widget_template.center_alignment)
        label.setFont(font)
        vertical_layout.addWidget(label)

        value = self.sample_widget_template.label(set_text=str(status_value), set_alighment=self.sample_widget_template.center_alignment)
        font.setPointSize(60)
        value.setFont(font)
        vertical_layout.addWidget(value)

        return widget

    def get_total_company_link(self):
        '''

        :return:
        '''
        all_link_list = []
        filter_link_list = []
        overview_link_list = []
        summery_link_list = []

        all_link_list = list(set(link_db.get_unique_names()))
        filter_link_list = list(set(filter_link_db.get_unique_names()))
        overview_link_list = list(set(overview_db.get_unique_names()))
        summery_link_list = list(set(summery_db.get_unique_names()))
        certification_list = list(certification_db.get_all_certifications())

        return len(all_link_list), len(filter_link_list), len(overview_link_list), len(summery_link_list), len(certification_list)
