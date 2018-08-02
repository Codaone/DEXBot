import re

from .ui.worker_item_widget_ui import Ui_widget
from .confirmation import ConfirmationDialog
from .edit_worker import EditWorkerView
from dexbot.storage import db_worker
from dexbot.controllers.worker_controller import WorkerController
from dexbot.views.errors import gui_error

from PyQt5 import QtCore, QtWidgets


class WorkerItemWidget(QtWidgets.QWidget, Ui_widget):

    def __init__(self, worker_name, config, main_ctrl, view):
        super().__init__()

        self.main_ctrl = main_ctrl
        self.running = False
        self.worker_name = worker_name
        self.worker_config = self.main_ctrl.config.get_worker_config(worker_name)
        self.view = view

        self.setupUi(self)

        self.edit_button.clicked.connect(lambda: self.handle_edit_worker())
        self.toggle.mouseReleaseEvent = lambda _: self.toggle_worker()
        self.onoff.mouseReleaseEvent = lambda _: self.toggle_worker()

        self.setup_ui_data(config)

    def setup_ui_data(self, config):
        worker_name = self.worker_name
        self.set_worker_name(worker_name)

        market = config['workers'][worker_name]['market']
        self.set_worker_market(market)

        module = config['workers'][worker_name]['module']
        strategies = WorkerController.get_strategies()
        self.set_worker_strategy(strategies[module]['name'])

        profit = db_worker.get_item(worker_name, 'profit')
        if profit:
            self.set_worker_profit(profit)
        else:
            self.set_worker_profit(0)

        percentage = db_worker.get_item(worker_name, 'slider')
        if percentage:
            self.set_worker_slider(percentage)
        else:
            self.set_worker_slider(50)

    @gui_error
    def toggle_worker(self, ):
        if self.horizontalLayout_5.alignment() != QtCore.Qt.AlignRight:
            self.start_worker()
        else:
            self.pause_worker()

    def _toggle_worker(self, toggle_label_text, toggle_alignment):
        _translate = QtCore.QCoreApplication.translate
        self.toggle_label.setText(_translate("widget", toggle_label_text))
        self.horizontalLayout_5.setAlignment(toggle_alignment)

        # TODO: better way of repainting the widget
        self.toggle.hide()
        self.toggle.show()

    @gui_error
    def start_worker(self):
        self.set_status("Starting worker")
        self._start_worker()
        self.main_ctrl.start_worker(self.worker_name, self.worker_config, self.view)

    def _start_worker(self):
        self.running = True
        self._toggle_worker('TURN WORKER OFF', QtCore.Qt.AlignRight)

    @gui_error
    def pause_worker(self):
        self.set_status("Pausing worker")
        self._pause_worker()
        self.main_ctrl.pause_worker(self.worker_name)

    def _pause_worker(self):
        self.running = False
        self._toggle_worker('TURN WORKER ON', QtCore.Qt.AlignLeft)

    def set_worker_name(self, value):
        self.worker_name_label.setText(value)

    def set_worker_strategy(self, value):
        value = value.upper()
        self.strategy_label.setText(value)

    def set_worker_market(self, value):
        values = re.split("[/:]", value)
        market = '/'.join(values)
        self.currency_label.setText(market)
        self.base_asset_label.setText(values[1])
        self.quote_asset_label.setText(values[0])

    def set_worker_profit(self, value):
        value = float(value)
        if value >= 0:
            value = '+' + str(value)

        value = str(value) + '%'
        self.profit_label.setText(value)

    def set_worker_slider(self, value):
        bar_width = self.bar.width()

        spacing = self.bar.layout().spacing()
        margin_left = self.bar.layout().contentsMargins().left()
        margin_right = self.bar.layout().contentsMargins().right()
        total_padding = spacing + margin_left + margin_right
        usable_width = (bar_width - total_padding)

        # So we keep the roundness of bars.
        # If bar width is less than 2 * border-radius, it squares the corners
        base_width = usable_width * (value / 100)
        if base_width < 20:
            base_width = 20
        if base_width > usable_width - 20:
            base_width = usable_width - 20

        self.base_asset_label.setMaximumWidth(base_width)
        self.base_asset_label.setMinimumWidth(base_width)

    @gui_error
    def remove_widget_dialog(self):
        dialog = ConfirmationDialog(
            'Are you sure you want to remove worker "{}"?'.format(self.worker_name))
        return_value = dialog.exec_()
        if return_value:
            self.remove_widget()

    def remove_widget(self):
        account = self.worker_config['workers'][self.worker_name]['account']

        self.main_ctrl.remove_worker(self.worker_name)
        self.main_ctrl.bitshares_instance.wallet.removeAccount(account)
        self.view.remove_worker_widget(self.worker_name)
        self.main_ctrl.config.remove_worker_config(self.worker_name)
        self.deleteLater()

    def reload_widget(self, worker_name):
        """ Reload the data of the widget
        """
        self.worker_config = self.main_ctrl.config.get_worker_config(worker_name)
        self.setup_ui_data(self.worker_config)
        self._pause_worker()

    @gui_error
    def handle_edit_worker(self):
        edit_worker_dialog = EditWorkerView(self, self.main_ctrl.bitshares_instance,
                                            self.worker_name, self.worker_config)
        return_value = edit_worker_dialog.exec_()

        # User clicked save
        if return_value:
            new_worker_name = edit_worker_dialog.worker_name
            self.view.change_worker_widget_name(self.worker_name, new_worker_name)
            self.main_ctrl.remove_worker(self.worker_name)
            self.main_ctrl.config.replace_worker_config(self.worker_name,
                                                        new_worker_name,
                                                        edit_worker_dialog.worker_data)
            self.worker_name = new_worker_name
            self.reload_widget(new_worker_name)

    def set_status(self, status):
        self.worker_status.setText(status)
