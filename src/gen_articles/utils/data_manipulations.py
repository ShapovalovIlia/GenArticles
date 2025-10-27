import logging
from pathlib import Path

import pandas as pd

from gen_articles.datamodels import Article, Config

logger = logging.getLogger(__name__)


def get_phrases(path: str, max_phrases: int | None = None) -> list[str]:
    if max_phrases:
        df = pd.read_csv(path).head(max_phrases)
    else:
        df = pd.read_csv(path)

    phrases = [str(x) for x in df["Фраза"].dropna().tolist()]

    logger.info(f"Считано {len(phrases)} фраз, путь {path}")

    return phrases


def save_article(article: Article, output_dir: str) -> None:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    file_path = output_dir / f"{article.title}.txt"

    keywords = ", ".join(article.keywords or [])

    content = (
        f"url: {article.url}\n"
        f"title: {article.title}\n"
        f"description: {article.description}\n"
        f"keywords: {keywords}\n\n"
        f"{article.text}\n"
    )

    with file_path.open(mode="w", encoding="utf-8", newline="\n") as f:
        f.write(content)

    logger.info(f"Сохранено: {file_path}")


def save_article(article: Article, output_dir: str) -> None:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    file_path = output_dir / f"{article.title}.txt"

    keywords = ", ".join(article.keywords or [])

    content = (
        f"url: {article.url}\n"
        f"title: {article.title}\n"
        f"description: {article.description}\n"
        f"keywords: {keywords}\n\n"
        f"{article.text}\n"
    )

    with file_path.open(mode="w", encoding="utf-8", newline="\n") as f:
        f.write(content)

    logger.info(f"Сохранено: {file_path}")


def save_article(article: Article, output_dir: str) -> None:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    file_path = output_dir / f"{article.title}.txt"

    keywords = ", ".join(article.keywords or [])

    content = (
        f"url: {article.url}\n"
        f"title: {article.title}\n"
        f"description: {article.description}\n"
        f"keywords: {keywords}\n\n"
        f"{article.text}\n"
    )

    with file_path.open(mode="w", encoding="utf-8", newline="\n") as f:
        f.write(content)

    logger.info(f"Сохранено: {file_path}")
