from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Fact:
    key: str
    value: str | None


@dataclass(frozen=True)
class Product:
    name: str
    manufacturer: str | None
    specs: tuple[Fact, ...]
    description: str | None
    expected_specs: tuple[str, ...] = ()


@dataclass(frozen=True)
class EditorialPlan:
    """The model chooses source references, never writes technical claims."""

    title_style: Literal["name", "name_manufacturer"]
    highlighted_spec_keys: tuple[str, ...]
    description_sentence_ids: tuple[int, ...]
    buyer_focus: Literal["procurement", "engineering"]
    query_spec_keys: tuple[str, ...]


@dataclass(frozen=True)
class Characteristic:
    name: str
    value: str
    source: str | None


@dataclass(frozen=True)
class MissingField:
    field: str
    message: str


@dataclass(frozen=True)
class CommercialBlock:
    audience: str
    task: str
    caveat: str


@dataclass(frozen=True)
class Card:
    seo_title: str
    seo_description: str
    characteristics: tuple[Characteristic, ...]
    search_queries: tuple[str, ...]
    commercial: CommercialBlock
    missing_fields: tuple[MissingField, ...]
    warnings: tuple[str, ...]
    source_sentence_ids: tuple[int, ...]
    source_description: str | None


class InvalidPlan(ValueError):
    """The proposed editorial plan refers to unprovided or invalid evidence."""
