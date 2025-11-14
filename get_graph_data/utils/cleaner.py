import pandas as pd
from pathlib import Path

RAW_PATH = Path(__file__).resolve().parents[1] / "data/raw"
CLEAN_PATH = Path(__file__).resolve().parents[1] / "data/cleaned"

def clean_all():
    CLEAN_PATH.mkdir(parents=True, exist_ok=True)

    # 1. 公司信息
    df_company = pd.read_csv(RAW_PATH / "company_info.csv")
    df_company = df_company.drop_duplicates(subset=["symbol"])
    df_company.to_csv(CLEAN_PATH / "company_clean.csv", index=False)

    # 2. 市场指数
    df_index = pd.read_csv(RAW_PATH / "market_index_all.csv")
    df_index = df_index.dropna()
    df_index.to_csv(CLEAN_PATH / "market_index_clean.csv", index=False)

    # 3. 新闻
    df_news = pd.read_csv(RAW_PATH / "news_sentiment.csv")
    df_news = df_news.drop_duplicates(subset=["title"])
    df_news.to_csv(CLEAN_PATH / "news_clean.csv", index=False)

    print("所有文件清洗完成并保存到 data/cleaned/")

if __name__ == "__main__":
    clean_all()
