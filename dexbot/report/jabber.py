#!/usr/bin/python3

import sleekxmpp
import time
import os
import logging
import threading
import dexbot.report.chat
from dexbot.basestrategy import ConfigElement

import pudb


class Reporter(sleekxmpp.ClientXMPP, dexbot.report.chat.ChatReporter):

    """
    A Reporter for Jabber/XMPP
    """

    @classmethod
    def configure(kls):
        return [
            ConfigElement("recipient", "string", "",
                          "The Jabber ID to send updates to", None),
            ConfigElement("jid", "string", "",
                          "The Jabber ID to send updates from (i.e. the bot's own ID)", None),
            ConfigElement("password", "string", "",
                          "The the bot's password", None),
            ConfigElement("commands", "bool", False,
                          "Set to allow bot to receive commands. UNDERSTAND SECURITY IMPLICATIONS FIRST", None)]

    def __init__(self, recipient, jid, password, worker_infrastructure, commands=False):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)
        # The session_start event will be triggered when
        # the bot establishes its connection with the server
        # and the XML streams are ready for use. We want to
        # listen for this event so that we we can initialize
        # our roster.
        self.recipient = recipient
        self.add_event_handler("session_start", self.start, threaded=True)
        self.add_event_handler('message', self.message)
        self.register_plugin('xep_0030')  # Service Discovery
        self.register_plugin('xep_0199')  # XMPP Ping
        self.jabber_ready = threading.Event()
        self.commands = commands
        dexbot.report.chat.ChatReporter.__init__(self, worker_infrastructure)
        assert self.connect(use_tls=True), "failed to connect to Jabber"
        self.process(block=False)

    def start(self, event):
        self.send_presence()
        self.get_roster()
        self.jabber_ready.set()

    def __del__(self):
        self.shutdown()

    def shutdown(self):
        sleekxmpp.ClientXMPP.disconnect(self)

    def send_message(self, message, worker_name='N/A', level=logging.INFO, reply_ref=None):
        assert self.jabber_ready.wait(120), "Jabber not ready in reasonable time"
        if worker_name != 'N/A':
            message = "[{}]: {}".format(worker_name, message)
        if reply_ref:
            reply_ref.reply(message).send()
        else:
            sleekxmpp.ClientXMPP.send_message(self, mto=self.recipient,
                                              mbody=message,
                                              mtype='chat')

    def message(self, msg):
        if msg['type'] in ('chat', 'normal'):
            if msg['from'].bare == self.recipient and self.commands:
                self.receive_message(str(msg['body']), reply_ref=msg)
            else:
                if msg['to'].bare != msg['from'].bare:
                    self.send_message("Go away", reply_ref=msg)


if __name__ == '__main__':
    r = Reporter("ian@jabber.twilightparadox.com", "bot@jabber.twilightparadox.com",
                 os.environ['JABBER_PASSWORD'], None)
    r.send_message("hello python 6")
    time.sleep(1)
    r.disconnect()
