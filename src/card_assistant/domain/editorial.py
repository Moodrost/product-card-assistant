import re

from card_assistant.domain.models import (
    Card,
    Characteristic,
    CommercialBlock,
    EditorialPlan,
    InvalidPlan,
    MissingField,
    Product,
)

NO_DATA = "данных нет"


def source_sentences(product: Product) -> tuple[str, ...]:
    """Whole sentences retain negations; decimal points are not split."""
    if not product.description:
        return ()
    text = " ".join(product.description.split())
    return tuple(s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip())


def validate_plan(product: Product, plan: EditorialPlan) -> None:
    available = {s.key for s in product.specs if s.value}
    sentences = source_sentences(product)
    if plan.title_style not in {"name", "name_manufacturer"}:
        raise InvalidPlan("Неизвестный вариант заголовка.")
    if plan.buyer_focus not in {"procurement", "engineering"}:
        raise InvalidPlan("Неизвестная аудитория.")
    for keys, limit in ((plan.highlighted_spec_keys, 4), (plan.query_spec_keys, 2)):
        if len(keys) > limit or len(set(keys)) != len(keys) or not set(keys) <= available:
            raise InvalidPlan("Модель сослалась на отсутствующую характеристику.")
    ids = plan.description_sentence_ids
    if len(ids) > 2 or len(set(ids)) != len(ids):
        raise InvalidPlan("Некорректные ссылки на исходное описание.")
    if any(type(i) is not int or not 0 <= i < len(sentences) for i in ids):
        raise InvalidPlan("Модель сослалась на отсутствующее предложение.")


def missing_fields(product: Product) -> tuple[MissingField, ...]:
    missing = []
    if not product.manufacturer:
        missing.append(MissingField("manufacturer", "Уточните производителя: данных нет."))
    if not product.description:
        missing.append(MissingField("description", "Добавьте назначение или фрагмент паспорта."))
    if not product.specs:
        missing.append(MissingField("specs", "Технические характеристики: данных нет."))
    known = {s.key: s.value for s in product.specs}
    keys = dict.fromkeys(
        [s.key for s in product.specs if not s.value] + list(product.expected_specs)
    )
    for key in keys:
        if not known.get(key):
            missing.append(MissingField(f"specs.{key}", f"{key}: данных нет; требуется уточнение."))
    return tuple(missing)


def _title(product: Product, plan: EditorialPlan) -> tuple[str, bool]:
    title = product.name
    if plan.title_style == "name_manufacturer" and product.manufacturer:
        combined = f"{product.name} — {product.manufacturer}"
        if len(combined) <= 70:
            title = combined
    if len(title) <= 70:
        return title, False
    cut = title[:69].rsplit(" ", 1)[0] or title[:69]
    return cut + "…", True


