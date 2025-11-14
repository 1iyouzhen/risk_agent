import time
import json
import requests
from typing import Optional, Dict, Any
from .config import OPENAI_API_KEY, OPENAI_CHAT_MODEL, OPENAI_BASE_URL, REQUEST_TIMEOUT, REQUEST_RETRIES


class LLMClient:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, model: Optional[str] = None,
                 timeout: int = REQUEST_TIMEOUT, retries: int = REQUEST_RETRIES):
        self.base_url = base_url or OPENAI_BASE_URL
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model or OPENAI_CHAT_MODEL
        self.timeout = timeout
        self.retries = retries

    def chat(self, messages: list[Dict[str, Any]], temperature: float = 0.2) -> str:
        if not self.api_key:
            return ""
        url = self.base_url.rstrip('/') + "/v1/chat/completions"
        headers = {
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }
        last_err = None
        for _ in range(max(1, self.retries)):
            try:
                resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=self.timeout)
                if resp.status_code == 200:
                    j = resp.json()
                    return j.get("choices", [{}])[0].get("message", {}).get("content", "")
                last_err = Exception(f"http {resp.status_code}")
            except Exception as e:
                last_err = e
            time.sleep(0.5)
        return ""
