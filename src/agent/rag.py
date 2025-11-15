
"""
RAG utilities: unified embedding provider, sparse/dense helpers, retrieval that is compatible with Storage.
"""
import json
import math
import requests
from typing import List, Dict, Optional
from collections import Counter
from src.agent.config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_EMBED_MODEL, EMBED_PROVIDER, BAAI_MODEL, EMBED_PREFIX_ENABLED

# sparse helpers
def build_terms(text: str) -> Dict[str, int]:
    if not text:
        return {}
    words = []
    for w in text.lower().split():
        w2 = ''.join([c for c in w if c.isalnum()])
        if w2:
            words.append(w2)
    tf = {}
    for w in words:
        tf[w] = tf.get(w, 0) + 1
    return tf


def embed_text(terms: Dict[str, int]) -> Dict[str, float]:
    total = sum(terms.values())
    if total == 0:
        return {}
    return {k: v / total for k, v in terms.items()}


def cosine_sparse(a: Dict[str, float], b: Dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    s = 0.0
    for k, v in a.items():
        if k in b:
            s += v * b[k]
    na = math.sqrt(sum([v * v for v in a.values()]))
    nb = math.sqrt(sum([v * v for v in b.values()]))
    if na == 0 or nb == 0:
        return 0.0
    return s / (na * nb)


def cosine_dense(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    s = 0.0
    na = 0.0
    nb = 0.0
    for va, vb in zip(a, b):
        s += va * vb
        na += va * va
        nb += vb * vb
    if na == 0 or nb == 0:
        return 0.0
    return s / (math.sqrt(na) * math.sqrt(nb))


# Embedding provider
class EmbeddingProvider:
    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or (EMBED_PROVIDER if EMBED_PROVIDER else ("openai" if OPENAI_API_KEY else "local"))
        self.openai_key = OPENAI_API_KEY
        self.openai_base = OPENAI_BASE_URL if 'OPENAI_BASE_URL' in globals() else None
        self.openai_model = OPENAI_EMBED_MODEL
        self.baai_model_name = BAAI_MODEL
        self._baai_model = None
        self._baai_load_attempted = False
        if self.provider == 'baai':
            try:
                import sentence_transformers
            except Exception:
                print("[warning] sentence_transformers未安装，provider=baai无法使用，自动切换到openai")
                self.provider = 'openai' if OPENAI_API_KEY else 'local'

    def _prefix(self, text: str, is_query: bool):
        if not EMBED_PREFIX_ENABLED:
            return text
        if self.provider == 'baai':
            return ('查询: ' if is_query else '文档: ') + text
        return text

    # openai
    def _embed_openai(self, text: str):
        if not self.openai_key or not self.openai_base or not self.openai_model:
            return None
        url = self.openai_base.rstrip('/') + '/v1/embeddings'
        headers = {"Authorization": f"Bearer {self.openai_key}", "Content-Type": "application/json"}
        payload = {"model": self.openai_model, "input": text}
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=20)
            if r.status_code != 200:
                return None
            j = r.json()
            return j.get('data', [{}])[0].get('embedding')
        except Exception:
            return None

    def _embed_batch_openai(self, texts: List[str]) -> Optional[List[List[float]]]:
        if not self.openai_key or not self.openai_base or not self.openai_model:
            return None
        url = ""                # 文本嵌入模型的URL
        headers = {"Authorization": "Bearer sk-", "Content-Type": "application/json"}
        payload = {"model": self.openai_model, "input": texts}
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            if r.status_code != 200:
                return None
            j = r.json()
            data = j.get('data', [])
            return [item.get('embedding') for item in data]
        except Exception:
            return None

    # baai (local sentence-transformers)
    def _load_baai(self):
        if self._baai_model is not None or self._baai_load_attempted:
            return self._baai_model
        self._baai_load_attempted = True
        try:
            from sentence_transformers import SentenceTransformer
            self._baai_model = SentenceTransformer(self.baai_model_name)
            return self._baai_model
        except Exception:
            self._baai_model = None
            return None

    def _embed_baai(self, text: str) -> Optional[List[float]]:
        m = self._load_baai()
        if m is None:
            return None
        try:
            v = m.encode([text])
            if hasattr(v, 'tolist'):
                return v[0].tolist()
            return list(v[0])
        except Exception:
            return None

    def _embed_batch_baai(self, texts: List[str]) -> Optional[List[List[float]]]:
        m = self._load_baai()
        if m is None:
            return None
        try:
            v = m.encode(texts)
            if hasattr(v, 'tolist'):
                return v.tolist()
            return [list(row) for row in v]
        except Exception as e:
            print('[baai] 文本嵌入操作失败', e)
            return None

    # public
    def embed_text(self, text: str, is_query: bool = False):
        if not text:
            return None
        t = self._prefix(text, is_query)
        if self.provider == 'openai':
            return self._embed_openai(t)
        if self.provider == 'baai':
            return self._embed_baai(t)
        return None

    def embed_batch(self, texts: List[str], is_query: bool = False):
        if not texts:
            return None
        ts = [self._prefix(t, is_query) for t in texts]
        if self.provider == 'openai':
            return self._embed_batch_openai(ts)
        if self.provider == 'baai':
            return self._embed_batch_baai(ts)
        return None

# retrieval helpers compatible with Storage
def retrieve_similar(storage, text, top_k=3, provider: Optional[EmbeddingProvider] = None):
    # try dense first
    ep = provider or EmbeddingProvider()
    q_vec = ep.embed_text(text, is_query=True)
    rows = storage.get_all_embeddings()
    scored = []
    if q_vec is not None:
        for aid, terms_json, vec_json in rows:
            try:
                v = json.loads(vec_json)
            except Exception:
                v = None
            if isinstance(v, list):
                s = cosine_dense(q_vec, v)
            elif isinstance(v, dict):
                q_tf = embed_text(build_terms(text))
                s = cosine_sparse(q_tf, v)
            else:
                s = 0.0
            scored.append((s, aid))
    else:
        # sparse fallback
        q_tf = embed_text(build_terms(text))
        for aid, terms_json, vec_json in rows:
            try:
                v = json.loads(vec_json)
            except Exception:
                v = None
            if isinstance(v, dict):
                s = cosine_sparse(q_tf, v)
            else:
                # try comparing with terms_json
                try:
                    t = json.loads(terms_json)
                    if isinstance(t, dict):
                        s = cosine_sparse(q_tf, t)
                    else:
                        s = 0.0
                except Exception:
                    s = 0.0
            scored.append((s, aid))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [aid for _, aid in scored[:top_k]]


def retrieve_documents(texts, query_text, top_k=3, provider: Optional[EmbeddingProvider] = None):
    ep = provider or EmbeddingProvider()
    q_dense = ep.embed_text(query_text, is_query=True)
    scored = []
    if q_dense is not None:
        # try batch dense for texts
        dense_embs = ep.embed_batch(texts)
        if dense_embs:
            for t, v in zip(texts, dense_embs):
                if v is None:
                    # fallback to sparse
                    s = cosine_sparse(embed_text(build_terms(query_text)), embed_text(build_terms(t)))
                else:
                    s = cosine_dense(q_dense, v)
                scored.append((s, t))
        else:
            # dense batch failed, fallback to sparse
            q_tf = embed_text(build_terms(query_text))
            for t in texts:
                s = cosine_sparse(q_tf, embed_text(build_terms(t)))
                scored.append((s, t))
    else:
        q_tf = embed_text(build_terms(query_text))
        for t in texts:
            s = cosine_sparse(q_tf, embed_text(build_terms(t)))
            scored.append((s, t))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [x[1] for x in scored[:top_k]]
