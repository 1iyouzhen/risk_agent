import os

DEFAULT_DB_PATH = "risk_agent.sqlite"
RISK_MONITOR_THRESHOLD = 0.5
RISK_INTERVENE_THRESHOLD = 0.7
TOP_K = int(os.environ.get("RAG_TOP_K", "3"))
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_CHAT_MODEL = os.environ.get("OPENAI_CHAT_MODEL", "deepseek-chat")
OPENAI_EMBED_MODEL = os.environ.get("OPENAI_EMBED_MODEL", "text-embedding-3-small")
EMBED_PROVIDER = os.environ.get("EMBED_PROVIDER", "baai")
BAAI_MODEL = os.environ.get("BAAI_MODEL", "BAAI/bge-m3")
EMBED_PREFIX_ENABLED = os.environ.get("EMBED_PREFIX_ENABLED", "1") == "1"
KNOWLEDGE_DIRS = os.environ.get("KNOWLEDGE_DIRS", "knowledge_docs").split(";")
RAG_MIN_SCORE = float(os.environ.get("RAG_MIN_SCORE", "0.25"))
RAG_MIN_SOURCES = int(os.environ.get("RAG_MIN_SOURCES", "2"))
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com")
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "20"))
REQUEST_RETRIES = int(os.environ.get("REQUEST_RETRIES", "2"))
