import collections

from dexbot.views.errors import gui_error

from PyQt5 import QtWidgets


class StrategyController:
    """ Parent controller for strategies that don't have a custom controller
    """

    def __init__(self, view, configure, worker_controller, worker_data):
        self.view = view
        self.configure = configure
        self.worker_controller = worker_controller

        self.set_values(configure, worker_data)

    def validation_errors(self):
        return []

    def set_values(self, configure, worker_config):
        for option in configure:
            if worker_config and worker_config.get(option.key) is not None:
                value = worker_config[option.key]
            else:
                value = option.default

            element = self.elements.get(option.key)

            if element is None:
                continue

            if option.type in ('int', 'float', 'string'):
                element.setValue(value)
            if option.type == 'bool':
                if value:
                    element.setChecked(True)
                else:
                    element.setChecked(False)
            if option.type == 'choice':
                # Fill the combobox
                for tag, label in option.extra:
                    element.addItem(label, tag)
                # Set the value
                index = element.findData(value)
                element.setCurrentIndex(index)

    @property
    def values(self):
        data = {}
        for key, element in self.elements.items():
            class_name = element.__class__.__name__
            if class_name in ('QDoubleSpinBox', 'QSpinBox', 'QLineEdit', 'QSlider'):
                data[key] = element.value()
            elif class_name == 'QCheckBox':
                data[key] = element.isChecked()
            elif class_name == 'QComboBox':
                data[key] = element.currentData()
        return data

    @property
    def elements(self):
        """ Use ConfigElements of the strategy to find the input elements
        """
        elements = {}
        types = (
            QtWidgets.QDoubleSpinBox,
            QtWidgets.QSpinBox,
            QtWidgets.QLineEdit,
            QtWidgets.QCheckBox,
            QtWidgets.QComboBox,
            QtWidgets.QSlider
        )

        for option in self.configure:
            element_name = ''.join([option.key, '_input'])
            element = self.view.findChild(types, element_name)
            if element is not None:
                elements[option.key] = element
        return elements


