from dataclasses import dataclass
from typing import Protocol

from card_assistant.domain.editorial import build_card
from card_assistant.domain.models import Card, EditorialPlan, InvalidPlan, Product


class GenerationError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class DraftPlanner(Protocol):
    async def plan(self, product: Product) -> EditorialPlan: ...


@dataclass
class GenerateCard:
    planner: DraftPlanner

    async def execute(self, product: Product) -> Card:
        plan = await self.planner.plan(product)
        try:
            return build_card(product, plan)
        except InvalidPlan as exc:
            raise GenerationError(
                "invalid_model_output",
                "Ответ модели не прошёл проверку фактов. "
                "Повторите запрос или уточните исходные данные.",
            ) from exc
