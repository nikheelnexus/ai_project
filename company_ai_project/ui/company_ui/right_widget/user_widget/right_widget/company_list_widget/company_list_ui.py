import json
from PyQt5.QtCore import QTimer

from pyqt_common_widget.import_module import *
from pyqt_common_widget import sample_widget_template
from company_ai_project.ui.company_ui.right_widget.user_widget.right_widget.user_common_right_widget import \
    user_common_right_ui
from company_ai_project.database.user_database import user_comparable
from company_ai_project.database.company_database import company_information, company_name_link


# PDF Viewer Widget
class company_list_ui(QWidget):
    def __init__(self, parent=None, commmon_widget=None):
        super().__init__(parent)
        self.commmon_widget = commmon_widget
        self.sample_widget_template = sample_widget_template.SAMPLE_WIDGET_TEMPLATE()
        self.user_common_right_ui = user_common_right_ui.user_common_right_ui(commmon_widget=self.commmon_widget)
        self.company_information_db = company_information.CompanyInformationTable()
        self.company_name_link_db = company_name_link.CompanyNameLink()
        self.comparable_db = user_comparable.UserComparableDB()

        # Cache for storing loaded data
        self.cached_company_data = []  # Will store all loaded company data
        self.current_country = ""
        self.current_filter = ""
        self.current_min_score = 50  # Default minimum score

        # Timer for debouncing filter input
        self.filter_timer = QTimer()
        self.filter_timer.setSingleShot(True)
        self.filter_timer.timeout.connect(self.apply_filter)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.main_widget())
        self.setLayout(self.layout)

        # Load initial data
        self.load_initial_data()

        # Connect signals
        self.country_combobox.currentIndexChanged.connect(self.on_country_changed)
        self.minimum_score_lineedit.textChanged.connect(self.on_min_score_changed)

    def main_widget(self):
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget)

        splitter = QSplitter()
        splitter.addWidget(self.left_widget())
        splitter.addWidget(self.user_common_right_ui)
        vertical_layout.addWidget(splitter)

        return widget

    def left_widget(self):
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget, set_spacing=5)

        vertical_layout.addWidget(self.minimum_score_widget())
        vertical_layout.addWidget(self.country_widget())
        vertical_layout.addWidget(self.company_list_treewidget_def())

        return widget

    def minimum_score_widget(self):
        widget = self.sample_widget_template.widget_def()
        horizontal_layout = self.sample_widget_template.horizontal_layout(parent_self=widget)

        minumum_score_label = self.sample_widget_template.label(set_text="Minimum Score:")
        horizontal_layout.addWidget(minumum_score_label)

        self.minimum_score_lineedit = self.sample_widget_template.line_edit(set_text='50')
        horizontal_layout.addWidget(self.minimum_score_lineedit)

        return widget

    def country_widget(self):
        widget = self.sample_widget_template.widget_def()
        horizontal_layout = self.sample_widget_template.horizontal_layout(parent_self=widget)

        country_label = self.sample_widget_template.label(set_text="Country:")
        horizontal_layout.addWidget(country_label)

        self.country_combobox = self.sample_widget_template.comboBox(parent_self=widget)
        horizontal_layout.addWidget(self.country_combobox)

        return widget

    def company_list_treewidget_def(self):
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget)

        self.filter_lineedit = self.sample_widget_template.line_edit()
        self.filter_lineedit.textChanged.connect(self.on_filter_text_changed)
        vertical_layout.addWidget(self.filter_lineedit)

        self.company_list_treewidget = self.sample_widget_template.treeWidget()
        self.company_list_treewidget.setColumnCount(2)
        self.company_list_treewidget.setHeaderLabels(['Company Name', 'Compatibility Score'])
        self.company_list_treewidget.selectionModel().selectionChanged.connect(
            self.company_list_treewidget_selection_def)
        vertical_layout.addWidget(self.company_list_treewidget)

        return widget

    def load_initial_data(self):
        """Load all comparable company data once and cache it"""
        user_data = self.commmon_widget.user_data
        if not user_data:
            return

        user_data = user_data[0]
        website = user_data['website']
        company_name = self.company_name_link_db.search_companies(website)
        if company_name:
            company_name = company_name[0]
        comparable_companies = self.comparable_db.get_user_comparisons(user_unique_name=company_name.get('unique_name'))

        self.cached_company_data = []
        all_countries = []

        for eachCompany in comparable_companies:
            json_data = eachCompany.get('jsondata', {})
            if not json_data:
                continue

            score_str = json_data.get('overall_compatibility_score', '0%')
            score = int(score_str.split('%')[0])
            #client_website = eachCompany.get('client_website', '')
            client_unique_name = eachCompany.get('client_unique_name', '')
            company_name_link = self.company_name_link_db.get_company(unique_name=client_unique_name)

            if company_name_link:
                unique_name = company_name_link.get('unique_name', '')
                website = company_name_link.get('website', '')

                # Get company information
                company_info = self.company_information_db.get_company_information(unique_name)
                office_country_val = ""

                if company_info:
                    company_data = company_info.get('company_data', {})
                    office_country_val = company_data.get('office_country', '')

                    if office_country_val and office_country_val not in all_countries:
                        all_countries.append(office_country_val)
                # Cache all the data
                self.cached_company_data.append({
                    'score': score,
                    'company_name': company_name_link.get('company_name', ''),
                    'company_name_link': company_name_link,
                    'comparable_json': json_data,
                    'office_country': office_country_val,
                    'company_information': company_info,
                    'original_data': eachCompany,
                    'client_website': website
                })

        # Populate country combobox
        self.populate_country_combobox(all_countries)

        # Initial display
        self.apply_filter()

    def populate_country_combobox(self, countries):
        """Populate country combobox with sorted countries"""
        self.country_combobox.blockSignals(True)
        self.country_combobox.clear()
        self.country_combobox.addItem("All Countries")

        for country in sorted(countries):
            self.country_combobox.addItem(country)

        self.country_combobox.blockSignals(False)

    def on_filter_text_changed(self, text):
        """Handle filter text changes with debouncing"""
        self.current_filter = text.lower()
        # Restart timer on each key press (300ms delay)
        self.filter_timer.stop()
        self.filter_timer.start(300)

    def on_country_changed(self):
        """Handle country selection changes"""
        self.current_country = self.country_combobox.currentText()
        if self.current_country == "All Countries":
            self.current_country = ""
        self.apply_filter()

    def on_min_score_changed(self, text):
        """Handle minimum score changes"""
        try:
            self.current_min_score = int(text) if text else 0
        except ValueError:
            self.current_min_score = 0
        self.apply_filter()

    def apply_filter(self):
        """Apply all filters (country, text, and minimum score) to cached data"""
        filtered_data = []

        for company_info in self.cached_company_data:
            # Apply minimum score filter
            if company_info['score'] < self.current_min_score:
                continue

            # Apply country filter
            if self.current_country and company_info['office_country'] != self.current_country:
                continue

            # Apply text filter - show only if filter text IS in company name
            if self.current_filter and self.current_filter not in company_info['company_name'].lower():
                continue

            filtered_data.append(company_info)

        # Update tree widget with filtered data
        self._update_treewidget(filtered_data)

    def _update_treewidget(self, filtered_data):
        """Update tree widget with filtered data"""
        self.company_list_treewidget.clear()

        # If no companies match the filter, show a message
        if not filtered_data:
            item = QTreeWidgetItem(self.company_list_treewidget)
            item.setText(0, "No companies match the current filters")
            item.setText(1, "")
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)  # Make it non-selectable
            return

        # Define color thresholds
        COLOR_GREEN = QColor(0, 180, 0)
        COLOR_ORANGE = QColor(255, 140, 0)
        COLOR_RED = QColor(220, 0, 0)
        COLOR_DEFAULT = QColor(0, 0, 0)

        # Sort companies by score in descending order
        filtered_data.sort(key=lambda x: x['score'], reverse=True)

        # Add items to the tree widget
        for company_info in filtered_data:
            score = company_info['score']
            company_name = company_info['company_name']

            item = QTreeWidgetItem(self.company_list_treewidget)
            full_name = f"{company_name} ({score}%)"
            item.setText(0, full_name)
            item.setText(1, f"{score}%")

            # Store the company data
            item.setData(0, Qt.UserRole, company_info['company_name_link'])
            item.setData(1, Qt.UserRole, company_info['comparable_json'])

            # Determine color based on score
            text_color = COLOR_DEFAULT
            if score > 60:
                text_color = COLOR_GREEN
            elif score > 40:
                text_color = COLOR_ORANGE
            elif score > 20:
                text_color = COLOR_RED

            # Apply colors
            item.setForeground(1, QBrush(text_color))
            item.setForeground(0, QBrush(text_color))

        # Resize columns to fit their contents
        for i in range(self.company_list_treewidget.columnCount()):
            self.company_list_treewidget.resizeColumnToContents(i)

    def company_list_treewidget_selection_def(self):
        selected_items = self.company_list_treewidget.selectedItems()
        if selected_items:
            selected_item = selected_items[0]
            company_name_link_data = selected_item.data(0, Qt.UserRole)
            comparable_json = selected_item.data(1, Qt.UserRole)
            self.user_common_right_ui.update_ui(company_name_link_data, comparable_json)

    def update_ui(self):
        """Reload all data (call this when user data changes)"""
        self.load_initial_data()