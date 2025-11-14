import os
import csv


class GraphClient:
    def __init__(self, dir_path):
        self.dir_path = dir_path
        self.edges = []
        self._load()

    def _load(self):
        fp = os.path.join(self.dir_path, "relations.csv")
        if not os.path.isfile(fp):
            return
        with open(fp, "r", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                self.edges.append(row)

    def neighbors(self, src_type, src_id):
        res = []
        for e in self.edges:
            if e.get("src_type") == src_type and e.get("src_id") == src_id:
                res.append(e)
        return res

    def describe_account(self, account_id, limit=5):
        items = self.neighbors("Account", account_id)
        out = []
        for e in items[:limit]:
            out.append(f"{e.get('src_type')}:{e.get('src_id')} -[{e.get('rel')}]→ {e.get('dst_type')}:{e.get('dst_id')}")
        return out

    def describe_company(self, symbol, limit=5):
        items = self.neighbors("Company", symbol)
        out = []
        for e in items[:limit]:
            out.append(f"{e.get('src_type')}:{e.get('src_id')} -[{e.get('rel')}]→ {e.get('dst_type')}:{e.get('dst_id')}")
        return out
