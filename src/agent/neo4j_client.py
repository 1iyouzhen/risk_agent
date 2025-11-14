from .neo4j_config import get_neo4j_config

class Neo4jClient:
    def __init__(self, uri=None, user=None, password=None):
        if not uri or not user or not password:
            uri, user, password = get_neo4j_config()
        self.driver = None
        try:
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(uri, auth=(user, password)) if uri else None
        except Exception:
            self.driver = None

    def available(self):
        return self.driver is not None

    def close(self):
        if self.driver:
            self.driver.close()

    def upsert_relation(self, src_type, src_id, rel, dst_type, dst_id):
        if not self.driver:
            return
        q = (
            "MERGE (a:" + src_type + " {id:$src_id}) "
            "MERGE (b:" + dst_type + " {id:$dst_id}) "
            "MERGE (a)-[r:REL {type:$rel}]->(b) "
        )
        try:
            with self.driver.session() as s:
                s.run(q, src_id=src_id, dst_id=dst_id, rel=rel)
        except Exception:
            pass

    def describe_account(self, account_id, limit=5):
        if not self.driver:
            return []
        q = "MATCH (a:Account {id:$id})-[r:REL]->(b) RETURN labels(b) as labels, b.id as bid, r.type as rel LIMIT $lim"
        out = []
        try:
            with self.driver.session() as s:
                res = s.run(q, id=account_id, lim=limit)
                for r in res:
                    labels = r["labels"]
                    lab = labels[0] if labels else "Node"
                    out.append(f"Account:{account_id} -[{r['rel']}]→ {lab}:{r['bid']}")
        except Exception:
            return out
        return out

    def describe_company(self, symbol, limit=5):
        if not self.driver:
            return []
        out = []
        try:
            with self.driver.session() as s:
                q1 = "MATCH (c:Company {symbol:$symbol})-[r:LINKED_TO_INDEX]->(m:MarketIndex) RETURN m.name as name, r.correlation as corr LIMIT $lim"
                res1 = s.run(q1, symbol=symbol, lim=limit)
                for r in res1:
                    name = r.get("name", "Index")
                    corr = r.get("corr", "")
                    out.append(f"Company:{symbol} -[LINKED_TO_INDEX corr={corr}]→ MarketIndex:{name}")
                q2 = "MATCH (c:Company {symbol:$symbol})-[r:HAS_RISK_EVENT]->(n:News) RETURN n.title as title, r.impact as impact LIMIT $lim"
                res2 = s.run(q2, symbol=symbol, lim=limit)
                for r in res2:
                    title = r.get("title", "News")
                    impact = r.get("impact", "")
                    out.append(f"Company:{symbol} -[HAS_RISK_EVENT impact={impact}]→ News:{title}")
        except Exception:
            return out
        return out
