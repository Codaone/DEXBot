from dexbot.storage import Storage
from . import graph
import re
import datetime
import smtplib
import getpass
import socket
import io
import time
import logging
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import COMMASPACE, formatdate

log = logging.getLogger(__name__)

from dexbot.storage import SQLiteHandler

"""
A framework for reporting
an an email based reporter
"""

class Reporter:
    """Abstract base class for reporter plugins
    """

    def ontick(self):
        """Called for every tick
        """
        pass

EMAIL_DEFAULT = {
    'server': '127.0.0.1',
    'port': 25,
    'subject': 'DEXBot Regular Report'}

signalled = False

INTRO = """
<html>
  <head>
    <style>
       tr.debug {
         color: gray;
         background_color: white;
       }
       tr.warn {
         color: black;
         background-color: lightsalmon;
       }
       tr.critical {
         font-weight: bold;
         background-color: orangered;
         color: black;
       }
       table#log {
          font-size: smaller;
       }
    </style>
  </head>
  <body>"""


LOGLEVELS = {0: 'debug', 1: 'info', 2: 'warn', 3: 'critical'}


class EmailReporter(Storage,Reporter):

    def __init__(self, **config):
        self.worker_inf = config['worker_infrastructure']
        self.config = config
        
        Storage.__init__(self, "reporter")
        if not "lastrun" in self:
            self['lastrun'] = self.lastrun = time.time()
        else:
            self.lastrun = self['lastrun']
        logging.getLogger("dexbot.per_bot").addHandler(
            SQLiteHandler())  # and log to SQLIte DB

    def ontick(self):
        now = time.time()
        # because we are consulting lastrun every tick, we keep a RAM copy
        # as well as one serialised via storage.Storage
        if now - self.lastrun > 24 * 60 * 60 * self.config['days']:
            try:
                self.run_report(datetime.datetime.fromtimestamp(self.lastrun))
            finally:
                self['lastrun'] = self.lastrun = now

    def run_report_week(self):
        """Genrate report for the past week on-the-spot"""
        self.run_report(datetime.datetime.fromtimestamp(
            time.time() - 7 * 24 * 60 * 60),
            subject="DEXBot on-the-spot report")

    def run_report(self, start, subject=None):
        """Generate report
        start: timestamp to begin"""
        msg = io.StringIO()
        files = []
        msg.write(INTRO)
        for workername, worker in self.worker_inf.workers.items():
            msg.write("<h1>Worker {}</h1>\n".format(workername))
            msg.write('<h2>Settings</h2><table id="worker">')
            for key, value in self.worker_inf.config['workers'][workername].items():
                msg.write("<tr><td>{}</td><td>{}</tr>".format(key, value))
            msg.write("</table><h2>Graph</h2>")
            fname = worker.graph(start=start)
            if fname is not None:
                msg.write("<p><img src=\"cid:{}\"></p>".format(basename(fname)))
                files.append(fname)
            else:
                msg.write("<p>Not enough data to graph.<p>")
            msg.write("<h2>Balance History</h2>")
            data = graph.query_to_dicts(worker.query_journal(start=start))
            if len(data) == 0:
                msg.write("<p>No data</p>")
            else:
                msg.write('<table id="journal"><tr><th>Date</th>')
                cols = data[max(data.keys())].keys()
                for i in cols:
                    msg.write('<th>{}</th>'.format(i))
                msg.write('</tr>')
                for stamp in sorted(data.keys()):
                    msg.write('<tr><td>{}</td>'.format(stamp))
                    for i in cols:
                        msg.write('<td>{}</td>'.format(data[stamp][i]))
                    msg.write('</tr>')
                msg.write('</table>')
            msg.write('<h2>Log</h2><table id="log">')
            logs = worker.query_log(start=start)
            for entry in logs:
                msg.write('<tr class="{}"><td>{}</td><td>{}</td></tr>'.format(
                    LOGLEVELS[entry.severity],
                    entry.stamp,
                    entry.message))
        msg.write("</table></body></html>")
        self.send_mail(msg.getvalue(), files, subject)

    def send_mail(self, text, files=None, subject=None):
        nc = EMAIL_DEFAULT.copy()
        nc.update(self.config)
        if subject is not None:
            nc['subject'] = subject
        self.config = nc
        msg = MIMEMultipart('related')
        if not "send_from" in self.config:
            self.config['send_from'] = getpass.getuser() + "@" + \
                socket.gethostname()
        msg['From'] = self.config['send_from']
        msg['To'] = self.config.get('send_to', self.config['send_from'])
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = self.config['subject']

        msg.attach(MIMEText(text, "html"))

        for f in files or []:
            with open(f, "rb") as fd:
                part = MIMEImage(
                    fd.read(),
                    name=basename(f)
                )
            # After the file is closed
            part['Content-Disposition'] = 'inline; filename="%s"' % basename(
                f)
            part['Content-ID'] = '<{}>'.format(basename(f))
            msg.attach(part)

        smtp = smtplib.SMTP(self.config['server'], port=self.config['port'])
        if "user" in self.config:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(self.config['user'], self.config['password'])
        smtp.send_message(msg)
        smtp.close()

