from pathlib import Path
from markdown import markdownFromFile

input_dir = Path("data/articles/gpt_5_nano/new/txt/document_city")
output_dir = Path("data/articles/gpt_5_nano/new/html/document_city")

output_dir.mkdir(parents=True, exist_ok=True)

for src_path in input_dir.iterdir():
    if not src_path.is_file():
        continue

    dest_path = output_dir / (src_path.stem + ".html")

    html_output = markdownFromFile(input=str(src_path), output=str(dest_path))
