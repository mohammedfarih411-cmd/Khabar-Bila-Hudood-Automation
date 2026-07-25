from datetime import datetime, timezone
import json
from types import SimpleNamespace
import unittest

from src.news import Article
from src.verification import (
    GeminiEditorialVerifier,
    GeminiEvidenceAssessment,
    VerificationStatus,
)


class FakeResponse:
    def __init__(
        self,
        *,
        text: str = "",
        parsed=None,
        candidates=None,
    ) -> None:
        self.text = text
        self.parsed = parsed
        self.candidates = candidates or []


class FakeModels:
    def __init__(self, responses) -> None:
        self.responses = list(responses)
        self.calls = []

    def generate_content(
        self,
        *,
        model,
        contents,
        config,
    ):
        self.calls.append(
            {
                "model": model,
                "contents": contents,
                "config": config,
            }
        )

        if not self.responses:
            raise AssertionError("No fake response available")

        return self.responses.pop(0)


class FakeClient:
    def __init__(self, responses) -> None:
        self.models = FakeModels(responses)


def make_article() -> Article:
    return Article(
        title="Government announces a new public measure",
        url="https://example.com/news/measure",
        source="Example News",
        summary="A concise RSS summary.",
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


def grounded_candidate():
    return SimpleNamespace(
        grounding_metadata=SimpleNamespace(
            grounding_chunks=[
                SimpleNamespace(
                    web=SimpleNamespace(
                        title="Reuters",
                        uri="https://www.reuters.com/example",
                    )
                )
            ]
        )
    )


class GeminiEditorialVerifierTests(unittest.TestCase):
    def test_verifies_grounded_and_corroborated_article(
        self,
    ) -> None:
        assessment = GeminiEvidenceAssessment(
            trusted_original_source=True,
            corroborating_sources=(
                ["Reuters | https://www.reuters.com/example"]
            ),
            contradictions=[],
            social_media_only=False,
            recycled_or_outdated=False,
            rationale="The central facts are independently supported.",
        )

        client = FakeClient(
            [
                FakeResponse(
                    text="Reuters independently confirms the event.",
                    candidates=[grounded_candidate()],
                ),
                FakeResponse(parsed=assessment),
            ]
        )

        verifier = GeminiEditorialVerifier(client=client)
        audit = verifier.verify(make_article())

        self.assertEqual(
            audit.result.status,
            VerificationStatus.VERIFIED,
        )
        self.assertEqual(
            audit.research.sources,
            (
                "Reuters | "
                "https://www.reuters.com/example",
            ),
        )
        self.assertEqual(len(client.models.calls), 2)

    def test_rejects_material_contradictions(self) -> None:
        assessment = GeminiEvidenceAssessment(
            trusted_original_source=True,
            corroborating_sources=["Reuters"],
            contradictions=["The reported date does not match."],
            social_media_only=False,
            recycled_or_outdated=False,
            rationale="Sources report different dates.",
        )

        client = FakeClient(
            [
                FakeResponse(text="Conflicting dates were found."),
                FakeResponse(parsed=assessment),
            ]
        )

        audit = GeminiEditorialVerifier(
            client=client
        ).verify(make_article())

        self.assertEqual(
            audit.result.status,
            VerificationStatus.REJECTED,
        )

    def test_parses_json_when_parsed_value_is_unavailable(
        self,
    ) -> None:
        payload = {
            "trusted_original_source": False,
            "corroborating_sources": [],
            "contradictions": [],
            "social_media_only": False,
            "recycled_or_outdated": False,
            "rationale": "The publisher could not be confirmed.",
        }

        client = FakeClient(
            [
                FakeResponse(text="Insufficient publisher evidence."),
                FakeResponse(text=json.dumps(payload)),
            ]
        )

        audit = GeminiEditorialVerifier(
            client=client
        ).verify(make_article())

        self.assertEqual(
            audit.result.status,
            VerificationStatus.INSUFFICIENT_EVIDENCE,
        )

    def test_rejects_empty_research_response(self) -> None:
        verifier = GeminiEditorialVerifier(
            client=FakeClient([FakeResponse(text="")])
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "no grounded research text",
        ):
            verifier.research_article(make_article())


if __name__ == "__main__":
    unittest.main()
