import os
import asyncio
import logging
import random
from typing import Optional

from openai import AsyncOpenAI

try:
    from openai import RateLimitError, APIConnectionError, APIStatusError, APIError, BadRequestError
except Exception:  # совместимость
    RateLimitError = APIConnectionError = APIStatusError = APIError = BadRequestError = Exception

from gen_articles.utils import get_phrases, save_article
from gen_articles.datamodels import Config
from gen_articles.pipeline.pipeline_core import generate_article


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


class RateLimiter:
    """Простой троттлинг по RPM (requests per minute) с взаимным исключением."""
    def __init__(self, rpm: int):
        rpm = max(1, int(rpm))
        self.min_interval = 60.0 / rpm
        self._lock = asyncio.Lock()
        self._last_ts = 0.0

    async def wait(self) -> None:
        async with self._lock:
            loop = asyncio.get_running_loop()
            now = loop.time()
            wait_for = self.min_interval - (now - self._last_ts)
            if wait_for > 0:
                await asyncio.sleep(wait_for)
            self._last_ts = loop.time()


async def retry(coro_factory, *, attempts: int = 6, base: float = 0.6, cap: float = 20.0):
    """Экспоненциальный бэкофф с джиттером для 429/5xx/сетевых ошибок."""
    for i in range(attempts):
        try:
            return await coro_factory()
        except BadRequestError as e:
            # 4xx по вине запроса – ретраи бессмысленны.
            logger.error("Невалидный запрос без ретраев: %r", e)
            raise
        except (RateLimitError, APIConnectionError, APIStatusError, APIError, TimeoutError) as e:
            backoff = min(cap, base * (2 ** i)) * (1.0 + random.random() * 0.2)
            logger.warning("Ретрай %d/%d через %.2fs из-за: %r", i + 1, attempts, backoff, e)
            await asyncio.sleep(backoff)
    # финальная попытка
    return await coro_factory()


async def worker(name: str,
                 queue: asyncio.Queue,
                 client: AsyncOpenAI,
                 limiter: RateLimiter,
                 config: Config,
                 output_dir: str):
    while True:
        item: Optional[str] = await queue.get()
        if item is None:
            queue.task_done()
            logger.info("Воркер %s завершён", name)
            return

        phrase = item
        try:
            await limiter.wait()

            async def call():
                # Если generate_article принимает client с опциями таймаута – лучше жёстко задавать:
                # client_opt = client.with_options(timeout=60)
                # return await generate_article(client=client_opt, system_prompt=config.system_prompt, query=phrase)
                return await generate_article(client=client, system_prompt=config.system_prompt, query=phrase)

            article = await retry(call)
            save_article(article, output_dir=output_dir)
            logger.info("✓ Сгенерировано: %s", phrase)
        except Exception as e:
            logger.exception("✗ Ошибка при обработке '%s': %r", phrase, e)
        finally:
            queue.task_done()


async def main():
    logger.info("Запуск генерации статей")

    categorie = "document_city"
    config = Config(
        csv_path=f"/Users/ilasapovalov/Desktop/GenArticles/data/phrases/{categorie}.csv",
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
        asyncio.create_task(worker(f"w{i+1}", queue, client, limiter, config, config.output_dir))
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
