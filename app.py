#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整的 main.py：在原有 demo 功能基础上补全了生成数据、训练、评估、RAG 查询、导出等功能分支。
直接替换你的原文件或作为参考文件使用。
"""

import argparse
import json
import math
import os
import random
import sqlite3
import sys
from datetime import datetime, timedelta

import pandas as pd
import requests

from src.agent.config import DEFAULT_DB_PATH, RISK_MONITOR_THRESHOLD, RISK_INTERVENE_THRESHOLD, TOP_K, OPENAI_API_KEY, OPENAI_CHAT_MODEL
from src.agent.decision import decide
from src.agent.explainability import explain_contributions
from src.agent.knowledge_base import load_knowledge, retrieve_knowledge
from src.agent.rag import build_terms, embed_text, retrieve_similar
from src.agent.reporting import generate_report
from src.agent.storage import Storage
from src.agent.models.risk_forecast import RiskForecaster
from src.agent.models.trainable_forecaster import TrainableForecaster
from src.agent.data import FEATURES
from src.agent.data import build_samples
from src.agent.data import ensure_entity_ids_consistent
from src.agent.vector_store import VectorStore
from src.agent.graph_client import GraphClient
from src.agent.neo4j_client import Neo4jClient
from src.agent.llm_client import LLMClient
from src.agent.retriever import retrieve_all


def generate_demo_series(entity_id, start_date, periods):
    """生成模拟的金融时间序列数据"""
    series = []
    date = start_date
    base_income = random.randint(3000, 15000)
    base_credit = random.randint(550, 750)
    delinquency = 0
    market = 1000
    for i in range(periods):
        amount = max(0, random.gauss(800, 250))
        income = base_income + random.randint(-500, 500)
        credit_score = max(300, min(850, base_credit + random.randint(-20, 20)))
        if random.random() < 0.1:
            delinquency = min(10, delinquency + 1)
        else:
            delinquency = max(0, delinquency - 1)
        market_index = market + random.randint(-30, 30)
        series.append({
            "entity_id": entity_id,
            "timestamp": date.strftime("%Y-%m-%d"),
            "amount": float(f"{amount:.2f}"),
            "income": income,
            "credit_score": credit_score,
            "delinquencies": delinquency,
            "market_index": market_index,
        })
        date += timedelta(days=30)
    return series


def run_demo(args):
    print("正在运行Demo模式...")
    path = args.db
    storage = Storage(path)
    storage.init()
    knowledge = load_knowledge()
    vs = VectorStore()
    try:
        vs.add_knowledge_dirs()
    except Exception:
        pass

    company_map = {}
    try:
        company_df = pd.read_csv(os.path.join(os.getcwd(), "get_graph_data", "data", "cleaned", "company_clean.csv"))
        for _, row in company_df.iterrows():
            name = str(row.get("name", "")).strip()
            symbol = str(row.get("symbol", "")).strip()
            if name:
                company_map[name] = {"name": name, "symbol": symbol}
            if symbol:
                company_map[symbol] = {"name": name, "symbol": symbol}
    except Exception:
        company_df = None

    gc = GraphClient("graph_data")
    n4 = Neo4jClient()
    forecaster = RiskForecaster() if not args.model else TrainableForecaster.load(args.model)
    all_records = []

    # 生成模拟数据（5 个实体，每个 12 期）
    use_names = []
    if company_df is not None:
        try:
            use_names = [str(n).strip() for n in list(company_df["name"])[:5]]
        except Exception:
            use_names = []
    for e in range(5):
        entity_id = use_names[e] if e < len(use_names) else f"E{e+1}"
        series = generate_demo_series(entity_id, datetime(2023, 1, 1), 12)
        all_records.extend(series)

    assessments_by_entity = {}
    export_data = []  # 用于 CSV 导出

    # 主循环：预测 -> 解释 -> 报告 -> 存储 -> 向量化
    for record in all_records:
        risk = forecaster.score(record)
        contributions = explain_contributions(record)
        cname = company_map.get(record["entity_id"], {}).get("name", record["entity_id"]) if company_map else record["entity_id"]
        text = generate_report({"entity_id": record["entity_id"], "company_name": cname}, risk, contributions, [], [], [], "")
        storage_id = storage.save_assessment(record["entity_id"], record["timestamp"], risk, "")
        storage.save_report(storage_id, text)

        for k, v in record.items():
            if k in ["entity_id", "timestamp"]:
                continue
            c = contributions.get(k, 0.0)
            try:
                storage.save_feature(storage_id, k, float(v), float(c))
            except Exception:
                pass

        try:
            terms = build_terms(text)
            vec = embed_text(terms)
            storage.save_embedding(storage_id, json.dumps(terms), json.dumps(vec))
        except Exception:
            pass

        # 导出行
        row = {
            "EntityID": record["entity_id"],
            "Timestamp": record["timestamp"],
            "RiskScore": risk,
            "ReportText": text
        }
        for feature, value in contributions.items():
            row[f"Contribution_{feature}"] = value
        export_data.append(row)

        if record["entity_id"] not in assessments_by_entity:
            assessments_by_entity[record["entity_id"]] = []
        assessments_by_entity[record["entity_id"]].append((storage_id, risk))

    # 基于历史+知识库生成最终决策与更新报告
    for entity_id, items in assessments_by_entity.items():
        items.sort(key=lambda x: x[0])
        for idx, (assessment_id, risk) in enumerate(items):
            history_ids = [i for i, _ in items[max(0, idx-3):idx]]
            history_reports = storage.get_reports(history_ids)
            current_text = storage.get_report(assessment_id)
            similar = retrieve_similar(storage, current_text, top_k=TOP_K)
            similar = [i for i in similar if i != assessment_id]
            similar_reports = storage.get_reports(similar)
            knowledge_refs = retrieve_knowledge(knowledge, current_text, top_k=TOP_K)
            try:
                vs_items = vs.search(current_text, top_k=TOP_K)
            except Exception:
                vs_items = []
            for it in vs_items:
                knowledge_refs.append(it.get("text", "")[:160])

            graph_refs = []
            try:
                graph_refs.extend(gc.describe_account(entity_id, limit=TOP_K))
                graph_refs.extend(gc.describe_company(entity_id, limit=TOP_K))
            except Exception:
                pass
            try:
                if n4.available():
                    graph_refs.extend(n4.describe_company(entity_id, limit=TOP_K))
            except Exception:
                pass

            countermeasures = ""
            if OPENAI_API_KEY:
                try:
                    context_parts = []
                    cname = company_map.get(entity_id, {}).get("name", entity_id) if company_map else entity_id
                    sym = company_map.get(entity_id, {}).get("symbol", "") if company_map else ""
                    context_parts.append("公司:" + cname + (f" (symbol:{sym})" if sym else ""))
                    context_parts.append("当前报告:" + (current_text[:500] if current_text else ""))
                    if args.query:
                        context_parts.append("用户查询:" + args.query)
                    if similar_reports:
                        context_parts.append("Top-K相似匹配:" + "\n".join([t[:200] for t in similar_reports]))
                    if graph_refs:
                        context_parts.append("图关系参考:" + "\n".join(graph_refs))
                    if knowledge_refs:
                        context_parts.append("外部知识参考:" + "\n".join(knowledge_refs))
                    prompt = (
                            "你是金融风控分析助手，请根据以下RAG检索结果与当前企业风险数据，但是如果检索结果不足不要胡编乱造，请回复‘知识库中暂无相关信息’。检索到相关信息输出结构化报告，分为以下三部分：\n"
                            "【主要风险】：列出当前主要风险点（如信用、负债、市场波动等），简短句子形式。\n"
                            "【指标说明】：解释风险评分的关键影响因素（可以基于amount、income、credit_score等），每条单独成行。\n"
                            "【应对建议】：根据主要风险与指标说明，提出针对性可执行的风险应对措施，每条单独成行，不连成一段。\n\n"
                            "请保持输出为纯文本格式，无需HTML标签。\n\n"
                            + "\n\n".join(context_parts)
                    )
                    llm = LLMClient()
                    countermeasures = llm.chat([
                        {"role": "system", "content": "你是金融风控助手，提供简洁、可执行的建议。"},
                        {"role": "user", "content": prompt}
                    ], temperature=0.2) or ""
                except Exception:
                    countermeasures = ""
            if not countermeasures:
                cm_items = []
                for it in vs_items:
                    t = it.get("text", "")
                    if t:
                        cm_items.append(t.strip()[:200])
                if cm_items:
                    countermeasures = "；".join([f"参考：{s}" for s in cm_items[:TOP_K]])

            decision = decide(risk, [r for _, r in items[max(0, idx-3):idx]])
            try:
                storage.update_decision(assessment_id, decision)
            except Exception:
                pass
            cname = company_map.get(entity_id, {}).get("name", entity_id) if company_map else entity_id
            updated_text = generate_report({"entity_id": entity_id, "company_name": cname}, risk, {}, history_reports, similar_reports, knowledge_refs, graph_refs, countermeasures)
            try:
                storage.update_report(assessment_id, updated_text)
            except Exception:
                pass
            info = None
            try:
                info = storage.get_assessment(assessment_id)
            except Exception:
                pass
            if info:
                for r in export_data:
                    if r.get("EntityID") == info.get("entity_id") and r.get("Timestamp") == info.get("timestamp"):
                        r["ReportText"] = updated_text
                        break

    # 导出 CSV
    df = pd.DataFrame(export_data)
    csv_path = os.path.join(os.getcwd(), "risk_reports.csv")
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"CSV报告已导出到：{csv_path}")

    # 导出HTML报告
    html_dir = os.path.join(os.getcwd(), "html_reports")
    os.makedirs(html_dir, exist_ok=True)

    for row in export_data:
        html_path = os.path.join(html_dir, f"{row['EntityID']}_{row['Timestamp']}.html")

        # 拆分模型输出的三部分内容
        report_text = row["ReportText"]
        sections = {"主要风险": "", "指标说明": "", "应对建议": ""}
        for key in sections.keys():
            if f"【{key}】" in report_text:
                part = report_text.split(f"【{key}】")[1]
                # 截断到下一个【】
                for next_key in sections.keys():
                    if next_key != key and f"【{next_key}】" in part:
                        part = part.split(f"【{next_key}】")[0]
                sections[key] = part.strip()

        # 格式化为HTML
        html_content = f"""
        <html>
        <head>
            <meta charset='utf-8'>
            <title>风险报告 - {row['EntityID']}</title>
            <style>
                body {{ font-family: "Microsoft YaHei", sans-serif; margin: 40px; }}
                h2 {{ color: #222; }}
                h3 {{ color: #444; margin-top: 30px; }}
                ul {{ line-height: 1.8; }}
                p {{ line-height: 1.8; }}
                .block {{ background-color: #f7f7f7; border-radius: 10px; padding: 15px; }}
            </style>
        </head>
        <body>
            <h2>风险报告 - {row['EntityID']}</h2>
            <p><strong>时间：</strong>{row['Timestamp']}</p>
            <p><strong>风险评分：</strong>{row['RiskScore']:.4f}</p>

            <h3>解释性贡献：</h3>
            <div class="block">
            <ul>
            {''.join([f"<li>{k.replace('Contribution_', '')}: {v:.4f}</li>" for k, v in row.items() if k.startswith('Contribution_')])}
            </ul>
            </div>

            <h3>主要风险：</h3>
            <div class="block">
            {sections['主要风险'].replace('-', '<br>- ')}
            </div>

            <h3>指标说明：</h3>
            <div class="block">
            {sections['指标说明'].replace('-', '<br>- ')}
            </div>

            <h3>应对建议：</h3>
            <div class="block">
            {sections['应对建议'].replace('-', '<br>- ')}
            </div>
        </body></html>
        """

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

    print(f"HTML报告已生成到文件夹：{html_dir}")
    print(f"Demo完成！数据库：{path}  模型：{'固定模型' if not args.model else args.model}")
    print(f"监控阈值={RISK_MONITOR_THRESHOLD}, 干预阈值={RISK_INTERVENE_THRESHOLD}")


def run_generate(args):
    out = args.input_csv or "synthetic_training.csv"
    n_entities = 50
    periods = 18
    print(f"生成 {n_entities} 个实体，每个 {periods} 期的数据，保存到 {out} ...")
    rows = []
    for i in range(n_entities):
        eid = f"E{i+1}"
        rows.extend(generate_demo_series(eid, datetime(2023, 1, 1), periods))
    df = pd.DataFrame(rows)
    df.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"完成，保存 {len(df)} 行到 {out}")


def run_train(args):
    csv_path = args.input_csv or "synthetic_training.csv"
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"训练文件未找到: {csv_path}")
    print(f"加载训练数据 {csv_path} ...")
    df = pd.read_csv(csv_path)
    try:
        ensure_entity_ids_consistent(df)
    except Exception:
        pass
    print("初始化并训练模型...")
    rows = df.to_dict(orient="records")
    X, y = build_samples(rows)
    model = TrainableForecaster(FEATURES)
    try:
        model.fit(X, y, lr=1e-4, epochs=50)
        model.save(args.model or "trained_forecaster.model")
        print("训练完成，模型已保存。")
    except Exception as e:
        print("训练失败:", e)


def run_assess(args):
    csv_path = args.input_csv or "synthetic_training.csv"
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"评估文件未找到: {csv_path}")
    storage = Storage(args.db)
    storage.init()
    model = RiskForecaster() if not args.model else TrainableForecaster.load(args.model)
    df = pd.read_csv(csv_path)
    export_rows = []
    for _, row in df.iterrows():
        record = row.to_dict()
        risk = model.score(record)
        contributions = explain_contributions(record)
        report = generate_report(record, risk, contributions, [], [], [], "")
        sid = storage.save_assessment(record.get("entity_id", ""), record.get("timestamp", ""), risk, "")
        storage.save_report(sid, report)
        for k, v in record.items():
            if k in ["entity_id", "timestamp"]:
                continue
            try:
                storage.save_feature(sid, k, float(v), float(contributions.get(k, 0.0)))
            except Exception:
                pass
        export_rows.append({"EntityID": record.get("entity_id"), "Timestamp": record.get("timestamp"), "RiskScore": risk})
    out = os.path.join(os.getcwd(), "assess_results.csv")
    pd.DataFrame(export_rows).to_csv(out, index=False, encoding="utf-8-sig")
    print(f"评估完成，结果保存到 {out}")


def run_query(args):
    q = args.query
    if not q:
        print("请通过 --query '你的问题' 提供查询内容。")
        return

    # === 初始化组件 ===
    storage = Storage(args.db)
    knowledge = load_knowledge()
    vs = VectorStore()
    try:
        vs.add_knowledge_dirs()
    except Exception:
        pass

    # === 定义安全 join 函数 ===
    def safe_join(items, source_name="未知来源"):
        try:
            # 过滤掉 None，并将所有元素转成字符串
            return "\n".join(str(i) for i in items if i is not None)
        except Exception as e:
            print(f"[警告] 在拼接 {source_name} 时发生错误：{e}")
            print(f"[调试信息] {source_name} 内容示例：{items[:5] if isinstance(items, list) else items}")
            return ""

    # === 检索多源信息 ===
    gc = GraphClient("graph_data")
    n4 = Neo4jClient()
    result = retrieve_all(storage, load_knowledge(), vs, gc, n4, q, top_k=TOP_K)
    hits = result.get("hits", [])
    is_valid = result.get("valid", False)

    # === 构建上下文 ===
    context = []
    if hits:
        texts = []
        for h in hits:
            if h.get("text"):
                texts.append(h["text"])
        if texts:
            context.append("证据:\n" + safe_join(texts, "证据"))

    # === 构建 Prompt ===
    prompt = (
        "你是金融风控分析师。要求是结合以下信息，如果检索信息不足不要胡编乱造，"
        "请回复‘知识库中暂无相关信息’。\n"
        "如果检索到内容，请给出结构化回答，包含以下三部分：\n"
        "【主要发现】：基于检索证据总结关键要点。\n"
        "【相关信息】：指出与用户查询最相关的知识库内容。\n"
        "【结论】：根据证据给出你的最终判断。\n\n"
        + "\n\n".join(context)
        + f"\n\n用户查询：{q}\n"
    )

    # === 调用模型 ===
    try:
        llm = LLMClient()
        answer = llm.chat([
            {"role": "system", "content": "你是专业的金融风控分析师。输出必须准确、基于证据，不允许虚构。"},
            {"role": "user", "content": prompt}
        ], temperature=0.2)
    except Exception as e:
        print("调用远程模型失败，", e)
        print("\n=== 本地检索结果（未调用或调用失败）===\n")
        print("数据库报告匹配:")
        for i, h in enumerate(hits[:TOP_K]):
            print(i+1, h.get("text", "")[:200])
        return

    print("\n=== AI回答 ===\n")
    print(answer)



def run_export(args):
    storage = Storage(args.db)
    try:
        reports = storage.export_all_reports()
        df = pd.DataFrame(reports)
        path = args.output or os.path.join(os.getcwd(), "exported_reports.csv")
        df.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"导出完成: {path}")
        return
    except Exception:
        # 退回：直接从 sqlite 数据库读取
        db_path = args.db or DEFAULT_DB_PATH
        if not os.path.exists(db_path):
            print("找不到数据库文件，也无法从storage导出。")
            return
        try:
            con = sqlite3.connect(db_path)
            df = pd.read_sql_query("SELECT * FROM assessments", con)
            out = args.output or os.path.join(os.getcwd(), "exported_reports_from_sqlite.csv")
            df.to_csv(out, index=False, encoding="utf-8-sig")
            print(f"从 sqlite 导出完成: {out}")
        except Exception as e:
            print("导出失败:", e)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", help="运行示例模式")
    parser.add_argument("--generate", action="store_true", help="生成模拟数据")
    parser.add_argument("--train", action="store_true", help="训练模型")
    parser.add_argument("--assess", action="store_true", help="对数据进行风险评估")
    parser.add_argument("--query", type=str, default="", help="执行自然语言查询")
    parser.add_argument("--export", action="store_true", help="导出报告")
    parser.add_argument("--input_csv", type=str, default="synthetic_training.csv")
    parser.add_argument("--output", type=str, default="")
    parser.add_argument("--model", type=str, default="")
    parser.add_argument("--db", type=str, default=DEFAULT_DB_PATH)
    args = parser.parse_args()

    # 兼容：当没有参数时默认走 demo（保留原行为）
    if len(sys.argv) == 1:
        args.demo = True

    try:
        if args.demo:
            run_demo(args)
        elif args.generate:
            run_generate(args)
        elif args.train:
            run_train(args)
        elif args.assess:
            run_assess(args)
        elif args.query:
            run_query(args)
        elif args.export:
            run_export(args)
        else:
            print("请指定操作：--demo / --generate / --train / --assess / --query / --export")
    except Exception as e:
        print("程序运行出错：", e)
