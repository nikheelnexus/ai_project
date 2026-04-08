from pyqt_common_widget.import_module import *
from pyqt_common_widget import sample_widget_template, color_variable
import re
from pyqt_common_widget.import_module import *
from pyqt_common_widget import sample_widget_template
from company_ai_project.ui.company_ui import left_widget, right_widget
from company_ai_project.database.company_database import company_information, company_name_link, overview


# PDF Viewer Widget
class company_overview_widget(QWidget):
    def __init__(self, parent=None, commmon_widget=None):
        super().__init__(parent)
        self.sample_widget_template = sample_widget_template.SAMPLE_WIDGET_TEMPLATE()
        self.color_variable = color_variable.COLOR_VARIABLE()
        self.commmon_widget = commmon_widget
        self.company_name_link_db = company_name_link.CompanyNameLink()
        self.company_information_db = company_information.CompanyInformationTable()
        self.overview_db = overview.OverviewTable()
        self.summery_db = overview.SummaryTable()

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

        self.overview_textedit = QTextEdit()
        self.company_summery = QTextEdit()

        tab_widget.addTab(self.overview_textedit, "Company Overview")
        tab_widget.addTab(self.company_summery, "Company Summery")

        return widget

    def update_ui(self, company_data):
        '''

        :return:
        '''
        unique_name = company_data['unique_name']
        overview = self.overview_db.get_overview(unique_name=unique_name)
        if overview:
            overview_text = overview.get('overview')
            small_overview_text = overview.get('small_overview')
            total_overview = f"## Small Overview\n\n{small_overview_text}\n\n## Detailed Overview\n\n{overview_text}"
            overview_html = self.markdown_to_html(total_overview)
            self.overview_textedit.setHtml(overview_html)
        else:
            self.overview_textedit.setHtml("<h2 style='color: #ffffff;'>No Overview Available</h2>")

        summery = self.summery_db.get_summary(unique_name=unique_name)
        if summery:
            summery = summery.get('summary')
            summery_html = self.markdown_to_html(summery)
            self.company_summery.setHtml(summery_html)
        else:
            self.company_summery.setHtml("<h2 style='color: #ffffff;'>No Summary Available</h2>")



    def markdown_to_html(self, text):
        """Simple yet beautiful markdown to HTML converter with dark theme"""

        # Basic conversions with dark theme styling
        text = re.sub(r'^# (.*)$',
                      r'<h1 style="color: #ffffff; border-bottom: 2px solid #3498db; padding-bottom: 10px; font-size: 24px; margin: 20px 0;">\1</h1>',
                      text, flags=re.MULTILINE)
        text = re.sub(r'^## (.*)$',
                      r'<h2 style="color: #ffffff; background: #3a3a3a; padding: 12px; border-left: 4px solid #e74c3c; margin: 18px 0; font-size: 20px; border-radius: 4px;">\1</h2>',
                      text, flags=re.MULTILINE)

        # Convert bullet points
        text = re.sub(r'^- (.*)$',
                      r'<li style="margin: 8px 0; padding: 5px 0; color: #e0e0e0; font-size: 16px;">\1</li>', text,
                      flags=re.MULTILINE)
        text = re.sub(r'(<li style=.*?</li>)',
                      r'<ul style="margin: 15px 0; padding-left: 30px; list-style: none; font-size: 16px;">\1</ul>',
                      text,
                      flags=re.DOTALL)

        # Convert bold and links
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #e74c3c; font-size: 16px;">\1</strong>', text)
        text = re.sub(r'(https?://[^\s]+)',
                      r'<a href="\1" style="color: #3498db; text-decoration: none; font-size: 16px;">\1</a>', text)

        # Handle regular paragraphs
        lines = text.split('\n')
        processed_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('<') and not line.startswith('-') and not line.startswith('#'):
                processed_lines.append(
                    f'<p style="color: #e0e0e0; font-size: 16px; margin: 10px 0; line-height: 1.6;">{line}</p>')
            else:
                processed_lines.append(line)

        text = '\n'.join(processed_lines)

        # Wrap in beautiful dark theme container
        html_content = f"""
        <div style="
            font-family: 'Arial', sans-serif;
            line-height: 1.7;
            color: #ffffff;
            background: #2b2b2b;
            padding: 25px;
            border-radius: 10px;
            font-size: 16px;
        ">
            {text}
        </div>
        """

        return html_content
