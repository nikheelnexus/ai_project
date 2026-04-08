from pyqt_common_widget.import_module import *
from pyqt_common_widget import sample_widget_template, color_variable

from pyqt_common_widget.import_module import *
from pyqt_common_widget import sample_widget_template
from company_ai_project.ui.company_ui.right_widget.dashboard import overall_status_widget, bottom_widget



# PDF Viewer Widget
class dashboard_common(QWidget):
    def __init__(self, parent=None, commmon_widget=None):
        super().__init__(parent)
        self.sample_widget_template = sample_widget_template.SAMPLE_WIDGET_TEMPLATE()
        self.color_variable = color_variable.COLOR_VARIABLE()
        self.commmon_widget = commmon_widget

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.main_widget())
        self.setLayout(self.layout)

    def main_widget(self):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget, set_spacing=5)

        overall_status_widget_class = overall_status_widget.overall_status_widget(commmon_widget=self.commmon_widget)
        vertical_layout.addWidget(overall_status_widget_class)

        stake_widget = QStackedWidget()
        stake_widget.addWidget(bottom_widget.bottom_widget())
        vertical_layout.addWidget(stake_widget)


        return widget

