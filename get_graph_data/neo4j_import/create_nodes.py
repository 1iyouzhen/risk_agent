from neo4j import GraphDatabase
import pandas as pd
from pathlib import Path

"""
创建节点导入neo4j中
"""

CLEAN_PATH = Path(__file__).resolve().parents[1] / "data/cleaned"    # 保存路径
URI = "bolt://localhost:7687"
AUTH = ("your_username", "your_password")

driver = GraphDatabase.driver(URI, auth=AUTH)

def create_company_nodes(tx, row):
    # 将Pandas的row转成dict，防止Series的取值异常
    data = row.to_dict()

    # 给缺失字段设置默认值，防止 ParameterMissing
    data.setdefault("market_cap", None)
    data.setdefault("pe_ratio", None)
    data.setdefault("pb_ratio", None)
    data.setdefault("risk_score", None)

    tx.run("""
        MERGE (c:Company {symbol: $symbol})
        SET c.name = $name,
            c.price = $price,
            c.percent_change = $percent_change,
            c.high = $high,
            c.low = $low,
            c.open = $open,
            c.prev_close = $prev_close,
            c.volume = $volume,
            c.turnover = $turnover,
            c.market_cap = $market_cap,
            c.pe_ratio = $pe_ratio,
            c.pb_ratio = $pb_ratio,
            c.risk_score = $risk_score
    """, **data)


def create_market_nodes(tx, row):
    data = row.to_dict()

    # 根据实际列构建动态Cypher属性设置
    props = []
    for key in data.keys():
        if key != "code":  # code用作唯一索引，不重复设置
            props.append(f"m.{key} = ${key}")
    cypher = f"""
        MERGE (m:MarketIndex {{code: $code}})
        SET {', '.join(props)}
    """
    tx.run(cypher, **data)


def create_news_nodes(tx, row):
    tx.run("""
        MERGE (n:News {title: $title})
        SET n.sentiment = $sentiment,
            n.score = $score
    """, **row.to_dict())


def main():
    with driver.session() as session:
        df_company = pd.read_csv(CLEAN_PATH / "company_clean.csv")
        df_market = pd.read_csv(CLEAN_PATH / "market_index_clean.csv")
        df_news = pd.read_csv(CLEAN_PATH / "news_clean.csv")

        print("开始导入Company节点...")
        for _, row in df_company.iterrows():
            session.execute_write(create_company_nodes, row)

        print("开始导入MarketIndex节点...")
        for _, row in df_market.iterrows():
            session.execute_write(create_market_nodes, row)

        print("开始导入News节点...")
        for _, row in df_news.iterrows():
            session.execute_write(create_news_nodes, row)

    print("所有节点已成功导入Neo4j！")


if __name__ == "__main__":
    main()

