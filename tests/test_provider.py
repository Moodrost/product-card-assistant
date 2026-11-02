import asyncio
import json

import httpx
import openai
import pytest

from card_assistant.adapters.planners import OpenAIPlanner
from card_assistant.application.generate import GenerationError

PLAN = {
    "title_style": "name_manufacturer",
    "highlighted_spec_keys": ["класс точности"],
    "description_sentence_ids": [0],
    "buyer_focus": "engineering",
    "query_spec_keys": [],
}


def envelope(content):
    return {
        "id": "resp_test",
        "object": "response",
        "created_at": 0,
        "status": "completed",
        "model": "gpt-4.1-mini",
        "output": [
            {
                "id": "msg_test",
                "type": "message",
                "status": "completed",
                "role": "assistant",
                "content": content,
            }
        ],
    }


async def test_actual_sdk_wire_contract_with_structured_schema(product):
    requests = []

    def handle(request):
        requests.append(request)
        return httpx.Response(
            200,
            json=envelope([{"type": "output_text", "text": json.dumps(PLAN), "annotations": []}]),
        )

    async with openai.AsyncOpenAI(
        api_key="test-only",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handle)),
        max_retries=0,
    ) as client:
        plan = await OpenAIPlanner(client, "gpt-4.1-mini", 2).plan(product)
    body = json.loads(requests[0].content)
    assert requests[0].url.path == "/v1/responses"
    assert body["text"]["format"]["type"] == "json_schema"
    assert body["text"]["format"]["strict"] is True
    assert body["store"] is False
    assert body["input"][0]["role"] == "system"
    assert "недоверенные" in body["input"][0]["content"]
    assert json.loads(body["input"][1]["content"])["available_specs"]["класс точности"] == "1,5"
    assert plan.buyer_focus == "engineering"


@pytest.mark.parametrize(
    "status,code",
    [
        (401, "provider_auth"),
        (429, "provider_rate_limit"),
        (500, "provider_unavailable"),
        (400, "provider_unavailable"),
    ],
)
async def test_provider_errors_are_sanitized(product, status, code):
    def handle(request):
        return httpx.Response(
            status, json={"error": {"message": "PRIVATE PROVIDER BODY", "type": "api_error"}}
        )

    async with openai.AsyncOpenAI(
        api_key="test-only",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handle)),
        max_retries=0,
    ) as client:
        with pytest.raises(GenerationError) as error:
            await OpenAIPlanner(client, "test-model", 2).plan(product)
    assert error.value.code == code
    assert "PRIVATE" not in error.value.message


@pytest.mark.parametrize(
    "content,code",
    [
        ([{"type": "refusal", "refusal": "Cannot comply"}], "model_refusal"),
        ([{"type": "output_text", "text": "not json", "annotations": []}], "invalid_model_output"),
        (
            [
                {
                    "type": "output_text",
                    "text": json.dumps({**PLAN, "extra": "invented value"}),
                    "annotations": [],
                }
            ],
            "invalid_model_output",
        ),
    ],
)
async def test_refusal_and_malformed_responses(product, content, code):
    async with openai.AsyncOpenAI(
        api_key="test-only",
        http_client=httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json=envelope(content))
            )
        ),
        max_retries=0,
    ) as client:
        with pytest.raises(GenerationError) as error:
            await OpenAIPlanner(client, "test-model", 2).plan(product)
    assert error.value.code == code


async def test_total_deadline_bounds_network_and_retries(product):
    async def handle(request):
        await asyncio.sleep(1)
        return httpx.Response(500)

    async with openai.AsyncOpenAI(
        api_key="test-only", http_client=httpx.AsyncClient(transport=httpx.MockTransport(handle))
    ) as client:
        with pytest.raises(GenerationError) as error:
            await OpenAIPlanner(client, "test-model", 0.02).plan(product)
    assert error.value.code == "provider_timeout"
