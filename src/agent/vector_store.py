import os
import json
from .rag import build_terms, embed_text, cosine_sparse, cosine_dense, EmbeddingProvider
from .config import TOP_K, KNOWLEDGE_DIRS


class VectorStore:
    def __init__(self):
        self.items = []
        self._provider = EmbeddingProvider()
        self._faiss = None
        self._dim = None
        try:
            import faiss  # type: ignore
            self._faiss = {"mod": faiss, "index": None}
        except Exception:
            self._faiss = None

    def add(self, text, metadata):
        vec = self._provider.embed_text(text, is_query=False)
        if vec is None:
            tf = build_terms(text)
            vec = embed_text(tf)
        idx = len(self.items)
        it = {"text": text, "metadata": metadata, "vec": vec}
        self.items.append(it)
        if isinstance(vec, list) and self._faiss is not None:
            try:
                import numpy as np
                dv = len(vec)
                if self._dim is None:
                    self._dim = dv
                    index = self._faiss["mod"].IndexFlatIP(dv)
                    self._faiss["index"] = index
                if self._dim == dv and self._faiss["index"] is not None:
                    x = np.array([vec]).astype('float32')
                    n = np.linalg.norm(x, axis=1, keepdims=True)
                    x = x / (n + 1e-12)
                    self._faiss["index"].add(x)
            except Exception:
                pass

    def _chunk_text(self, text, max_len=400, overlap=50):
        out = []
        if not text:
            return out
        words = text.split()
        i = 0
        while i < len(words):
            chunk = " ".join(words[i:i+max_len])
            out.append(chunk)
            i += max_len - overlap
        return out

    def add_dir(self, path):
        if not os.path.isdir(path):
            return 0
        count = 0
        for root, _, files in os.walk(path):
            for f in files:
                if f.lower().endswith(('.txt', '.md')):
                    fp = os.path.join(root, f)
                    try:
                        with open(fp, "r", encoding="utf-8") as fh:
                            text = fh.read()
                        chunks = self._chunk_text(text)
                        if not chunks:
                            chunks = [text]
                        for idx, ch in enumerate(chunks):
                            self.add(ch, {"source": fp, "chunk": idx})
                            count += 1
                    except Exception:
                        pass
        return count

    def add_knowledge_dirs(self):
        total = 0
        for d in KNOWLEDGE_DIRS:
            if d:
                total += self.add_dir(d)
        return total

    def search(self, query_text, top_k=TOP_K):
        q = self._provider.embed_text(query_text, is_query=True)
        if q is None:
            tf = build_terms(query_text)
            q = embed_text(tf)
        if isinstance(q, list) and self._faiss is not None and self._faiss["index"] is not None and self._dim == len(q):
            try:
                import numpy as np
                x = np.array([q]).astype('float32')
                n = np.linalg.norm(x, axis=1, keepdims=True)
                x = x / (n + 1e-12)
                D, I = self._faiss["index"].search(x, min(top_k, len(self.items)))
                res = []
                for i, d in zip(I[0], D[0]):
                    if i >= 0 and i < len(self.items):
                        it = self.items[i]
                        res.append({"text": it["text"], "metadata": it["metadata"], "vec": it["vec"], "score": float(d)})
                return res[:top_k]
            except Exception:
                pass
        scored = []
        for it in self.items:
            s = 0.0
            if isinstance(q, list) and isinstance(it["vec"], list):
                s = cosine_dense(q, it["vec"])
            elif isinstance(q, dict) and isinstance(it["vec"], dict):
                s = cosine_sparse(q, it["vec"])
            scored.append((s, it))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [x[1] for x in scored[:top_k]]
