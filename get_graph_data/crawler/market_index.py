# financial_risk_kg/crawler/market_index.py
import requests
import pandas as pd
import time
import random
from pathlib import Path

RAW_PATH = Path(__file__).resolve().parents[1] / "data/raw"

def fetch_all_indices(max_pages=5):
    """
    从东方财富爬取全部主要市场指数（含上证、深证、行业、概念等）
    """
    url = "https://push2.eastmoney.com/api/qt/clist/get"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://quote.eastmoney.com/",
    }

    params = {
        "pn": "1",          # 页码
        "pz": "50",         # 每页爬取相关信息的数量
        "po": "1",
        "np": "1",
        "fltt": "2",
        "fid": "f3",
        "invt": "2",
        "fs": "m:1+t:2",    # 指数市场（m:1 表示指数）
        "fields": "f12,f13,f14,f2,f3,f4,f5,f6,f7,f8,f9,f10,f15,f16,f17,f18,f20,f21,f23",
        "order_by": "f3",
    }

    all_indices = []

    for page in range(1, max_pages + 1):
        params["pn"] = str(page)
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            data = resp.json().get("data", {})
            diff = data.get("diff", [])
            if not diff:
                print(f"第 {page} 页为空，停止。")
                break

            for d in diff:
                all_indices.append({
                    "code": f"{d.get('f12')}.{d.get('f13')}",
                    "name": d.get("f14"),
                    "price": d.get("f2"),
                    "percent_change": d.get("f3"),
                    "change_amount": d.get("f4"),
                    "volume": d.get("f5"),
                    "turnover": d.get("f6"),
                    "amplitude": d.get("f7"),
                    "high": d.get("f15"),
                    "low": d.get("f16"),
                    "open": d.get("f17"),
                    "prev_close": d.get("f18"),
                })

            print(f"第 {page} 页，共 {len(diff)} 条指数数据")
            time.sleep(random.uniform(1, 2))
        except Exception as e:
            print(f"第 {page} 页请求失败：{e}")
            continue

    # 保存数据
    RAW_PATH.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(all_indices)
    df.to_csv(RAW_PATH / "market_index_all.csv", index=False, encoding="utf-8-sig")

    print(f"\n共获取 {len(df)} 条指数行情数据，已保存到 data/raw/market_index_all.csv")

if __name__ == "__main__":
    fetch_all_indices(max_pages=10)  # 可调整页数
