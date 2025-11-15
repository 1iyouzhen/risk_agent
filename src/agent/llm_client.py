import json
import time
import requests
from src.agent.config import OPENAI_API_KEY, OPENAI_CHAT_MODEL, OPENAI_BASE_URL, REQUEST_TIMEOUT, REQUEST_RETRIES

def chat(messages, temperature=0.2):
    if not OPENAI_API_KEY:
        raise Exception("missing OPENAI_API_KEY")
    url = OPENAI_BASE_URL.rstrip("/") + "/v1/chat/completions"
    headers = {"Authorization": "Bearer " + OPENAI_API_KEY, "Content-Type": "application/json"}
    payload = {"model": OPENAI_CHAT_MODEL, "messages": messages, "temperature": temperature}
    last = None
    for _ in range(max(1, REQUEST_RETRIES)):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                j = resp.json()
                return j.get("choices", [{}])[0].get("message", {}).get("content", "")
            last = Exception(f"http {resp.status_code}: {resp.text[:120]}")
        except Exception as e:
            last = e
        time.sleep(0.5)
    if last:
        raise last
    raise Exception("unknown error")