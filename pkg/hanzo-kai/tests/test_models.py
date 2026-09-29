from collections.abc import Callable

import pytest
from wire import KEY, Wire, Client, reply
from hanzo_kai import Model, Pricing, RetryPolicy, AuthenticationError, APIResponseValidationError

Build = Callable[..., Client]

# Rows as GET https://api.hanzo.ai/v1/models serves them, and the shapes around them.
LISTING = {
    "object": "list",
    "data": [
        {
            "id": "aion-labs/aion-2.0",
            "object": "model",
            "created": 1790629327,
            "owned_by": "aion-labs",
            "premium": True,
            "context_window": 131072,
            "outputs": ["text"],
            "pricing": {
                "prompt": "0.00000096",
                "completion": "0.00000192",
                "input_per_million": 0.96,
                "output_per_million": 1.92,
            },
        },
        {
            "id": "hanzo/kai",
            "object": "model",
            "created": 1790629327,
            "owned_by": "hanzo",
            "premium": False,
            "outputs": ["decision"],
            "pricing": {
                "prompt": "0.000000021",
                "completion": "0",
                "input_per_million": 0.021,
                "output_per_million": 0,
            },
        },
        {
            "id": "kai",
            "object": "model",
            "created": 1790629327,
            "owned_by": "hanzo",
            "premium": False,
            "outputs": ["decision"],
            "pricing": {
                "prompt": "0.000000021",
                "completion": "0",
                "input_per_million": 0.021,
                "output_per_million": 0,
            },
        },
        {
            "id": "no-outputs",
            "object": "model",
            "outputs": None,
            "pricing": {"input_per_million": -1200000, "output_per_million": -1200000},
        },
        {"id": "no-field", "object": "model"},
        "not a row",
    ],
}


def test_lists_the_decision_models(client: Build) -> None:
    wire = Wire(reply(json_body=LISTING))
    found = client(wire).models()
    request = wire.requests[0]
    assert request.method == "GET" and str(request.url) == "https://api.hanzo.ai/v1/models"
    assert request.headers["authorization"] == f"Bearer {KEY}" and not request.content
    assert [model.id for model in found] == ["hanzo/kai", "kai"]
    kai = found[1]
    assert isinstance(kai, Model) and isinstance(kai.pricing, Pricing)
    assert (kai.owned_by, kai.created, kai.pricing.input_per_million, kai.pricing.output_per_million) == (
        "hanzo",
        1790629327,
        0.021,
        0,
    )
    assert (kai.pricing.prompt, kai.pricing.completion) == ("0.000000021", "0")
    assert kai.model_extra == {"object": "model", "premium": False, "outputs": ["decision"]}


def test_listing_that_does_not_fit(client: Build) -> None:
    with pytest.raises(APIResponseValidationError) as caught:
        client(Wire(reply(json_body={"models": []}))).models()
    assert caught.value.field_path == "data"
    with pytest.raises(APIResponseValidationError) as caught:
        client(Wire(reply(json_body={"data": [{"outputs": ["decision"]}]}))).models()
    assert caught.value.field_path == "data.0.id"


def test_listing_errors(client: Build) -> None:
    refusal = {"status": "error", "msg": "authentication required"}
    with pytest.raises(AuthenticationError) as caught:
        client(Wire(reply(401, refusal))).models(retry=RetryPolicy(max_retries=0), extra_headers={"X-Team": "ops"})
    assert caught.value.message == "authentication required"
    assert caught.value.endpoint == "GET https://api.hanzo.ai/v1/models"
