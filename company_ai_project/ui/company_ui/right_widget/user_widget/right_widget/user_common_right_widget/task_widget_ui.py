import json
import re

from pyqt_common_widget.import_module import *
from pyqt_common_widget import sample_widget_template
from company_ai_project.ui.company_ui.right_widget.company_common_widget import company_common


# PDF Viewer Widget
class task_widget(QWidget):
    def __init__(self, task, parent=None, commmon_widget=None, ):
        super().__init__(parent)
        self.commmon_widget = commmon_widget
        self.task = task
        self.sample_widget_template = sample_widget_template.SAMPLE_WIDGET_TEMPLATE()
        self.company_common = company_common.company_common(commmon_widget=self.commmon_widget)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.main_widget())
        self.setLayout(self.layout)

    def main_widget(self):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget)

        vertical_layout.addWidget(self.task_name_button_widget(self.task))

        tab_widget = QTabWidget()
        vertical_layout.addWidget(tab_widget)

        for each_task in self.task:
            task_name = each_task.get('task_name')
            task_widget = self.task_common_widget(each_task)
            tab_widget.addTab(task_widget, task_name)

        return widget

    def task_name_button_widget(self, tasks_list):
        """
        Create buttons for multiple tasks with color coding based on status

        :param tasks_list: List of task data dictionaries
        :return: Widget containing colored buttons for all tasks
        """
        widget = self.sample_widget_template.widget_def()
        horizontal_layout = self.sample_widget_template.horizontal_layout(parent_self=widget, set_spacing=5)

        # Define colors based on status
        status_colors = {
            'pending': '#ff4444',  # Red
            'in_progress': '#ffaa00',  # Orange/Amber
            'completed': '#44ff44',  # Green
            'blocked': '#ff8800',  # Dark Orange
            'review': '#4444ff',  # Blue
            'cancelled': '#888888'  # Gray
        }

        # Create a button for each task
        for task in tasks_list:
            task_name = task.get('task_name', 'Unnamed Task')
            status = task.get('status', 'pending').lower()

            # Get color for current task status
            button_color = status_colors.get(status, '#888888')

            # Create button with styling
            button = self.sample_widget_template.pushButton(set_text=task_name)

            # Apply color styling to the button
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {button_color};
                    color: white;
                    border: 2px solid {button_color};
                    border-radius: 5px;
                    padding: 8px 15px;
                    font-weight: bold;
                    min-width: 100px;
                }}
                QPushButton:hover {{
                    background-color: white;
                    color: {button_color};
                    border: 2px solid {button_color};
                }}
                QPushButton:pressed {{
                    background-color: {button_color};
                    color: white;
                    opacity: 0.8;
                }}
            """)

            # Set tooltip with status
            status_display = status.replace('_', ' ').title()
            button.setToolTip(f"Status: {status_display}")

            # Optionally connect button click to a function
            # button.clicked.connect(lambda checked, t=task: self.task_button_clicked(t))

            horizontal_layout.addWidget(button)

        return widget


    def task_common_widget(self, task):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget)

        splitter = self.sample_widget_template.splitter_def(parent_self=widget,
                                                            set_orientation=self.sample_widget_template.horizonatal)
        vertical_layout.addWidget(splitter)

        tab_widget = QTabWidget()
        splitter.addWidget(tab_widget)

        tab_widget.addTab(self._task_common_widget(task), "Task Common")
        tab_widget.addTab(self.data_widget(), "Data")

        splitter.addWidget(self.chat_widget())

        return widget

    def _task_common_widget(self, task):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget)

        vertical_layout.addWidget(self.task_name_owner_widget(task))
        if task.get('depends_on'):
            vertical_layout.addWidget(self.depend_widget(task))

        vertical_layout.addWidget(self.due_date_widget(task))
        vertical_layout.addWidget(self.description_widget(task))
        vertical_layout.addWidget(self.deliverable_widget(task))
        vertical_layout.addWidget(self.success_criteria_widget(task))

        vertical_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        return widget

    def data_widget(self):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget)

        return widget

    def task_name_owner_widget(self, task):
        widget = self.sample_widget_template.widget_def()
        horizontal_layout = self.sample_widget_template.horizontal_layout(parent_self=widget)

        task_name = self.sample_widget_template.label(set_text=task.get('task_name'))
        horizontal_layout.addWidget(task_name)

        owner_name = self.sample_widget_template.label(set_text=task.get('owner'))
        horizontal_layout.addWidget(owner_name)

        return widget

    def depend_widget(self, task):
        '''

        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        horizontal_layout = self.sample_widget_template.horizontal_layout(parent_self=widget)

        dpeend_labe = self.sample_widget_template.label(set_text='Depend Task')
        horizontal_layout.addWidget(dpeend_labe)

        depend_widget = self.sample_widget_template.widget_def()
        depend_horizontal_layout = self.sample_widget_template.horizontal_layout(parent_self=depend_widget)
        for each in task.get('depends_on'):
            button = self.sample_widget_template.pushButton(set_text=each)
            depend_horizontal_layout.addWidget(button)
        horizontal_layout.addWidget(depend_widget)

        return widget

    def due_date_widget(self, task):
        '''

        :param task:
        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        horizontal_layout = self.sample_widget_template.horizontal_layout(parent_self=widget)

        label = self.sample_widget_template.label(set_text='Due Date')
        horizontal_layout.addWidget(label)

        due_date = self.sample_widget_template.label(set_text=str(task.get('due_by_day')))
        horizontal_layout.addWidget(due_date)

        return widget

    def description_widget(self, task):
        '''

        :param task:
        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        horizontal_layout = self.sample_widget_template.horizontal_layout(parent_self=widget)

        label = self.sample_widget_template.label(set_text='description')
        horizontal_layout.addWidget(label)

        text_edit = QTextEdit()
        text_edit.setText(task.get('description'))
        horizontal_layout.addWidget(text_edit)

        return widget

    def deliverable_widget(self, task):
        '''

        :param task:
        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        horizontal_layout = self.sample_widget_template.horizontal_layout(parent_self=widget)

        label = self.sample_widget_template.label(set_text='Delivery')
        horizontal_layout.addWidget(label)

        text_edit = QTextEdit()
        text_edit.setText(task.get('deliverable'))
        horizontal_layout.addWidget(text_edit)


        return widget

    def success_criteria_widget(self, task):
        '''

        :param task:
        :return:
        '''
        widget = self.sample_widget_template.widget_def()
        horizontal_layout = self.sample_widget_template.horizontal_layout(parent_self=widget)

        label = self.sample_widget_template.label(set_text='Success Criteria')
        horizontal_layout.addWidget(label)

        text_edit = QTextEdit()
        text_edit.setText(task.get('success_criteria'))
        horizontal_layout.addWidget(text_edit)

        return widget

    def chat_widget(self):
        widget = self.sample_widget_template.widget_def()
        vertical_layout = self.sample_widget_template.vertical_layout(parent_self=widget)

        chat_label = self.sample_widget_template.label(set_text='Chat Widget')
        vertical_layout.addWidget(chat_label)

        return widget
