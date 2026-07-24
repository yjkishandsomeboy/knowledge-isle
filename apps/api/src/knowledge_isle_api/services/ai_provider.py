from typing import Any

import httpx

from knowledge_isle_api.core.config import settings
from knowledge_isle_api.services.retrieval import RetrievedEvidence


async def generate_answer(question: str, evidence: list[RetrievedEvidence]) -> str:
    if not evidence:
        return "没有在当前知识库中找到足够相关的内容。"
    if not settings.ai_base_url or not settings.ai_api_key:
        sources = "\n".join(f"[{index}] {item.snippet}" for index, item in enumerate(evidence, 1))
        return f"AI 服务尚未配置。已找到以下相关原文片段：\n\n{sources}"

    context = "\n\n".join(
        f"[{index}] 文件：{item.filename}\n{item.snippet}"
        for index, item in enumerate(evidence, 1)
    )
    payload = {
        "model": settings.ai_model,
        "input": [
            {
                "role": "system",
                "content": (
                    "你是 Knowledge Isle 的知识库助手。只根据提供的资料回答；"
                    "资料不足时明确说明。使用 [1] 形式标注引用。"
                ),
            },
            {"role": "user", "content": f"问题：{question}\n\n资料：\n{context}"},
        ],
    }
    headers = {"Authorization": f"Bearer {settings.ai_api_key}"}
    async with httpx.AsyncClient(timeout=settings.ai_timeout_seconds) as client:
        response = await client.post(
            f"{settings.ai_base_url.rstrip('/')}/responses", json=payload, headers=headers
        )
        response.raise_for_status()
        return _extract_output_text(response.json())


def _extract_output_text(body: dict[str, Any]) -> str:
    if isinstance(body.get("output_text"), str):
        return body["output_text"]
    texts: list[str] = []
    for output in body.get("output", []):
        for content in output.get("content", []):
            text = content.get("text")
            if isinstance(text, str):
                texts.append(text)
    if not texts:
        raise ValueError("AI provider returned no text output")
    return "\n".join(texts)
