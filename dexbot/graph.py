"""
A graph utility module

Currently temporary comand-line interface for demo purposes

python3 -m dexbot.graph <botname> <period> <quote> <base>
botname: name of bot in the config
period: time to graph, number followed by unit, "d" days "w" weeks,
  so 4d = 4 days, 2w = two weeks
quote: symbol of quote unit
base: symbol of base unit

Prints out the name of a .png file containing the graph

Graphs convert the base amounts into quote, using the final price,
and then graph these two plus their total.

This conversion is to try to factor out capital gains/losses over the graphed
period (which usually swamp bot profits)

In the long run
- some API to access from the GUI: need to discuss with GUI devs
- CLI will generate HTML reports with graphs and e-mail to the user at regular intervals
"""

from dexbot import storage
from os.path import join
import os
import tempfile
import sys
import numpy

import datetime
import time
import matplotlib
matplotlib.use('AGG')  # anti-Grain Geometry: the backend for PNG files
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def query_to_dicts(rows):
    """Translate SQLAlchemy rows result (from Journal) into
    dictionary keyed by datetime, of dictionaries keyed by 'key' value
    values are 'amount' field.
    """
    by_dates = {}
    for i in rows:
        if not i.stamp in by_dates:
            by_dates[i.stamp] = {}
        by_dates[i.stamp][i.key] = i.amount
    return by_dates


def apply_dicts_to_graph(plot, data):
    """
    Graph a dictionary of dictionaries originally from query_to_dicts
    (possibly with intervening modifications)
    """
    dates = sorted(list(data.keys()))
    all_keys = list(data[dates[0]].keys())
    for k in all_keys:
        ydata = [data[d][k] for d in dates]
        plot.plot(dates, ydata, label=k)
    plot.set_xlim(min(dates), max(dates))


def do_graph(data):
    """Take some data orignally from query_to_dicts
    (possibly modified), and produce a graph
    Returns: path to temporary file
    """
    # from originally the examples in the matplotlib docs
    daylocator = mdates.DayLocator()
    daysFmt = mdates.DateFormatter('%b %d')

    fig, ax = plt.subplots()

    apply_dicts_to_graph(ax, data)
    # format the ticks
    ax.xaxis.set_major_locator(daylocator)
    ax.xaxis.set_major_formatter(daysFmt)

    # format the coords message box
    def price(x):
        return '$%1.2f' % x
    #ax.format_xdata = mdates.DateFormatter('%Y-%m-%d')
    ax.format_ydata = price
    ax.grid(True)
    ax.legend()
    # rotates and right aligns the x labels, and moves the bottom of the
    # axes up to make room for them
    fig.autofmt_xdate()

    fd, plotfile = tempfile.mkstemp(suffix='.png')
    os.close(fd)
    plt.savefig(plotfile, bbox_inches='tight')
    return plotfile


def rebase_data(data, quote, base):
    """Take some data and rebase it in the quote unit using the final price
    (NOT the price when the tranaction occurred) and add a total amount
    The point here is to try to factor out capital changes and isolate out
    bot profits/losses
    """
    last = max(data.keys())
    finalprice = data[last]['price']

    def process(v):
        n = {quote: v[quote], base: v[base] / finalprice}
        n['total'] = n[quote] + n[base]
        return n
    return {k: process(v) for k, v in data.items()}


if __name__ == '__main__':
    botname = sys.argv[1]
    start = sys.argv[2]
    quote = sys.argv[3]
    base = sys.argv[4]
    s = storage.Storage(botname)
    data = query_to_dicts(s.query_journal(start))
    data = rebase_data(data, quote, base)
    print(do_graph(data))
