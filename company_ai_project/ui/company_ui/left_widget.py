from pyqt_common_widget.import_module import *
from pyqt_common_widget import sample_widget_template, color_variable
from functools import partial
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QWidget


# PDF Viewer Widget
class left_widget(QWidget):
    def __init__(self, parent=None, commmon_widget=None, widget_list=[]):
        super().__init__(parent)
        self.sample_widget_template = sample_widget_template.SAMPLE_WIDGET_TEMPLATE()
        self.color_variable = color_variable.COLOR_VARIABLE()
        self.commmon_widget = commmon_widget
        self.widget_list = widget_list
        self.layout = self.sample_widget_template.vertical_layout(parent_self=self)
        self.layout.addWidget(self.main_widget())
        self.setLayout(self.layout)

        val = 300
        self.is_collapsed = False
        # self.setMinimumSize(QSize(val, 0))
        self.setMaximumSize(QSize(val, self.sample_widget_template.max_size))

    def main_widget(self):
        '''
        Main widget container
        '''
        # Initialize collapse state
        self.is_collapsed = False
        self.collapsed_width = 80  # Width when collapsed (enough for smaller buttons)
        self.expanded_width = 300  # Width when expanded

        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget, set_spacing=5)

        self.collapse_button = self.sample_widget_template.pushButton(
            set_text='<<',
            set_object_name='collapse_button_object'
        )
        self.collapse_button.clicked.connect(self.collapse_button_def)
        vertical_layout.addWidget(self.collapse_button)

        self._button_list_widget = self.button_list_widget()
        vertical_layout.addWidget(self._button_list_widget)

        # Set initial size
        self.setMaximumWidth(self.expanded_width)

        return widget

    def button_list_widget(self):
        '''
        Create the button list based on widget_list parameter
        '''
        self.all_button = []
        self.button_full_texts = {}  # Store original button texts with icons

        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget, set_spacing=5)

        # Define button data with icons and text
        button_data = []
        # Add buttons only if they're in the widget_list
        if 'dashboard_common_widget' in self.widget_list:
            button_data.append(
                ("Dashboard", "📊", "dashboard_common_object", self.color_variable.green_color.get_value()))

        if 'company_list_widget' in self.widget_list:
            button_data.append(
                ("Company List", "🏢", "company_list_object", None))

        if 'exibition_list_widget' in self.widget_list:
            button_data.append(("Exhibition List", "🎪", "exibition_object", None))

        if 'manual_list_widget' in self.widget_list:
            button_data.append(("Manual List", "📖", "manual_object", None))

        if 'user_widget' in self.widget_list:
            button_data.append(("USER WIDGET", "👤", "user_widget_object", None))

        if 'all_user_widget' in self.widget_list:
            button_data.append(("All User Button", "👥", "all_user_button_object", None))

        if 'certification_widget' in self.widget_list:
            button_data.append(("Certification", "📜", "certification_widget_object", None))

        if 'auto_widget' in self.widget_list:
            button_data.append(("Auto Run", "⚡", "auto_run_object", None))

        if 'mail_widget' in self.widget_list:
            button_data.append(("Mail Widget", "✉️", "mail_widget_object", None))

        a = 0
        for text, icon, object_name, bg_color in button_data:
            # Create stylesheet if background color is provided
            stylesheet = None
            if bg_color:
                stylesheet = self.sample_widget_template.styleSheet_def(
                    obj_name=object_name,
                    background_color=bg_color,
                    color=self.color_variable.white_color.get_value(),
                    border_radius=1
                )

            # Create button with icon + text
            full_text = f"{icon} {text}"
            button = self.sample_widget_template.pushButton(
                set_text=full_text,
                set_object_name=object_name,
                set_styleSheet=stylesheet
            )

            # Store the original full text
            self.button_full_texts[button] = full_text
            button.setToolTip(text)  # Tooltip for when only icon is shown

            button.clicked.connect(partial(self.right_widget_change, a, button))
            vertical_layout.addWidget(button)
            self.all_button.append(button)
            a += 1

        vertical_layout.addItem(self.sample_widget_template.spaceItem())

        # Make the button list and texts accessible
        widget.all_button = self.all_button
        widget.button_full_texts = self.button_full_texts

        return widget

    def right_widget_change(self, val, button):
        '''
        Change the right widget index in a stacked widget.
        '''
        # Update all buttons
        for each in self.all_button:
            each.setStyleSheet("")  # Clear any inline styles

        # Update the clicked button
        button.setStyleSheet(self.sample_widget_template.styleSheet_def(
            obj_name=button.objectName(),
            background_color=self.color_variable.green_color.get_value(),
            color=self.color_variable.white_color.get_value(),
            border_radius=1
        ))

        # Force stylesheet re-application
        self.refresh_styles()

        try:
            self.commmon_widget.right_widget_class.right_widget_stake_widget.setCurrentIndex(val)
        except AttributeError as e:
            print(f"❌ AttributeError: {e}")
            print("Make sure commmon_widget.right_widget_class exists")
        except IndexError as e:
            print(f"❌ IndexError: Invalid index {val}. Button count: {len(self.all_button)}")
        except Exception as e:
            print(f"❌ Unexpected error while changing widget index: {e}")

    def refresh_styles(self):
        """Refresh widget styles to apply property changes"""
        for widget in self.all_button:
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()

    def collapse_button_def(self):
        '''
        Toggle collapse/expand state
        '''
        if self.is_collapsed:
            self.is_collapsed = False
            # Expand the widget
            self.setMaximumWidth(self.expanded_width)
            self.collapse_button.setText('<<')
            self.resize_buttons(expanded=True)  # Show icons + text
        else:
            self.is_collapsed = True
            # Collapse the widget
            self.setMaximumWidth(self.collapsed_width)
            self.collapse_button.setText('>>')
            self.resize_buttons(expanded=False)  # Show only icons

        # Refresh the layout
        self.updateGeometry()
        if self.parent():
            self.parent().updateGeometry()

    def resize_buttons(self, expanded=True):
        """Resize buttons and change text based on collapse state"""
        if hasattr(self._button_list_widget, 'all_button'):
            for button in self._button_list_widget.all_button:
                if expanded:
                    # Expanded state - show icon + text
                    original_text = self._button_list_widget.button_full_texts.get(button, button.text())
                    button.setText(original_text)
                    button.setFixedSize(QSize())  # Clear fixed size
                    button.setMinimumSize(0, 0)
                    button.setMaximumSize(QSize(16777215, 16777215))
                    # Reset font size
                    font = button.font()
                    font.setPointSize(8)
                    button.setFont(font)
                else:
                    # Collapsed state - show only icon
                    current_text = button.text()
                    # Extract the icon (first character/emoji)
                    if current_text and len(current_text) > 0:
                        # Find the first emoji/icon (usually at the start)
                        icon = current_text.split(' ')[0] if ' ' in current_text else current_text
                        button.setText(icon)
                    button.setFixedSize(60, 40)  # Smaller button size
                    # Increase font size for better icon visibility
                    font = button.font()
                    font.setPointSize(12)
                    button.setFont(font)
