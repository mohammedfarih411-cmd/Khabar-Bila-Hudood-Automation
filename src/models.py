from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib


@dataclass(slots=True)
class Article:
    title: str
    url: str
    source: str
    summary: str = ""
    published_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    category: str = "world"
    score: float = 0.0

    @property
    def fingerprint(self) -> str:
        normalized = " ".join(self.title.casefold().split())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
