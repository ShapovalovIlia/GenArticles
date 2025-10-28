import os
import asyncio
import logging

from openai import AsyncOpenAI

from gen_articles.utils import get_phrases_txt
from gen_articles.datamodels import Config
from gen_articles.gen_pipeline.pipeline_core import (
    RateLimiter,
    gen_aricle_worker,
)


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

    categorie = "document_city"
    config = Config(
        phrases_path=f"/Users/ilasapovalov/Desktop/GenArticles/data/phrases/cleaned/{categorie}.txt",
        output_dir=f"/Users/ilasapovalov/Desktop/GenArticles/data/articles/gpt_5_nano/new/{categorie}",
        system_prompt_path=f"/Users/ilasapovalov/Desktop/GenArticles/data/system_prompts/articles/new/{categorie}.txt",
    )

    os.makedirs(config.output_dir, exist_ok=True)

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    rpm = int(os.getenv("OPENAI_RPM", "30"))
    concurrency = int(os.getenv("OPENAI_CONCURRENCY", "10"))

    limiter = RateLimiter(rpm=rpm)

    # Получаем все фразы; если внутри get_phrases есть лимит — убери
    phrases = get_phrases_txt(config.phrases_path, 20)

    queue: asyncio.Queue = asyncio.Queue()
    for q in phrases:
        q = q[0].upper() + q[1:]
        queue.put_nowait(q)

    workers = [
        asyncio.create_task(
            gen_aricle_worker(
                f"w{i + 1}", queue, client, limiter, config, config.output_dir
            )
        )
        for i in range(concurrency)
    ]

    # Корректное завершение
    try:
        await queue.join()
    finally:
        for _ in workers:
            queue.put_nowait(None)
        await asyncio.gather(*workers, return_exceptions=True)

    logger.info("Генерация завершена")


if __name__ == "__main__":
    asyncio.run(main())
