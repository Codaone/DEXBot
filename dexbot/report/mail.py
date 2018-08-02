import dexbot.storage
import dexbot.report
from dexbot.basestrategy import ConfigElement
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


class Reporter(dexbot.storage.Storage, dexbot.report.BaseReporter):

    @classmethod
    def configure(kls):
        return [
            ConfigElement("send_from", "string", "",
                          "The address to send e-mail reports from", None),
            ConfigElement("send_to", "string", "",
                          "The address to send e-mail reports to", None),
            ConfigElement("server", "string", "",
                          "The SMTP server to use", None),
            ConfigElement("user", "string", "",
                          "The user name to log on the SMTP server", None),
            ConfigElement("send_from", "string", "",
                          "SMTP server password", None)]

    def __init__(self, **config):
        self.worker_inf = config['worker_infrastructure']
        self.config = config

        dexbot.storage.Storage.__init__(self, "reporter")
        if not "lastrun" in self:
            self['lastrun'] = self.lastrun = time.time()
        else:
            self.lastrun = self['lastrun']
        logging.getLogger("dexbot.per_bot").addHandler(
            dexbot.storage.SQLiteHandler())  # and log to SQLIte DB

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
        """Generate report for the past week on-the-spot"""
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
