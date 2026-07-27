from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Protocol

from google import genai

from ..models import Article


@dataclass(slots=True)
class EditorialPackage:
    approved: bool
    confidence: float
    reason: str
    title_ar: str = ""
    script_ar: str = ""
    description_ar: str = ""
    tags: tuple[str, ...] = ()
    hashtags: tuple[str, ...] = ()


class ArticleVerifier(Protocol):
    def verify(self, article: Article) -> EditorialPackage: ...


_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "approved": {"type": "boolean"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "reason": {"type": "string"},
        "title_ar": {"type": "string"},
        "script_ar": {"type": "string"},
        "description_ar": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}, "maxItems": 15},
        "hashtags": {"type": "array", "items": {"type": "string"}, "maxItems": 3},
    },
    "required": [
        "approved",
        "confidence",
        "reason",
        "title_ar",
        "script_ar",
        "description_ar",
        "tags",
        "hashtags",
    ],
    "additionalProperties": False,
}


class GeminiTruthGuard:
    def __init__(self, api_key: str, model: str, minimum_confidence: float = 0.8) -> None:
        if not api_key.strip():
            raise ValueError("GEMINI_API_KEY is required")
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.minimum_confidence = minimum_confidence

    def verify(self, article: Article) -> EditorialPackage:
        prompt = f"""
أنت محرر قناة خبر بلا حدود. طبّق سياسة TRUTHGUARD بدقة: الدقة والحياد قبل السرعة.
لا تعتمد على معلومات خارج النص المقدم، ولا تخترع حقائق. ارفض الخبر عند الغموض الجوهري،
أو عند وجود صياغة شائعة/غير مؤكدة، أو عندما لا تكفي المادة لصناعة خبر مسؤول.

المصدر: {article.source}
العنوان: {article.title}
الرابط: {article.url}
تاريخ النشر: {article.published_at.isoformat()}
الملخص:
{article.summary}

عند الموافقة: اكتب عنوانًا عربيًا صحفيًا غير مضلل، ونصًا عربيًا محايدًا، ووصف YouTube،
وكلمات مفتاحية، وثلاثة وسوم كحد أقصى. عند الرفض اترك حقول النشر فارغة واشرح السبب.
""".strip()
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={
                "temperature": 0.2,
                "response_mime_type": "application/json",
                "response_schema": _RESPONSE_SCHEMA,
            },
        )
        if not response.text:
            raise RuntimeError("Gemini returned an empty response")
        data = json.loads(response.text)
        confidence = max(0.0, min(1.0, float(data["confidence"])))
        approved = bool(data["approved"]) and confidence >= self.minimum_confidence
        return EditorialPackage(
            approved=approved,
            confidence=confidence,
            reason=str(data["reason"]).strip(),
            title_ar=str(data["title_ar"]).strip() if approved else "",
            script_ar=str(data["script_ar"]).strip() if approved else "",
            description_ar=str(data["description_ar"]).strip() if approved else "",
            tags=tuple(str(item).strip() for item in data["tags"] if str(item).strip()) if approved else (),
            hashtags=tuple(str(item).strip() for item in data["hashtags"] if str(item).strip()) if approved else (),
        )


def build_truthguard(config: dict) -> GeminiTruthGuard:
    ai_config = config["ai"]
    return GeminiTruthGuard(
        api_key=os.environ.get("GEMINI_API_KEY", ""),
        model=str(ai_config["model"]),
        minimum_confidence=float(ai_config.get("minimum_confidence", 0.8)),
    )
