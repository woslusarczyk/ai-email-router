import os

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://ollama:11434")
MODEL_NAME = os.environ.get("MODEL_NAME", "llama3.2")
SMTP_HOST = os.environ.get("SMTP_HOST", "mailhog")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "1025"))