def _description(product: Product, plan: EditorialPlan) -> tuple[str, tuple[int, ...]]:
    # Only complete source units are inserted. Never truncate a unit/value/negation.
    intro = f"{product.name}. Производитель: {product.manufacturer or NO_DATA}."
    facts = {s.key: s.value for s in product.specs if s.value}
    evidence: list[str] = []
    selected_ids: list[int] = []
    budget = 420 - len(intro)
    for i in plan.description_sentence_ids:
        fragment = f"В исходном описании указано: «{source_sentences(product)[i]}»."
        if len(fragment) <= budget:
            evidence.append(fragment)
            selected_ids.append(i)
            budget -= len(fragment) + 1
    for key in plan.highlighted_spec_keys:
        fragment = f"{key}: {facts[key]}."
        if len(fragment) <= budget:
            evidence.append(fragment)
            budget -= len(fragment) + 1
    if not evidence:
        evidence.append("Назначение и параметры следует уточнить по полным исходным данным.")

    focus = {
        "procurement": (
            "Для подготовки закупки сопоставьте указанные параметры с техническим заданием. "
            "При сравнении предложений проверяйте полное обозначение и исполнение прибора: "
            "совпадение названия само по себе не подтверждает совместимость."
        ),
        "engineering": (
            "Для технического подбора сопоставьте приведённые сведения с условиями применения. "
            "До включения прибора в проект проверьте полное обозначение и исполнение: "
            "по одному названию нельзя подтвердить совместимость с оборудованием."
        ),
    }[plan.buyer_focus]
    closing = (
        "Полный перечень переданных характеристик приведён отдельно. Для пропущенных значений "
        "используется пометка «данных нет»; она требует уточнения, "
        "а не означает отсутствие функции. "
        "Перед заказом согласуйте с поставщиком сведения, которых нет в исходных материалах. "
        "Условия поставки, наличие и комплектация здесь не подтверждены. "
        "Это черновик карточки: перед публикацией сверьте его с актуальным паспортом производителя."
    )
    text = "\n\n".join([intro + " " + " ".join(evidence), focus, closing])
    # Sparse input cannot honestly produce 800 characters of technical facts.
    # The remainder is explicit purchasing guidance, never invented product benefits.
    if len(text) < 800:
        text += (
            " Не переносите параметры похожих моделей в эту карточку. "
            "Используйте описание как основу для обсуждения требований с менеджером."
        )
    if not 800 <= len(text) <= 1200:
        raise InvalidPlan("Не удалось собрать описание в пределах 800–1200 символов.")
    return text, tuple(selected_ids)


def build_card(product: Product, plan: EditorialPlan) -> Card:
    validate_plan(product, plan)
    title, shortened = _title(product, plan)
    description, sentence_ids = _description(product, plan)
    missing = missing_fields(product)
    characteristics = [
        Characteristic(
            "Производитель",
            product.manufacturer or NO_DATA,
            "manufacturer" if product.manufacturer else None,
        )
    ]
    for spec in product.specs:
        characteristics.append(
            Characteristic(
                spec.key, spec.value or NO_DATA, f"specs.{spec.key}" if spec.value else None
            )
        )
    existing = {s.key for s in product.specs}
    for key in product.expected_specs:
        if key not in existing:
            characteristics.append(Characteristic(key, NO_DATA, None))
    if not product.specs and not product.expected_specs:
        characteristics.append(Characteristic("Технические характеристики", NO_DATA, None))

    queries = [product.name]
    if product.manufacturer:
        queries.append(f"{product.name} {product.manufacturer}")
    values = {s.key: s.value for s in product.specs}
    queries.extend(f"{product.name} {k} {values[k]}" for k in plan.query_spec_keys)
    queries.extend(
        [f"{product.name} характеристики", f"{product.name} описание", f"{product.name} подбор"]
    )
    queries = list(dict.fromkeys(queries))[:5]
    task = "Подбор по переданным характеристикам; конкретное назначение требует уточнения."
    if sentence_ids:
        task = (
            "Заявленное назначение и сведения из описания: "
            f"«{source_sentences(product)[sentence_ids[0]]}»."
        )
    return Card(
        seo_title=title,
        seo_description=description,
        characteristics=tuple(characteristics),
        search_queries=tuple(queries),
        commercial=CommercialBlock(
            audience={
                "procurement": "Специалистам по закупке контрольно-измерительных приборов.",
                "engineering": "Инженерам, подбирающим прибор по техническому заданию.",
            }[plan.buyer_focus],
            task=task,
            caveat=(
                "Пригодность для конкретной среды и условий эксплуатации "
                "необходимо подтвердить по паспорту."
            ),
        ),
        missing_fields=missing,
        warnings=(
            "Исходные данные не проверялись по внешним источникам; "
            "требуется редакторская проверка.",
        )
        + (
            ("Название сокращено для SEO; полное наименование сохранено во входных данных.",)
            if shortened
            else ()
        ),
        source_sentence_ids=sentence_ids,
        source_description=product.description,
    )
