from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Dict, Any
import os
from datetime import datetime

from src.agent.config import DEFAULT_DB_PATH, TOP_K
from src.agent.storage import Storage
from src.agent.vector_store import VectorStore
from src.agent.knowledge_base import load_knowledge
from src.agent.graph_client import GraphClient
from src.agent.neo4j_client import Neo4jClient
from src.agent.retriever import retrieve_all
from src.agent.llm_client import LLMClient
from src.agent.training import train_model

app = FastAPI()


@app.post("/query")
def api_query(payload: Dict[str, Any]):
    q = str(payload.get("query", "")).strip()
    if not q:
        return JSONResponse({"error": "empty query"}, status_code=400)
    db = payload.get("db", DEFAULT_DB_PATH)
    storage = Storage(db)
    storage.init()
    vs = VectorStore()
    try:
        vs.add_knowledge_dirs()
    except Exception:
        pass
    gc = GraphClient("graph_data")
    n4 = Neo4jClient()
    result = retrieve_all(storage, load_knowledge(), vs, gc, n4, q, top_k=TOP_K)
    hits = result.get("hits", [])
    is_valid = result.get("valid", False)
    content = "证据不足"
    if is_valid:
        llm = LLMClient()
        ctx = "\n".join([h.get("text", "") for h in hits if h.get("text")])
        prompt = "你是金融风控分析师，结合以下证据回答：\n" + ctx + "\n用户查询：" + q + "\n输出包含【主要风险】、【指标说明】、【应对建议】。"
        content = llm.chat([{ "role": "system", "content": "你是金融风控助手" }, {"role": "user", "content": prompt}], temperature=0.2) or content
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    try:
        d = os.path.join(os.getcwd(), "html_reports")
        os.makedirs(d, exist_ok=True)
        fn = f"query_{now.replace(' ', '_').replace(':','-')}.html"
        html = ["<html><head><meta charset='utf-8'><title>查询结果</title></head><body>"]
        html.append(f"<h2>查询</h2><p>{q}</p>")
        html.append("<h3>证据</h3><div><ul>")
        for h in hits:
            if h.get('text'):
                html.append(f"<li>{h['text']}</li>")
        html.append("</ul></div>")
        html.append("<h3>回答</h3><div><pre>")
        html.append(content)
        html.append("</pre></div>")
        html.append("</body></html>")
        with open(os.path.join(d, fn), "w", encoding="utf-8") as f:
            f.write("".join(html))
    except Exception:
        pass
    return {"query": q, "valid": is_valid, "hits": hits, "answer": content, "timestamp": now}


@app.get("/reports")
def list_reports():
    d = os.path.join(os.getcwd(), "html_reports")
    os.makedirs(d, exist_ok=True)
    files = [f for f in os.listdir(d) if f.lower().endswith(".html")]
    items = sorted(files)
    html = ["<html><head><meta charset='utf-8'><title>报告列表</title></head><body><h2>报告列表</h2><ul>"]
    for f in items:
        html.append(f"<li><a href='/reports/view?file={f}' target='_blank'>{f}</a></li>")
    html.append("</ul></body></html>")
    return HTMLResponse("".join(html))


@app.get("/reports/view")
def view_report(file: str):
    d = os.path.join(os.getcwd(), "html_reports")
    fp = os.path.join(d, file)
    if not os.path.isfile(fp):
        return HTMLResponse("<h3>Not Found</h3>", status_code=404)
    with open(fp, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.post("/train")
def api_train(payload: Dict[str, Any]):
    kind = payload.get("kind", "patchtst")
    params = payload.get("params", {})
    res = train_model(kind, params)
    return res
