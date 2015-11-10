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

import kellyCriterion


class MonteCarloTradingAlgorithm(TradingAlgorithm):


    def initialize(self):

        self.i = 0
        self.kelly = kellyCriterion.KellyCriterion()
        self.mcHistoryDays = 10
        self.mcIterations = 100

        # The number of days in the future to simulate
        self.mcFutureDays = 1

        self.add_history(self.mcHistoryDays, '1d', 'price')
        # Need to manually specify the analyze in this mode of execution.
        #  It would come for free if using the  run_algo.py CLI.
        #self._analyze = self.analyze



    def monteCarloIteration(self, mean, std, start):
        import random
        sample = list()
        for i in range(0, self.mcFutureDays, 1):
            sample.append(random.gauss(mean, std))

        curPrice = start
        walk = list()
        for d in sample:
            newPrice = curPrice + d
            curPrice = newPrice
            walk.append(curPrice)

        return walk[-1]

    def _handle_data(self, context, data):
        """
        Overloading the _handle_data method. It must be _handle_data (with leading underscore), not handle_data,
        in order to take advantage of base class's history container auto updates, which we use in the history call below.
        :param context: TradingAlogorithm base class passes in an extra self so we are calling this context
        :param data: The data.
        :return:
        """
        # Skip first X days to get full windows
        self.i += 1
        if self.i < self.mcHistoryDays:
            return

        # What day are we currently processing?
        print(self.datetime)

        sym = symbol(eqSymbol)

        # Compute averages
        # history() has to be called with the same params
        # from above and returns a pandas dataframe.
        histData = self.history(self.mcHistoryDays, '1d', 'price')
        curPrice = histData[sym][-1]

        priceDiffs = histData[sym].diff()
        meanDiff = priceDiffs.mean()
        sdDiff = priceDiffs.std()

        mcResults = list()
        for i in range(0, self.mcIterations, 1):
            res = self.monteCarloIteration(meanDiff, sdDiff, curPrice)
            mcResults.append(res)
        # Convert to a panadas series so we can use the statistics functions.
        mcResultsPd = pd.Series(mcResults)

        # What is the price we predict for tomorrow?
        # Using some summary statistic of the individual Monte Carlo iteration results.
        predictedPrice = mcResultsPd.mean()


        wagerFrac = self.kelly.WagerFraction(priceDiffs, curPrice, predictedPrice)
        shares = (self.portfolio.cash * wagerFrac) / curPrice
        #low = mcResultsPd.min()
        #high = mcResultsPd.max()
        #expLoss = curPrice - low
        #expGain = high - curPrice
        #diff = (predictedPrice - curPrice) / curPrice;

        # Trading logic
        if shares > 0:
            # order_target orders as many shares as needed to
            # achieve the desired number of shares.
            self.order(sym, shares)
            #print("Buying up to 100 shares")

        # Save values for later inspection
        self.record(eqSymbol, data[sym].price,
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

if __name__ == "__main__":
    # Load data manually from Yahoo! finance
    eqSymbol = 'AAPL'
    start = datetime(2011, 1, 1, 0, 0, 0, 0, pytz.utc)
    end = datetime(2012, 1, 1, 0, 0, 0, 0, pytz.utc)
    data = load_bars_from_yahoo(stocks=[eqSymbol], start=start,
                                end=end)

    # Create algorithm object
    algo_obj = MonteCarloTradingAlgorithm()


    # Run algorithm
    perf_manual = algo_obj.run(data)

    print(perf_manual)
