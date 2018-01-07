*****
Setup
*****

Requirements -- Linux
---------------------

To run in the background you need systemd and *lingering* enabled::

   sudo loginctl enable-linger $USER

On some systems, such as the Raspberry Pi, you need to reboot for this to take effect.

You need to have python3 installed, including the ``pip`` tool, and the development tools for C extensions.
Plus for the configuration you need the ``dialog`` command.

On Ubuntu/Debian type systems::

   sudo apt-get install dialog python3-pip python3-dev


On other distros you need to check the documentation for how to install packages, the names should be very similar.
  
Installation
------------

::

   pip3 install git+https://github.com/ihaywood3/DEXBot.git [--user]

If you install using the ``--user`` flag, the binaries of
``dexbot`` and ``uptick`` are located in ``~/.local/bin``.
Otherwise they should be globally reachable.

Adding Keys
-----------

It is important to *install* the private key of your
bot's account into a local wallet. This can be done using
``uptick`` which is installed as a dependency of ``dexbot``::

   uptick addkey

Easy Configuration
------------------

``dexbot`` can be configured using::

    dexbot configure

This will walk you through the configuration process.
Read more about this in the :doc:`configuration`.

