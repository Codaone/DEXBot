*****
Setup
*****

Installation
------------

::

   pip3 install stakemachine     [--user]

If you install using the ``--user`` flag, the binaries of
``stakemachine`` and ``uptick`` are located in ``~/.local/bin``.
Otherwise they should be globally reachable.

Adding Keys
-----------
It is important to *install* the private key of your
bot's account into the pybitshares wallet. This can be done using
``uptick`` which is installed as a dependency of ``stakemachine``::

   uptick addkey

Configuration
-------------

``stakemachine`` can be configured using

    stakemachine configure

This will walk you through the configuration process. If `systemd`
is available it wil offer to install a user service to automatically
run stakemachine in the background.

Manual Configuration
--------------------

You will need to create configuration file in YAML format. The default
file name is ``config.yml``, otherwise you can specify a different
config file using the ``--configfile X`` parameter of ``stakemachine``.

Read more about the :doc:`configuration`.

Running
-------
The bot can be run by::

    stakemachine run

It will ask for your wallet passphrase (that you have provide when
adding your private key to pybitshares using ``uptick addkey``).

If you want to prevent the password dialog, you can predefine an
environmental variable ``UNLOCK``, if you understand the security
implications.