class ChatReporter(Reporter, logging.Handler):

    """
    Base class for reporters that use a chat system (XMPP, Telegram, etc)
    """

    def __init__(self, worker_inf):
        logging.Handler.__init__(self)
        logging.getLogger("dexbot").addHandler(self)
        logging.getLogger("dexbot.per_bot").addHandler(self)
        self.worker_inf = worker_inf
        Reporter.__init__(self)

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
        May wish to colourise/prettify output through log metadata

        MUST be able to cope with reply_ref = None: i.e. initiating a conversation with
        the user. (I know for Telegram this is tricky)
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
        #import pudb ; pudb.set_trace()
        worker_name = 'N/A'
        try:
            message = message.strip()
            if message.startswith("/"):
                message = message[1:]
            splits = message.split(":")
            if len(splits) == 1:
                if len(self.worker_inf.workers) > 1:
                    self.send_message("You need to specify which worker using name: before the command", level=logging.ERROR, reply_ref=reply_ref)
                    return
                worker_name, self.worker = list(self.worker_inf.workers.items())[0]
            else:
                worker_name = splits[0].strip()
                if worker_name not in self.worker_inf.workers:
                    self.send_message("No such worker", level=logging.ERROR, worker_name=worker_name, reply_ref=reply_ref)
                    return
                message = splits[1]
                self.worker = self.workers_inf.workers[workername]
            message = message.split()
            body = getattr(self, "cmd_"+message[0]) (*message[1:]) or "OK"
            self.send_message(body, level=logging.INFO, worker_name=worker_name, reply_ref=reply_ref)
        except (IndexError, ValueError, KeyError, AttributeError, TypeError):
            self.send_message("Invalid command, use \"help\" for help", level=logging.ERROR, worker_name=worker_name, reply_ref=reply_ref)

    def cmd_stop(self):
        """Stop a bot
        """
        self.worker_inf.do_next_tick(self.worker.cancel_all)
        self.worker.disabled = True

    def cmd_kick(self):
        """Restart a stopped or frozen bot
        """
        self.worker.disabled = False
        self.worker_inf.do_next_tick(self.worker.reassess)

    def cmd_price(self, price):
        """Manually set the baseprice (forces recalculation of all orders)
        """
        price = float(price)
        self.worker.disabled = False
        self.worker_inf.do_next_tick(lambda: self.worker.updateorders(price))
   
    def cmd_help(self, cmd=None):
        """List all available commands
        """
        if cmd is None:
            s = ", ".join(i[4:] for i in dir(self) if i.startswith('cmd_'))
            return "Commands available: {}\nUse \"help cmd\" for details".format(s)
        return getattr(self, 'cmd_'+cmd).__doc__