class RelativeOrdersController(StrategyController):

    def __init__(self, view, configure, worker_controller, worker_data):
        # Check if there is worker data. This prevents error when multiplying None type when creating worker.
        if worker_data:
            # QSlider uses (int) values and manual_offset is stored as (float) with 0.1 precision.
            # This reverts it so QSlider can handle the number, when fetching from config.
            worker_data['manual_offset'] = worker_data['manual_offset'] * 10

        super().__init__(view, configure, worker_controller, worker_data)

        self.view = view
        self.configure = configure
        self.worker_controller = worker_controller

        # Refresh center price market label
        self.onchange_asset_labels()

        # Refresh center price market label every time the text changes is base or quote asset input fields
        worker_controller.view.base_asset_input.textChanged.connect(self.onchange_asset_labels)
        worker_controller.view.quote_asset_input.textChanged.connect(self.onchange_asset_labels)

        widget = self.view.strategy_widget

        # Event connecting
        widget.external_feed_input.clicked.connect(self.onchange_external_feed_input)
        widget.relative_order_size_input.clicked.connect(self.onchange_relative_order_size_input)
        widget.dynamic_spread_input.clicked.connect(self.onchange_dynamic_spread_input)
        widget.center_price_dynamic_input.clicked.connect(self.onchange_center_price_dynamic_input)
        widget.manual_offset_input.valueChanged.connect(self.onchange_manual_offset_input)
        widget.reset_on_partial_fill_input.clicked.connect(self.onchange_reset_on_partial_fill_input)
        widget.reset_on_price_change_input.clicked.connect(self.onchange_reset_on_price_change_input)
        widget.custom_expiration_input.clicked.connect(self.onchange_custom_expiration_input)

        # Trigger the onchange events once
        self.onchange_relative_order_size_input(widget.relative_order_size_input.isChecked())
        self.onchange_center_price_dynamic_input(widget.center_price_dynamic_input.isChecked())
        self.onchange_external_feed_input(widget.external_feed_input.isChecked())
        self.onchange_dynamic_spread_input(widget.dynamic_spread_input.isChecked())
        self.onchange_reset_on_partial_fill_input(widget.reset_on_partial_fill_input.isChecked())
        self.onchange_reset_on_price_change_input(widget.reset_on_price_change_input.isChecked())
        self.onchange_custom_expiration_input(widget.custom_expiration_input.isChecked())
        self.onchange_manual_offset_input()

    @property
    def values(self):
        # This turns the int value of manual_offset from QSlider to float with desired precision.
        values = super().values
        values['manual_offset'] = values['manual_offset'] / 10
        return values

    def onchange_external_feed_input(self, checked):
        if checked:
            self.view.strategy_widget.external_price_source_input.setDisabled(False)

            self.view.strategy_widget.reset_on_price_change_input.setChecked(False)
            self.view.strategy_widget.price_change_threshold_input.setDisabled(True)
            self.view.strategy_widget.center_price_depth_input.setDisabled(True)
        else:
            self.view.strategy_widget.center_price_depth_input.setEnabled(True)
            self.view.strategy_widget.external_price_source_input.setDisabled(True)

    def onchange_manual_offset_input(self):
        value = self.view.strategy_widget.manual_offset_input.value() / 10
        text = "{}%".format(value)
        self.view.strategy_widget.manual_offset_amount_label.setText(text)

    def onchange_dynamic_spread_input(self, checked):
        if checked:
            self.view.strategy_widget.market_depth_amount_input.setDisabled(False)
            self.view.strategy_widget.dynamic_spread_factor_input.setDisabled(False)
            # Disable the spread field if dynamic spread in use
            self.view.strategy_widget.spread_input.setDisabled(True)
        else:
            self.view.strategy_widget.market_depth_amount_input.setDisabled(True)
            self.view.strategy_widget.dynamic_spread_factor_input.setDisabled(True)
            # Enable spread field if dynamic not in use
            self.view.strategy_widget.spread_input.setDisabled(False)

    def onchange_relative_order_size_input(self, checked):
        if checked:
            self.order_size_input_to_relative()
        else:
            self.order_size_input_to_static()

    def onchange_center_price_dynamic_input(self, checked):
        if checked:
            self.view.strategy_widget.center_price_input.setDisabled(True)
            self.view.strategy_widget.center_price_depth_input.setDisabled(False)
            self.view.strategy_widget.reset_on_price_change_input.setDisabled(False)
            self.view.strategy_widget.external_feed_input.setEnabled(True)

            if self.view.strategy_widget.external_feed_input.isChecked():
                self.view.strategy_widget.external_price_source_input.setEnabled(True)

            if self.view.strategy_widget.reset_on_price_change_input.isChecked():
                self.view.strategy_widget.price_change_threshold_input.setDisabled(False)
        else:
            self.view.strategy_widget.center_price_input.setDisabled(False)
            self.view.strategy_widget.center_price_depth_input.setDisabled(True)

            # Disable and uncheck reset_on_price_change
            self.view.strategy_widget.reset_on_price_change_input.setDisabled(True)
            self.view.strategy_widget.reset_on_price_change_input.setChecked(False)

            self.view.strategy_widget.price_change_threshold_input.setDisabled(True)
            self.view.strategy_widget.external_feed_input.setChecked(False)
            self.view.strategy_widget.external_feed_input.setDisabled(True)
            self.view.strategy_widget.external_price_source_input.setDisabled(True)

    def onchange_reset_on_partial_fill_input(self, checked):
        if checked:
            self.view.strategy_widget.partial_fill_threshold_input.setDisabled(False)
        else:
            self.view.strategy_widget.partial_fill_threshold_input.setDisabled(True)

    def onchange_reset_on_price_change_input(self, checked):
        if checked and self.view.strategy_widget.center_price_dynamic_input.isChecked():
            self.view.strategy_widget.price_change_threshold_input.setDisabled(False)

            # Disable external price feed
            self.view.strategy_widget.external_feed_input.setChecked(False)
            self.view.strategy_widget.external_price_source_input.setDisabled(True)
            self.view.strategy_widget.center_price_depth_input.setEnabled(True)
        else:
            self.view.strategy_widget.price_change_threshold_input.setDisabled(True)

    def onchange_custom_expiration_input(self, checked):
        if checked:
            self.view.strategy_widget.expiration_time_input.setDisabled(False)
        else:
            self.view.strategy_widget.expiration_time_input.setDisabled(True)

    def onchange_asset_labels(self):
        base_symbol = self.worker_controller.view.base_asset_input.text()
        quote_symbol = self.worker_controller.view.quote_asset_input.text()

        if quote_symbol:
            self.set_quote_asset_label(quote_symbol)
        else:
            self.set_quote_asset_label('')

        if base_symbol and quote_symbol:
            text = '{} / {}'.format(base_symbol, quote_symbol)
            self.set_center_price_market_label(text)
        else:
            self.set_center_price_market_label('')

    def order_size_input_to_relative(self):
        self.view.strategy_widget.amount_input.setSuffix('%')
        self.view.strategy_widget.amount_input.setDecimals(2)
        self.view.strategy_widget.amount_input.setMaximum(100.00)
        self.view.strategy_widget.amount_input.setMinimumWidth(170)

    def order_size_input_to_static(self):
        self.view.strategy_widget.amount_input.setSuffix('')
        self.view.strategy_widget.amount_input.setDecimals(8)
        self.view.strategy_widget.amount_input.setMaximum(1000000000.000000)

    def set_center_price_market_label(self, text):
        self.view.strategy_widget.center_price_market_label.setText(text)

    def set_quote_asset_label(self, text):
        self.view.strategy_widget.amount_input_asset_label.setText(text)
        self.view.strategy_widget.center_price_depth_input_asset_label.setText(text)
        self.view.strategy_widget.market_depth_amount_input_asset_label.setText(text)

    def validation_errors(self):
        error_texts = []
        if not self.view.strategy_widget.amount_input.value():
            error_texts.append("Order size can't be 0")
        if not self.view.strategy_widget.spread_input.value():
            error_texts.append("Spread can't be 0")
        return error_texts


