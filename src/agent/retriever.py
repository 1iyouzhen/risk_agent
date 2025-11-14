import json
from typing import List, Dict, Any
from .config import TOP_K, RAG_MIN_SCORE, RAG_MIN_SOURCES
from .rag import build_terms, embed_text, cosine_sparse, cosine_dense, EmbeddingProvider


def _score_text(query_vec, item_vec):
    if isinstance(query_vec, list) and isinstance(item_vec, list):
        return cosine_dense(query_vec, item_vec)
    if isinstance(query_vec, dict) and isinstance(item_vec, dict):
        return cosine_sparse(query_vec, item_vec)
    return 0.0


def _query_vectors(qtext):
    ep = EmbeddingProvider()
    q_dense = ep.embed_text(qtext, is_query=True)
    q_sparse = embed_text(build_terms(qtext))
    return q_dense, q_sparse


def retrieve_all(storage, knowledge, vector_store, graph_client, neo4j_client, query_text: str, top_k: int = TOP_K):
    q_dense, q_sparse = _query_vectors(query_text)
    hits: List[Dict[str, Any]] = []

    try:
        rows = storage.get_all_embeddings()
        scored = []
        for aid, terms_json, vec_json in rows:
            try:
                v = json.loads(vec_json)
            except Exception:
                v = None
            try:
                t = json.loads(terms_json)
            except Exception:
                t = None
            if q_dense is not None and isinstance(v, list):
                s = cosine_dense(q_dense, v)
            elif isinstance(v, dict) and isinstance(q_sparse, dict):
                s = cosine_sparse(q_sparse, v)
            elif isinstance(t, dict) and isinstance(q_sparse, dict):
                s = cosine_sparse(q_sparse, t)
            else:
                s = 0.0
            scored.append((s, aid))
        scored.sort(key=lambda x: x[0], reverse=True)
        for s, aid in scored[:top_k]:
            hits.append({"source": "history", "id": aid, "score": s})
    except Exception:
        pass

    try:
        krefs = knowledge
        for t in krefs:
            tf = build_terms(t)
            v = embed_text(tf)
            if q_dense is not None:
                s = 0.0
            else:
                s = _score_text(q_sparse, v)
            hits.append({"source": "knowledge", "text": t, "score": s})
    except Exception:
        pass

    try:
        vs_items = vector_store.search(query_text, top_k=top_k)
        for it in vs_items:
            vec = it.get("vec", None)
            if q_dense is not None and isinstance(vec, list):
                s = cosine_dense(q_dense, vec)
            elif isinstance(vec, dict) and isinstance(q_sparse, dict):
                s = cosine_sparse(q_sparse, vec)
            else:
                s = 0.0
            hits.append({"source": "vector", "text": it.get("text", ""), "score": s})
    except Exception:
        pass

    try:
        for t in graph_client.describe_company(query_text, limit=top_k):
            hits.append({"source": "graph_csv", "text": t, "score": 0.3})
    except Exception:
        pass
    try:
        if neo4j_client and neo4j_client.available():
            for t in neo4j_client.describe_company(query_text, limit=top_k):
                hits.append({"source": "graph_neo4j", "text": t, "score": 0.4})
    except Exception:
        pass

    hits.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    valid_hits = [h for h in hits if h.get("score", 0.0) >= RAG_MIN_SCORE]
    sources = set([h.get("source", "") for h in valid_hits])
    ok = len(sources) >= RAG_MIN_SOURCES
    return {"hits": hits[:top_k], "valid": ok}
