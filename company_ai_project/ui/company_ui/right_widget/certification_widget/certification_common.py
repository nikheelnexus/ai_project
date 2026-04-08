from pyqt_common_widget.import_module import *
import re
from pyqt_common_widget import sample_widget_template, color_variable
from pyqt_common_widget.import_module import *
from pyqt_common_widget import sample_widget_template
from company_ai_project.database.certification_database import certification_db

_certification_db = certification_db.CertificationDB()
# PDF Viewer Widget
class certification_common(QWidget):
    def __init__(self, parent=None, commmon_widget=None):
        super().__init__(parent)
        self.sample_widget_template = sample_widget_template.SAMPLE_WIDGET_TEMPLATE()
        self.color_variable = color_variable.COLOR_VARIABLE()
        self.commmon_widget = commmon_widget

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.main_widget())
        self.setLayout(self.layout)
        self.update_ui()

    def main_widget(self):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget, set_spacing=5)

        splitter = self.sample_widget_template.splitter_def(parent_self=widget, set_orientation=self.sample_widget_template.horizonatal)
        vertical_layout.addWidget(splitter)

        splitter.addWidget(self.certification_tree_widget_def())

        self.certification_textedit = QTextEdit()
        splitter.addWidget(self.certification_textedit)

        return widget

    def certification_tree_widget_def(self):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget)

        self.filter_line_edit = self.sample_widget_template.line_edit()
        self.filter_line_edit.textChanged.connect(self.filter_line_edit_changed)
        vertical_layout.addWidget(self.filter_line_edit)

        self.certification_tree_widget = self.sample_widget_template.treeWidget(setHeaderHidden=True)
        self.certification_tree_widget.selectionModel().selectionChanged.connect(self.on_certification_item_clicked)
        vertical_layout.addWidget(self.certification_tree_widget)


        return widget

    def on_certification_item_clicked(self):
        '''

        :return:
        '''
        selected_item = self.certification_tree_widget.selectedItems()
        if selected_item:
            selected_item = selected_item[0]
            data = selected_item.data(0, Qt.UserRole)
            certification_data = data.get('certification_data')
            text = self.markdown_to_html(certification_data)
            self.certification_textedit.setHtml(text)

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

    def filter_line_edit_changed(self):
        '''

        :return:
        '''
        text = self.filter_line_edit.text()
        self.update_ui(text=text)
        print(text)

    def update_ui(self, text=''):
        '''
        Update the UI with certifications, optionally filtered by search text
        :param text: Search text to filter certifications (empty string shows all)
        :return:
        '''
        get_all_certification = _certification_db.get_all_certifications()
        self.certification_tree_widget.clear()
        a = 1

        for each in get_all_certification:
            certification_name = f'{a} : {each["certification_name"]}'

            # Display if: no search text OR search text matches certification name
            if not text or text.lower() in certification_name.lower():
                item = QTreeWidgetItem(self.certification_tree_widget)
                item.setText(0, certification_name)
                item.setData(0, Qt.UserRole, each)
                a += 1