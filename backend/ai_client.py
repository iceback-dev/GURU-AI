import os
import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
URL = "https://openrouter.ai/api/v1/chat/completions"


async def ask_ai(system: str, user: str, max_tokens: int = 4000) -> str:
    if not API_KEY or API_KEY.startswith("sk-or-v1-xxx"):
        raise RuntimeError("Set OPENROUTER_API_KEY")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://your-vercel-app.vercel.app",
        "X-Title": "ForgeAI",
    }
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }

    async with httpx.AsyncClient(timeout=55) as client:  # < 60s Vercel limit
        r = await client.post(URL, headers=headers, json=body)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]
