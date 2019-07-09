import sys

from dexbot.config import Config
from dexbot.controllers.main_controller import MainController
from dexbot.views.worker_list import MainView

from PyQt5.QtWidgets import QApplication


class App(QApplication):
    def __init__(self, sys_argv):
        super(App, self).__init__(sys_argv)

        # Init config
        config = Config()

        # Init main controller
        self.main_controller = MainController(config)

        # Init main view
        self.main_view = MainView(self.main_controller)

        # Show main view
        self.main_view.show()


def main():
    app = App(sys.argv)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
