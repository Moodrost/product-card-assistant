import re

from card_assistant.domain.models import Card


def escape_md(value: str, *, multiline: bool = False) -> str:
    if not multiline:
        value = value.replace("\n", " ").replace("\r", " ")
    return re.sub(r"([\\`*_{}\[\]()<>#+!|~-])", r"\\\1", value)


def to_markdown(card: Card) -> str:
    lines = [
        f"# {escape_md(card.seo_title)}",
        "",
        "## SEO-описание",
        "",
        escape_md(card.seo_description, multiline=True),
        "",
        "## Характеристики",
        "",
        "| Параметр | Значение |",
        "| --- | --- |",
        *[f"| {escape_md(c.name)} | {escape_md(c.value)} |" for c in card.characteristics],
        "",
        "## Поисковые запросы",
        "",
        *[f"- {escape_md(q)}" for q in card.search_queries],
        "",
        "## Для менеджера",
        "",
        escape_md(card.commercial.audience),
        "",
        escape_md(card.commercial.task),
        "",
        escape_md(card.commercial.caveat),
        "",
        "## Перед публикацией",
        "",
        *[f"- {escape_md(m.message)}" for m in card.missing_fields],
        *[f"- {escape_md(w)}" for w in card.warnings],
    ]
    if card.source_description:
        lines += [
            "",
            "## Полное исходное описание (для проверки)",
            "",
            escape_md(card.source_description, multiline=True),
        ]
    return "\n".join(lines) + "\n"
