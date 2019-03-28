import importlib

import dexbot.controllers.strategy_controller

from PyQt5 import QtWidgets, QtCore, QtGui


class StrategyFormWidget(QtWidgets.QWidget):

    def __init__(self, controller, strategy_module, worker_config=None):
        super().__init__()
        self.controller = controller
        self.module_name = strategy_module.split('.')[-1]

        strategy_class = getattr(
            importlib.import_module(strategy_module),
            'Strategy'
        )
        # For strategies uses autogeneration, we need the strategy configs without the defaults
        configure = strategy_class.configure(return_base_config=False)
        form_module = controller.strategies[strategy_module].get('form_module')
        try:
            widget = getattr(
                importlib.import_module(form_module),
                'Ui_Form'
            )
            self.strategy_widget = widget()
            self.strategy_widget.setupUi(self)
        except (ValueError, AttributeError):
            # Generate the strategy form widget automatically
            self.strategy_widget = AutoStrategyFormGenerator(self, configure)

        # Assemble the controller class name
        parts = self.module_name.split('_')
        class_name = ''.join(map(str.capitalize, parts))
        class_name = ''.join([class_name, 'Controller'])

        try:
            # Try to get the controller from the internal set
            strategy_controller = getattr(
                dexbot.controllers.strategy_controller,
                class_name
            )
        except AttributeError:
            try:
                # look in the strategy module itself (external strategies may do this)
                strategy_controller = getattr(
                    importlib.import_module(strategy_module),
                    'StrategyController'
                )
            except AttributeError:
                # The controller doesn't exist, use the default controller
                strategy_controller = getattr(
                    dexbot.controllers.strategy_controller,
                    'StrategyController'
                )

        self.strategy_controller = strategy_controller(self, configure, controller, worker_config)

    @property
    def values(self):
        """ Returns all the form values based on the selected strategy
        """
        return self.strategy_controller.values


class AutoStrategyFormGenerator:
    """ Automatic strategy form UI generator
    """

    def __init__(self, view, configure):
        self.view = view
        self.index = 0
        self.elements = {}

        self.vertical_layout = QtWidgets.QVBoxLayout(view)
        self.vertical_layout.setContentsMargins(0, 0, 0, 0)

        self.group_box = QtWidgets.QGroupBox(view)
        self.group_box.setTitle("Worker Parameters")
        self.vertical_layout.addWidget(self.group_box)
        self.form_layout = QtWidgets.QFormLayout(self.group_box)

        for option in configure:
            self.add_element(option)

    def __getattr__(self, item):
        element = self.view.findChild(QtWidgets.QWidget, item)
        if element is None:
            raise AttributeError
        return element

    def add_element(self, option):
        key = option.key
        element_type = option.type
        title = option.title
        description = option.description
        extra = option.extra

        if element_type == 'float':
            element = self.add_double_spin_box(
                key, title, extra[0], extra[1], extra[2], extra[3], description)
        elif element_type == 'int':
            element = self.add_spin_box(
                key, title, extra[0], extra[1], extra[2], description)
        elif element_type == 'string':
            element = self.add_line_edit(key, title, description)
        elif element_type == 'bool':
            element = self.add_checkbox(key, title, description)
        elif element_type == 'choice':
            element = self.add_combo_box(key, title, description)
        else:
            return

        element_name = ''.join([key, '_input'])
        element.setObjectName(element_name)
        self.elements[key] = element
        self.index += 1

    def _add_label_wrap(self, key):
        wrap = QtWidgets.QWidget(self.group_box)
        wrap.setMinimumSize(QtCore.QSize(120, 0))
        wrap.setMaximumSize(QtCore.QSize(120, 16777215))

        layout = QtWidgets.QHBoxLayout(wrap)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        element_name = ''.join([key, '_wrap'])
        wrap.setObjectName(element_name)
        self.form_layout.setWidget(self.index, QtWidgets.QFormLayout.LabelRole, wrap)
        return wrap

    def _add_tooltip(self, key, tooltip_text, container):
        tooltip = QtWidgets.QLabel(container)
        font = QtGui.QFont()
        font.setBold(True)
        tooltip.setFont(font)
        tooltip.setCursor(QtGui.QCursor(QtCore.Qt.WhatsThisCursor))

        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        tooltip.setSizePolicy(size_policy)

        tooltip.setText('?')
        tooltip.setToolTip(tooltip_text)

        element_name = ''.join([key, '_tooltip'])
        tooltip.setObjectName(element_name)
        layout = container.layout()
        layout.addWidget(tooltip)

    def add_label(self, key, text, description=''):
        wrap = self._add_label_wrap(key)
        label = QtWidgets.QLabel(wrap)
        label.setWordWrap(True)

        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        label.setSizePolicy(size_policy)

        element_name = ''.join([key, '_label'])
        label.setObjectName(element_name)
        layout = wrap.layout()
        layout.addWidget(label)
        label.setText(text)

        if description:
            self._add_tooltip(key, description, wrap)

    def add_double_spin_box(self, key, text, minimum, maximum, precision, suffix='', description=''):
        self.add_label(key, text, description)

        input_field = QtWidgets.QDoubleSpinBox(self.group_box)
        input_field.setDecimals(precision)
        if minimum is not None:
            input_field.setMinimum(minimum)
        if maximum is not None:
            input_field.setMaximum(maximum)
        if suffix:
            input_field.setSuffix(suffix)

        input_field.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        input_field.setSizePolicy(size_policy)
        input_field.setMinimumSize(QtCore.QSize(170, 0))
        input_field.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)

        self.form_layout.setWidget(self.index, QtWidgets.QFormLayout.FieldRole, input_field)
        return input_field

    def add_spin_box(self, key, text, minimum, maximum, suffix='', description=''):
        self.add_label(key, text, description)

        input_field = QtWidgets.QSpinBox(self.group_box)
        if minimum is not None:
            input_field.setMinimum(minimum)
        if maximum is not None:
            input_field.setMaximum(maximum)
        if suffix:
            input_field.setSuffix(suffix)

        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        input_field.setSizePolicy(size_policy)
        input_field.setMinimumSize(QtCore.QSize(170, 0))
        input_field.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)

        self.form_layout.setWidget(self.index, QtWidgets.QFormLayout.FieldRole, input_field)
        return input_field

    def add_line_edit(self, key, text, description=''):
        self.add_label(key, text, description)

        input_field = QtWidgets.QLineEdit(self.group_box)
        self.form_layout.setWidget(self.index, QtWidgets.QFormLayout.FieldRole, input_field)
        return input_field

    def add_checkbox(self, key, text, description=''):
        self.add_label(key, '', description)

        input_field = QtWidgets.QCheckBox(self.group_box)
        input_field.setText(text)

        self.form_layout.setWidget(self.index, QtWidgets.QFormLayout.FieldRole, input_field)
        return input_field

    def add_combo_box(self, key, text, description=''):
        self.add_label(key, text, description)

        input_field = QtWidgets.QComboBox(self.group_box)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        input_field.setSizePolicy(size_policy)
        input_field.setMinimumSize(QtCore.QSize(170, 0))

        self.form_layout.setWidget(self.index, QtWidgets.QFormLayout.FieldRole, input_field)
        return input_field
