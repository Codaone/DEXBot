import collections

""" Strategies need to specify their own configuration values, so each strategy can have a class method 'configure'
    which returns a list of ConfigElement named tuples.

    Tuple fields as follows:
        - Key: The key in the bot config dictionary that gets saved back to config.yml
        - Type: "int", "float", "bool", "string" or "choice"
        - Default: The default value, must be same type as the Type defined
        - Title: Name shown to the user, preferably not too long
        - Description: Comments to user, full sentences encouraged
        - Extra:
              :int: a (min, max, suffix) tuple
              :float: a (min, max, precision, suffix) tuple
              :string: a regular expression, entries must match it, can be None which equivalent to .*
              :bool, ignored
              :choice: a list of choices, choices are in turn (tag, label) tuples.
              NOTE: 'labels' get presented to user, and 'tag' is used as the value saved back to the config dict!
"""
ConfigElement = collections.namedtuple('ConfigElement', 'key type default title description extra')

""" Strategies have different needs for the details they want to show for the user. These elements help to build a
    custom details window for the strategy.

    Tuple fields as follows:
        - Type: 'graph', 'text', 'table'
        - Name: The name of the tab, shows at the top
        - Title: The title is shown inside the tab
        - File: Tabs can also show data from files, pass on the file name including the file extension
                in strategy's `configure_details`.

                Below folders and representative file types that inside the folders.

                Location        File extensions
                ---------------------------
                dexbot/graphs   .png, .jpg
                dexbot/data     .csv
                dexbot/logs     .log, .txt (.csv, will print as raw data)

          NOTE: To avoid conflicts with other custom strategies, when generating names for files, use slug or worker's
          name when generating files or create custom folders. Add relative path to 'file' parameter if file is in
          custom folder inside default folders. Like shown below:

          `DetailElement('log', 'Worker log', 'Log of worker's actions', 'my_custom_folder/example_worker.log')`
"""
DetailElement = collections.namedtuple('DetailTab', 'type name title file')


class BaseConfig:

    @classmethod
    def configure(cls, return_base_config=True):
        """ Return a list of ConfigElement objects defining the configuration values for this class.

            User interfaces should then generate widgets based on these values, gather data and save back to
            the config dictionary for the worker.

            NOTE: When overriding you almost certainly will want to call the ancestor and then
            add your config values to the list.

            :param return_base_config: bool:
            :return: Returns a list of config elements
        """

        # Common configs
        base_config = [
            ConfigElement('account', 'string', '', 'Account',
                          'BitShares account name for the bot to operate with',
                          ''),
            ConfigElement('market', 'string', 'BTS/USD', 'Market',
                          'BitShares market to operate on, in the format QUOTE/BASE, for example \"BTS/USD\"',
                          r'[A-Z0-9\.]+[:\/][A-Z0-9\.]+'),
            ConfigElement('fee_asset', 'string', 'BTS', 'Fee asset',
                          'Asset to be used to pay transaction fees',
                          r'[A-Z\.]+')
        ]

        if return_base_config:
            return base_config
        return []

    @classmethod
    def configure_details(cls, include_default_tabs=True):
        """ Return a list of ConfigElement objects defining the configuration values for this class.

            User interfaces should then generate widgets based on these values, gather data and save back to
            the config dictionary for the worker.

            NOTE: When overriding you almost certainly will want to call the ancestor and then
            add your config values to the list.

            :param include_default_tabs: bool:
            :return: Returns a list of Detail elements
        """

        # Common configs
        details = []

        if include_default_tabs:
            return details
        return []
