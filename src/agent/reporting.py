def generate_report(x, risk, contributions, history_texts, similar_texts, knowledge_refs, graph_refs, countermeasures=""):
    entity = x.get("company_name", x.get("entity_id", ""))
    parts = []
    parts.append(f"公司: {entity}")
    parts.append(f"风险分数: {risk:.4f}")
    if contributions:
        sorted_items = sorted(contributions.items(), key=lambda kv: abs(kv[1]), reverse=True)
        top = sorted_items[:5]
        parts.append("关键特征贡献:")
        for k, v in top:
            parts.append(f"- {k}: {v:.4f}")
    if history_texts:
        parts.append("历史相似报告:")
        for t in history_texts[:3]:
            parts.append(f"- {t[:160]}")
    if similar_texts:
        parts.append("Top-K相似匹配:")
        for t in similar_texts[:3]:
            parts.append(f"- {t[:160]}")
    if graph_refs:
        parts.append("图关系参考:")
        for g in graph_refs:
            parts.append(f"- {g}")
    if knowledge_refs:
        parts.append("外部知识参考:")
        for k in knowledge_refs:
            parts.append(f"- {k}")
    if countermeasures:
        parts.append("风险对策:")
        parts.append(countermeasures)
    return "\n".join(parts)
