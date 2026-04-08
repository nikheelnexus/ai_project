from pyqt_common_widget.import_module import *
from pyqt_common_widget import sample_widget_template
from company_ai_project.ui.company_ui import left_widget, right_widget_ui


# PDF Viewer Widget
class commonWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sample_widget_template = sample_widget_template.SAMPLE_WIDGET_TEMPLATE()
        # self.company_database = company_db.CompanyDB()
        # self.exibition_database = exibition_database_new.ExhibitorDB()
        # self.certification_database = certification_database.CertificationDB()
        # self.user_database = user_db.UserDB()
        # self.company_database.get_all_companies()

        self.dashboard_common_widget = True
        self.company_list_widget = True
        self.exibition_list_widget = True
        self.manual_list_widget = True
        self.user_widget = True
        # self.all_user_widget = False
        self.certification_widget = True
        # self.auto_widget = False
        # self.mail_widget = False

        widget_list = []
        if self.dashboard_common_widget:
            widget_list.append('dashboard_common_widget')

        if self.company_list_widget:
            widget_list.append('company_list_widget')

        if self.exibition_list_widget:
            widget_list.append('exibition_list_widget')

        if self.manual_list_widget:
            widget_list.append('manual_list_widget')

        if self.user_widget:
            widget_list.append('user_widget')
        '''
        if self.all_user_widget:
            widget_list.append('all_user_widget')
        '''
        if self.certification_widget:
            widget_list.append('certification_widget')
        '''
        if self.auto_widget:
            widget_list.append('auto_widget')
        if self.mail_widget:
            widget_list.append('mail_widget')
        '''
        print(widget_list)

        self.left_widget_class = left_widget.left_widget(commmon_widget=self, widget_list=widget_list)
        self.right_widget_class = right_widget_ui.right_widget(commmon_widget=self, widget_list=widget_list)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.main_widget())
        self.setLayout(self.layout)

    def main_widget(self):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget)

        splitter = self.sample_widget_template.splitter_def(parent_self=widget,
                                                            set_orientation=self.sample_widget_template.horizonatal)
        vertical_layout.addWidget(splitter)

        splitter.addWidget(self.left_widget_class)

        self.right_main_stake_widget = QStackedWidget()
        splitter.addWidget(self.right_main_stake_widget)

        self.right_main_stake_widget.addWidget(self.right_widget_class)

        return widget
