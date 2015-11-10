__author__ = 'TBD'


class KellyCriterion:

    def __init__(self):
        self.initialized = True

    def DetermineProbability(self, historyDiffs):

        ups = 0.0
        for d in historyDiffs:
                ups += (d > 0)

        return ups / historyDiffs.shape[0]

    def WagerFraction(self, historyDiffs, curPrice, predictedPrice):
        """
        https://en.wikipedia.org/wiki/Kelly_criterion
        :param historyDiffs:
        :param curPrice:
        :param predictedPrice:
        :return: The fraction of the bank roll to wagers
        """
        p = self.DetermineProbability(historyDiffs)
        q = 1 - p
        b = (predictedPrice - curPrice) / curPrice
        f = ((b * p) - q) / b
        return f