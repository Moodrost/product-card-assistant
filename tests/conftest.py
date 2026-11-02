import json
from pathlib import Path

import pytest

from card_assistant.web.schemas import ProductInput


@pytest.fixture
def products():
    return json.loads(
        (Path(__file__).parents[1] / "examples" / "products.json").read_text(encoding="utf-8")
    )


@pytest.fixture
def product(products):
    return ProductInput.model_validate(products[0]).to_domain()
