import json
import webbrowser
import urllib.parse
from pyqt_common_widget.import_module import *
import re
from pyqt_common_widget import sample_widget_template, color_variable
from pyqt_common_widget.import_module import *
from pyqt_common_widget import sample_widget_template
from company_ai_project.database.exibition_database import exibition_db
from company_ai_project.ui.company_ui.right_widget.manual_widget import manual_common
from company_ai_project.ui.company_ui.right_widget.company_common_widget import company_common

_exibition_db = exibition_db.ExhibitorDB()


# PDF Viewer Widget
class exibition_common(QWidget):
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

        splitter = self.sample_widget_template.splitter_def(parent_self=widget,
                                                            set_orientation=self.sample_widget_template.horizonatal)
        vertical_layout.addWidget(splitter)

        splitter.addWidget(self.exibition_tree_widget_def())

        self.right_stake_widget = QStackedWidget()
        self.right_stake_widget.addWidget(self.company_manual_widget())
        self.right_stake_widget.addWidget(self.company_common_widget())
        splitter.addWidget(self.right_stake_widget)

        return widget

    def company_manual_widget(self):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget)

        self.maual_widget = manual_common.manual_widget(commmon_widget=self.commmon_widget, database='Exibition', widget=self)
        vertical_layout.addWidget(self.maual_widget)

        return widget

    def company_common_widget(self):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget)

        self.company_common_class = company_common.company_common(commmon_widget=self.commmon_widget)
        vertical_layout.addWidget(self.company_common_class)

        return widget

    def exibition_tree_widget_def(self):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget)

        self.status_label = self.sample_widget_template.label(set_text='Exhibition Status: ')
        vertical_layout.addWidget(self.status_label)

        self.search_google_checkbox = self.sample_widget_template.checkbox(set_text='Search Google if no website',
                                                                           set_checked=True)
        vertical_layout.addWidget(self.search_google_checkbox)

        self.filter_line_edit = self.sample_widget_template.line_edit()
        self.filter_line_edit.textChanged.connect(self.filter_line_edit_changed)
        vertical_layout.addWidget(self.filter_line_edit)

        self.exibition_tree_widget = self.sample_widget_template.treeWidget(setHeaderHidden=True)
        self.exibition_tree_widget.selectionModel().selectionChanged.connect(self.on_exibition_item_clicked)
        vertical_layout.addWidget(self.exibition_tree_widget)

        return widget

    def on_exibition_item_clicked(self):
        '''

        :return:
        '''
        selected_item = self.exibition_tree_widget.selectedItems()
        if selected_item:
            selected_item = selected_item[0]
            data = selected_item.data(0, Qt.UserRole)
            company_name = data.get('company_name')
            company_website = data.get('company_website')
            if not company_website:
                self.right_stake_widget.setCurrentIndex(0)
                self.maual_widget.update_ui(company_name=company_name,
                                            website=company_website)
                if self.search_google_checkbox.isChecked():
                    self.search_company_in_browser(company_name)
            else:
                self.right_stake_widget.setCurrentIndex(1)

    def search_company_in_browser(self, company_name):
        '''
        Search the company name in Firefox
        :return:
        '''
        encoded_query = urllib.parse.quote(company_name)

        # Format the Google search URL
        search_url = f"https://www.google.com/search?q={encoded_query}"

        webbrowser.open(search_url)


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
        get_all_exibition = _exibition_db.get_all_exhibitors()
        self.exibition_tree_widget.clear()

        # Separate items with and without websites
        items_with_website = []
        items_without_website = []

        for each in get_all_exibition:
            website = each.get('company_website', '')
            # Check if website exists
            if website and website.strip():
                # Has website - normal color
                items_with_website.append(each)
            else:
                # No website - red color
                items_without_website.append(each)

        # Counter for numbering
        counter = 1
        # FIRST: Add all "No Website" items with numbers (these will be on top)
        for each in items_without_website:
            item = QTreeWidgetItem()
            company_name = each['company_name']
            item.setData(0, Qt.UserRole, each)
            item.setText(0, f"{counter}. {company_name} (No Website)")
            item.setForeground(0, QColor(255, 0, 0))  # Red color
            item.setToolTip(0, "No website available")
            self.exibition_tree_widget.addTopLevelItem(item)
            counter += 1

        # SECOND: Add all items with websites with numbers (these will be below)
        for each in items_with_website:
            item = QTreeWidgetItem()
            company_name = each['company_name']
            item.setData(0, Qt.UserRole, each)
            item.setText(0, f"{counter}. {company_name}")
            # make a item green
            item.setForeground(0, QColor(0, 255, 0))  # Green color
            self.exibition_tree_widget.addTopLevelItem(item)
            counter += 1
        status = f'Total Exhibitors: {len(get_all_exibition)} | With Website: {len(items_with_website)} | Without Website: {len(items_without_website)}'
        self.status_label.setText(status)

        # Apply search filter if needed
        if text:
            self.filter_exibition_tree(text)

    def filter_exibition_tree(self, text):
        '''Filter tree items based on search text'''
        for i in range(self.exibition_tree_widget.topLevelItemCount()):
            item = self.exibition_tree_widget.topLevelItem(i)
            company_name = item.text(0)
            # Check if item matches search text (case-insensitive)
            if text.lower() in company_name.lower():
                item.setHidden(False)
            else:
                item.setHidden(True)
