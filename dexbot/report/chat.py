import dexbot
import dexbot.report
import re
import datetime
import time
import logging
from os.path import basename

log = logging.getLogger(__name__)


class ChatReporter(dexbot.report.BaseReporter, logging.Handler):

    """
    Base class for reporters that use a chat system (XMPP, Telegram, etc)
    """

    def __init__(self, worker_inf):
        logging.Handler.__init__(self)
        logging.getLogger("dexbot").addHandler(self)
        logging.getLogger("dexbot.per_bot").addHandler(self)
        self.worker_inf = worker_inf
        dexbot.report.BaseReporter.__init__(self)

    def emit(self, record):
        # Use default formatting:
        self.format(record)
        notes = record.msg
        if record.exc_info:
            notes += " " + \
                logging._defaultFormatter.formatException(record.exc_info)
        self.send_message(notes, level=record.levelno, worker_name=getattr(record,'worker_name','N/A'))

    def send_message(self, message, worker_name='N/A', level=logging.INFO, reply_ref=None):
        """
        Send the user a message
        May wish to colourise/prettify output through log metadata passed in via worker_name/level 
        reply_ref: opaque reference from the chat system for replying to messages

        (this function MUST be able to cope with reply_ref = None: i.e. initiating a conversation with
        the user, I know for Telegram this is tricky)
        """
        pass

    def receive_message(self, message, reply_ref=None):
        """
        Chat layer receives a message and calls here for parsing and execution
        SECURITY: descendant code is responsible for making sure messages only
        get here if sent by an authorised user

        reply_ref: an opaque object, some chat systems use this for replying
        will be passed in to send_message if supplied
        """
        worker_name = 'N/A'
        try:
            message = message.strip()
            if message.startswith("/"):
                message = message[1:]
            splits = message.split(":")
            if len(splits) == 1:
                if len(self.worker_inf.workers) == 1:
                    worker_name, self.worker = list(self.worker_inf.workers.items())[0]
                message = splits[0]
            else:
                worker_name = splits[0].strip()
                if worker_name not in self.worker_inf.workers:
                    self.send_message("No such worker", level=logging.ERROR, worker_name=worker_name, reply_ref=reply_ref)
                    return
                message = splits[1]
                self.worker = self.workers_inf.workers[workername]
            message = message.split()
            command = message[0].lower()
            # a few comand synonyms
            if command == 'hello': command = 'ping'
            if command == 'license': command = 'licence'
            if command == 'info': command = 'help'
            if command == '?': command = 'help'
            
            if worker_name == 'N/A' and (not command in ['licence', 'ping', 'version', 'help']):
                return "You need to specify which worker this command applies to, use 'worker name: command'"
            reply = getattr(self, "cmd_"+message[0]) (*message[1:]) or "OK"
            if type(reply) is list:
                reply = "\n".join(reply)
            reply = reply.strip()
            self.send_message(reply, level=logging.INFO, reply_ref=reply_ref)
        except (IndexError, ValueError, KeyError, AttributeError, TypeError):
            self.send_message("Invalid command, use 'help' for help", level=logging.ERROR, worker_name=worker_name, reply_ref=reply_ref)

    def cmd_stop(self):
        """Stop a bot
        """
        self.worker_inf.do_next_tick(self.worker.cancel_all)
        self.worker.disabled = True

    def cmd_kick(self):
        """Restart a stopped or frozen bot. 
        """
        self.worker.disabled = False
        self.worker_inf.do_next_tick(self.worker.reassess)

    def cmd_price(self, price):
        """'price N' Manually set the baseprice to N (forces recalculation of all orders)
        """
        price = float(price)
        self.worker.disabled = False
        self.worker_inf.do_next_tick(lambda: self.worker.updateorders(price))


    def cmd_reset(self):
        """Reset the orders with the same baseprice
        {only really makes sense after you have changed settings)
        """
        if self.worker.disabled:
            return "sorry I'm disabled (use 'kick')"
        if "price" not in self.worker:
            return "But I haven't got a base price set! (use 'price'}"
        self.worker_inf.do_next_tick(lambda: self.worker.updateorders(self.worker['price']))
        
    def cmd_help(self, cmd=None):
        """List all available commands. Use 'help cmd' to get more info on a command
        """
        if cmd is None:
            s = ", ".join(i[4:] for i in dir(self) if i.startswith('cmd_'))
            return "Commands available: {}\nUse \"help cmd\" for details".format(s)
        return getattr(self, 'cmd_'+cmd).__doc__.strip()

    def cmd_ping(self):
        """Check DEXBot is alive
        """
        pass

    def cmd_describe(self):
        """Give a worker's strategy description
        """
        return type(self.worker).__doc__
    
    def cmd_parameters(self):
        """Describe a strategy's parameters
        """
        kls = type(self.worker)
        return ["{} ({}) {}".format(conf.key, conf.type, conf.description) for conf in kls.configure()]

    def cmd_settings(self):
        """Return the current settings of all the strategy parameters
        """
        return ["{}: {}".format(*i) for i in self.worker.worker.items()]

    def cmd_status(self):
        """Return current status and open orders
        """
        if self.worker.disabled:
            return "disabled (use 'kick')"
        s = ["running in {} account {}".format(self.worker.worker['market'],self.worker.worker['account'])]
        if "price" in self.worker:
            s.append("base price is {}".format(self.worker['price']))
        for o in self.worker.orders:
            s.append(str(o))
        return s

    def cmd_set(self, key, value):
        """'set KEY VALUE' set configuration parameter KEY to VALUE. 
        This will not make the worker enter new orders: use 'reset' when you are done changing values.
        This will not permanently save changes.
        """
        kls = type(self.worker)
        no_such_conf = True
        for conf in kls.configure():
            if conf.key == key:
                no_such_conf = False
                if conf.type == 'int':
                    try:
                        value = int(value)
                        if conf.extra:
                            min, max = conf.extra
                            assert value < max and value >= min
                    except:
                        return "{} is not a valid value for {}".format(value, key)
                elif conf.type == 'float':
                    try:
                        value = float(value)
                        if conf.extra:
                            min, max = conf.extra
                            assert value < max and value >= min
                    except:
                        return "{} is not a valid value for {}".format(value, key)
        if no_such_conf:
            return "no such configuration value (use 'parameters')"
        self.worker.worker[key] = value

    def cmd_licence(self):
        """Display the licence
        """
        return """The MIT License (MIT)

Copyright for portions of project DEXBot are held by ChainSquad GmbH 2017
as part of project stakemachine. All other copyright for project DEXBot
are held by Codaone Oy 2018.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE."""
                
    def cmd_version(self):
        """Return the version
        """
        return "DEXBot/"+dexbot.__version__
