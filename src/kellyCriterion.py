__author__ = 'TBD'


class KellyCriterion:

    def __init__(self):
        self.initialized = True

    def DetermineProbability(self, historyDiffs, predictedPrice, curPrice):

        if(predictedPrice > curPrice):
            ups = 0.0
            for d in historyDiffs:
                    ups += (d < -1*(predictedPrice - curPrice))
            return 1-ups / historyDiffs.shape[0]
        else:
            ups = 0.0
            for d in historyDiffs:
                    ups += (d > (curPrice - predictedPrice))
            return 1-ups / historyDiffs.shape[0]

    def WagerFraction(self, historyDiffs, curPrice, predictedPrice):
        """
        https://en.wikipedia.org/wiki/Kelly_criterion
        :param historyDiffs:
        :param curPrice:
        :param predictedPrice:
        :return: The fraction of the bank roll to wagers
        """

        p = self.DetermineProbability(historyDiffs, predictedPrice, curPrice)
        q = 1 - p
        b = (predictedPrice - curPrice) / curPrice
        f = ((b * p) - q) / b

        # limit long and short leverage
        if(f > 2.5):
            f = 2.5
        elif (f < -2.5):
            f = -2.5

        return f