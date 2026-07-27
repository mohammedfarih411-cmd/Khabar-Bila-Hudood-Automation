# AGENTS.md

## Working rules

- Never commit API keys, OAuth client secrets, refresh tokens, cookies, or generated credential files.
- Store runtime credentials in GitHub Actions secrets or local environment variables.
- Keep YouTube uploads private by default.
- Do not publish an article unless verification and editorial checks pass.
- Prefer deterministic filtering and duplicate checks before calling paid AI APIs.
- Every behavior change must include or update tests.
- Work on a feature branch and merge through a pull request after CI passes.
- Do not log full AI responses, tokens, credentials, or personal data.
- Treat failures in verification, media generation, or upload as fail-closed: do not publish.

## Commands

```bash
python -m unittest discover -s tests -v
python -m src.main
```
