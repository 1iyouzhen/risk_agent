import csv
from datetime import datetime, timedelta
import random


FEATURES = ["amount", "income", "credit_score", "delinquencies", "market_index"]


def load_csv(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)
    return rows


def to_float(x, k):
    v = x.get(k, 0)
    try:
        return float(v)
    except Exception:
        return 0.0


def build_samples(rows):
    X = []
    y = []
    for row in rows:
        xi = [to_float(row, k) for k in FEATURES]
        X.append(xi)
        y.append(int(row.get("label", 0)))
    return X, y


def generate_synthetic(entity_count=50, periods=24, seed=42):
    random.seed(seed)
    data = []
    start = datetime(2023, 1, 1)
    for e in range(entity_count):
        entity_id = f"E{e+1}"
        date = start
        base_income = random.randint(3000, 15000)
        base_credit = random.randint(550, 750)
        delinquency = 0
        market = 1000
        for i in range(periods):
            amount = max(0, random.gauss(800, 250))
            income = base_income + random.randint(-500, 500)
            credit_score = max(300, min(850, base_credit + random.randint(-20, 20)))
            if random.random() < 0.15:
                delinquency = min(10, delinquency + 1)
            else:
                delinquency = max(0, delinquency - 1)
            market_index = market + random.randint(-30, 30)
            risk_linear = 0.002*amount -0.00003*income -0.0025*credit_score +0.08*delinquency +0.0002*market_index
            label = 1 if risk_linear > 0.7 else 0
            data.append({
                "entity_id": entity_id,
                "timestamp": date.strftime("%Y-%m-%d"),
                "amount": float(f"{amount:.2f}"),
                "income": income,
                "credit_score": credit_score,
                "delinquencies": delinquency,
                "market_index": market_index,
                "label": label,
            })
            date += timedelta(days=30)
    return data


def write_csv(path, rows):
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)

def ensure_entity_ids_consistent(rows, valid_symbols=None):
    if not valid_symbols:
        return rows
    out = []
    for r in rows:
        eid = r.get("entity_id")
        if eid in valid_symbols:
            out.append(r)
    return out
