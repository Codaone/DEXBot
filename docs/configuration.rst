Configuration Questions
=======================

The configuration consists of a series of questions about the bots you wish to configure.


1. The Bot Name.
      
   Choose a unique name for your bot, DEXBot doesn't care what you call it.
   It is used to identify the bot in the logs so should be fairly short.

2. The Bot Strategy
      
   DEXBot provides a number of different bot strategies. They can be quite different in
   how they behave (i.e. spend *your* money) so it is important you understand the strategy
   before deploying a bot.

   a. :doc:`echo` For testing this just logs events on a market, does no trading.
   b. :doc:`follow_orders` My (Ian Haywood) main bot, an extension of stakemachine's `wall`,
      it has been used to provide liquidity on AUD:BTS. 
      Does function but by no mean perfect, see caveats in the docs.

3. Strategy-specific questions

   The questions that follow are determined by the strategy chosen, and each strategy will have its own questions around
   amounts to trade, spreads etc. See the strategy documentations linked above. But the first two strategy questions
   are nearly universal amongst the strategies so are documented here:
   
   a. The Account.

      This is the same account name as the one where you entered the keys into ``uptick`` earlier on: the bot must
      always have the private key so it can execute trades.

   b. The Market.
      
      This is the main market the bot trade on. They are specified by the quote asset, a colon (:), and the base asset, for example
      the market for BitShares priced in US dollars is called BTS:USD. BitShares always provides a "reverse" market so
      there will be a USD:BTS with the same trades, the only difference is the prices will be the inverse (1/x) of BTS:USD.

4. the Node.

   DEXBot needs to have a public node (also called "witness") that gives access to the BitShares blockchain.

   DEXBot uses ``wss://status200.bitshares.apasia.tech/ws`` as its default node
   If you run your own witness node then you can edit ``config.yml`` to change the node value.

5. Reporting

   DEXBot can send regular reports via e-mail of its activities. See :doc:`reports`
   
6. Systemd.

   If the configuration tool detects systemd (the process control system on most modern Linux systems) it will offer to install dexbot
   as a background service, this will run continuously in the background whenever you are logged in. if you enabled lingering
   as described, it will run whenever the computer is turned on.

7. The Passphrase

   If you select yes above, the final question will be the password you entered to protect the private key with ``uptick``.
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

It will ask for your wallet passphrase (that you provided when
adding your private key using ``uptick addkey``).
