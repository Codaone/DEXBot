from dexbot.strategies.config_parts.base_config import BaseConfig, ConfigElement


class KothConfig(BaseConfig):
    @classmethod
    def configure(cls, return_base_config=True):
        config = [
            ConfigElement(
                'mode',
                'choice',
                'both',
                'Mode',
                'Operational mode',
                ([('both', 'Buy + sell'), ('buy', 'Buy only'), ('sell', 'Sell only')]),
            ),
            ConfigElement(
                'lower_bound',
                'float',
                0,
                'Lower bound',
                'Do not place sell orders lower than this bound',
                (0, 10000000, 8, ''),
            ),
            ConfigElement(
                'upper_bound',
                'float',
                0,
                'Upper bound',
                'Do not place buy orders higher than this bound',
                (0, 10000000, 8, ''),
            ),
            ConfigElement(
                'buy_order_amount',
                'float',
                0,
                'Amount (BASE)',
                'Fixed order size for buy orders, expressed in BASE asset, unless "relative order size"' ' selected',
                (0, None, 8, ''),
            ),
            ConfigElement(
                'sell_order_amount',
                'float',
                0,
                'Amount (QUOTE)',
                'Fixed order size for sell orders, expressed in QUOTE asset, unless "relative order size"' ' selected',
                (0, None, 8, ''),
            ),
            ConfigElement(
                'relative_order_size',
                'bool',
                False,
                'Relative order size',
                'Amount is expressed as a percentage of the account balance of quote/base asset',
                None,
            ),
            ConfigElement(
                'buy_order_size_threshold',
                'float',
                0,
                'Ignore smaller buy orders',
                'Ignore buy orders which are smaller than this threshold (BASE). '
                'If unset, use own order size as a threshold',
                (0, None, 8, ''),
            ),
            ConfigElement(
                'sell_order_size_threshold',
                'float',
                0,
                'Ignore smaller sell orders',
                'Ignore sell orders which are smaller than this threshold (QUOTE). '
                'If unset, use own order size as a threshold',
                (0, None, 8, ''),
            ),
            ConfigElement(
                'min_order_lifetime',
                'int',
                6,
                'Min order lifetime',
                'Minimum order lifetime before order reset, seconds',
                (1, None, ''),
            ),
        ]

        return BaseConfig.configure(return_base_config) + config

    @classmethod
    def configure_details(cls, include_default_tabs=True):
        return BaseConfig.configure_details(include_default_tabs) + []
