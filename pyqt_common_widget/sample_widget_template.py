
from pyqt_common_widget.import_module import *
from pyqt_common_widget import styleSheet, commomProperty
try:
    from importlib import reload
except:
    pass

for each in [styleSheet, commomProperty]:
    reload(each)

class SAMPLE_WIDGET_TEMPLATE():

    def __init__(self):
        self.styleSheet_class = styleSheet.STYLESHEET()
        self.commomProperty = commomProperty.CommonProperty()
        self.max_size = 16777215
        self.vertical = 'vertical'
        self.horizonatal = 'horizonatal'
        self.validator = QDoubleValidator()

        self.lineedit_type_float = 'float'
        self.lineedit_type_string = 'string'
        self.lineedit_type_int = 'int'

        self.left_alignment = 'left'
        self.right_alignment = 'right'
        self.center_alignment = 'center'
        self.justify_alignment = 'justify'

        self.message_information = QMessageBox.information
        self.message_question = QMessageBox.question
        self.message_warning = QMessageBox.warning
        self.message_critical = QMessageBox.critical


    def widget_def(self, parent_self= '', set_object_name='', min_size=[0, 0], max_size=[16777215, 16777215], set_styleSheet='''''',
                   x=0, y=0, width=120, height=80):
        '''

        :param parent_self:
        :param set_object_name:
        :param min_size:
        :param max_size:
        :param set_styleSheet:
        :param x:
        :param y:
        :param width:
        :param height:
        :return:
        '''
        if parent_self == '':
            widget = QWidget()
        else:
            widget = QWidget(parent_self)

        widget.setObjectName(set_object_name)
        widget.setMinimumSize(QSize(min_size[0], min_size[1]))
        widget.setMaximumSize(QSize(max_size[0], max_size[1]))
        widget.setStyleSheet(set_styleSheet)
        widget.setGeometry(QRect(x, y, width, height))
        return widget

    def dock_widget_def(self, parent_self, set_object_name, window_title='', set_styleSheet=''''''):
        '''

        :param parent_self:
        :param set_object_name:
        :param window_title:
        :param set_styleSheet:
        :return:
        '''
        dock_widget = QDockWidget(parent_self)

        dock_widget.setObjectName(set_object_name)
        dock_widget.setWindowTitle(window_title)
        dock_widget.setStyleSheet(set_styleSheet)
        return dock_widget

    def splitter_def(self, parent_self, set_orientation='vertical', set_object_name='', set_handle_width=2,
                     set_styleSheet='''''', min_size=[0, 0], max_size=[16777215, 16777215]):
        '''

        :param parent_self:
        :param set_orientation:
        :param set_object_name:
        :param set_handle_width:
        :param set_styleSheet:
        :param min_size:
        :param max_size:
        :return:
        '''
        splitter = QSplitter(parent_self)
        if set_orientation == self.vertical:
            splitter.setOrientation(Qt.Vertical)
        else:
            splitter.setOrientation(Qt.Horizontal)

        splitter.setObjectName(set_object_name)
        splitter.setHandleWidth(set_handle_width)
        splitter.setStyleSheet(set_styleSheet)
        splitter.setMinimumSize(QSize(min_size[0], min_size[1]))
        splitter.setMaximumSize(QSize(max_size[0], max_size[1]))
        return splitter

    def vertical_layout(self, parent_self, set_contents_margins=[0, 0, 0, 0], set_spacing=0, set_object_name=''):
        '''

        :param parent_self:
        :param set_contents_margins:
        :param set_spacing:
        :param set_object_name:
        :return:
        '''
        vertical_layout = QVBoxLayout(parent_self)
        vertical_layout.setContentsMargins(QMargins(set_contents_margins[0], set_contents_margins[1], set_contents_margins[2], set_contents_margins[3]))
        vertical_layout.setSpacing(set_spacing)
        vertical_layout.setObjectName(set_object_name)
        return vertical_layout

    def horizontal_layout(self, parent_self, set_contents_margins=[0, 0, 0, 0], set_spacing=0, set_object_name=''):
        '''

        :param parent_self:
        :param set_contents_margins:
        :param set_spacing:
        :param set_object_name:
        :return:
        '''
        horizontal_layout = QHBoxLayout(parent_self)
        horizontal_layout.setContentsMargins(QMargins(set_contents_margins[0], set_contents_margins[1], set_contents_margins[2], set_contents_margins[3]))
        horizontal_layout.setSpacing(set_spacing)
        horizontal_layout.setObjectName(set_object_name)
        return horizontal_layout

    def grid_layout(self, parent_self='', set_contents_margins=[0, 0, 0, 0], set_horizontal_space=0,
                    set_vertical_space=0, set_object_name='', set_spacing=0):
        '''

        :param parent_self:
        :param set_contents_margins:
        :param set_horizontal_space:
        :param set_vertical_space:
        :param set_object_name:
        :param set_spacing:
        :return:
        '''
        if parent_self == '':
            grid_layout = QGridLayout()
        else:
            grid_layout = QGridLayout(parent_self)

        grid_layout.setContentsMargins(QMargins(set_contents_margins[0], set_contents_margins[1], set_contents_margins[2], set_contents_margins[3]))
        grid_layout.setHorizontalSpacing(set_horizontal_space)
        grid_layout.setVerticalSpacing(set_vertical_space)
        grid_layout.setObjectName(set_object_name)
        grid_layout.setSpacing(set_spacing)
        return grid_layout

    def label(self, set_alighment='left', set_object_name='', set_text='', set_tool_tip='', set_status='',
              set_styleSheet='''''', min_size=[0, 0], max_size=[16777215, 16777215]):
        '''

        :param set_alighment:
        :param set_object_name:
        :param set_text:
        :param set_tool_tip:
        :param set_status:
        :param set_styleSheet:
        :param min_size:
        :param max_size:
        :return:
        '''
        label = QLabel()
        if set_alighment == self.left_alignment:
            label.setAlignment(Qt.AlignLeft)
        elif set_alighment == self.right_alignment:
            label.setAlignment(Qt.AlignRight)
        elif set_alighment == self.center_alignment:
            label.setAlignment(Qt.AlignCenter)
        elif set_alighment == self.justify_alignment:
            label.setAlignment(Qt.AlignJustify)
        else:
            label.setAlignment(Qt.AlignLeft)

        label.setObjectName(set_object_name)
        label.setText(set_text)
        label.setToolTip(set_tool_tip)
        label.setStatusTip(set_status)
        label.setStyleSheet(set_styleSheet)
        label.setMinimumSize(QSize(min_size[0], min_size[1]))
        label.setMaximumSize(QSize(max_size[0], max_size[1]))
        return label

    def pushButton(self, parent_self='', min_size=[0, 0], max_size=[16777215, 16777215], set_text='',
                   set_object_name='',
                   set_tool_tip='', set_status='', set_icon='', set_icon_size=[0, 0],
                   set_styleSheet='''''', setCheckable=False, setChecked=False, setAutoRepeat=False,
                   setAutoExclusive=False, setAutoRepeatDelay=300, setAutoRepeatInterval=100,
                   connect=''):
        '''

        :param parent_self:
        :param min_size:
        :param max_size:
        :param set_text:
        :param set_object_name:
        :param set_tool_tip:
        :param set_status:
        :param set_icon:
        :param set_icon_size:
        :param set_styleSheet:
        :param setCheckable:
        :param setChecked:
        :param setAutoRepeat:
        :param setAutoExclusive:
        :param setAutoRepeatDelay:
        :param setAutoRepeatInterval:
        :param connect:
        :return:
        '''
        if parent_self == '':
            pushButton = QPushButton()
        else:
            pushButton = QPushButton(parent_self)

        pushButton.setMinimumSize(QSize(min_size[0], min_size[1]))
        pushButton.setMaximumSize(QSize(max_size[0], max_size[1]))
        pushButton.setText(set_text)
        pushButton.setObjectName(set_object_name)
        pushButton.setToolTip(set_tool_tip)
        pushButton.setStatusTip(set_status)
        pushButton.setIcon(QIcon(set_icon))
        pushButton.setIconSize(QSize(set_icon_size[0], set_icon_size[1]))
        pushButton.setStyleSheet(set_styleSheet)
        pushButton.setCheckable(setCheckable)
        pushButton.setChecked(setChecked)
        pushButton.setAutoRepeat(setAutoRepeat)
        pushButton.setAutoExclusive(setAutoExclusive)
        pushButton.setAutoRepeatDelay(setAutoRepeatDelay)
        pushButton.setAutoRepeatInterval(setAutoRepeatInterval)
        if connect != '':
            pushButton.clicked.connect(connect)
        return pushButton

    def line_edit(self, parent_self='', set_object_name='', set_text='', set_styleSheet='''''', set_PlaceholderText='',
                  type='', text_changed=''):
        '''

        :param parent_self:
        :param set_object_name:
        :param set_text:
        :param set_styleSheet:
        :param set_PlaceholderText:
        :param type:
        :return:
        '''
        if parent_self == '':
            line_edit = QLineEdit()
        else:
            line_edit = QLineEdit(parent_self)

        line_edit.setObjectName(set_object_name)
        line_edit.setText(set_text)
        line_edit.setStyleSheet(set_styleSheet)
        line_edit.setPlaceholderText(set_PlaceholderText)
        if type == self.lineedit_type_int:
            line_edit.setValidator(QIntValidator())
        elif type == self.lineedit_type_float:
            line_edit.setValidator(QDoubleValidator())
        elif type == self.lineedit_type_string:
            line_edit.setValidator(QRegExpValidator())

        if text_changed != '':
            line_edit.textChanged.connect(text_changed)


        return line_edit

    def checkbox(self, set_text='', set_object_name='', set_tool_tip='', set_status='', set_checked=False,
                 stateChanged='', set_styleSheet=''''''):
        '''

        :param set_text:
        :param set_object_name:
        :param set_tool_tip:
        :param set_status:
        :param set_checked:
        :param stateChanged:
        :param set_styleSheet:
        :return:
        '''
        checkbox = QCheckBox()
        checkbox.setText(set_text)
        checkbox.setObjectName(set_object_name)
        checkbox.setToolTip(set_tool_tip)
        checkbox.setStatusTip(set_status)
        checkbox.setChecked(set_checked)
        checkbox.setStyleSheet(set_styleSheet)
        if stateChanged != '':
            checkbox.stateChanged.connect(stateChanged)
        return checkbox

    def set_object_name(self, obj_name, set_object_name='', else_name=''):
        '''

        :param obj_name:
        :param set_object_name:
        :param else_name:
        :return:
        '''
        if set_object_name != '':
            obj_name.setObjectName(else_name)
        else:
            obj_name.setObjectName(set_object_name)

    def tab_widget(self, parent_self, set_layout_direction='left', set_object_name='', set_styleSheet=''''''):
        '''

        :param parent_self:
        :param set_layout_direction:
        :param set_object_name:
        :param set_styleSheet:
        :return:
        '''
        tab_widget = QTabWidget(parent_self)
        if set_layout_direction == 'left':
            tab_widget.setLayoutDirection(Qt.LeftToRight)
        elif set_layout_direction == 'right':
            tab_widget.setLayoutDirection(Qt.RightToLeft)
        elif set_layout_direction == 'top':
            tab_widget.setLayoutDirection(Qt.TopToBottom)
        elif set_layout_direction == 'bottom':
            tab_widget.setLayoutDirection(Qt.BottomToTop)
        else:
            tab_widget.setLayoutDirection(Qt.LeftToRight)

        tab_widget.setObjectName(set_object_name)
        tab_widget.setStyleSheet(set_styleSheet)
        return tab_widget

    def scrollArea(self, parent_self, set_obj_name='', set_widget_resizable=True, set_styleSheet=''''''):
        '''

        :param parent_self:
        :param set_obj_name:
        :param set_widget_resizable:
        :param set_styleSheet:
        :return:
        '''
        scrollArea = QScrollArea(parent_self)
        scrollArea.setWidgetResizable(set_widget_resizable)
        scrollArea.setObjectName(set_obj_name)
        scrollArea.setStyleSheet(set_styleSheet)
        return scrollArea

    def list_widget(self, parent_self, set_obj_name='', set_styleSheet='''''', set_header_hidden=True, set_grid_size=0):
        '''

        :param parent_self:
        :param set_obj_name:
        :param set_styleSheet:
        :return:
        '''
        list_widget = QListWidget(parent_self)
        list_widget.setObjectName(set_obj_name)
        list_widget.setStyleSheet(set_styleSheet)
        list_widget.setGridSize(QSize(set_grid_size, set_grid_size))
        list_widget.setHeaderHidden(set_header_hidden)

        return list_widget

    def treeWidget(self, parent_self='', setHeaderHidden=False):
        '''

        :param parent_self:
        :param setHeaderHidden:
        :return:
        '''
        if parent_self == '':
            treeWidget = QTreeWidget()
        else:
            treeWidget = QTreeWidget(parent_self)
        treeWidget.setHeaderHidden(setHeaderHidden)
        return treeWidget

    def styleSheet_def(self, obj_name, color=[], background_color=[],
                       border_pix=0, border_type='Solid',
                       padding=0, padding_top=0, padding_bottom=0,
                       selection_background_color=[],
                       selection_color=[], spacing=0,
                       width=0, height=0, margin_top=0,
                       margin_bottom=0, image='',
                       margin_left=0, margin_right=0,
                       background=[], opacity=0,
                       outline=None, font_weight='',
                       border_radius=0, subcontrol_origin='',
                       subcntrol_position=[], left=0,
                       padding_left=0, padding_right=0,
                       margin=0,
                       alternate_background_color=[], border_color=[],
                       min_width=0, max_width=0,
                       border_left=[],
                       border_top_color=[],
                       border_right_color=[], border_bottom_color=[],
                       border_left_color=[], gridline_color=[],
                       font_size=0,
                       border=[5, 'solid', [0, 255, 127]],
                       extra='',
                       hover=False,
                       hover_background_color=[],
                       hover_color=[]):

        '''
                Specify the StyhleSheet

                @param obj_name : specify the object name in string
                @type obj_name: str

                @param color : specify the color in list
                @type color: list or str

                @param background_color : specify the baclkground color in list
                @type background_color: list or str

                @param alternate_background_color : specify the alternate background color
                @type alternate_background_color: list or str

                @param border_color : specify the border color in list
                @type border_color: list or str

                @param border_top_color : specify the border top color in list
                @type border_top_color: list or str

                @param border_right_color : specify the border right color in list
                @type border_right_color: list or str

                @param border_bottom_color : specify the border bottom color in list
                @type border_bottom_color: list or str

                @param border_left_color : specify the boirder left color in list
                @type border_left_color: list or str

                @param gridline_color : specify the gridline color in list
                @type gridline_color: list or str

                @param selection_background_color : specify the selection background color in list
                @type selection_background_color: list or str

                @param selection_color : specify the selection color in list
                @type selection_color: list or str

                @param font_size : specify font size
                @type font_size: int or float

                @param font_weight : specify the font weight
                @type font_weight: str
                '''

        if obj_name[0] != '#':
            obj_name = '#' + obj_name

            # SPECIFY THE START OF THE COLOR
        string_val = ''.join([obj_name, '{\n'])
        space = '    '
        # ADD COLOR IF  SPECIFIED
        if color:
            string_val = ''.join([string_val, space, self.styleSheet_class.set_color(color)])

        # ADD BACKGROUND COLOR IF  SPECIFIED
        if background_color:
            string_val = ''.join([string_val, space, self.styleSheet_class.set_background_color(background_color)])

        if extra != '':
            string_val = ''.join([string_val, space, extra])

        # ADD BORDER IF  SPECIFIED
        if border:
            string_val = ''.join([string_val, space, self.styleSheet_class.set_border(border)])

            # ADD BORDER
            if border_pix != 0:
                string_val = ''.join([string_val, space,
                                      self.styleSheet_class.set_border(pix=border_pix, type=border_type,
                                                                       color=border_color)])

            if padding != 0:
                string_val = ''.join([string_val, space, self.styleSheet_class.set_padding(padding_val=padding)])

            if padding_top != 0:
                string_val = ''.join([string_val, space, self.styleSheet_class.set_padding_top(value=padding_top)])

            if padding_bottom != 0:
                string_val = ''.join(
                    [string_val, space, self.styleSheet_class.set_padding_bottom(value=padding_bottom)])

            if padding_left != 0:
                string_val = ''.join([string_val, space, self.styleSheet_class.set_padding_left(value=padding_left)])

            if padding_right != 0:
                string_val = ''.join([string_val, space, self.styleSheet_class.set_padding_right(value=padding_right)])

            if selection_background_color:
                string_val = ''.join([string_val, space, self.styleSheet_class.set_selection_background_color(
                    color=selection_background_color)])

            if selection_color:
                string_val = ''.join(
                    [string_val, space, self.styleSheet_class.set_selection_color(color=selection_color)])

            if spacing != 0:
                string_val = ''.join([string_val, space, self.styleSheet_class.set_spacing(spacing)])

            if width != 0:
                string_val = ''.join([string_val, space, self.styleSheet_class.set_width(value=width)])

            if height != 0:
                string_val = ''.join([string_val, space, self.styleSheet_class.set_height(value=height)])

            if margin != 0:
                string_val = ''.join([string_val, space, self.styleSheet_class.set_margin(value=margin)])

            if margin_top != 0:
                string_val = ''.join([string_val, space, self.styleSheet_class.set_margine_top(value=margin_top)])

            if margin_bottom != 0:
                string_val = ''.join([string_val, space, self.styleSheet_class.set_margine_bottom(value=margin_bottom)])

            if image != '':
                string_val = ''.join([string_val, space, self.styleSheet_class.set_image(value=image)])

            if margin_left != 0:
                string_val = ''.join([string_val, space, self.styleSheet_class.set_margin_left(value=margin_left)])

            if margin_right != 0:
                string_val = ''.join([string_val, space, self.styleSheet_class.set_margin_right(value=margin_right)])

            if background != []:
                string_val = ''.join([string_val, space, self.styleSheet_class.set_background(value=background)])

            if opacity != 0:
                string_val = ''.join([string_val, space, self.styleSheet_class.set_opacity(value=opacity)])

            if outline != None:
                string_val = ''.join([string_val, space, self.styleSheet_class.set_outline(value=outline)])

            if font_weight != '':
                string_val = ''.join([string_val, space, self.styleSheet_class.set_font_weight(value=font_weight)])

            if border_radius != 0:
                string_val = ''.join([string_val, space, self.styleSheet_class.set_border_radius(value=border_radius)])

            if subcontrol_origin != '':
                string_val = ''.join(
                    [string_val, space, self.styleSheet_class.set_subcontrol_origin(value=subcontrol_origin)])

            if subcntrol_position != []:
                if len(subcntrol_position) == 2:
                    if type(subcntrol_position[0]) is str and type(subcntrol_position[1]) is str:
                        string_val = ''.join([string_val, space, self.styleSheet_class.set_subcontrol_poistion(
                            pos_one=subcntrol_position[0], pos_two=subcntrol_position[1])])

            if left != 0:
                string_val = ''.join([string_val, space, self.styleSheet_class.set_left(value=left)])

            if alternate_background_color != []:
                string_val = ''.join([string_val, space, self.styleSheet_class.set_alternate_background_color(
                    color=alternate_background_color)])

            if min_width != 0:
                string_val = ''.join([string_val, space, self.styleSheet_class.set_min_width(value=min_width)])

            if max_width != 0:
                string_val = ''.join([string_val, space, self.styleSheet_class.set_max_width(value=max_width)])

            if border_left != []:
                string_val = ''.join([string_val, space,
                                      self.styleSheet_class.set_border_left(pix=border_left[0], type=border_left[1],
                                                                            color=border_left[2])])

            '''
                    if background_color:
                string_val = ''.join([string_val, space, self.styleSheet_class.set_background_color(background_color)])

            '''
            string_val = string_val + '}'

            if hover == True:
                string_val = self.hover(string_val=string_val, obj_name=obj_name, space=space,
                                        hover_background_color=hover_background_color,
                                        color=color)

            return string_val

    def hover(self, string_val, obj_name, space, hover_background_color=[], color=[]):
        '''

        :param string_val:
        :param obj_name:
        :param space:
        :param hover_background_color:
        :param color:
        :return:
        '''
        string_val = ''.join([string_val, ''.join(['\n', obj_name, ':']), 'hover{', '\n'])

        string_val = ''.join([string_val, space, self.styleSheet_class.set_background_color(hover_background_color)])

        string_val = ''.join([string_val, space, self.styleSheet_class.set_color(color)])

        string_val = string_val + '}'

        return string_val

    def action(self, parent_self, name='', setStatusTip='', setToolTip=''):
        '''
        CREATE ACTION AND RETURN
        @param parent_self: PARENT OBJECT
        @param name: NAME OF THE ACTION
        @return:
        '''
        # ACTION NAME

        action_name = QAction(name, parent_self)

        # SET STATUS TIP
        action_name.setStatusTip(setStatusTip)

        # SET TOOL TIP
        action_name.setToolTip(setToolTip)

        return action_name

    def comboBox(self, parent_self='', addItems=[], setEditable=False, currentIndexChanged='', set_object_name='',
                 set_styleSheet=''''''):
        '''

        :param parent_self:
        :param addItems:
        :param setEditable:
        :param currentIndexChanged:
        :param set_object_name:
        :param set_styleSheet:
        :return:
        '''
        # CREATE COMBO BOX
        if parent_self != '':
            combo_box = QComboBox()
        else:
            combo_box = QComboBox(parent_self)

        combo_box.setObjectName(set_object_name)
        combo_box.setStyleSheet(set_styleSheet)
        combo_box.setEditable(setEditable)
        combo_box.addItems(addItems)
        #combo_box.currentIndexChanged.connect(currentIndexChanged)
        return combo_box

    def tableWidget(self):
        '''

        :return:
        '''
        tableWidget = QTableWidget()

        return tableWidget

    def spaceItem(self):
        '''

        :return:
        '''
        spacerItem = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        return spacerItem

    def plainTextEdit(self):
        '''

        :return:
        '''

        plainTextEdit = QPlainTextEdit()

        return plainTextEdit

    def setObjectName(self, text=''):
        '''

        :param text:
        :return:
        '''
        text = text.replace(' ', '_')

        obj_name = text + '_Object'

        return obj_name

    def displayMessage(self, text='', setInformativeText='', setWindowTitle='Sample', setDetailedText='', message='',
                       set_styleSheet='''''', set_object_name=''):
        '''

        :param text:
        :param setInformativeText:
        :param setWindowTitle:
        :param setDetailedText:
        :param message:
        :param set_styleSheet:
        :param set_object_name:
        :return:
        '''
        msg = QMessageBox()
        if message != '':
            msg.setIcon(message)
        else:
            msg.setIcon(QMessageBox.Information)
        msg.setText(text)
        msg.setObjectName(set_object_name)
        msg.setInformativeText(setInformativeText)
        msg.setWindowTitle(setWindowTitle)
        msg.setDetailedText(setDetailedText)
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        msg.setFixedHeight(1000)
        msg.setFixedWidth(1000)
        msg.setStyleSheet(set_styleSheet)

        return msg

    def removeObject(self, layout_name):
        if layout_name is not None:
            while layout_name.count():
                item = layout_name.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.removeObject(item.layout())








































