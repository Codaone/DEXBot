**********************
Follow Orders Strategy
**********************

This strategy places a buy and a sell walls into a specific market.
It buys below a base price, and sells above the base price.

It then reacts to orders filled (hence the name), when one order is
completely filled, new walls are constructed using the filled order
as the new base price.

Configuration Questions
=======================

Spread
------

Percentage difference between buy and sell price. So a spread of 5% means the bot sells at 2.5%
above the base price and buys 2.5% below.

Wall Percent
------------

This is the "wall height": the default amount to buy/sell, expressed as a percentage of the account balance.
So for sells, its that percentage of your balance of the 'quote' asset, and for buys
its that same percentage of your balance of the 'base' asset.

The advantage of this method (a change from early versions with 'fixed' wall heights) is it makes the bot 'self-correcting'
if it sells to much of one asset, it will enter small orders for that asset, until the
market gives it and opposing trade and it can rebalance itself.

Remember if you are using 'staggers' (see below) each order is the same: so you probably need to use
quite a small percentage here.

Max
---

The bot will stop trading if the base price goes above this value, it will shut down until you manually
restart it. (i.e. it won't restart itself if the price drops)

Remember prices are base/quote, so on AUD:BTS, that's the price of 1 AUD in BTS.

Min
---

Same in reverse: stop running if prices go below this value.

Start
-----

The initial price, as a percentage of the spread between the highest bid and lowest ask. So "0" means
the highest bid, "100" means the lowest ask, 50 means the midpoint between them, and so on.

*Important*: you need to look at your chosen market carefully and get a sense of its orderbook before setting this,
justing setting "50" blind can lead to stupid prices especially in illiquid markets.

Reset
-----

Normally the bot checks if it has previously placed orders in the market and uses those. If true,
this option forces the bot to cancel any existing orders when it starts up, and re-calculate
the starting price as above.

Staggers
--------

Number of additional (or "staggered") orders to place. By default this is "1" (so
no additional orders). 2 or more means multiple sell and buy orders at different prices.

Stagger Spread
--------------

The gap between each staggered order (as a percentage of the base price).

So say the spread is 5%, staggers is "2", and "stagger spread" is 4%, then there will be 2
buy orders: 2.5% and 6.5% (4% + 2.5%) below the base price, and two sells 2.5% and 6.5% above.
The order amounts are all the same (see `wall percent` option).

Bot problems
============

Like all liquidity bots, the bot really works best with a "even"
market, i.e. where are are counterparties both buying and selling.

With a severe "bear" market, the
bot can be stuck being the sole participant that is still buying against a herd of panicked humans frantically selling.
It repeatingly buys into the market and so it can
run out of one asset quite quickly (although it will have bought it at
lower and lower prices).

I don't have a simple good solution (and happy to hear suggestions from experienced traders)

