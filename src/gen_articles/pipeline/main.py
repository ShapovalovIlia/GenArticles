import os
import asyncio
import logging

from openai import AsyncOpenAI

from gen_articles.utils import get_phrases
from gen_articles.datamodels import Config
from gen_articles.pipeline.pipeline_core import RateLimiter, gen_aricle_worker


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

    categorie = "new/"
    config = Config(
        csv_path=f"/Users/ilasapovalov/Desktop/GenArticles/data/phrases/cleaned/{categorie}.csv",
        output_dir=f"/Users/ilasapovalov/Desktop/GenArticles/data/articles/gpt_5_nano/{categorie}",
        system_prompt_path=f"/Users/ilasapovalov/Desktop/GenArticles/data/system_prompts/{categorie}.txt",
    )

    os.makedirs(config.output_dir, exist_ok=True)

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    rpm = int(os.getenv("OPENAI_RPM", "30"))
    concurrency = int(os.getenv("OPENAI_CONCURRENCY", "10"))

    limiter = RateLimiter(rpm=rpm)

    # Получаем все фразы; если внутри get_phrases есть лимит — убери
    phrases = get_phrases(config.csv_path)

    queue: asyncio.Queue = asyncio.Queue()
    for q in phrases:
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
