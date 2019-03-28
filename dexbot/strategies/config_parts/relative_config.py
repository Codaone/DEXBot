from dexbot.strategies.config_parts.base_config import BaseConfig, ConfigElement


class RelativeConfig(BaseConfig):

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
        # External exchanges used to calculate center price
        EXCHANGES = [
            # ('none', 'None. Use Manual or Bitshares DEX Price (default)'),
            ('gecko', 'Coingecko'),
            ('waves', 'Waves DEX'),
            ('kraken', 'Kraken'),
            ('bitfinex', 'Bitfinex'),
            ('gdax', 'Gdax'),
            ('binance', 'Binance')
        ]

        relative_orders_config = [
            ConfigElement('external_feed', 'bool', False, 'External price feed',
                          'Use external reference price instead of center price acquired from the market', None),
            ConfigElement('external_price_source', 'choice', EXCHANGES[0], 'External price source',
                          'The bot will try to get price information from this source', EXCHANGES),
            ConfigElement('amount', 'float', 1, 'Amount',
                          'Fixed order size, expressed in quote asset, unless "relative order size" selected',
                          (0, None, 8, '')),
            ConfigElement('relative_order_size', 'bool', False, 'Relative order size',
                          'Amount is expressed as a percentage of the account balance of quote/base asset', None),
            ConfigElement('spread', 'float', 5, 'Spread',
                          'The percentage difference between buy and sell', (0, 100, 2, '%')),
            ConfigElement('dynamic_spread', 'bool', False, 'Dynamic spread',
                          'Enable dynamic spread which overrides the spread field', None),
            ConfigElement('market_depth_amount', 'float', 0, 'Market depth',
                          'From which depth will market spread be measured? (QUOTE amount)',
                          (0.00000001, 1000000000, 8, '')),
            ConfigElement('dynamic_spread_factor', 'float', 1, 'Dynamic spread factor',
                          'How many percent will own spread be compared to market spread?',
                          (0.01, 1000, 2, '%')),
            ConfigElement('center_price', 'float', 0, 'Center price',
                          'Fixed center price expressed in base asset: base/quote', (0, None, 8, '')),
            ConfigElement('center_price_dynamic', 'bool', True, 'Measure center price from market orders',
                          'Estimate the center from closest opposite orders or from a depth', None),
            ConfigElement('center_price_depth', 'float', 0, 'Measurement depth',
                          'Cumulative quote amount from which depth center price will be measured',
                          (0.00000001, 1000000000, 8, '')),
            ConfigElement('center_price_offset', 'bool', False, 'Center price offset based on asset balances',
                          'Automatically adjust orders up or down based on the imbalance of your assets', None),
            ConfigElement('manual_offset', 'float', 0, 'Manual center price offset',
                          "Manually adjust orders up or down. "
                          "Works independently of other offsets and doesn't override them", (-50, 100, 2, '%')),
            ConfigElement('reset_on_partial_fill', 'bool', True, 'Reset orders on partial fill',
                          'Reset orders when buy or sell order is partially filled', None),
            ConfigElement('partial_fill_threshold', 'float', 30, 'Fill threshold',
                          'Order fill threshold to reset orders', (0, 100, 2, '%')),
            ConfigElement('reset_on_price_change', 'bool', False, 'Reset orders on center price change',
                          'Reset orders when center price is changed more than threshold '
                          '(set False for external feeds)', None),
            ConfigElement('price_change_threshold', 'float', 2, 'Price change threshold',
                          'Define center price threshold to react on', (0, 100, 2, '%')),
            ConfigElement('custom_expiration', 'bool', False, 'Custom expiration',
                          'Override order expiration time to trigger a reset', None),
            ConfigElement('expiration_time', 'int', 157680000, 'Order expiration time',
                          'Define custom order expiration time to force orders reset more often, seconds',
                          (30, 157680000, ''))
        ]

        return BaseConfig.configure(return_base_config) + relative_orders_config

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
        return BaseConfig.configure_details(include_default_tabs) + []
