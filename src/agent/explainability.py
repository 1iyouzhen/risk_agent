def explain_contributions(x):
    w = {
        "amount": 0.002,
        "income": -0.00003,
        "credit_score": -0.0025,
        "delinquencies": 0.08,
        "market_index": 0.0002,
    }
    c = {}
    for k, wt in w.items():
        v = float(x.get(k, 0.0))
        c[k] = wt * v
    return c

