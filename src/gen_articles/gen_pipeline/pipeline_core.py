import asyncio
import logging
import random
from typing import Optional

from openai import (
    AsyncOpenAI,
    RateLimitError,
    APIConnectionError,
    APIStatusError,
    APIError,
    BadRequestError,
)

from gen_articles.datamodels import Article, Config
from gen_articles.utils import parse_article, save_article


logger = logging.getLogger(__name__)


async def generate_article(
    system_prompt: str, client: AsyncOpenAI, query: str
) -> Article:
    logging.info(f"Генерация статьи для фразы: {query}")

    try:
        response = await client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Поисковая фраза: {query}"},
            ],
        )

        article = parse_article(response.choices[0].message.content.strip())

        usage = getattr(response, "usage", None)
        # Совместимо и с Responses API, и с Chat Completions
        prompt_tokens = getattr(usage, "prompt_tokens", None) or getattr(
            usage, "input_tokens", 0
        )
        completion_tokens = getattr(
            usage, "completion_tokens", None
        ) or getattr(usage, "output_tokens", 0)
        total_tokens = getattr(
            usage, "total_tokens", prompt_tokens + completion_tokens
        )

        logger.info(
            "Успешно: %s, Токены: prompt=%s, completion=%s, total=%s",
            query,
            prompt_tokens,
            completion_tokens,
            total_tokens,
        )

        return article

    except Exception as e:
        logging.error(f"Ошибка при генерации для '{query}': {e}")

        return ""


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


async def retry(
    coro_factory, *, attempts: int = 6, base: float = 0.6, cap: float = 20.0
):
    """Экспоненциальный бэкофф с джиттером для 429/5xx/сетевых ошибок."""
    for i in range(attempts):
        try:
            return await coro_factory()
        except BadRequestError as e:
            # 4xx по вине запроса – ретраи бессмысленны.
            logger.error("Невалидный запрос без ретраев: %r", e)
            raise
        except (
            RateLimitError,
            APIConnectionError,
            APIStatusError,
            APIError,
            TimeoutError,
        ) as e:
            backoff = min(cap, base * (2**i)) * (1.0 + random.random() * 0.2)
            logger.warning(
                "Ретрай %d/%d через %.2fs из-за: %r",
                i + 1,
                attempts,
                backoff,
                e,
            )
            await asyncio.sleep(backoff)
    # финальная попытка
    return await coro_factory()


async def gen_aricle_worker(
    name: str,
    queue: asyncio.Queue,
    client: AsyncOpenAI,
    limiter: RateLimiter,
    config: Config,
    output_dir: str,
):
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
                return await generate_article(
                    client=client,
                    system_prompt=config.system_prompt,
                    query=phrase,
                )

            article = await retry(call)
            save_article(article, output_dir=output_dir)
            logger.info("✓ Сгенерировано: %s", phrase)
        except Exception as e:
            logger.exception("✗ Ошибка при обработке '%s': %r", phrase, e)
        finally:
            queue.task_done()


async def normalize_phrases_worker(
    name: str,
    queue: asyncio.Queue,
    client: AsyncOpenAI,
    limiter: RateLimiter,
    config: Config,
    output_dir: str,
):
    while True:
        item: Optional[str] = await queue.get()

        if item is None:
            queue.task_done()
            logger.info("Воркер %s завершён", name)
            return

        phrase = item
        try:
            await limiter.wait()

            phrases = []

            async def call():
                return await generate_article(
                    client=client,
                    system_prompt=config.system_prompt,
                    query=phrase,
                )

            article = await retry(call)

            save_article(article, output_dir=output_dir)
            logger.info("✓ Сгенерировано: %s", phrase)

        except Exception as e:
            logger.exception("✗ Ошибка при обработке '%s': %r", phrase, e)
        finally:
            queue.task_done()
