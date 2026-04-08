from pyqt_common_widget.import_module import *
from pyqt_common_widget import sample_widget_template, color_variable
import re
from pyqt_common_widget.import_module import *
from pyqt_common_widget import sample_widget_template
from company_ai_project.database.company_database import company_information, company_name_link, overview, link



# PDF Viewer Widget
class company_link_widget(QWidget):
    def __init__(self, parent=None, commmon_widget=None):
        super().__init__(parent)
        self.sample_widget_template = sample_widget_template.SAMPLE_WIDGET_TEMPLATE()
        self.color_variable = color_variable.COLOR_VARIABLE()
        self.commmon_widget = commmon_widget
        self.link_db = link.LinkTable()
        self.filter_link_db = link.FilterLinkTable()


        self.layout = QVBoxLayout()
        self.layout.addWidget(self.main_widget())
        self.setLayout(self.layout)

    def main_widget(self):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget)

        link_label = self.sample_widget_template.label(set_text='Company Links')
        vertical_layout.addWidget(link_label)

        stake_widget = QStackedWidget()
        vertical_layout.addWidget(stake_widget)

        splitter = self.sample_widget_template.splitter_def(parent_self=widget,
                                                            set_orientation=self.sample_widget_template.horizonatal)
        stake_widget.addWidget(splitter)

        splitter.addWidget(self.link_tree_widget_def())
        splitter.addWidget(self.right_widget())

        return widget

    def link_tree_widget_def(self):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget)

        self.total_link_label = self.sample_widget_template.label(set_text='Total Links: 0')
        vertical_layout.addWidget(self.total_link_label)

        filter_lineedit = self.sample_widget_template.line_edit(set_text='', set_PlaceholderText='Filter Links...')
        vertical_layout.addWidget(filter_lineedit)

        self.link_tree_widget = self.sample_widget_template.treeWidget(setHeaderHidden=True)
        self.link_tree_widget.selectionModel().selectionChanged.connect(self.on_link_selection_changed)
        vertical_layout.addWidget(self.link_tree_widget)

        return widget

    def right_widget(self):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget)

        self.link_information = QTextEdit()
        vertical_layout.addWidget(self.link_information)

        return widget


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

    def update_ui(self, company_data):
        """Update the link tree widget with color coding, green items at top."""
        self.link_tree_widget.clear()
        unique_name = company_data['unique_name']
        link_data = self.link_db.get_links_by_unique_name(unique_name=unique_name)
        filter_link_data = self.filter_link_db.get_filter_links_by_unique_name(unique_name=unique_name)

        # Separate links with and without overview
        links_with_overview = []
        links_without_overview = []
        total_link = len(link_data)
        total_filter_link = len(filter_link_data)
        self.total_link_label.setText(f'Total Link: {total_link}, Filtered Link: {total_filter_link}')
        for each in link_data:
            link = each.get('link', '')
            link_overview = each.get('link_overview')

            if link_overview and str(link_overview).strip():
                # Has overview - will be green
                links_with_overview.append((link, link_overview))
            else:
                # No overview or empty
                links_without_overview.append((link, link_overview))

        a = 1
        # Add green items first (top of the tree)
        for link, link_overview in links_with_overview:
            item = QTreeWidgetItem(self.link_tree_widget)
            text = f'{a} {link}'
            item.setText(0, text)
            item.setData(0, Qt.UserRole, link_overview)
            item.setForeground(0, Qt.green)
            a+=1

        # Then add items without overview
        for link, link_overview in links_without_overview:
            item = QTreeWidgetItem(self.link_tree_widget)
            text = f'{a} {link}'
            item.setText(0, text)
            item.setData(0, Qt.UserRole, link_overview)
            # Default color (no need to set, or set to gray if you prefer)
            a+=1

        self.link_tree_widget.expandAll()



    def on_link_selection_changed(self):
        '''

        :return:
        '''
        selected_items = self.link_tree_widget.selectedItems()
        if selected_items:
            selected_item = selected_items[0]
            link_overview = selected_item.data(0, Qt.UserRole)
            if not link_overview:
                self.link_information.setHtml('')

            if link_overview:
                link_html = self.markdown_to_html(link_overview)
                self.link_information.setHtml(link_html)


