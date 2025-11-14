
import pandas as pd
from pathlib import Path
import json

RAW_PATH = Path(__file__).resolve().parents[1] / "data/raw"
CLEAN_PATH = Path(__file__).resolve().parents[1] / "data/raw"

def clean_all():
    # 读取JSON并转DataFrame
    json_file = RAW_PATH / "company_info.json"
    if json_file.exists():
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        df_company = pd.DataFrame(data)
        print(f"Loaded {len(df_company)} records from company_info.json")
    else:
        print("company_info.json not found!")
        return

    # 可以选择性地清洗
    df_company = df_company.drop_duplicates(subset=["symbol"])
    df_company = df_company.fillna("未知")

    # 保存为 CSV
    CLEAN_PATH.mkdir(parents=True, exist_ok=True)
    df_company.to_csv(CLEAN_PATH / "company_info.csv", index=False, encoding="utf-8-sig")
    print(f"Cleaned company_info.csv saved to {CLEAN_PATH}")

if __name__ == "__main__":
    clean_all()
