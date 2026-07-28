from __future__ import annotations

from dataclasses import dataclass
import json
import os
import re
from typing import Any, Protocol

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
        "hashtags": {"type": "array", "items": {"type": "string"}, "minItems": 5, "maxItems": 5},
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
}

_MOJIBAKE_MARKERS = ("Ø", "Ù", "Ã", "Â", "â€")


def _repair_text(value: Any) -> str:
    """Return clean Unicode text and repair common UTF-8/Windows mojibake."""
    text = str(value or "").strip()
    if not text or not any(marker in text for marker in _MOJIBAKE_MARKERS):
        return text
    try:
        repaired = text.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text
    return repaired if repaired else text


def _parse_json_response(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


class GeminiTruthGuard:
    def __init__(self, api_key: str, model: str, minimum_confidence: float = 0.8) -> None:
        if not api_key.strip():
            raise ValueError("GEMINI_API_KEY is required")
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.minimum_confidence = minimum_confidence

    def verify(self, article: Article) -> EditorialPackage:
        prompt = f"""
أنت محرر قناة «خبر بلا حدود». طبّق سياسة TRUTHGUARD بدقة: الدقة والحياد قبل السرعة.
لا تعتمد على معلومات خارج النص المقدم، ولا تخترع حقائق. ارفض الخبر عند الغموض الجوهري،
أو عند وجود صياغة شائعة أو غير مؤكدة، أو عندما لا تكفي المادة لصناعة خبر مسؤول.

المصدر: {article.source}
العنوان: {article.title}
الرابط: {article.url}
تاريخ النشر: {article.published_at.isoformat()}
الملخص:
{article.summary}

عند الموافقة، اكتب جميع حقول النشر بالعربية الفصحى المعاصرة السليمة فقط.

قواعد العنوان العربي title_ar، وهو النص الذي سيظهر في الصورة المصغرة:
- اكتب عنوانًا خبريًا واضحًا ومفهومًا من 6 إلى 12 كلمة.
- استخدم العربية الفصحى، ولا تستخدم العامية أو الترجمة الحرفية الركيكة.
- اجعل ترتيب الكلمات طبيعيًا كما في عناوين القنوات الإخبارية العربية المحترفة.
- لا تستخدم كلمات إنجليزية إلا اسم علم لا يوجد له مقابل عربي شائع.
- لا تضف عبارات مثيرة مثل «لن تصدق» أو «صدمة» أو «عاجل» إلا إذا كانت حقيقة في الخبر.
- لا تضع نقطة في نهاية العنوان، ولا تكرر الكلمات.

اكتب script_ar كنص تعليق صوتي عربي فصيح وسلس، بجمل قصيرة قابلة للنطق الطبيعي.
واكتب وصفًا عربيًا ليوتيوب، وكلمات مفتاحية عربية، وخمسة وسوم هاشتاغ عربية مرتبطة مباشرة بالخبر، دون تكرار.
لا تستخدم نصًا مشوهًا أو ترميزًا مثل Ø أو Ù.
عند الرفض اترك حقول النشر فارغة واشرح السبب.
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
        data = _parse_json_response(response.text)
        confidence = max(0.0, min(1.0, float(data["confidence"])))
        approved = bool(data["approved"]) and confidence >= self.minimum_confidence
        return EditorialPackage(
            approved=approved,
            confidence=confidence,
            reason=_repair_text(data["reason"]),
            title_ar=_repair_text(data["title_ar"]) if approved else "",
            script_ar=_repair_text(data["script_ar"]) if approved else "",
            description_ar=_repair_text(data["description_ar"]) if approved else "",
            tags=tuple(
                cleaned
                for item in data["tags"]
                if (cleaned := _repair_text(item))
            ) if approved else (),
            hashtags=tuple(
                cleaned
                for item in data["hashtags"]
                if (cleaned := _repair_text(item))
            ) if approved else (),
        )


def build_truthguard(config: dict) -> GeminiTruthGuard:
    ai_config = config["ai"]
    return GeminiTruthGuard(
        api_key=os.environ.get("GEMINI_API_KEY", ""),
        model=str(ai_config["model"]),
        minimum_confidence=float(ai_config.get("minimum_confidence", 0.8)),
    )
