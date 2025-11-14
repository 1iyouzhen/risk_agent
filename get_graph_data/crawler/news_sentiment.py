import requests
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
from textblob import TextBlob

RAW_PATH = Path(__file__).resolve().parents[1] / "data/raw"

def fetch_financial_news():
    """
    爬取新浪财经新闻标题并做简单情感分析
    """
    url = "https://finance.sina.com.cn/stock/"
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    res.encoding = res.apparent_encoding  # 自动识别网页编码

    soup = BeautifulSoup(res.text, "html.parser")

    titles = [a.text.strip() for a in soup.select("a") if len(a.text.strip()) > 10][:100]
    news_data = []

    for title in titles:
        sentiment = TextBlob(title).sentiment.polarity
        if sentiment > 0.05:
            label = "positive"
        elif sentiment < -0.05:
            label = "negative"
        else:
            label = "neutral"

        news_data.append({"title": title, "sentiment": label, "score": round(sentiment, 3)})

    df = pd.DataFrame(news_data)
    RAW_PATH.mkdir(parents=True, exist_ok=True)
    df.to_csv(RAW_PATH / "news_sentiment.csv", index=False, encoding="utf-8-sig")  # Excel打开不乱码
    print(f"news_sentiment.csv saved! 共 {len(df)} 条新闻")

if __name__ == "__main__":
    fetch_financial_news()
