def load_knowledge():
    items = []
    #items.append("监管阈值参考: 当风险分数超过0.7需加强干预与限额管理")
    #items.append("评分卡实践: WOE分箱与PSI监控用于稳定性评估")
    #items.append("图关系识别: 账户-设备-邮箱多实体关系有助于识别团伙欺诈")
    #items.append("宏观波动: 市场指数下行期需提高逾期监控频率")
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

