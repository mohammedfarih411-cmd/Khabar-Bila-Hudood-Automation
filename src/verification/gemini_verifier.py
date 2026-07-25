from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from ..news import Article
from .policy import (
    VerificationEvidence,
    VerificationResult,
    verify_article,
)


class GeminiEvidenceAssessment(BaseModel):
    """Structured editorial evidence extracted from grounded research."""

    trusted_original_source: bool = Field(
        description=(
            "True only when the original publisher is confirmed as "
            "a recognized and accountable news organization."
        )
    )
    corroborating_sources: list[str] = Field(
        default_factory=list,
        description=(
            "Independent sources corroborating the central claim. "
            "Include source name and URL when available."
        ),
    )
    contradictions: list[str] = Field(
        default_factory=list,
        description=(
            "Material conflicts involving dates, figures, identities, "
            "locations, or the central event."
        ),
    )
    social_media_only: bool = Field(
        default=False,
        description=(
            "True when the claim is supported only by social-media "
            "posts or other unverified user-generated material."
        ),
    )
    recycled_or_outdated: bool = Field(
        default=False,
        description=(
            "True when an old event is being presented as current or "
            "the publication date is misleading."
        ),
    )
    rationale: str = Field(
        description=(
            "A concise explanation based only on the supplied "
            "grounded research."
        )
    )


@dataclass(frozen=True, slots=True)
class GroundedResearch:
    """Research text and web sources returned by Gemini grounding."""

    text: str
    sources: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class GeminiVerificationAudit:
    """Auditable output from the Gemini verification workflow."""

    result: VerificationResult
    research: GroundedResearch
    assessment: GeminiEvidenceAssessment


def _normalize_unique(values: list[str]) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        normalized = " ".join(str(value).split())

        if not normalized:
            continue

        key = normalized.casefold()

        if key in seen:
            continue

        seen.add(key)
        result.append(normalized)

    return tuple(result)


def _extract_grounding_sources(response: Any) -> tuple[str, ...]:
    """Extract source titles and URLs from Gemini grounding metadata."""

    extracted: list[str] = []

    for candidate in getattr(response, "candidates", None) or []:
        metadata = getattr(candidate, "grounding_metadata", None)

        if metadata is None:
            continue

        for chunk in getattr(
            metadata,
            "grounding_chunks",
            None,
        ) or []:
            web = getattr(chunk, "web", None)

            if web is None:
                continue

            title = " ".join(
                str(getattr(web, "title", "") or "").split()
            )
            uri = " ".join(
                str(getattr(web, "uri", "") or "").split()
            )

            if title and uri:
                extracted.append(f"{title} | {uri}")
            elif uri:
                extracted.append(uri)

    return _normalize_unique(extracted)


def _article_research_prompt(article: Article) -> str:
    return f"""
You are performing pre-publication research for a conservative
news-verification system.

Investigate the following article using current web sources.

Title: {article.title}
Publisher: {article.source}
URL: {article.url}
Published at: {article.published_at}
RSS summary:
{article.summary}

Research requirements:
1. Determine whether the URL belongs to the stated original publisher.
2. Identify independent reputable sources covering the same event.
3. Compare names, dates, places, figures, and the central claim.
4. Detect whether the story is old material presented as current.
5. Detect whether the claim originates only from social media.
6. Do not approve or rewrite the article.
7. Clearly state when evidence cannot be confirmed.

Return concise factual research notes. Mention the source used for
every material fact.
""".strip()


def _assessment_prompt(
    article: Article,
    research: GroundedResearch,
) -> str:
    source_lines = (
        "\n".join(
            f"- {source}"
            for source in research.sources
        )
        or "- No grounding metadata was returned."
    )

    return f"""
Evaluate the evidence for this news article conservatively.

Article title: {article.title}
Original publisher claimed by feed: {article.source}
Original URL: {article.url}
Publication date: {article.published_at}

Grounded research notes:
{research.text}

Grounding sources:
{source_lines}

Rules:
- Use only the supplied research and grounding sources.
- Do not treat the original publisher as independent corroboration.
- A search result snippet alone is not sufficient corroboration.
- Set trusted_original_source to false when publisher identity or
  accountability cannot be confirmed.
- List only genuinely independent corroborating sources.
- Record material contradictions explicitly.
- Mark social_media_only true when no accountable publisher or
  primary authority supports the claim.
- Mark recycled_or_outdated true when an old event is presented as new.
- When evidence is incomplete, remain conservative.
""".strip()


class GeminiEditorialVerifier:
    """Two-stage grounded verifier for collected news articles."""

    def __init__(
        self,
        *,
        model: str = "gemini-2.5-pro",
        api_key: str | None = None,
        client: Any | None = None,
        minimum_corroborating_sources: int = 1,
    ) -> None:
        if minimum_corroborating_sources < 0:
            raise ValueError(
                "minimum_corroborating_sources cannot be negative"
            )

        if client is None:
            resolved_key = api_key or os.getenv("GEMINI_API_KEY")

            if not resolved_key:
                raise RuntimeError(
                    "GEMINI_API_KEY is missing or empty"
                )

            client = genai.Client(api_key=resolved_key)

        self._client = client
        self._model = model
        self._minimum_corroborating_sources = (
            minimum_corroborating_sources
        )

    def research_article(
        self,
        article: Article,
    ) -> GroundedResearch:
        """Research an article with Google Search grounding."""

        response = self._client.models.generate_content(
            model=self._model,
            contents=_article_research_prompt(article),
            config=types.GenerateContentConfig(
                tools=[
                    types.Tool(
                        google_search=types.GoogleSearch()
                    )
                ],
                temperature=0.0,
            ),
        )

        research_text = str(
            getattr(response, "text", "") or ""
        ).strip()

        if not research_text:
            raise RuntimeError(
                "Gemini returned no grounded research text"
            )

        return GroundedResearch(
            text=research_text,
            sources=_extract_grounding_sources(response),
        )

    def assess_research(
        self,
        article: Article,
        research: GroundedResearch,
    ) -> GeminiEvidenceAssessment:
        """Convert grounded research into structured evidence."""

        response = self._client.models.generate_content(
            model=self._model,
            contents=_assessment_prompt(article, research),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=GeminiEvidenceAssessment,
                temperature=0.0,
            ),
        )

        parsed = getattr(response, "parsed", None)

        if isinstance(parsed, GeminiEvidenceAssessment):
            return parsed

        if isinstance(parsed, dict):
            return GeminiEvidenceAssessment.model_validate(parsed)

        response_text = str(
            getattr(response, "text", "") or ""
        ).strip()

        if not response_text:
            raise RuntimeError(
                "Gemini returned no structured assessment"
            )

        return GeminiEvidenceAssessment.model_validate_json(
            response_text
        )

    def verify(
        self,
        article: Article,
    ) -> GeminiVerificationAudit:
        """Research, assess, and apply the publication policy."""

        research = self.research_article(article)
        assessment = self.assess_research(article, research)

        result = verify_article(
            article,
            VerificationEvidence(
                trusted_original_source=(
                    assessment.trusted_original_source
                ),
                corroborating_sources=tuple(
                    assessment.corroborating_sources
                ),
                contradictions=tuple(
                    assessment.contradictions
                ),
                social_media_only=assessment.social_media_only,
                recycled_or_outdated=(
                    assessment.recycled_or_outdated
                ),
            ),
            minimum_corroborating_sources=(
                self._minimum_corroborating_sources
            ),
        )

        return GeminiVerificationAudit(
            result=result,
            research=research,
            assessment=assessment,
        )
