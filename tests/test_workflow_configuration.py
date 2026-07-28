from pathlib import Path
import unittest


class WorkflowConfigurationTests(unittest.TestCase):
    """Guard the automatic production wiring in GitHub Actions."""

    def test_news_workflow_runs_every_thirty_minutes(self) -> None:
        workflow = Path(".github/workflows/news.yml").read_text(encoding="utf-8")

        self.assertIn('cron: "*/30 * * * *"', workflow)
        self.assertIn("github.event_name == 'schedule'", workflow)

    def test_news_workflow_wires_required_secrets_and_database_cache(self) -> None:
        workflow = Path(".github/workflows/news.yml").read_text(encoding="utf-8")

        for secret in (
            "GEMINI_API_KEY",
            "ELEVENLABS_API_KEY",
            "ELEVENLABS_VOICE_ID",
            "YOUTUBE_TOKEN_JSON",
        ):
            self.assertIn(f"secrets.{secret}", workflow)
        self.assertIn("actions/cache/restore@v4", workflow)
        self.assertIn("actions/cache/save@v4", workflow)
        self.assertIn("data/news.db", workflow)


if __name__ == "__main__":
    unittest.main()