class StaggeredOrdersController(StrategyController):

    def __init__(self, view, configure, worker_controller, worker_data):
        self.view = view
        self.configure = configure
        self.worker_controller = worker_controller

        if view:
            if not self.view.strategy_widget.center_price_dynamic_input.isChecked():
                self.view.strategy_widget.center_price_input.setDisabled(False)

        super().__init__(view, configure, worker_controller, worker_data)

        widget = self.view.strategy_widget

        # Event connecting
        widget.center_price_dynamic_input.clicked.connect(self.onchange_center_price_dynamic_input)

        # Trigger the onchange events once
        self.onchange_center_price_dynamic_input(widget.center_price_dynamic_input.isChecked())

    def onchange_center_price_dynamic_input(self, checked):
        if checked:
            self.view.strategy_widget.center_price_input.setDisabled(True)
        else:
            self.view.strategy_widget.center_price_input.setDisabled(False)

    def set_required_base(self, text):
        self.view.strategy_widget.required_base_text.setText(text)

    def set_required_quote(self, text):
        self.view.strategy_widget.required_quote_text.setText(text)

    def validation_errors(self):
        error_texts = []
        if not self.view.strategy_widget.spread_input.value():
            error_texts.append("Spread can't be 0")
        if not self.view.strategy_widget.increment_input.value():
            error_texts.append("Increment can't be 0")
        if not self.view.strategy_widget.lower_bound_input.value():
            error_texts.append("Lower bound can't be 0")
        return error_texts
