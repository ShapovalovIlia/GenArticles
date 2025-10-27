from pathlib import Path
import json
import re

INPUT_DIRS = [
    "/Users/ilasapovalov/Desktop/GenArticles/data/articles/gpt_5_nano/documents",
]
OUTPUT_FILE = "/Users/ilasapovalov/Desktop/GenArticles/data/articles/gpt_5_nano/links.json"

# Включать только файлы с этими расширениями. Пустой список => брать все файлы.
ALLOWED_EXTS = [".txt", ".md"]  # можно [] чтобы брать любые

URL_PREFIX_RE = re.compile(
    r"^\ufeff?\s*url\s*:\s*(.+)\s*$", re.IGNORECASE
)  # допускает BOM и пробелы


def iter_files(dirs):
    seen = set()
    for d in map(Path, dirs):
        if d.is_file():
            fp = d.resolve()
            if fp not in seen:
                seen.add(fp)
                yield fp
        elif d.is_dir():
            for f in sorted(d.rglob("*")):
                if f.is_file():
                    fp = f.resolve()
                    if fp not in seen:
                        seen.add(fp)
                        yield fp


def allowed(file: Path) -> bool:
    if not ALLOWED_EXTS:
        return True
    return file.suffix.lower() in {ext.lower() for ext in ALLOWED_EXTS}


def extract_url(file: Path) -> str | None:
    try:
        with file.open("r", encoding="utf-8", errors="replace") as fh:
            first = fh.readline()
    except Exception:
        return None
    m = URL_PREFIX_RE.match(first)
    if not m:
        return None
    url = m.group(1).strip()
    return url or None


def build_index(input_dirs, out_path):
    items = []
    for f in iter_files(input_dirs):
        if not allowed(f):
            continue
        url = extract_url(f)
        if not url:
            continue
        items.append(
            {
                "name": f.stem,
                "url": url,
            }
        )
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# Запуск
build_index(INPUT_DIRS, OUTPUT_FILE)
