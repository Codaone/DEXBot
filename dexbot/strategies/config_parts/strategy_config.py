from dexbot.strategies.config_parts.base_config import BaseConfig, ConfigElement, DetailElement


class StrategyConfig(BaseConfig):
    """ this is the configuration template for the strategy_template class
    """

    @classmethod
    def configure(cls, return_base_config=True):
        """ This function is used to auto generate fields for GUI

            :param return_base_config: If base config is used in addition to this configuration.
            :return: List of ConfigElement(s)
        """

        """ As a demonstration this template has two fields in the worker configuration. Upper and lower bound.
            Documentation of ConfigElements can be found from base.py.
        """
        return BaseConfig.configure(return_base_config) + [
            ConfigElement('lower_bound', 'float', 1, 'Lower bound',
                          'The bottom price in the range',
                          (0, 10000000, 8, '')),
            ConfigElement('upper_bound', 'float', 10, 'Upper bound',
                          'The top price in the range',
                          (0, 10000000, 8, '')),
        ]

    @classmethod
    def configure_details(cls, include_default_tabs=True):
        """ This function defines the tabs for detailed view of the worker. Further documentation is found in base.py

            :param include_default_tabs: If default tabs are included as well
            :return: List of DetailElement(s)

            NOTE: Add files to user data folders to see how they behave as an example.
        """
        return BaseConfig.configure_details(include_default_tabs) + [
            DetailElement('graph', 'Graph', 'Graph', 'graph.jpg'),
            DetailElement('table', 'Orders', 'Data from csv file', 'example.csv'),
            DetailElement('text', 'Log', 'Log data', 'example.log')
        ]
