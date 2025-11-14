from src.agent.config import RISK_MONITOR_THRESHOLD, RISK_INTERVENE_THRESHOLD


def decide(current_risk, recent_history):
    rising = False
    if recent_history:
        rising = current_risk > sum(recent_history) / len(recent_history)
    if current_risk >= RISK_INTERVENE_THRESHOLD and rising:
        return "干预型"
    if current_risk >= RISK_MONITOR_THRESHOLD:
        return "监测型"
    return "防御型" if rising else "正常"

