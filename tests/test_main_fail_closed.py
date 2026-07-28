from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from src import main as main_module


class MainFailureTests(unittest.TestCase):
    """Ensure production failures stop GitHub Actions instead of looking successful."""

    @patch.object(main_module, "produce_and_publish")
    @patch.object(main_module, "run_pipeline")
    @patch.object(main_module, "setup_logger")
    @patch.object(main_module, "load_config")
    def test_media_failure_is_raised(
        self,
        load_config: Mock,
        setup_logger: Mock,
        run_pipeline: Mock,
        produce_and_publish: Mock,
    ) -> None:
        load_config.return_value = {
            "project": {"language": "ar"},
            "ai": {"enabled": False, "model": "test-model"},
            "logging": {},
            "production": {"enabled": True},
        }
        setup_logger.return_value = Mock()
        article = SimpleNamespace(fingerprint="article-1")
        package = SimpleNamespace(
            title_ar="عنوان عربي",
            tags=(),
            hashtags=(),
        )
        run_pipeline.return_value = SimpleNamespace(
            selected=[article],
            editorial={"article-1": package},
        )
        produce_and_publish.side_effect = RuntimeError("upload failed")

        with self.assertRaisesRegex(RuntimeError, "upload failed"):
            main_module.main()


if __name__ == "__main__":
    unittest.main()
