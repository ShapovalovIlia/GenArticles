import os
import asyncio
import logging

from openai import AsyncOpenAI

from gen_articles.utils import get_phrases_csv
from gen_articles.datamodels import Config


logging.basicConfig(
    level=logging.INFO,
    format="%(name)s %(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(
            "/Users/ilasapovalov/Desktop/GenArticles/data/logs/generation.log",
            encoding="utf-8",
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


async def main():
    # логику logger опускаю
    categorie = "document_city"
    config = Config(
        phrases_path=f"/Users/ilasapovalov/Desktop/GenArticles/data/phrases/{categorie}.csv",
        output_path=f"/Users/ilasapovalov/Desktop/GenArticles/data/phrases/cleaned/{categorie}.txt",
        system_prompt_path=f"/Users/ilasapovalov/Desktop/GenArticles/data/system_prompts/phrases/{categorie}.txt",
    )

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    phrases = get_phrases_csv(config.phrases_path)

    # корректная разбивка по 30
    batches = [phrases[i : i + 30] for i in range(0, len(phrases), 30)]

    # загрузка system prompt
    with open(config.system_prompt_path, "r", encoding="utf-8") as f:
        system_prompt = f.read().strip()

    # гарантируем существование директории
    os.makedirs(os.path.dirname(config.output_path), exist_ok=True)

    with open(config.output_path, "w", encoding="utf-8") as file:
        for batch in batches:
            if not batch:
                continue
            response = await client.chat.completions.create(
                model="gpt-5-nano",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": "Поисковые фразы:\n" + "\n".join(batch),
                    },
                ],
            )
            content = response.choices[0].message.content or ""
            file.write(content + "\n")


if __name__ == "__main__":
    asyncio.run(main())
