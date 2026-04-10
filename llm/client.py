import requests

class LLMClient:

    def __init__(self, model="mistral:latest"):
        self.model = model
        self.url = "http://localhost:11434/api/generate"

    def generate(self, prompt):
        try:
            response = requests.post(
                self.url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=10
            )
            response.raise_for_status()
            return response.json()["response"]
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Ollama connection failed: {e}. Ensure Ollama is running at {self.url}")