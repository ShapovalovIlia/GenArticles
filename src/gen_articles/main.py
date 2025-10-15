import os
import asyncio
import logging

from openai import AsyncOpenAI

from gen_articles.utils import get_phrases, save_article
from gen_articles.datamodels import Config
from gen_articles.pipeline_core import generate_article


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
    logger.info("Запуск генерации статей")

    config = Config(
        csv_path="/Users/ilasapovalov/Desktop/GenArticles/data/phrases/service_city.csv",
        output_dir="/Users/ilasapovalov/Desktop/GenArticles/data/articles/gpt_5_nano",
        system_prompt_path="/Users/ilasapovalov/Desktop/GenArticles/data/system_prompts/service_city.txt",
    )

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    phrases = get_phrases(config.csv_path)

    tasks = [
        generate_article(
            client=client, system_prompt=config.system_prompt, query=q
        )
        for q in phrases
    ]


    results = await asyncio.gather(*tasks)



    for article in results:
        save_article(article, output_dir=config.output_dir)


asyncio.run(main())
