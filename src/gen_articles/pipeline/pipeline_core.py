import logging

from openai import AsyncOpenAI

from gen_articles.datamodels import Article, Config
from gen_articles.utils import parse_article


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
        print(response.choices[0].message)

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
