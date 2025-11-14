# File: src/agent/storage.py
"""
Optimized Storage (sqlite) compatible with existing schema and batch embedding.
"""
import sqlite3
import json
import os

class Storage:
    def __init__(self, path):
        self.path = path
        d = os.path.dirname(path)
        if d and not os.path.exists(d):
            os.makedirs(d, exist_ok=True)

    def connect(self):
        return sqlite3.connect(self.path)

    def init(self):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id TEXT,
                timestamp TEXT,
                risk_score REAL,
                decision TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                assessment_id INTEGER,
                report_text TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS features (
                assessment_id INTEGER,
                feature_name TEXT,
                value REAL,
                contribution REAL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                assessment_id INTEGER,
                terms TEXT,
                vector TEXT
            )
        """)
        conn.commit()
        conn.close()

    # basic operations
    def save_assessment(self, entity_id, timestamp, risk_score, decision):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO assessments(entity_id, timestamp, risk_score, decision) VALUES(?,?,?,?)",
            (entity_id, timestamp, risk_score, decision)
        )
        conn.commit()
        aid = cur.lastrowid
        conn.close()
        return aid

    def update_decision(self, assessment_id, decision):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("UPDATE assessments SET decision=? WHERE id= ?", (decision, assessment_id))
        conn.commit()
        conn.close()

    # reports
    def save_report(self, assessment_id, text):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("INSERT INTO reports(assessment_id, report_text) VALUES(?,?)", (assessment_id, text))
        conn.commit()
        conn.close()

    def update_report(self, assessment_id, text):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("UPDATE reports SET report_text=? WHERE assessment_id=?", (text, assessment_id))
        conn.commit()
        conn.close()

    def get_report(self, assessment_id):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("SELECT report_text FROM reports WHERE assessment_id=?", (assessment_id,))
        row = cur.fetchone()
        conn.close()
        return row[0] if row else ""

    def get_reports(self, ids):
        if not ids:
            return []
        conn = self.connect()
        cur = conn.cursor()
        q = f"SELECT report_text FROM reports WHERE assessment_id IN ({','.join([str(i) for i in ids])})"
        cur.execute(q)
        rows = cur.fetchall()
        conn.close()
        return [r[0] for r in rows]

    # embeddings
    def save_embedding(self, assessment_id, terms, vector):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("INSERT INTO embeddings(assessment_id, terms, vector) VALUES(?,?,?)", (assessment_id, terms, vector))
        conn.commit()
        conn.close()

    def save_embeddings_batch(self, items):
        # items: list of tuples (assessment_id, terms_json, vector_json)
        if not items:
            return
        conn = self.connect()
        cur = conn.cursor()
        cur.executemany("INSERT INTO embeddings(assessment_id, terms, vector) VALUES(?,?,?)", items)
        conn.commit()
        conn.close()

    def get_all_embeddings(self):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("SELECT assessment_id, terms, vector FROM embeddings")
        rows = cur.fetchall()
        conn.close()
        return rows

    def clear_embeddings(self):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("DELETE FROM embeddings")
        conn.commit()
        conn.close()

    def count_embeddings(self):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM embeddings")
        n = cur.fetchone()[0]
        conn.close()
        return n


