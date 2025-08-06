import logging
import time
from typing import Optional

import requests

class OllamaClient:
    """Simple HTTP client for the local Ollama LLM server.

    Contains basic retry/back-off so transient network hiccups on Wi-Fi
    do not crash the assistant."""

    def __init__(self, host: str, port: int = 11434, endpoint: str = "/api/chat", max_retries: int = 3):
        self.base_url = f"http://{host}:{port}"
        self.endpoint = endpoint
        self.url = f"{self.base_url}{self.endpoint}"
        self.max_retries = max_retries
        logging.info("Ollama client initialised for %s", self.url)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def send_message(self, message: str, model: str = "llama2") -> Optional[str]:
        """Send *message* to Ollama and return the string response or *None* on
        failure after max_retries."""
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": message}],
            "stream": False,
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                logging.info("[LLM] → '%s' (attempt %d)", message[:60], attempt)
                resp = requests.post(self.url, json=payload, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    reply = data.get("message", {}).get("content", "").strip()
                    logging.info("[LLM] ← '%s'", reply[:60])
                    return reply or None

                logging.warning("Ollama HTTP %s – %s", resp.status_code, resp.text[:120])

            except (requests.ConnectionError, requests.Timeout) as e:
                logging.warning("Ollama connection issue: %s", e)
            except Exception as e:  # Catch-all so assistant keeps running
                logging.error("Unexpected error when talking to Ollama: %s", e)

            # Exponential back-off before next attempt
            sleep_seconds = 2 ** attempt
            time.sleep(sleep_seconds)

        logging.error("Exceeded maximum retries to Ollama")
        return None

    def test_connection(self) -> bool:
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False
