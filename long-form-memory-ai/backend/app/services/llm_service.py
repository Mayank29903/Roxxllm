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
            "HTTP-Referer": "http://localhost:8000",
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

        # ---------- DEBUG: REQUEST ----------
        print("\n========== LLM REQUEST ==========")
        print("URL:", f"{self.base_url}/chat/completions")
        print("MODEL:", self.model)
        print("STREAM:", stream)
        print("PAYLOAD:")
        print(json.dumps(payload, indent=2))
        print("=================================\n")

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

                        print("HTTP STATUS:", response.status_code)

                        async for line in response.aiter_lines():
                            if not line:
                                continue

                            print("RAW STREAM:", line)

                            if line.strip() == "data: [DONE]":
                                print("STREAM DONE")
                                break

                            if not line.startswith("data:"):
                                continue

                            data = line.replace("data:", "").strip()

                            try:
                                chunk = json.loads(data)
                            except Exception as e:
                                print("STREAM JSON ERROR:", e)
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

                    print("HTTP STATUS:", response.status_code)
                    print("\n========== RAW RESPONSE ==========")
                    print(response.text)
                    print("=================================\n")

                    response.raise_for_status()
                    result = response.json()

                    print("\n========== PARSED RESPONSE ==========")
                    print(json.dumps(result, indent=2))
                    print("====================================\n")

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
            import traceback
            traceback.print_exc()
            yield {
                "type": "error",
                "content": f"LLM failure: {str(e)}"
            }