from dataclasses import replace

import pytest

from card_assistant.adapters.planners import DemoPlanner
from card_assistant.domain.editorial import build_card, source_sentences
from card_assistant.domain.models import EditorialPlan, Fact, InvalidPlan, Product
from card_assistant.web.schemas import ProductInput


async def test_examples_keep_exact_values_and_required_lengths(products):
    for item in products:
        product = ProductInput.model_validate(item).to_domain()
        card = build_card(product, await DemoPlanner().plan(product))
        assert 1 <= len(card.seo_title) <= 70
        assert 800 <= len(card.seo_description) <= 1200
        assert 3 <= len(card.search_queries) <= 5
        assert len(card.search_queries) == len(set(card.search_queries))
        values = {c.name: c.value for c in card.characteristics}
        for fact in product.specs:
            assert values[fact.key] == (fact.value or "данных нет")
        assert card.commercial.audience and card.commercial.task


async def test_sparse_input_reports_unknowns_without_inventing_specs():
    product = Product("X", None, (), None, ("точность",))
    card = build_card(product, await DemoPlanner().plan(product))
    assert {m.field for m in card.missing_fields} == {
        "manufacturer",
        "description",
        "specs",
        "specs.точность",
    }
    assert all(c.value == "данных нет" and c.source is None for c in card.characteristics)
    assert 800 <= len(card.seo_description) <= 1200


@pytest.mark.parametrize(
    "change",
    [
        {"highlighted_spec_keys": ("взрывозащита",)},
        {"query_spec_keys": ("питание",)},
        {"description_sentence_ids": (-1,)},
        {"description_sentence_ids": (999,)},
        {"description_sentence_ids": (True,)},
        {"highlighted_spec_keys": ("класс точности", "класс точности")},
    ],
)
async def test_unsupported_evidence_is_rejected(product, change):
    plan = await DemoPlanner().plan(product)
    with pytest.raises(InvalidPlan):
        build_card(product, replace(plan, **change))


async def test_negation_is_preserved_as_a_whole_sentence():
    product = Product(
        "Датчик",
        None,
        (Fact("погрешность", "0.5 %"),),
        "Точность 0.5 %. Не подходит для газа. Для газа нужна другая модель.",
    )
    assert source_sentences(product) == (
        "Точность 0.5 %.",
        "Не подходит для газа.",
        "Для газа нужна другая модель.",
    )
    plan = EditorialPlan("name", ("погрешность",), (1,), "engineering", ())
    card = build_card(product, plan)
    assert "«Не подходит для газа.»" in card.seo_description
    assert "«Не подходит для газа.»" in card.commercial.task


@pytest.mark.parametrize("linebreak", ["\n", "\r\n", "\n\n"])
def test_line_wrapping_cannot_separate_a_negation(linebreak):
    product = Product("Датчик", None, (), f"Не{linebreak}подходит для газа.")
    assert source_sentences(product) == ("Не подходит для газа.",)
    plan = EditorialPlan("name", (), (0,), "engineering", ())
    card = build_card(product, plan)
    assert "«Не подходит для газа.»" in card.seo_description
    assert card.source_description == product.description
    with pytest.raises(InvalidPlan):
        build_card(product, replace(plan, description_sentence_ids=(1,)))


async def test_large_evidence_is_omitted_whole_and_remains_in_characteristics():
    product = Product("Н" * 160, "П" * 120, (Fact("длинный параметр", "З" * 200),), "Д" * 6000)
    card = build_card(product, await DemoPlanner().plan(product))
    assert len(card.seo_title) <= 70
    assert 800 <= len(card.seo_description) <= 1200
    assert "З" * 200 not in card.seo_description
    assert card.characteristics[1].value == "З" * 200
    assert card.source_sentence_ids == ()
    assert len(card.warnings) == 2


async def test_domain_has_no_framework_or_sdk_imports():
    from pathlib import Path

    root = Path(__file__).parents[1] / "src" / "card_assistant" / "domain"
    for file in root.glob("*.py"):
        content = file.read_text(encoding="utf-8")
        assert "from fastapi" not in content
        assert "import openai" not in content
        assert "from pydantic" not in content
