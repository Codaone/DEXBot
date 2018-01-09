Configuration Questions
=======================

The configuration consists of a series of questions about the bots you wish to configure.

1. the Node.

   You need to set the public node that gives access to the BitShares blockchain. Pick the one closest to you.

   (Please submit a `Github bug report <https://github.com/ihaywood3/DEXBot/issues/new>`_ if you think items need to added or removed from this list).

2. The Bot Name.
      
   Choose a unique name for your bot, DEXBot doesn't care what you call it. It is used to identify the bot in the logs so should be fairly short.

3. The Bot Strategy
      
   DEXBot provides a number of different bot strategies. They can be quite different in
   how they behave (i.e. spend *your* money) so it is important you understand the strategy
   before deploying a bot.

   a. :doc:`echo` For testing this just logs events on a market, does no trading.
   b. :doc:`wall` a basic liquidity bot maintaining a "wall" of buy and sell orders around the market price.

   Technically the questions that follow are determined by the strategy chosen, and each strategy will have its own questions around
   amounts to trade, spreads etc. See the strategy documentations linked above. But two questions are nearly universal among strategies
   so are documented here.

3. The Account.

   This is the same account name as the one where you entered the keys into ``uptick`` earlier on: the bot must
   always have the private key so it can execute trades.

4. The Market.
      
   This is the main market the bot trade on. They are specified by the quote asset, a colon (:), and the base asset, for example
   the market for BitShares priced in US dollars is called BTS:USD. BitShares always provides a "reverse" market so
   there will be a USD:BTS with the same trades, the only difference is the prices will be the inverse (1/x) of BTS:USD.

5. Systemd.

   If the configuration tool detects systemd (the process control system on most modern systems) it will offer to install dexbot
   as a background service, this will run continuously in the background whenever you are logged in. if you enabled lingering
   as described, it wil run whenever the computer is turned on.

6. If you select yes above, the final question will be the password you entered to protect the private key with ``uptick``.
   Entering it here is a security risk: the configuration tool will save the password to a file on the computer. This
   means anyone with access to the computer can access your private key and spend the money in your account.

   There is no alternative to enable 24/7 bot trading without you being physically present to enter the password every time
   the bot wnats to execute a trade (which defeats the purpose of using a bot). It does mean you need to think carefully
   where dexbot is installed: my advice is on the computer in a secure location that you control behind a properly-
   configured firewall/router.

Manual Running
--------------

If you are not using systemd, the bot can be run manually by::

    dexbot run

It will ask for your wallet passphrase (that you have provide when
adding your private key to pybitshares using ``uptick addkey``).

If you want to prevent the password dialog, you can predefine an
environmental variable ``UNLOCK``, if you understand the security
implications.
