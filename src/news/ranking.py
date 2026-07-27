from __future__ import annotations

from ..models import Article

ITALY_TERMS = {"italy", "italia", "italian", "rome", "roma", "milan", "milano"}
IMMIGRATION_TERMS = {
    "immigration", "immigrant", "migrant", "migration", "refugee", "asylum",
    "هجرة", "مهاجر", "لاجئ", "لجوء",
}
EXCLUDED_TERMS = {
    "economy", "finance", "stocks", "crypto", "market", "اقتصاد", "بورصة", "عملات رقمية",
}


def classify_and_score(article: Article) -> Article:
    text = f"{article.title} {article.summary}".casefold()
    tokens = set(text.replace("-", " ").split())

    if tokens & EXCLUDED_TERMS:
        article.category = "excluded"
        article.score = -100.0
    elif tokens & ITALY_TERMS:
        article.category = "italy"
        article.score = 30.0
    elif tokens & IMMIGRATION_TERMS:
        article.category = "immigration"
        article.score = 20.0
    else:
        article.category = "world"
        article.score = 10.0

    article.score += min(len(article.summary) / 500.0, 2.0)
    return article


def rank_articles(articles: list[Article]) -> list[Article]:
    ranked = [classify_and_score(article) for article in articles]
    return sorted(
        (article for article in ranked if article.category != "excluded"),
        key=lambda article: (article.score, article.published_at),
        reverse=True,
    )
