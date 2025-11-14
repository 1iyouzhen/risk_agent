import math


class RiskForecaster:
    def __init__(self):
        self.w = {
            "amount": 0.002,
            "income": -0.00003,
            "credit_score": -0.0025,
            "delinquencies": 0.08,
            "market_index": 0.0002,
        }

    def score(self, x):
        s = 0.0
        for k, w in self.w.items():
            v = float(x.get(k, 0.0))
            s += w * v
        z = max(-10, min(10, s))
        return 1.0 / (1.0 + math.exp(-z))

