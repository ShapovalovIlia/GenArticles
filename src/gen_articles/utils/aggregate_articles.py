# Склеивает все .txt из указанных папок/файлов в один файл без CLI.
# Настрой параметры ниже и запусти скрипт.

from pathlib import Path

INPUT_PATHS = [
    "/Users/ilasapovalov/Desktop/GenArticles/data/articles/gpt_5_nano/documents"
]
OUTPUT_FILE = "/Users/ilasapovalov/Desktop/GenArticles/data/articles/gpt_5_nano/documents_merged.txt"
SEPARATOR = "___________________________________________"


def iter_txt_files(paths):
    seen = set()
    for p in map(Path, paths):
        if p.is_file() and p.suffix.lower() == ".txt":
            fp = p.resolve()
            if fp not in seen:
                seen.add(fp)
                yield fp
        elif p.is_dir():
            for f in sorted(p.rglob("*.txt")):
                if f.is_file():
                    fp = f.resolve()
                    if fp not in seen:
                        seen.add(fp)
                        yield fp


def merge_txt(paths, out_path, separator=SEPARATOR):
    files = list(iter_txt_files(paths))
    if not files:
        return
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="\n") as out:
        for i, f in enumerate(files):
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
            except Exception:
                text = f.read_text(errors="replace")
            if i > 0:
                out.write("\n" + separator + "\n")
            out.write(text.rstrip("\n"))


# Запуск
merge_txt(INPUT_PATHS, OUTPUT_FILE)
