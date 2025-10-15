import re
import ast

from gen_articles.datamodels import Article

_ALLOWED_KEYS = {"url", "title", "description", "keywords"}


def _unquote(s: str) -> str:
    s = s.strip()
    if (s.startswith('"') and s.endswith('"')) or (
        s.startswith("'") and s.endswith("'")
    ):
        return s[1:-1].strip()
    return s


def _parse_keywords(raw: str) -> list[str]:
    raw = raw.strip()
    # JSON-/Python-like list: ["a","b"] or ['a','b']
    if raw.startswith("[") and raw.endswith("]"):
        try:
            val = ast.literal_eval(raw)
            if isinstance(val, (list, tuple)):
                return [str(x).strip() for x in val if str(x).strip()]
        except Exception:
            pass
    # Fallback: comma-separated line
    items = [i.strip() for i in raw.split(",")]
    # Drop empty and surrounding quotes
    out = []
    for it in items:
        it = _unquote(it)
        if it:
            out.append(it)
    return out


def parse_article(text_blob: str) -> Article:
    """
    Ожидается «плоский» фронт-маттер в первых строках:
      url: ...
      title: ...
      description: ...
      keywords: a, b, c   |  ["a","b","c"]
    Далее — произвольный основной текст (Markdown/HTML/плейнтекст).
    """
    lines = text_blob.splitlines()
    meta: dict[str, str] = {}
    body_start = 0
    seen_meta = False

    for i, line in enumerate(lines):
        # Пустая строка завершают фронт-маттер, если он уже начат
        if not line.strip():
            if seen_meta:
                body_start = i + 1
                break
            else:
                continue

        m = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$", line)
        if m:
            key = m.group(1).strip().lower()
            val = m.group(2)
            if key in _ALLOWED_KEYS:
                meta[key] = val.strip()
                seen_meta = True
                continue

        # Первая «неключевая» строка — старт тела, если фронт-маттер был
        if seen_meta:
            body_start = i
            break
        else:
            # Фронт-маттер отсутствует — всё считается телом
            body_start = 0
            break
    else:
        # Дошли до конца файла (возможен фронт-маттер без пустой строки)
        body_start = len(lines) if seen_meta else 0

    # Валидация и нормализация метаданных
    try:
        url = _unquote(meta["url"])
        title = _unquote(meta["title"])
        description = _unquote(meta["description"])
        keywords_raw = meta.get("keywords", "")
    except KeyError as e:
        missing = ", ".join(
            k for k in ("url", "title", "description") if k not in meta
        )
        raise ValueError(
            f"Отсутствуют обязательные поля фронт-маттера: {missing}"
        ) from e

    keywords = _parse_keywords(keywords_raw) if keywords_raw else []
    body = "\n".join(lines[body_start:]).strip()

    return Article(
        url=url,
        title=title,
        description=description,
        keywords=keywords,
        text=body,
    )
