import json
import re

from pyqt_common_widget.import_module import *
from pyqt_common_widget import sample_widget_template
from company_ai_project.ui.company_ui.right_widget.company_common_widget import company_common
from company_ai_project.ui.company_ui.right_widget.user_widget.right_widget.user_common_right_widget import \
    company_task_widget


# PDF Viewer Widget
class user_common_right_ui(QWidget):
    def __init__(self, parent=None, commmon_widget=None, phase_widget=False):
        super().__init__(parent)
        self.commmon_widget = commmon_widget
        self.sample_widget_template = sample_widget_template.SAMPLE_WIDGET_TEMPLATE()
        self.company_common = company_common.company_common(commmon_widget=self.commmon_widget, replace_widget_=True)
        self.phase_widget = phase_widget

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.main_widget())
        self.setLayout(self.layout)

    def main_widget(self):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget)

        tab_widget = QTabWidget()
        vertical_layout.addWidget(tab_widget)

        tab_widget.addTab(self.company_common_information_widget(), "Company Information")
        self.company_task_widget = None
        if self.phase_widget:
            self.company_task_widget = company_task_widget.company_task_widget(commmon_widget=self.commmon_widget)
            tab_widget.addTab(self.company_task_widget, "Company Task")

        return widget

    def company_common_information_widget(self):
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget)

        vertical_layout.addWidget(self.comparable_widget())
        vertical_layout.addWidget(self.company_information_comparable_widget())
        vertical_layout.addWidget(self.company_common_informaion_widget())

        return widget

    def comparable_widget(self):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def(min_size=[0, 0], max_size=[16777215, 200])
        horizontal_layout = self.sample_widget_template.horizontal_layout(parent_self=widget)

        self.comparable_button = self.sample_widget_template.pushButton(set_text='None',
                                                                        set_object_name='comparable_score')
        self.comparable_button.setMinimumSize(150, 150)
        self.comparable_button.setMaximumSize(150, 150)
        horizontal_layout.addWidget(self.comparable_button)

        self.detail_textedit = QTextEdit()
        # Font settings
        font = QFont()
        font.setPointSize(12)
        font.setFamily("Segoe UI")
        self.detail_textedit.setFont(font)

        # Text alignment and word wrap
        self.detail_textedit.setAlignment(Qt.AlignLeft)
        self.detail_textedit.setWordWrapMode(QTextOption.WordWrap)

        # Set minimum size
        self.detail_textedit.setMinimumHeight(200)
        self.detail_textedit.setMinimumWidth(400)

        horizontal_layout.addWidget(self.detail_textedit)

        return widget

    def company_information_comparable_widget(self):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        horizontal_layout = self.sample_widget_template.horizontal_layout(parent_self=widget)

        company_information_button = self.sample_widget_template.pushButton(set_text='Company Information')
        horizontal_layout.addWidget(company_information_button)

        comparable_button = self.sample_widget_template.pushButton(set_text='Comparable Companies')
        horizontal_layout.addWidget(comparable_button)

        return widget

    def company_common_informaion_widget(self):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget)

        stake_widget = QStackedWidget()
        vertical_layout.addWidget(stake_widget)

        stake_widget.addWidget(self.company_common)

        return widget

    def update_ui(self, company_data, comparable_json={}, task_json={}):
        '''

        :return:
        '''
        self.company_common.update_ui(company_data)
        if comparable_json:
            score = comparable_json.get('overall_compatibility_score', 'N/A')
            score_explanation = comparable_json['conclusion'].get('score_explanation', 'N/A')
            self.detail_textedit.setText(score_explanation)

            self.comparable_button.setText(score)
            if '%' not in score:
                score = str(score) + '%'
            self.comparable_button.setText(str(score))
            result = int(float(re.sub(r'[^\d.]', '', str(score))))

            # Set color based on score
            if result >= 60:
                color = '#4CAF50'  # Green for high scores
            elif result >= 40:
                color = '#FF9800'  # Orange for medium scores
            elif result >= 20:
                color = '#FF5722'  # Dark orange for low-medium scores
            else:
                color = '#F44336'  # Red for low scores

            self.comparable_button.setStyleSheet(
                f"QPushButton#comparable_score {{ background-color: {color}; color: #000000; font-size: 30px; font-weight: bold; border-radius: 75px; }}")

        if task_json:
            if self.company_task_widget:
                self.company_task_widget._update(task_json)