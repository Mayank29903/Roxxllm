import httpx
import json
from typing import AsyncGenerator, List, Dict
from app.config import settings


class LLMService:
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL.rstrip("/")
        self.model = settings.LLM_MODEL

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": f"http://{settings.HOST}:{settings.PORT}",
            "X-Title": "LongFormMemoryAI",
        }

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        max_tokens: int = None,
        temperature: float = None,
        top_p: float = None
    ) -> AsyncGenerator[Dict[str, str], None]:

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
        }

        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if temperature is not None:
            payload["temperature"] = temperature
        if top_p is not None:
            payload["top_p"] = top_p


        try:
            async with httpx.AsyncClient(timeout=60) as client:

                # ---------- STREAMING ----------
                if stream:
                    async with client.stream(
                        "POST",
                        f"{self.base_url}/chat/completions",
                        headers=self.headers,
                        json=payload,
                    ) as response:

                        response.raise_for_status()

                        async for line in response.aiter_lines():
                            if not line:
                                continue


                            if line.strip() == "data: [DONE]":
                                break

                            if not line.startswith("data:"):
                                continue

                            data = line.replace("data:", "").strip()

                            try:
                                chunk = json.loads(data)
                            except Exception as e:
                                continue

                            delta = (
                                chunk.get("choices", [{}])[0]
                                .get("delta", {})
                                .get("content")
                            )

                            if delta:
                                yield {
                                    "type": "token",
                                    "content": delta
                                }

                # ---------- NON-STREAMING ----------
                else:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=self.headers,
                        json=payload,
                    )

                    response.raise_for_status()
                    result = response.json()

                    text = (
                        result.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content")
                    )

                    yield {
                        "type": "final",
                        "content": text or ""
                    }

        except Exception as e:
            yield {
                "type": "error",
                "content": f"LLM failure: {str(e)}"
            }
