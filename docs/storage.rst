*******
Storage
*******

This class allows to permanently store bot-specific data in a sqlite
database (``dexbot.sqlite``) using:

``self["key"] = "value"``

.. note:: Here, ``self`` refers to the instance of your bot's strategy
          when coding yaour own strategy.

The value is persistently stored and can be access later on using:

``print(self["key"])``.

.. note:: This applies a ``json.loads(json.dumps(value))``!

SQLite database
---------------
The user's data is stored in its OS protected user directory:

**OSX:**

 * `~/Library/Application Support/<AppName>`

**Windows:**

 * `C:\Documents and Settings\<User>\Application Data\Local Settings\<AppAuthor>\<AppName>`
 * `C:\Documents and Settings\<User>\Application Data\<AppAuthor>\<AppName>`

**Linux:**

 * `~/.local/share/<AppName>`

Where ``<AppName>`` is ``dexbot`` and ``<AppAuthor>`` is
``ChainSquad GmbH``.


Simple example
--------------


.. literalinclude:: ../dexbot/strategies/storagedemo.py
   :language: python
   :linenos:

**Example Output:**

::

  Current Wallet Passphrase: 
  previous block: None
  new block: 008c4c2424e6394ad4bf5a9756ae2ee883b0e049
  previous block: 008c4c2424e6394ad4bf5a9756ae2ee883b0e049
  new block: 008c4c257a76671144fdba251e4ebbe61e4593a4
  previous block: 008c4c257a76671144fdba251e4ebbe61e4593a4
  new block: 008c4c2617851b31d0b872e32fbff6f8248663a3
