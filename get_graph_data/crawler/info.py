# financial_risk_kg/crawler/company_info.py
import os
import json
import time
import random
import requests

def fetch_company_info():
    """获取上市公司基础信息"""
    url = "https://push2.eastmoney.com/api/qt/clist/get"

    params = {
        "pn": "1",             # 页码
        "pz": "50",            # 每页条数
        "po": "1",
        "np": "1",
        "fltt": "2",
        "invt": "2",
        "fid": "f3",
        "fs": "m:0+t:6,m:0+t:13",   # A股主板+科创板
        "fields": "f12,f14,f2,f3,f15,f16,f17,f18,f20,f21,f22,f23,f24,f25",
        "order_by": "f3",      # 排序字段，接口要求
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://quote.eastmoney.com/",
        "Accept": "application/json,text/plain,*/*"
    }

    all_data = []
    page = 1

    while True:
        params["pn"] = str(page)
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        data = resp.json()

        if "data" not in data or "diff" not in data["data"]:
            print("返回数据结构异常，接口可能改版。")
            print(data)
            break

        diff = data["data"]["diff"]
        if not diff:
            break

        for d in diff:
            try:
                company = {
                    "symbol": d.get("f12"),
                    "name": d.get("f14"),
                    "price": d.get("f2"),
                    "percent_change": d.get("f3"),
                    "high": d.get("f15"),
                    "low": d.get("f16"),
                    "open": d.get("f17"),
                    "prev_close": d.get("f18"),
                    "volume": d.get("f20"),
                    "turnover": d.get("f21"),
                }
                all_data.append(company)
            except Exception as e:
                print("跳过异常条目：", e)

        print(f"第 {page} 页，共 {len(diff)} 条")
        page += 1
        time.sleep(random.uniform(1, 2))

        if page > 3:  # 限制页数防止被封
            break

    # 保存到 JSON 文件
    save_path = os.path.join(os.path.dirname(__file__), "../data/raw/company_info.json")
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"已保存 {len(all_data)} 条公司信息到 {save_path}")

if __name__ == "__main__":
    fetch_company_info()

