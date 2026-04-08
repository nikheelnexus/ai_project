import json
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QTreeWidgetItem
from company_ai_project.database.company_database import company_name_link, link, overview

from pyqt_common_widget.import_module import *
from pyqt_common_widget import sample_widget_template, color_variable
from pyqt_common_widget import sample_widget_template
from company_ai_project.ui.company_ui.right_widget.company_common_widget import company_common
from company_ai_project.ui.company_ui.right_widget.manual_widget import manual_common
from company_ai_project.database.company_database import company_information, company_name_link

overview_db = overview.OverviewTable()


# PDF Viewer Widget
class company_list_widget(QWidget):
    def __init__(self, parent=None, commmon_widget=None):
        super().__init__(parent)
        self.sample_widget_template = sample_widget_template.SAMPLE_WIDGET_TEMPLATE()
        self.color_variable = color_variable.COLOR_VARIABLE()
        self.commmon_widget = commmon_widget
        self.company_common_class = company_common.company_common(commmon_widget=self.commmon_widget, replace_widget_=True)
        self.manual_common_class = manual_common.manual_widget(commmon_widget=self.commmon_widget,
                                                               widget=self)
        self.company_name_link_db = company_name_link.CompanyNameLink()
        self.company_information_db = company_information.CompanyInformationTable()
        # self.product_range_list = self.company_information_db.get_all_product_ranges()
        self.product_range_list = self.get_list(self.company_information_db.get_all_product_ranges())
        # self.country_list = self.company_information_db.get_all_countries()

        # Add timer for debouncing
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._update_ui_delayed)

        # Initialize cached companies
        self._cached_companies = None
        self._pending_update = False

        self.refresh_cached_companies()

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.main_widget())
        self.setLayout(self.layout)

        # Initial update with small delay to ensure UI is ready
        QTimer.singleShot(100, self.update_ui)

    def get_list(self, list_val):
        '''

        :return:
        '''
        final_list = list(list_val)
        final_list = sorted(final_list)
        final_list.append('All')  # Add empty option
        return final_list

    def refresh_cached_companies(self):
        """Refresh the cached company list from database."""
        try:
            companies = self.company_name_link_db.get_companies_by_date()

            # Ensure we have a list
            if not companies:
                companies = []

            self._cached_companies = []
            for i, company in enumerate(companies):
                if isinstance(company, dict):
                    # Make sure it has the expected structure
                    if 'company_name' not in company:
                        company['company_name'] = str(company.get('unique_name', f'Company_{i}'))
                    self._cached_companies.append(company)
                elif isinstance(company, str):
                    # Convert string to dictionary
                    self._cached_companies.append({'company_name': company, 'website': ''})
                else:
                    self._cached_companies.append({'company_name': str(company), 'website': ''})


        except Exception as e:
            print(f"Error refreshing cached companies: {e}")
            import traceback
            traceback.print_exc()
            self._cached_companies = []

    def main_widget(self):
        '''
        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget)

        label = self.sample_widget_template.label(set_text='COMPANY LIST',
                                                  set_alighment=self.sample_widget_template.center_alignment)
        vertical_layout.addWidget(label)

        vertical_layout.addWidget(self.top_widget())

        staker_widget = QStackedWidget()
        vertical_layout.addWidget(staker_widget)

        splitter = self.sample_widget_template.splitter_def(parent_self=widget,
                                                            set_orientation=self.sample_widget_template.horizonatal)
        staker_widget.addWidget(splitter)

        splitter.addWidget(self.left_widget())
        splitter.addWidget(self.right_widget())

        return widget

    def left_widget(self):
        '''
        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget, set_spacing=5)

        self.filter_combo_box = self.sample_widget_template.comboBox(parent_self=widget, setEditable=True)
        self.filter_combo_box.setInsertPolicy(QComboBox.NoInsert)  # Don't insert into list automatically

        # Set up completer for auto-completion
        completer = QCompleter(self.product_range_list)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.filter_combo_box.setCompleter(completer)

        self.filter_combo_box.addItems(self.product_range_list)
        self.filter_combo_box.lineEdit().returnPressed.connect(self.filter_combo_box_def)

        vertical_layout.addWidget(self.filter_combo_box)

        vertical_layout.addWidget(self.limit_widget())

        self.filter_lineedit = self.sample_widget_template.line_edit(
            set_PlaceholderText='Filter by Company Name or Website')
        self.filter_lineedit.textChanged.connect(self._schedule_update)
        vertical_layout.addWidget(self.filter_lineedit)

        self.company_tree_widget = self.sample_widget_template.treeWidget(setHeaderHidden=True)
        self.company_tree_widget.selectionModel().selectionChanged.connect(self.company_tree_widget_selection_changed)
        vertical_layout.addWidget(self.company_tree_widget)

        return widget

    def right_widget(self):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget)

        tab_widget = QTabWidget()
        vertical_layout.addWidget(tab_widget)
        tab_widget.addTab(self.company_common_class, "Company Details")
        tab_widget.addTab(self.manual_common_class, "Manual Entry")

        return widget

    def limit_widget(self):
        '''
        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        horizontal_layout = self.sample_widget_template.horizontal_layout(parent_self=widget)

        limit_label = self.sample_widget_template.label(set_text='Limit:')
        horizontal_layout.addWidget(limit_label)

        self.limit_lineedit = self.sample_widget_template.line_edit()
        self.limit_lineedit.setText(str(100))
        self.limit_lineedit.setAlignment(Qt.AlignCenter)
        self.limit_lineedit.textChanged.connect(self._schedule_update)
        horizontal_layout.addWidget(self.limit_lineedit)

        return widget

    def _schedule_update(self):
        """Schedule an update with debouncing."""
        if not self._pending_update:
            self._pending_update = True
            self.update_timer.start(300)  # 300ms delay

    def _update_ui_delayed(self):
        """Perform the actual UI update after delay."""
        self._pending_update = False
        self.update_ui()

    def top_widget(self):
        '''
        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget, set_spacing=5)

        vertical_layout.addWidget(self.button_switch_widget())

        return widget

    def filter_combo_box_def(self):
        '''
        :return:
        '''
        current_text = self.filter_combo_box.currentText()

        if current_text == 'All' or not current_text:
            # Show all companies from cache
            self.update_ui(company_list=None)
            return

        # Get company information based on product range
        company_info_list = self.company_information_db.search_company_information_by_text(search_text=current_text)
        company_list = []

        for company_info in company_info_list:
            if isinstance(company_info, dict):
                unique_name = company_info.get('unique_name')
            else:
                # If it's a string, use it as the unique name
                unique_name = str(company_info)

            # Get company details from name link database
            company_data = self.company_name_link_db.get_company(unique_name=unique_name)

            # Handle different return types
            if isinstance(company_data, dict):
                company_list.append(company_data)
            elif isinstance(company_data, str):
                # Convert string to dictionary
                company_list.append({'company_name': company_data, 'website': ''})
            elif company_data is not None:
                # Handle any other type that might be returned
                company_list.append({'company_name': str(company_data), 'website': ''})

        self.update_ui(company_list=company_list)

    def button_switch_widget(self):
        '''
        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        val = 8
        horizontal_layout = self.sample_widget_template.horizontal_layout(parent_self=widget, set_spacing=val)

        product_range_button = self.sample_widget_template.pushButton(set_text='Product Range')
        product_range_button.clicked.connect(self.on_product_range_clicked)
        horizontal_layout.addWidget(product_range_button)

        product_button = self.sample_widget_template.pushButton(set_text='Product')
        product_button.clicked.connect(self.on_product_clicked)
        horizontal_layout.addWidget(product_button)

        industry_button = self.sample_widget_template.pushButton(set_text='Industry')
        industry_button.clicked.connect(self.on_industry_clicked)
        horizontal_layout.addWidget(industry_button)

        # Add refresh button
        refresh_button = self.sample_widget_template.pushButton(set_text='Refresh List')
        refresh_button.clicked.connect(self.on_refresh_clicked)
        horizontal_layout.addWidget(refresh_button)

        # Add clear filter button
        clear_button = self.sample_widget_template.pushButton(set_text='Clear Filter')
        clear_button.clicked.connect(self.on_clear_filter_clicked)
        horizontal_layout.addWidget(clear_button)

        return widget

    def on_product_range_clicked(self):
        '''

        :return:
        '''
        self.filter_combo_box.clear()
        product_list = self.get_list(self.company_information_db.get_all_product_ranges())
        self.filter_combo_box.addItems(product_list)
        self.on_refresh_clicked()

    def on_product_clicked(self):
        '''

        :return:
        '''
        self.filter_combo_box.clear()
        product_list = self.get_list(self.company_information_db.get_all_product_names())
        self.filter_combo_box.addItems(product_list)
        self.on_refresh_clicked()

    def on_industry_clicked(self):
        self.filter_combo_box.clear()
        industry_list = self.get_list(self.company_information_db.get_all_industries())
        print(industry_list)
        self.filter_combo_box.addItems(industry_list)
        self.on_refresh_clicked()

    def on_refresh_clicked(self):
        """Refresh the company list from database."""
        self.refresh_cached_companies()
        self.update_ui()

    def on_clear_filter_clicked(self):
        """Clear all filters and show all companies."""
        self.filter_lineedit.clear()
        self.filter_combo_box.setCurrentText('All')
        self.update_ui()

    def update_ui(self, company_list=None):
        """Update the company tree widget with filtered and limited results.

        Args:
            company_list: Optional list of companies to display. If provided,
                         uses this list instead of cached companies.
        """
        filter_text = self.filter_lineedit.text().strip().lower()

        # Clear the tree widget
        self.company_tree_widget.clear()

        # Get limit with validation
        try:
            limit = int(self.limit_lineedit.text().strip())
            if limit <= 0:
                limit = 100  # Default value if invalid
        except (ValueError, AttributeError):
            limit = 100  # Default value

        # Determine which list to use
        if company_list is not None:
            # Use the provided company list (from filter_combo_box)
            companies_to_filter = company_list
        else:
            # Use cached companies (from database)
            companies_to_filter = self._cached_companies

        # Early return if no companies
        if not companies_to_filter:
            print("No companies to filter!")
            return

        # Filter companies
        filtered_companies = []

        if not filter_text:
            # No filter text - take first N companies from the appropriate source
            # Make sure we don't exceed available companies
            actual_limit = min(limit, len(companies_to_filter))
            filtered_companies = companies_to_filter[:actual_limit]
        else:
            # Filter with the search text
            count = 0
            for company in companies_to_filter:
                if count >= limit:
                    break

                # Safely get company name and website
                company_name = ''
                website = ''

                if isinstance(company, dict):
                    company_name = company.get('company_name', '')
                    website = company.get('website', '')
                elif isinstance(company, str):
                    company_name = company

                # Convert to lowercase for case-insensitive search
                company_name_lower = str(company_name).lower()
                website_lower = str(website).lower()

                # Check if filter text is in either field
                if filter_text in company_name_lower or filter_text in website_lower:
                    filtered_companies.append(company)
                    count += 1

        # Populate tree widget
        if filtered_companies:
            items = []

            for index, company in enumerate(filtered_companies, 1):
                # Safely get company name
                if isinstance(company, dict):
                    company_name = company.get('company_name', '')
                elif isinstance(company, str):
                    company_name = company
                else:
                    company_name = str(company)

                # Clean up the company name
                company_name = str(company_name).strip()

                # Debug: Print raw company name before formatting

                # Simple numbering - ensure no extra formatting
                final_text = f"{index}. {company_name}"

                # Debug the first few items
                unique_name = company['unique_name']
                oveview = overview_db.get_overview(unique_name=unique_name)

                item = QTreeWidgetItem()
                item.setText(0, final_text)
                item.setData(0, Qt.UserRole, company)
                if oveview:
                    # make item green
                    item.setForeground(0, QBrush(QColor(0, 255, 0)))  # Green
                else:
                    # make it red
                    item.setForeground(0, QBrush(QColor(255, 0, 0)))  # Red

                items.append(item)

            # Add all items at once
            self.company_tree_widget.addTopLevelItems(items)
            self.company_tree_widget.expandAll()

            # Check if tree widget has items

            # Verify first item text
        else:
            print("No companies to display after filtering")

    def company_tree_widget_selection_changed(self):
        '''
        :return:
        '''
        selected_items = self.company_tree_widget.selectedItems()
        if selected_items:
            selected_item = selected_items[0]
            company_data = selected_item.data(0, Qt.UserRole)
            self.company_common_class.update_ui(company_data)

            company_name = company_data.get('company_name', '')
            website = company_data.get('website', '')
            self.manual_common_class.update_ui(company_name=company_name,
                                               website=website)
