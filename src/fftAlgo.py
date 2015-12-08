from zipline.algorithm import TradingAlgorithm
from zipline.transforms import MovingAverage, batch_transform
from zipline.utils.factory import load_from_yahoo
from zipline.finance import commission,slippage
from zipline.utils.factory import load_bars_from_yahoo
import pytz
from datetime import datetime
import kellyCriterion

class HighFreqFilterAlgo(TradingAlgorithm):
    """Low pass filter algorithm. (Filters out high frequencies)

    This algorithm buys or sells/shorts stock iff a
    20% price discrepancy between the market price and the
    algo's defined "true" price are detected.

    The "true" prices are determined through the help of the
    Fast Fourier Transform and a simple high-pass filter.

    """
    def initialize(self):
        # To keep track of whether we invested in the stock or not
        self.invested = False
        self.set_slippage(slippage.FixedSlippage(spread=0.0))

        self.buy_orders = []
        self.sell_orders = []

        self.tradingdays = 0

        self.i = 0
        self.kelly = kellyCriterion.KellyCriterion()
        self.mcHistoryDays = 10
        self.mcIterations = 100

        self.add_history(self.mcHistoryDays, '1d', 'price')


    def _handle_data(self, context, data):
        self.i += 1
        if self.i < self.mcHistoryDays:
            return

        runningPrices.append(data[symbol].price)
        s = runningPrices
        if(self.tradingdays > 252):

            # Add Tail buffer to stock signal
            # set a number of days to our last closing price
            # we will remove these later
            for x in range(0,1000):
                s = np.append(s, data[symbol].price)

            #get spectrum of signal with Fourier Transform
            F = fft(s)

            #filter high frequency components of signals
            dt = 1/252.0
            f = fftfreq(len(F),dt)  # get sample frequency in samples per year

            F_filt = self.getfilteredsignal(F,f)
            F_filt = np.array(F_filt)

            # take inverse FFT to get smoothed time series signal
            s_filt = ifft(F_filt)

            # Remove Tail buffer from stock signal
            for x in range(0,1000):
                s = np.delete(s, len(s)-1)
                s_filt = np.delete(s_filt, len(s_filt)-1)

            # the current "true" price according to our algo
            currSmoothedPrice = s_filt[-1]
            runningFilteredPrices.append(currSmoothedPrice)

            self.record(symbol, data[symbol].price,
               'fft_price', currSmoothedPrice)

            histData = self.history(self.mcHistoryDays, '1d', 'price')
            curPrice = histData[symbol][-1]
            priceDiffs = histData[symbol].diff()

            wagerFrac = self.kelly.WagerFraction(priceDiffs, curPrice, currSmoothedPrice)
            self.order_target_percent(symbol,wagerFrac)

        else:
            runningFilteredPrices.append(data[symbol].price)
            self.record(symbol, data[symbol].price,
               'fft_price', data[symbol].price)

        self.tradingdays = self.tradingdays +1
        print(context.portfolio.portfolio_value)

    # filter the signal with simple low pass filter
    def filter_rule(self, x,freq):
        buff = 0.05
        highCut = 0.3
        if abs(freq)> (highCut+buff):
            return 0
        else:
            return x

    # method that generates our filtered signal
    def getfilteredsignal(self, yf_noise, f):
        filteredSignal = []
        for x in range(0, len(f)):
            temp = self.filter_rule(yf_noise[x],f[x])
            filteredSignal.append(temp)

        return filteredSignal

    def analyze(context, perf):
        fig = plt.figure()
        ax1 = fig.add_subplot(211)
        perf.portfolio_value.plot(ax=ax1)
        ax1.set_ylabel('portfolio value in $')

        ax2 = fig.add_subplot(212)
        perf[symbol].plot(ax=ax2)
        perf[['fft_price']].plot(ax=ax2)

        ax2.set_ylabel('price in $')
        plt.legend(loc=0)
        plt.show()

runningPrices = []
runningFilteredPrices = []
symbol = "GS"
transactionAmt = 200
buysellthresh = 0.2 #(20%)
if __name__ == "__main__":
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    from scipy.fftpack import fft
    from scipy.fftpack import ifft
    from scipy.fftpack import fftfreq

    # load data from yahoo finance
    start = datetime(2010, 1, 1, 0, 0, 0, 0, pytz.utc)
    end = datetime(2014, 1, 1, 0, 0, 0, 0, pytz.utc)
    data = load_bars_from_yahoo(stocks=[symbol], start=start,
                                end=end)

    filtalgo = HighFreqFilterAlgo()
    results = filtalgo.run(data)

    #print(results)
    print(results.ending_value[-1])




