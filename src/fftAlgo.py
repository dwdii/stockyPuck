from zipline.algorithm import TradingAlgorithm
from zipline.transforms import MovingAverage, batch_transform
from zipline.utils.factory import load_from_yahoo
from zipline.finance import commission,slippage

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

        self.set_commission(commission.PerTrade(cost=0))
        self.set_slippage(slippage.FixedSlippage(spread=0.0))

        self.buy_orders = []
        self.sell_orders = []

        self.tradingdays = 0;

    def handle_data(self, data):
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

            s_filt = ifft(F_filt)

            # Remove Tail buffer from stock signal
            for x in range(0,1000):
                s = np.delete(s, len(s)-1)
                s_filt = np.delete(s_filt, len(s_filt)-1)

            # the current "true" price according to our algo
            currSmoothedPrice = s_filt[-1]
            runningFilteredPrices.append(currSmoothedPrice)

            # if there are 20% discrepancies between the market price and the "true"
            # price, buy or sell/short accordingly
            if (data[symbol].price / (1+buysellthresh) > currSmoothedPrice):
                self.order(symbol, -transactionAmt) # if no stock owned, a negative order will short the stock
                self.invested = False
                self.sell_orders.append(data[symbol].datetime)
                print "{dt}: Selling {amt} shares.".format(dt=data[symbol].datetime, amt=transactionAmt)
            elif (data[symbol].price * (1+buysellthresh) < currSmoothedPrice):
                self.order(symbol, transactionAmt)
                self.invested = True
                self.buy_orders.append(data[symbol].datetime)
                print "{dt}: Buying {amt} shares.".format(dt=data[symbol].datetime, amt=transactionAmt)

        else:
            runningFilteredPrices.append(data[symbol].price)

        self.tradingdays = self.tradingdays +1

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

runningPrices = []
runningFilteredPrices = []
symbol = "AAPL"
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
    data = load_from_yahoo(stocks=[symbol]);

    filtalgo = HighFreqFilterAlgo()
    results = filtalgo.run(data)

    # plot chart showing the actual signal vs the alogo's
    # best guess at the time of the stock's underlying "true"
    # price
    plt.plot(runningFilteredPrices)
    plt.plot(runningPrices)
    plt.legend(['Filtered Signal','Original Signal'])
    plt.show()

    fig = plt.figure()
    ax1 = plt.subplot(211)
    ax1.set_title("Results: Buy and Sell/Short Orders")
    data[symbol].plot(ax=ax1)
    plt.plot(filtalgo.buy_orders, data[symbol].ix[filtalgo.buy_orders], '^', c='m', markersize=10, label='buy')
    plt.plot(filtalgo.sell_orders, data[symbol].ix[filtalgo.sell_orders], 'v', c='k', markersize=10, label='sell/short')
    plt.legend(loc=0)

    ax2 = plt.subplot(212)
    ax2.set_title("Portfolio Value ($)")
    results.portfolio_value.plot(ax=ax2)

    fig.tight_layout()
    plt.show()




