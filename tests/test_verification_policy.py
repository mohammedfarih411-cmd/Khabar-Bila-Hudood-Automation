from datetime import datetime, timezone
import unittest

from src.news import Article
from src.verification import (
    VerificationEvidence,
    VerificationStatus,
    filter_verified_articles,
    verify_article,
)


def make_article(
    *,
    url: str = "https://example.com/news/verified",
    source: str = "BBC News",
) -> Article:
    return Article(
        title="Verified test article",
        url=url,
        source=source,
        summary="A test summary.",
        published_at=datetime(
            2026,
            7,
            25,
            8,
            0,
            tzinfo=timezone.utc,
        ),
        priority_score=1,
    )


class VerificationPolicyTests(unittest.TestCase):
    def test_verifies_trusted_and_corroborated_article(self) -> None:
        result = verify_article(
            make_article(),
            VerificationEvidence(
                trusted_original_source=True,
                corroborating_sources=("Reuters",),
            ),
        )

        self.assertEqual(
            result.status,
            VerificationStatus.VERIFIED,
        )
        self.assertEqual(
            result.supporting_sources,
            ("BBC News", "Reuters"),
        )

    def test_rejects_social_media_only_claim(self) -> None:
        result = verify_article(
            make_article(),
            VerificationEvidence(
                trusted_original_source=False,
                social_media_only=True,
            ),
        )

        self.assertEqual(
            result.status,
            VerificationStatus.REJECTED,
        )

    def test_rejects_material_contradiction(self) -> None:
        result = verify_article(
            make_article(),
            VerificationEvidence(
                trusted_original_source=True,
                corroborating_sources=("Reuters",),
                contradictions=(
                    "Conflicting casualty figures",
                ),
            ),
        )

        self.assertEqual(
            result.status,
            VerificationStatus.REJECTED,
        )

    def test_rejects_recycled_or_outdated_article(self) -> None:
        result = verify_article(
            make_article(),
            VerificationEvidence(
                trusted_original_source=True,
                recycled_or_outdated=True,
            ),
        )

        self.assertEqual(
            result.status,
            VerificationStatus.REJECTED,
        )

    def test_marks_untrusted_source_as_insufficient(self) -> None:
        result = verify_article(
            make_article(source="Unknown Blog"),
            VerificationEvidence(
                trusted_original_source=False,
                corroborating_sources=("Reuters",),
            ),
        )

        self.assertEqual(
            result.status,
            VerificationStatus.INSUFFICIENT_EVIDENCE,
        )

    def test_requires_minimum_corroboration(self) -> None:
        result = verify_article(
            make_article(),
            VerificationEvidence(
                trusted_original_source=True,
            ),
        )

        self.assertEqual(
            result.status,
            VerificationStatus.INSUFFICIENT_EVIDENCE,
        )

    def test_original_source_does_not_count_as_corroboration(
        self,
    ) -> None:
        result = verify_article(
            make_article(),
            VerificationEvidence(
                trusted_original_source=True,
                corroborating_sources=("BBC News",),
            ),
        )

        self.assertEqual(
            result.status,
            VerificationStatus.INSUFFICIENT_EVIDENCE,
        )

    def test_publish_gate_returns_only_verified_articles(
        self,
    ) -> None:
        verified_article = make_article(
            url="https://example.com/news/one"
        )
        rejected_article = make_article(
            url="https://example.com/news/two"
        )

        verified_result = verify_article(
            verified_article,
            VerificationEvidence(
                trusted_original_source=True,
                corroborating_sources=("Reuters",),
            ),
        )

        rejected_result = verify_article(
            rejected_article,
            VerificationEvidence(
                trusted_original_source=False,
                social_media_only=True,
            ),
        )

        self.assertEqual(
            filter_verified_articles(
                [verified_result, rejected_result]
            ),
            [verified_article],
        )


if __name__ == "__main__":
    unittest.main()
