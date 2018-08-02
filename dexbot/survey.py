#!/usr/bin/python3 -u
from bitshares.notify import Notify
from bitshares.market import Market
from bitshares.price import FilledOrder
from bitshares.account import Account
from bitshares.amount import Amount
from bitshares.price import Price, Order, FilledOrder

import pdb
import requests, json, time, math, os.path, threading
from bitshares import BitShares


bitshares = BitShares()
#with open(os.path.expanduser("~/bts-passphrase.txt"),"r") as fd:
#    passphrase = fd.read().strip()
#bitshares.wallet.unlock(passphrase)

buys = {}
sells = {}

with open(os.path.expanduser("~/users.txt"),"r") as fd:
    for l in fd.readlines():
        bts_id = l.strip()
        acct = Account(bts_id)
        for o in acct.openorders:
            buy_sym = o['quote']['symbol']
            buy_amt = o['quote']['amount']
            sell_sym = o['base']['symbol']
            sell_amt = o['base']['amount']
            if buy_sym not in buys:
                buys[buy_sym] = 0.0
            buys[buy_sym] += buy_amt
            if sell_sym not in sells:
                sells[sell_sym] = 0.0
            sells[sell_sym] += sell_amt

buys = sorted(list(buys.items()), key=lambda x: -x[1])[:10]
sells = sorted(list(sells.items()), key=lambda x: -x[1])[:10]

print("""
<!--#set var="title" value="DEXBot Statistics" -->
<!--#include virtual="header.shtml" -->
<h3>Total Buy Orders</h3>
<table>
<tr><th>Asset</th><th>Amount</th></tr>
""")
for i in buys:
    print("<tr><td>{}</td><td>{}</td></tr>".format(*i))
print("""</table>
<h3>Total Sell Orders</h3>
<table>
<tr><th>Asset</th><th>Amount</th></tr>
""")
for i in sells:
    print("<tr><td>{}</td><td>{}</td></tr>".format(*i))
print("""</table>
<!--#include virtual="footer.shtml" -->
""")
          
