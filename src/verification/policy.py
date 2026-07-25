from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from ..news import Article


class VerificationStatus(str, Enum):
    """Possible editorial decisions for a collected article."""

    VERIFIED = "verified"
    REJECTED = "rejected"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


@dataclass(frozen=True, slots=True)
class VerificationEvidence:
    """Structured evidence gathered before an editorial decision."""

    trusted_original_source: bool
    corroborating_sources: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()
    social_media_only: bool = False
    recycled_or_outdated: bool = False


@dataclass(frozen=True, slots=True)
class VerificationResult:
    """Final decision and its auditable explanation."""

    article: Article
    status: VerificationStatus
    reason: str
    supporting_sources: tuple[str, ...] = ()


def _normalized_unique(values: Iterable[str]) -> tuple[str, ...]:
    normalized_values: list[str] = []
    seen: set[str] = set()

    for value in values:
        normalized = " ".join(str(value).split())

        if not normalized:
            continue

        key = normalized.casefold()

        if key in seen:
            continue

        seen.add(key)
        normalized_values.append(normalized)

    return tuple(normalized_values)


def verify_article(
    article: Article,
    evidence: VerificationEvidence,
    *,
    minimum_corroborating_sources: int = 1,
) -> VerificationResult:
    """
    Apply a conservative editorial policy.

    Publication is allowed only when the original source is trusted and the
    required number of independent corroborating sources is available.
    """

    if minimum_corroborating_sources < 0:
        raise ValueError(
            "minimum_corroborating_sources cannot be negative"
        )

    original_source = " ".join(article.source.split())

    corroborating_sources = tuple(
        source
        for source in _normalized_unique(
            evidence.corroborating_sources
        )
        if source.casefold() != original_source.casefold()
    )

    supporting_sources = _normalized_unique(
        (original_source, *corroborating_sources)
    )

    contradictions = _normalized_unique(
        evidence.contradictions
    )

    if (
        not article.title.strip()
        or not article.url.strip()
        or not original_source
    ):
        return VerificationResult(
            article=article,
            status=VerificationStatus.INSUFFICIENT_EVIDENCE,
            reason=(
                "The article is missing a title, URL, "
                "or identifiable source."
            ),
            supporting_sources=supporting_sources,
        )

    if evidence.social_media_only:
        return VerificationResult(
            article=article,
            status=VerificationStatus.REJECTED,
            reason=(
                "The claim is supported only by social-media material."
            ),
            supporting_sources=supporting_sources,
        )

    if evidence.recycled_or_outdated:
        return VerificationResult(
            article=article,
            status=VerificationStatus.REJECTED,
            reason=(
                "The article appears outdated, recycled, "
                "or detached from its original event date."
            ),
            supporting_sources=supporting_sources,
        )

    if contradictions:
        return VerificationResult(
            article=article,
            status=VerificationStatus.REJECTED,
            reason=(
                "Material contradictions were found: "
                + "; ".join(contradictions)
            ),
            supporting_sources=supporting_sources,
        )

    if not evidence.trusted_original_source:
        return VerificationResult(
            article=article,
            status=VerificationStatus.INSUFFICIENT_EVIDENCE,
            reason=(
                "The original publisher has not been confirmed "
                "as a trusted news source."
            ),
            supporting_sources=supporting_sources,
        )

    if (
        len(corroborating_sources)
        < minimum_corroborating_sources
    ):
        return VerificationResult(
            article=article,
            status=VerificationStatus.INSUFFICIENT_EVIDENCE,
            reason=(
                "Not enough independent corroborating sources "
                "were found."
            ),
            supporting_sources=supporting_sources,
        )

    return VerificationResult(
        article=article,
        status=VerificationStatus.VERIFIED,
        reason=(
            "The original source is trusted and the claim "
            "has sufficient independent corroboration."
        ),
        supporting_sources=supporting_sources,
    )


def filter_verified_articles(
    results: Iterable[VerificationResult],
) -> list[Article]:
    """Return only articles explicitly approved for publication."""

    return [
        result.article
        for result in results
        if result.status is VerificationStatus.VERIFIED
    ]
