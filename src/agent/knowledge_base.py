import os
import json
from typing import List
from src.agent.config import KNOWLEDGE_DIRS

def _list_files(dirs: List[str]):
    out = []
    for d in dirs:
        if not d:
            continue
        p = d
        if not os.path.isabs(p):
            p = os.path.abspath(p)
        if not os.path.isdir(p):
            continue
        for root, _, files in os.walk(p):
            for f in files:
                if f.lower().endswith(('.txt', '.md', '.pdf', '.docs')):
                    out.append(os.path.join(root, f))
    return sorted(out)

def _files_fingerprint(paths: List[str]):
    sig = []
    for fp in paths:
        try:
            st = os.stat(fp)
            sig.append(f"{os.path.abspath(fp)}|{int(st.st_mtime)}|{st.st_size}")
        except Exception:
            sig.append(f"{os.path.abspath(fp)}|0|0")
    return ";".join(sig)

def _read_text(fp):
    try:
        ext = os.path.splitext(fp)[1].lower()
        if ext in ('.txt', '.md'):
            with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        if ext == '.pdf':
            try:
                import PyPDF2
                with open(fp, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    return "\n".join([(p.extract_text() or "") for p in reader.pages])
            except Exception:
                return ""
        return ""
    except Exception:
        return ""

def _split_paragraphs(text: str, max_len: int = 800):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        return []
    items = []
    buf = []
    ln = 0
    for l in lines:
        if ln + len(l) > max_len:
            items.append(" ".join(buf))
            buf = [l]
            ln = len(l)
        else:
            buf.append(l)
            ln += len(l)
    if buf:
        items.append(" ".join(buf))
    return items

def load_knowledge():
    dirs = KNOWLEDGE_DIRS
    cache_dir = os.path.join(os.getcwd(), ".cache")
    cache_fp = os.path.join(cache_dir, "knowledge_cache.json")
    paths = _list_files(dirs)
    fp_sig = _files_fingerprint(paths)
    try:
        with open(cache_fp, 'r', encoding='utf-8') as f:
            cached = json.load(f)
    except Exception:
        cached = None
    if cached and cached.get('fingerprint') == fp_sig:
        return cached.get('items', [])
    items: List[str] = []
    for fp in paths:
        text = _read_text(fp)
        segments = _split_paragraphs(text)
        if segments:
            items.extend(segments)
        elif text:
            items.append(text)
    try:
        os.makedirs(cache_dir, exist_ok=True)
        with open(cache_fp, 'w', encoding='utf-8') as f:
            json.dump({"fingerprint": fp_sig, "items": items}, f, ensure_ascii=False)
    except Exception:
        pass
    return items


def retrieve_knowledge(items, text, top_k=3):
    s = text.lower()
    scored = []
    for it in items:
        c = 0
        for token in ["风险", "评分", "账户", "市场", "欺诈", "PSI"]:
            if token in it:
                if token in s:
                    c += 1
        scored.append((c, it))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [it for _, it in scored[:top_k]]

