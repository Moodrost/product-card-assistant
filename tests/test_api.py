from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from card_assistant.adapters.planners import DemoPlanner
from card_assistant.application.generate import DraftPlanner, GenerationError
from card_assistant.config import Settings
from card_assistant.web.api import create_app


def demo_settings():
    return Settings(_env_file=None, card_mode="demo", openai_api_key="")


def test_success_and_provenance(products):
    with TestClient(create_app(demo_settings())) as client:
        for product in products:
            response = client.post("/api/generate", json=product)
            assert response.status_code == 200
            data = response.json()
            assert data["meta"]["mode"] == "demo"
            assert data["meta"]["llm_called"] is False
            assert data["meta"]["model"] is None
            assert "## Для менеджера" in data["markdown"]
            assert data["meta"]["needs_review"] is True
            assert data["meta"]["description_length"] == len(data["card"]["seo_description"])
            assert data["card"]["characteristics"][1]["source"].startswith("specs.")


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"name": "   "},
        {"name": None},
        [],
        {"name": "X", "specs": "wrong"},
        {"name": "X", "specs": {"value": 24}},
        {"name": "X", "unexpected": "field"},
        {"name": "X", "description": "X" * 6001},
        {"name": "X", "specs": {"": "24 В"}},
        {"name": "X", "specs": {"p": "x", " p ": "y"}},
    ],
)
def test_invalid_fields_are_actionable_and_never_call_provider(payload):
    class MustNotRun(DraftPlanner):
        async def plan(self, product):
            raise AssertionError("Invalid input reached the LLM")

    with TestClient(create_app(demo_settings(), MustNotRun())) as client:
        response = client.post("/api/generate", json=payload)
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "invalid_input"
        assert response.json()["error"]["details"]


def test_bad_json():
    with TestClient(create_app(demo_settings())) as client:
        response = client.post(
            "/api/generate", content='{"name":', headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "invalid_input"


def test_missing_key_does_not_silently_use_demo():
    config = Settings(_env_file=None, card_mode="live", openai_api_key="")
    with TestClient(create_app(config)) as client:
        response = client.post("/api/generate", json={"name": "X"})
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "missing_api_key"
        assert client.get("/api/health").json() == {
            "status": "ok",
            "mode": "live",
            "configured": False,
        }


def test_bad_model_reference_is_not_returned_as_a_card(products):
    class MaliciousPlanner(DemoPlanner):
        async def plan(self, product):
            return replace(await super().plan(product), highlighted_spec_keys=("давление 999 МПа",))

    with TestClient(create_app(demo_settings(), MaliciousPlanner())) as client:
        response = client.post("/api/generate", json=products[0])
        assert response.status_code == 502
        assert response.json()["error"]["code"] == "invalid_model_output"
        assert "999" not in response.text


def test_markdown_escapes_html_and_table_separators():
    with TestClient(create_app(demo_settings())) as client:
        response = client.post(
            "/api/generate",
            json={"name": "<script>alert(1)</script>", "specs": {"A|B": "<b>x</b>"}},
        )
        assert response.status_code == 200
        assert "<script>" not in response.json()["markdown"]
        assert "A\\|B" in response.json()["markdown"]
        assert response.json()["card"]["characteristics"][1]["value"] == "<b>x</b>"


@pytest.mark.parametrize(
    "status,code",
    [(429, "provider_rate_limit"), (504, "provider_timeout"), (502, "provider_unavailable")],
)
def test_service_error_contract(status, code):
    class FailedPlanner(DraftPlanner):
        async def plan(self, product):
            raise GenerationError(code, "Безопасное сообщение")

    with TestClient(create_app(demo_settings(), FailedPlanner())) as client:
        response = client.post("/api/generate", json={"name": "X"})
        assert response.status_code == status
        assert response.json()["error"]["code"] == code
        assert len(response.json()["error"]["request_id"]) == 32


def test_health_never_exposes_key():
    config = Settings(_env_file=None, card_mode="demo", openai_api_key="private-key-not-for-output")
    with TestClient(create_app(config)) as client:
        assert "private-key" not in client.get("/api/health").text
