from pydantic import BaseModel, ConfigDict, Field, field_validator

from card_assistant.domain.models import Fact, Product


class ProductInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    name: str = Field(min_length=1, max_length=160)
    manufacturer: str | None = Field(default=None, max_length=120)
    specs: dict[str, str | None] = Field(default_factory=dict, max_length=40)
    description: str | None = Field(default=None, max_length=6000)
    expected_specs: list[str] = Field(default_factory=list, max_length=40)

    @field_validator("name", "manufacturer", "description")
    @classmethod
    def trim_fields(cls, value: str | None, info):
        if value is None:
            return None
        value = value.strip()
        if info.field_name == "name" and not value:
            raise ValueError("Укажите название товара.")
        if any(ord(char) < 32 and char not in "\n\r\t" for char in value):
            raise ValueError("Поле содержит недопустимые управляющие символы.")
        if info.field_name != "description":
            value = " ".join(value.split())
        return value or None

    @field_validator("specs")
    @classmethod
    def validate_specs(cls, value: dict[str, str | None]):
        clean: dict[str, str | None] = {}
        for key, item in value.items():
            key = " ".join(key.split())
            if not key or len(key) > 80:
                raise ValueError("Название характеристики должно содержать от 1 до 80 символов.")
            if key in clean:
                raise ValueError(
                    "Названия характеристик повторяются после удаления лишних пробелов."
                )
            if item is not None and len(item) > 200:
                raise ValueError("Значение характеристики не должно превышать 200 символов.")
            clean[key] = " ".join(item.split()) or None if item is not None else None
        return clean

    @field_validator("expected_specs")
    @classmethod
    def validate_expected(cls, value: list[str]):
        keys = list(dict.fromkeys(" ".join(key.split()) for key in value))
        if any(not key or len(key) > 80 for key in keys):
            raise ValueError("Ожидаемые характеристики должны содержать от 1 до 80 символов.")
        return keys

    def to_domain(self) -> Product:
        return Product(
            name=self.name,
            manufacturer=self.manufacturer,
            specs=tuple(Fact(k, v) for k, v in self.specs.items()),
            description=self.description,
            expected_specs=tuple(self.expected_specs),
        )
