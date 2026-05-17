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

                timeout=120
            )

            response.raise_for_status()

            data = response.json()

            return data.get(
                "response",
                ""
            )

        except Exception as e:

            print(
                f"[LLM ERROR]: {str(e)}"
            )

            # graceful fallback
            return '["2+2"]'