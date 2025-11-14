from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "123456lyz")

driver = GraphDatabase.driver(URI, auth=AUTH)

def create_relationships(tx):
    # 假设所有公司都与上证指数相关
    tx.run("""
        MATCH (c:Company), (m:MarketIndex {name: "上证指数"})
        MERGE (c)-[:LINKED_TO_INDEX {correlation: 0.7}]->(m)
    """)

    # 将新闻连接到随机公司
    tx.run("""
        MATCH (n:News {sentiment: "negative"}), (c:Company)
        WITH n, c LIMIT 10
        MERGE (c)-[:HAS_RISK_EVENT {impact: "high"}]->(n)
    """)

    tx.run("""
        MATCH (n:News {sentiment: "neutral"}), (c:Company)
        WITH n, c LIMIT 10
        MERGE (c)-[:HAS_RISK_EVENT {impact: "high"}]->(n)
    """)

    tx.run("""
        MATCH (n:News {sentiment: "positive"}), (c:Company)
        WITH n, c LIMIT 10
        MERGE (c)-[:HAS_RISK_EVENT {impact: "high"}]->(n)
    """)

def main():
    with driver.session() as session:
        session.execute_write(create_relationships)
    print("关系已建立完成！")

if __name__ == "__main__":
    main()
