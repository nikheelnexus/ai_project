from pyqt_common_widget.import_module import *
from pyqt_common_widget import sample_widget_template
from company_ai_project.ui.company_ui.right_widget.company_list import company_list_widget
from company_ai_project.ui.company_ui.right_widget.user_widget import common_widget as user_common_widget
from company_ai_project.ui.company_ui.right_widget.manual_widget import manual_common
from company_ai_project.ui.company_ui.right_widget.dashboard import dahboard_common
from company_ai_project.ui.company_ui.right_widget.certification_widget import certification_common
from company_ai_project.ui.company_ui.right_widget.exibition_widget import exibition_common


# PDF Viewer Widget
class right_widget(QWidget):
    def __init__(self, parent=None, commmon_widget=None, widget_list=[]):
        super().__init__(parent)
        self.sample_widget_template = sample_widget_template.SAMPLE_WIDGET_TEMPLATE()
        self.commmon_widget = commmon_widget
        self.widget_list = widget_list
        self.layout = self.sample_widget_template.vertical_layout(parent_self=self)
        self.layout.addWidget(self.main_widget())
        self.setLayout(self.layout)

    def main_widget(self):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget, set_spacing=5)

        self.right_widget_stake_widget = QStackedWidget()
        vertical_layout.addWidget(self.right_widget_stake_widget)

        if 'dashboard_common_widget' in self.widget_list:
            dahboard_common_widget_class = dahboard_common.dashboard_common(commmon_widget=self.commmon_widget)
            self.right_widget_stake_widget.addWidget(dahboard_common_widget_class)

        if 'company_list_widget' in self.widget_list:
            self.company_list_widget_class = company_list_widget.company_list_widget(commmon_widget=self.commmon_widget)
            self.right_widget_stake_widget.addWidget(self.company_list_widget_class)

        if 'exibition_list_widget' in self.widget_list:
            self.exibition_widget_class = exibition_common.exibition_common(commmon_widget=self.commmon_widget)
            self.right_widget_stake_widget.addWidget(self.exibition_widget_class)

        if 'manual_list_widget' in self.widget_list:
            self.manual_widget_class = manual_common.manual_widget(commmon_widget=self.commmon_widget)
            self.right_widget_stake_widget.addWidget(self.manual_widget_class)

        if 'user_widget' in self.widget_list:
            self.user_widget_class = user_common_widget.commonWidget(commmon_widget=self.commmon_widget)
            self.right_widget_stake_widget.addWidget(self.user_widget_class)

        if 'certification_widget' in self.widget_list:
            self.certification_widget_class = certification_common.certification_common(
                commmon_widget=self.commmon_widget)
            self.right_widget_stake_widget.addWidget(self.certification_widget_class)

        '''
        if 'company_name_website_widget' in self.widget_list:
            self.company_name_website_widget_class = company_name_website_widget_ui.company_name_website_widget(commmon_widget=self.commmon_widget)
            self.right_widget_stake_widget.addWidget(self.company_name_website_widget_class)
        
        if 'all_user_widget' in self.widget_list:
            self.all_user_widget_class = all_user_widget.user_widget(commmon_widget=self.commmon_widget)
            self.right_widget_stake_widget.addWidget(self.all_user_widget_class)
        
        if 'auto_widget' in self.widget_list:
            self.auto_widget_class = auto_widget.Auto_widget(commmon_widget=self.commmon_widget)
            self.right_widget_stake_widget.addWidget(self.auto_widget_class)

        if 'mail_widget' in self.widget_list:
            self.mail_widget_class = company_contact_email_status.company_contact_email_status(commmon_widget=self.commmon_widget)
            self.right_widget_stake_widget.addWidget(self.mail_widget_class)

        '''

        return widget
