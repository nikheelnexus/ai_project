from pyqt_common_widget.import_module import *
from pyqt_common_widget import sample_widget_template, color_variable
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import QProgressDialog, QMessageBox
from PyQt5.QtCore import Qt
from company_ai_project.database.company_database import company_name_link
from company_ai_project.database.company_database import company_information as _company_information


class company_information(QWidget):
    def __init__(self, parent=None, commmon_widget=None):
        super().__init__(parent)
        self.sample_widget_template = sample_widget_template.SAMPLE_WIDGET_TEMPLATE()
        self.color_variable = color_variable.COLOR_VARIABLE()
        self.commmon_widget = commmon_widget
        self.company_db = company_name_link.CompanyNameLink()
        self.company_information_db = _company_information.CompanyInformationTable()

        # Set green theme stylesheet
        self.set_dark_green_theme()
        self.data = {}
        self.layout = self.sample_widget_template.vertical_layout(parent_self=self)
        self.layout.addWidget(self.main_widget())
        self.setLayout(self.layout)
        # Initialize workers as None
        self.automation_worker = None
        self.company_info_worker = None

    def set_dark_green_theme(self):
        """Apply dark theme with green accents"""
        dark_green_theme_stylesheet = """
        QWidget {
            background-color: #1a1a1a;
            color: #ffffff;
            font-family: Arial, sans-serif;
        }

        QLabel {
            color: #ffffff;
            padding: 5px;
        }

        QLabel#business_analysis_label {
            font-size: 18px;
            font-weight: bold;
            color: #000000;
            background-color: #27ae60;
            border-radius: 8px;
            padding: 10px;
            margin: 5px;
            border: 2px solid #2ecc71;
        }

        QPushButton {
            background-color: #27ae60;
            color: #000000;
            border: none;
            padding: 8px 15px;
            border-radius: 6px;
            font-weight: bold;
            margin: 2px;
        }

        QPushButton:hover {
            background-color: #2ecc71;
        }

        QPushButton:pressed {
            background-color: #219653;
        }

        QPushButton#tag_button {
            background-color: #2ecc71;
            color: #000000;
            border: 1px solid #27ae60;
            padding: 6px 12px;
            border-radius: 4px;
            font-weight: normal;
        }

        QPushButton#tag_button:hover {
            background-color: #27ae60;
            color: #ffffff;
        }

        QGroupBox {
            font-weight: bold;
            color: #27ae60;
            border: 2px solid #27ae60;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 15px;
            background-color: #2d2d2d;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 10px;
            background-color: #27ae60;
            color: #000000;
            border-radius: 4px;
            font-weight: bold;
        }

        QScrollArea {
            border: none;
            background-color: transparent;
        }

        QScrollBar:vertical {
            border: none;
            background-color: #2d2d2d;
            width: 12px;
            margin: 0px;
        }

        QScrollBar::handle:vertical {
            background-color: #27ae60;
            border-radius: 6px;
            min-height: 20px;
        }

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }

        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background-color: #2d2d2d;
        }

        QLabel#bold_label {
            font-weight: bold;
            color: #2ecc71;
            font-size: 14px;
        }

        QLabel#normal_label {
            color: #bdc3c7;
            font-size: 12px;
        }
        """
        self.setStyleSheet(dark_green_theme_stylesheet)

    def main_widget(self):
        '''
        Main widget containing all company_widget overview sections
        :return: QWidget containing the main layout
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget, set_spacing=5)

        self.company_stake_widget = QStackedWidget()
        vertical_layout.addWidget(self.company_stake_widget)

        self.company_stake_widget.addWidget(self.company_information_widget())

        return widget

    def company_information_widget(self):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget, set_spacing=5)

        # BUSINESS ANALYSIS
        business_analysis_label = self.sample_widget_template.label(set_text="COMPANY INFORMATION",
                                                                    set_object_name="business_analysis_label",
                                                                    set_alighment=self.sample_widget_template.center_alignment)
        vertical_layout.addWidget(business_analysis_label)

        # Create scroll area for ALL content
        scroll_area = QScrollArea()
        scroll_widget = self.sample_widget_template.widget_def()
        scroll_layout = self.sample_widget_template.vertical_layout(parent_self=scroll_widget,
                                                                    set_spacing=10)  # Increased spacing

        # Add scroll area to main layout
        vertical_layout.addWidget(scroll_area)

        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Product Range Section
        scroll_layout.addWidget(self.product_range_widget())

        # Contact Email Section
        scroll_layout.addWidget(self.contact_email_widget())

        # Product List Section
        scroll_layout.addWidget(self.product_list_widget())

        # City Section
        scroll_layout.addWidget(self.city_widget())

        # Industry Section
        scroll_layout.addWidget(self.industry_widget())

        # Country Section
        scroll_layout.addWidget(self.country_widget())

        # Certifications Section
        scroll_layout.addWidget(self.certifications_widget())

        return widget

    def show_company_info_progress(self, message):
        """Show a non-blocking progress indicator for company info"""
        if not hasattr(self, 'company_info_progress_dialog'):
            self.company_info_progress_dialog = QProgressDialog(message, "Minimize", 0, 0, self)
            self.company_info_progress_dialog.setWindowTitle("Company Information Collection")
            # Non-modal - allows interaction with other windows
            self.company_info_progress_dialog.setWindowModality(Qt.NonModal)
            self.company_info_progress_dialog.setMinimumDuration(0)  # Show immediately
            self.company_info_progress_dialog.show()
            # Position it out of the way
            self.company_info_progress_dialog.move(100, 150)  # Different position than overview progress
        else:
            self.company_info_progress_dialog.setLabelText(message)
            self.company_info_progress_dialog.show()

    def on_company_info_progress(self, message):
        """Update company info progress message"""
        if hasattr(self, 'company_info_progress_dialog'):
            self.company_info_progress_dialog.setLabelText(message)

    def on_company_info_finished(self, success, message):
        """Called when company information collection completes"""
        self.hide_company_info_progress()

        # Clean up worker
        if self.company_info_worker:
            self.company_info_worker.deleteLater()
            self.company_info_worker = None

        # Show result notification
        if success:
            self.show_floating_notification("✅ Company information collected!")
            # Optional: Refresh any company info displays
            QTimer.singleShot(1000, self.refresh_company_info_display)
        else:
            self.show_floating_notification("❌ Company info collection failed!")

        # Optional: Show detailed message
        print(f"Company info collection finished: {message}")

    def hide_company_info_progress(self):
        """Hide the company info progress indicator"""
        if hasattr(self, 'company_info_progress_dialog'):
            self.company_info_progress_dialog.hide()

    def refresh_company_info_display(self):
        """Refresh any company information displays in your UI"""
        # Implement this based on how you display company information
        # For example:
        # self.update_company_info_ui()
        pass

    # Your existing show_floating_notification method (reuse it)
    def show_floating_notification(self, message):
        """Show a temporary notification that doesn't block UI"""
        from PyQt5.QtWidgets import QLabel
        from PyQt5.QtCore import QTimer

        # Create a floating label
        notification = QLabel(message, self)
        notification.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                color: white;
                padding: 10px;
                border: 1px solid #555;
                border-radius: 5px;
                font-size: 12px;
            }
        """)
        notification.adjustSize()

        # Position at bottom right
        parent_rect = self.rect()
        notification.move(parent_rect.right() - notification.width() - 10,
                          parent_rect.bottom() - notification.height() - 10)
        notification.show()

        # Auto-hide after 3 seconds
        QTimer.singleShot(3000, notification.deleteLater)

    def closeEvent(self, event):
        """Ensure all threads are properly cleaned up when widget closes"""
        running_threads = []

        if self.automation_worker and self.automation_worker.isRunning():
            running_threads.append("Overview Generation")
        if self.company_info_worker and self.company_info_worker.isRunning():
            running_threads.append("Company Information Collection")

        if running_threads:
            thread_list = "\n".join(running_threads)
            reply = QMessageBox.question(self, "Background Processes Running",
                                         f"The following processes are still running:\n{thread_list}\n\nDo you want to stop them and close?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                if self.automation_worker and self.automation_worker.isRunning():
                    self.automation_worker.terminate()
                    self.automation_worker.wait()
                if self.company_info_worker and self.company_info_worker.isRunning():
                    self.company_info_worker.terminate()
                    self.company_info_worker.wait()
            else:
                event.ignore()
                return
        event.accept()

    def product_range_widget(self):
        '''
        Create a product range widget with a group box that has only the title in bold
        :return: QWidget containing the product range section
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget, set_spacing=5)

        # Create group box
        grouobox = QGroupBox("Product Range")

        # Use stylesheet to make only the title bold
        grouobox.setStyleSheet("QGroupBox { font-weight: bold; }")
        grouobox.setAlignment(Qt.AlignCenter)

        # Create the inner widget for product range
        product_range_widget = self.sample_widget_template.widget_def()
        self.product_range_horizontal_layout = self.sample_widget_template.horizontal_layout(
            parent_self=product_range_widget)

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidget(product_range_widget)
        scroll_area.setWidgetResizable(True)  # Allow the widget to resize with the scroll area
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Optional: Set fixed dimensions for the scroll area if needed
        # scroll_area.setMinimumHeight(200)
        # scroll_area.setMaximumHeight(400)

        # Add the scroll area to the group box
        grouobox_layout = self.sample_widget_template.vertical_layout(parent_self=grouobox)
        grouobox_layout.addWidget(scroll_area)

        # Add group box to the main layout
        vertical_layout.addWidget(grouobox)

        return widget

    def set_product_range(self, product_range):
        '''
        Set product range data in the widget
        :param product_range: List of product range items
        '''
        # CLEAR LAYOUT
        while self.product_range_horizontal_layout.count():
            child = self.product_range_horizontal_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for each in product_range:
            button = self.sample_widget_template.pushButton(set_text=each,
                                                            set_object_name="tag_button")

            self.product_range_horizontal_layout.addWidget(button)

    def contact_email_widget(self):
        '''
        Create a contact email widget with a group box that has only the title in bold
        :return: QWidget containing the contact email section
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget, set_spacing=5)

        # Create group box
        grouobox = QGroupBox("Contact Email")

        # Use stylesheet to make only the title bold
        grouobox.setStyleSheet("QGroupBox { font-weight: bold; }")
        grouobox.setAlignment(Qt.AlignCenter)

        # Create the inner widget for contact email
        contact_widget = self.sample_widget_template.widget_def()
        self.contact_email_horizontal_layout = self.sample_widget_template.horizontal_layout(
            parent_self=contact_widget)

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidget(contact_widget)
        scroll_area.setWidgetResizable(True)  # Allow the widget to resize with the scroll area
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Optional: Set fixed dimensions for the scroll area if needed
        # scroll_area.setMinimumHeight(150)
        # scroll_area.setMaximumHeight(300)

        # Add the scroll area to the group box
        grouobox_layout = self.sample_widget_template.vertical_layout(parent_self=grouobox)
        grouobox_layout.addWidget(scroll_area)

        # Add group box to the main layout
        vertical_layout.addWidget(grouobox)

        return widget

    def set_contact_email(self, contact_email):
        '''
        Set contact email data in the widget
        :param contact_email: List of contact emails
        '''
        # CLEAR LAYOUT
        while self.contact_email_horizontal_layout.count():
            child = self.contact_email_horizontal_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for each in contact_email:
            button = self.sample_widget_template.pushButton(set_text=each,
                                                            set_object_name="tag_button")
            self.contact_email_horizontal_layout.addWidget(button)

    def product_list_widget(self):
        '''
        Create a product list widget with a group box that has only the title in bold
        :return: QWidget containing the product list section
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget, set_spacing=5)

        # Create group box
        grouobox = QGroupBox("Product List")

        # Use stylesheet to make only the title bold
        grouobox.setStyleSheet("QGroupBox { font-weight: bold; }")
        grouobox.setAlignment(Qt.AlignCenter)

        # Create the inner widget for product list
        product_list_widget = self.sample_widget_template.widget_def()
        self.product_list_grid_layout = self.sample_widget_template.grid_layout(
            parent_self=product_list_widget)

        # Add the inner widget to the group box
        grouobox_layout = self.sample_widget_template.vertical_layout(parent_self=grouobox)
        grouobox_layout.addWidget(product_list_widget)

        # Add group box to the main layout
        vertical_layout.addWidget(grouobox)

        return widget

    def set_product_list(self, product_list):
        '''
        Set product list data in the widget
        :param product_list: List of product dictionaries with name and description
        '''
        # CLEAR LAYOUT
        while self.product_list_grid_layout.count():
            child = self.product_list_grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # MAKE THIS GRID LAYOUT WITH 2 COLUMNS
        row = 0
        col = 0
        for each in product_list:
            widget = self.sample_widget_template.widget_def()
            vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget, set_spacing=2)

            product_name = each.get('name', 'N/A')
            product_description = each.get('description', 'N/A')
            product_name_label = self.sample_widget_template.pushButton(set_text=f"{product_name}",
                                                                        set_object_name="bold_label")

            product_name_label.setToolTip(product_description)
            # MAKE IT BOLD
            font = product_name_label.font()
            font.setBold(True)
            product_name_label.setFont(font)
            vertical_layout.addWidget(product_name_label)

            '''
            product_description_label = self.sample_widget_template.label(set_text=f"{product_description}",
                                                                          set_object_name="normal_label",
                                                                          set_alighment=self.sample_widget_template.center_alignment)
            vertical_layout.addWidget(product_description_label)
            '''
            self.product_list_grid_layout.addWidget(widget, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1

    def city_widget(self):
        '''
        Create a city widget with a group box that has only the title in bold
        :return: QWidget containing the city section
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget, set_spacing=5)

        # Create group box
        grouobox = QGroupBox("City")

        # Use stylesheet to make only the title bold
        grouobox.setStyleSheet("QGroupBox { font-weight: bold; }")
        grouobox.setAlignment(Qt.AlignCenter)

        # Create the inner widget for city
        city_widget = self.sample_widget_template.widget_def()
        self.city_horizontal_layout = self.sample_widget_template.horizontal_layout(
            parent_self=city_widget)

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidget(city_widget)
        scroll_area.setWidgetResizable(True)  # Allow the widget to resize with the scroll area
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Optional: Set fixed dimensions for the scroll area if needed
        # scroll_area.setMinimumHeight(120)
        # scroll_area.setMaximumHeight(250)

        # Add the scroll area to the group box
        grouobox_layout = self.sample_widget_template.vertical_layout(parent_self=grouobox)
        grouobox_layout.addWidget(scroll_area)

        # Add group box to the main layout
        vertical_layout.addWidget(grouobox)

        return widget

    def set_city(self, city):
        '''
        Set city data in the widget
        :param city: List of cities
        '''
        # CLEAR LAYOUT
        while self.city_horizontal_layout.count():
            child = self.city_horizontal_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for each in city:
            button = self.sample_widget_template.pushButton(set_text=each,
                                                            set_object_name="tag_button")
            self.city_horizontal_layout.addWidget(button)

    def industry_widget(self):
        '''
        Create a industry widget with a group box that has only the title in bold
        :return: QWidget containing the industry section
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget, set_spacing=5)

        # Create group box
        grouobox = QGroupBox("Industry")

        # Use stylesheet to make only the title bold
        grouobox.setStyleSheet("QGroupBox { font-weight: bold; }")
        grouobox.setAlignment(Qt.AlignCenter)

        # Create the inner widget for industry
        industry_widget = self.sample_widget_template.widget_def()
        self.industry_horizontal_layout = self.sample_widget_template.horizontal_layout(
            parent_self=industry_widget)

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidget(industry_widget)
        scroll_area.setWidgetResizable(True)  # Allow the widget to resize with the scroll area
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Optional: Set fixed dimensions for the scroll area if needed
        # scroll_area.setMinimumHeight(150)
        # scroll_area.setMaximumHeight(300)

        # Add the scroll area to the group box
        grouobox_layout = self.sample_widget_template.vertical_layout(parent_self=grouobox)
        grouobox_layout.addWidget(scroll_area)

        # Add group box to the main layout
        vertical_layout.addWidget(grouobox)

        return widget

    def set_industry(self, industry):
        '''
        Set industry data in the widget
        :param industry: List of industries
        '''
        # CLEAR LAYOUT
        while self.industry_horizontal_layout.count():
            child = self.industry_horizontal_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for each in industry:
            button = self.sample_widget_template.pushButton(set_text=each,
                                                            set_object_name="tag_button")
            self.industry_horizontal_layout.addWidget(button)

    def country_widget(self):
        '''
        Create a country widget with a group box that has only the title in bold
        :return: QWidget containing the country section
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget, set_spacing=5)

        # Create group box
        grouobox = QGroupBox("Country")

        # Use stylesheet to make only the title bold
        grouobox.setStyleSheet("QGroupBox { font-weight: bold; }")
        grouobox.setAlignment(Qt.AlignCenter)

        # Create the inner widget for country
        country_widget = self.sample_widget_template.widget_def()
        self.country_horizontal_layout = self.sample_widget_template.horizontal_layout(
            parent_self=country_widget)

        # Add the inner widget to the group box
        grouobox_layout = self.sample_widget_template.vertical_layout(parent_self=grouobox)
        grouobox_layout.addWidget(country_widget)

        # Add group box to the main layout
        vertical_layout.addWidget(grouobox)

        return widget

    def set_country(self, country):
        '''
        Set country data in the widget
        :param country: List of countries
        '''
        # CLEAR LAYOUT
        while self.country_horizontal_layout.count():
            child = self.country_horizontal_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for each in country:
            button = self.sample_widget_template.pushButton(set_text=each,
                                                            set_object_name="tag_button")
            self.country_horizontal_layout.addWidget(button)

    def certifications_widget(self):
        '''
        Create a certifications widget with a group box that has only the title in bold
        :return: QWidget containing the certifications section
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget, set_spacing=5)

        # Create group box
        grouobox = QGroupBox("Certifications")

        # Use stylesheet to make only the title bold
        grouobox.setStyleSheet("QGroupBox { font-weight: bold; }")
        grouobox.setAlignment(Qt.AlignCenter)

        # Create the inner widget for certifications
        certifications_widget = self.sample_widget_template.widget_def()
        self.certifications_horizontal_layout = self.sample_widget_template.horizontal_layout(
            parent_self=certifications_widget)

        # Add the inner widget to the group box
        grouobox_layout = self.sample_widget_template.vertical_layout(parent_self=grouobox)
        grouobox_layout.addWidget(certifications_widget)

        # Add group box to the main layout
        vertical_layout.addWidget(grouobox)

        return widget

    def set_certifications(self, certifications):
        '''
        Set certifications data in the widget
        :param certifications: List of certifications
        '''
        # CLEAR LAYOUT
        while self.certifications_horizontal_layout.count():
            child = self.certifications_horizontal_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for each in certifications:
            button = self.sample_widget_template.pushButton(set_text=each,
                                                            set_object_name="tag_button")
            self.certifications_horizontal_layout.addWidget(button)

    def update_information(self, data):
        '''
        Update all company_widget information widgets with new data
        :param company_information_data: Dictionary containing company_widget information
        '''

        self.data = data
        website = self.data.get('website', '') or self.data.get('company_website', '')
        company_data = self.company_db.search_companies(website)

        if not company_data:
            self.company_stake_widget.setCurrentIndex(1)
            return

        unique_name = company_data[0].get('unique_name', '')

        company_information_data = self.company_information_db.get_company_information(unique_name)

        if not company_information_data:
            self.company_stake_widget.setCurrentIndex(1)
            self.set_product_range([])
            self.set_contact_email([])
            self.set_product_list([])
            self.set_city([])
            self.set_industry([])
            self.set_country([])
            self.set_certifications([])

            return
        self.company_stake_widget.setCurrentIndex(0)
        company_information_data = company_information_data.get('company_data', {})
        try:
            if 'product_range' in company_information_data:
                self.set_product_range(company_information_data['product_range'])

            if 'contact_email' in company_information_data:
                self.set_contact_email(company_information_data['contact_email'])

            if 'product_list' in company_information_data:
                self.set_product_list(company_information_data['product_list'])

            if 'city' in company_information_data:
                self.set_city(company_information_data['city'])

            if 'industry' in company_information_data:
                self.set_industry(company_information_data['industry'])

            if 'country' in company_information_data:
                self.set_country(company_information_data['country'])

            if 'certifications' in company_information_data:
                self.set_certifications(company_information_data['certifications'])
        except Exception as e:
            print(f"Error updating company_widget information: {e}")

    def update_ui(self, company_data):
        '''

        :return:
        '''
        information = self.update_information(data=company_data)
