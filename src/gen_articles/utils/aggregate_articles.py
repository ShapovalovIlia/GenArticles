import re
import html
from pathlib import Path

SEPARATOR = "___________________________________________"

_FIRST_P_RE = re.compile(
    r"^\ufeff?\s*<p\b[^>]*>(?P<meta>.*?)</p>\s*", re.IGNORECASE | re.DOTALL
)


def _find_html_files(root: Path):
    return sorted(p for p in Path(root).rglob("*.html") if p.is_file())


def _extract(text: str):
    m = _FIRST_P_RE.match(text)
    if not m:
        return None, text
    meta = html.unescape(m.group("meta").strip())
    body = text[m.end() :]
    return meta, body


def merge_html(input_dir: str, out_path: str, separator: str = SEPARATOR):
    files = _find_html_files(Path(input_dir))
    if not files:
        return
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open("w", encoding="utf-8", newline="\n") as fh:
        for i, f in enumerate(files):
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
            except Exception:
                text = f.read_text(errors="replace")

            meta, body = _extract(text)

            if i > 0:
                fh.write("\n" + separator + "\n")

            if meta is not None:
                fh.write(meta.rstrip() + "\n")
                fh.write("\n")
                fh.write(body.rstrip("\n"))
            else:
                fh.write(text.rstrip("\n"))


merge_html(
    "data/articles/gpt_5_nano/new/html/document_city",
    "data/articles/gpt_5_nano/new/result/document_city_merged.txt",
)
