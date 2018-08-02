import sys

from PyQt5 import Qt
from bitshares import BitShares

from dexbot.config import Config
from dexbot.controllers.main_controller import MainController
from dexbot.views.worker_list import MainView
from dexbot.controllers.wallet_controller import WalletController
from dexbot.views.unlock_wallet import UnlockWalletView
from dexbot.views.create_wallet import CreateWalletView


class App(Qt.QApplication):
    def __init__(self, sys_argv):
        super(App, self).__init__(sys_argv)

        config = Config()
        bitshares_instance = BitShares(config['node'], num_retries=-1)

        # Wallet unlock
        unlock_ctrl = WalletController(bitshares_instance)
        if unlock_ctrl.wallet_created():
            unlock_view = UnlockWalletView(unlock_ctrl)
        else:
            unlock_view = CreateWalletView(unlock_ctrl)

        if unlock_view.exec_():
            bitshares_instance = unlock_ctrl.bitshares
            self.main_ctrl = MainController(bitshares_instance, config)
            self.main_view = MainView(self.main_ctrl)
            self.main_view.show()
        else:
            sys.exit()


def main():
    app = App(sys.argv)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
