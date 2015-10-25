__author__ = 'Daniel Dittenhafer'
__date__ = 'Oct 25, 2015'
__version__ = 1.0
# Based in part on: https://github.com/dwdii/IS602-AdvProgTech/blob/master/Lesson12/hw12_dittenhafer.ipynb

from zipline.api import order_target, record, symbol, history, add_history
from zipline.algorithm import TradingAlgorithm
from zipline.utils.factory import load_bars_from_yahoo

import matplotlib.pyplot as plt
import pandas as pd

import pytz
from datetime import datetime

mcHistoryDays = 10
mcIterations = 100
mcFutureDays = 1
eqSymbol = 'AAPL'

def initialize(context):
    add_history(mcHistoryDays, '1d', 'price')
    context.i = 0


def monteCarloIteration(mean, std, start):
    import random
    sample = list()
    for i in range(0, mcFutureDays, 1):
        sample.append(random.gauss(mean, std))

    curPrice = start
    walk = list()
    for d in sample:
        newPrice = curPrice + d
        curPrice = newPrice
        walk.append(curPrice)

    return walk[-1]

def handle_data(context, data):
    # Skip first X days to get full windows
    context.i += 1
    if context.i < mcHistoryDays:
        return

    # What day are we currently processing?
    print(context.datetime)

    sym = symbol(eqSymbol)

    # Compute averages
    # history() has to be called with the same params
    # from above and returns a pandas dataframe.
    histData = history(mcHistoryDays, '1d', 'price')
    curPrice = histData[sym][-1]

    priceDiffs = histData[sym].diff()
    meanDiff = priceDiffs.mean()
    sdDiff = priceDiffs.std()

    mcResults = list()
    for i in range(0, mcIterations, 1):
        res = monteCarloIteration(meanDiff, sdDiff, curPrice)
        mcResults.append(res)
    # Convert to a panadas series so we can use the statistics functions.
    mcResultsPd = pd.Series(mcResults)

    # What is the price we predict for tomorrow?
    # Using some summary statistic of the individual Monte Carlo iteration results.
    predictedPrice = mcResultsPd.mean()

    # Trading logic
    if predictedPrice > curPrice:
        # order_target orders as many shares as needed to
        # achieve the desired number of shares.
        order_target(sym, 100)
        #print("Buying up to 100 shares")
    elif predictedPrice < curPrice:
        order_target(sym, 0)
        #print("Selling down to 0 shares")

    # Save values for later inspection
    record(eqSymbol, data[sym].price,
           'mc_price', predictedPrice)


def analyze(context, perf):
    fig = plt.figure()
    ax1 = fig.add_subplot(211)
    perf.portfolio_value.plot(ax=ax1)
    ax1.set_ylabel('portfolio value in $')

    ax2 = fig.add_subplot(212)
    perf[eqSymbol].plot(ax=ax2)
    perf[['mc_price']].plot(ax=ax2)

    #perf_trans = perf.ix[[t != [] for t in perf.transactions]]
    #buys = perf_trans.ix[[t[0]['amount'] > 0 for t in perf_trans.transactions]]
    #sells = perf_trans.ix[
    #    [t[0]['amount'] < 0 for t in perf_trans.transactions]]
    #ax2.plot(buys.index, perf.mc_price.ix[buys.index],
    #         '^', markersize=10, color='m')
    #ax2.plot(sells.index, perf.mc_price.ix[sells.index],
    #        'v', markersize=10, color='k')
    ax2.set_ylabel('price in $')
    plt.legend(loc=0)
    plt.show()


# Load data manually from Yahoo! finance
start = datetime(2011, 1, 1, 0, 0, 0, 0, pytz.utc)
end = datetime(2012, 1, 1, 0, 0, 0, 0, pytz.utc)
data = load_bars_from_yahoo(stocks=[eqSymbol], start=start,
                            end=end)

# Create algorithm object passing in initialize and
# handle_data functions
algo_obj = TradingAlgorithm(initialize=initialize,
                            handle_data=handle_data)
# Need to manually specify the analyze in this mode of execution.
#  It would come for free if using the  run_algo.py CLI.
algo_obj._analyze = analyze


# Run algorithm
perf_manual = algo_obj.run(data)

print(perf_manual)
