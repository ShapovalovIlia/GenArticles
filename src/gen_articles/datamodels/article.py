class Article:
    def __init__(
        self,
        url: str,
        title: str,
        description: str,
        keywords: list[str],
        text: str,
    ) -> None:

        self.url = url
        self.title = title
        self.description = description
        self.keywords = keywords
        self.text = text
