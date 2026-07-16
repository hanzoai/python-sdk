"""Unit tests for hanzo_train over httpx.MockTransport -- no network."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from hanzo_train import (
    AdamParams,
    Datum,
    HanzoTrainError,
    LoraConfig,
    ModelInput,
    SamplingParams,
    ServiceClient,
    TrainingClient,
)

BASE = "http://engine"
Handler = Callable[[httpx.Request], httpx.Response]


def service(handler: Handler, api_key: str | None = None) -> ServiceClient:
    return ServiceClient(BASE, api_key=api_key, transport=httpx.MockTransport(handler))


def sent(request: httpx.Request) -> dict[str, Any]:
    return json.loads(request.content)


def info_json(**over: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": "tc-abc",
        "base_model": "m",
        "status": "ready",
        "lora_config": {"rank": 16, "alpha": 32.0, "target_modules": ["q_proj"]},
        "forward_backward_calls": 0,
        "optim_steps": 0,
    }
    data.update(over)
    return data


def test_create_defaults_and_no_wait() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        seen["body"] = sent(request)
        return httpx.Response(200, json=info_json(status="loading"))

    tc = service(handler).create_lora_training_client("m", wait=False)

    assert tc.id == "tc-abc"
    assert seen["method"] == "POST"
    assert seen["path"] == "/v1/training/clients"
    assert seen["body"]["base_model"] == "m"
    lora = seen["body"]["lora_config"]
    assert lora["rank"] == 16
    assert lora["alpha"] == 32.0
    assert lora["target_modules"] == [
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    ]


def test_create_custom_lora_config() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = sent(request)
        return httpx.Response(200, json=info_json(status="loading"))

    service(handler).create_lora_training_client(
        "m", lora_config=LoraConfig(rank=8, alpha=16.0, target_modules=["q_proj"]), wait=False
    )

    assert seen["body"]["lora_config"] == {
        "rank": 8,
        "alpha": 16.0,
        "target_modules": ["q_proj"],
    }


def test_create_wait_until_ready() -> None:
    calls = {"get": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            return httpx.Response(200, json=info_json(status="loading"))
        calls["get"] += 1
        status = "ready" if calls["get"] >= 2 else "loading"
        return httpx.Response(200, json=info_json(status=status))

    tc = service(handler).create_lora_training_client("m", wait=True, poll_interval=0.0)

    assert tc.id == "tc-abc"
    assert calls["get"] == 2


def test_create_wait_failed_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            return httpx.Response(200, json=info_json(status="loading"))
        return httpx.Response(200, json=info_json(status="failed", error="oom"))

    with pytest.raises(HanzoTrainError) as excinfo:
        service(handler).create_lora_training_client("m", wait=True, poll_interval=0.0)

    assert excinfo.value.status == 409
    assert "oom" in excinfo.value.message


def test_forward_backward_prompt_form() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["body"] = sent(request)
        return httpx.Response(200, json={"loss": 1.5, "num_tokens": 3, "metrics": {"loss": 1.5}})

    tc = TrainingClient(service(handler), "tc-abc")
    out = tc.forward_backward([{"prompt": "2+2=", "completion": "4"}]).result()

    assert seen["path"] == "/v1/training/clients/tc-abc/forward_backward"
    assert seen["body"]["data"] == [{"prompt": "2+2=", "completion": "4"}]
    assert out.loss == 1.5
    assert out.num_tokens == 3
    assert out.metrics == {"loss": 1.5}


def test_forward_backward_datum_form() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = sent(request)
        return httpx.Response(200, json={"loss": 0.5, "num_tokens": 3, "metrics": {"loss": 0.5}})

    tc = TrainingClient(service(handler), "tc-abc")
    datum = Datum(
        model_input=ModelInput(tokens=[1, 2, 3]), target_tokens=[2, 3, 4], weights=[0.0, 1.0, 1.0]
    )
    out = tc.forward_backward([datum]).result()

    assert seen["body"]["data"] == [
        {
            "model_input": {"tokens": [1, 2, 3]},
            "target_tokens": [2, 3, 4],
            "weights": [0.0, 1.0, 1.0],
        }
    ]
    assert out.loss == 0.5


def test_forward_backward_mixed_forms() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = sent(request)
        return httpx.Response(200, json={"loss": 1.0, "num_tokens": 6, "metrics": {"loss": 1.0}})

    tc = TrainingClient(service(handler), "tc-abc")
    tc.forward_backward(
        [
            {"prompt": "2+2=", "completion": "4"},
            Datum(model_input=ModelInput(tokens=[1]), target_tokens=[2], weights=[1.0]),
        ]
    ).result()

    assert seen["body"]["data"] == [
        {"prompt": "2+2=", "completion": "4"},
        {"model_input": {"tokens": [1]}, "target_tokens": [2], "weights": [1.0]},
    ]


def test_optim_step_explicit_params() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["body"] = sent(request)
        return httpx.Response(200, json={"optim_steps": 1})

    tc = TrainingClient(service(handler), "tc-abc")
    res = tc.optim_step(AdamParams(lr=1e-4)).result()

    assert seen["path"] == "/v1/training/clients/tc-abc/optim_step"
    assert seen["body"]["adam_params"] == {
        "lr": 1e-4,
        "beta1": 0.9,
        "beta2": 0.95,
        "eps": 1e-8,
        "weight_decay": 0.0,
    }
    assert res.optim_steps == 1


def test_optim_step_defaults() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = sent(request)
        return httpx.Response(200, json={"optim_steps": 7})

    tc = TrainingClient(service(handler), "tc-abc")
    res = tc.optim_step().result()

    assert seen["body"]["adam_params"]["lr"] == 1e-4
    assert res.optim_steps == 7


def test_sample_prompt_form() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["body"] = sent(request)
        return httpx.Response(200, json={"sequences": [{"tokens": [4], "text": "4"}]})

    tc = TrainingClient(service(handler), "tc-abc")
    resp = tc.sample(
        prompt="2+2=", sampling_params=SamplingParams(max_tokens=8, temperature=0.0), num_samples=1
    ).result()

    assert seen["path"] == "/v1/training/clients/tc-abc/sample"
    assert seen["body"]["prompt"] == "2+2="
    assert "tokens" not in seen["body"]
    assert seen["body"]["num_samples"] == 1
    assert seen["body"]["sampling_params"] == {
        "max_tokens": 8,
        "temperature": 0.0,
        "top_k": -1,
        "top_p": 1.0,
        "seed": 0,
        "stop_tokens": [],
    }
    assert resp.sequences[0].tokens == [4]
    assert resp.sequences[0].text == "4"


def test_sample_tokens_form_and_defaults() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = sent(request)
        return httpx.Response(200, json={"sequences": [{"tokens": [9], "text": "x"}]})

    tc = TrainingClient(service(handler), "tc-abc")
    tc.sample(tokens=[1, 2, 3]).result()

    assert seen["body"]["tokens"] == [1, 2, 3]
    assert "prompt" not in seen["body"]
    assert seen["body"]["sampling_params"]["max_tokens"] == 64
    assert seen["body"]["sampling_params"]["temperature"] == 1.0


def test_sample_requires_exactly_one_input() -> None:
    tc = TrainingClient(service(lambda r: httpx.Response(200, json={"sequences": []})), "tc-abc")

    with pytest.raises(ValueError):
        tc.sample()
    with pytest.raises(ValueError):
        tc.sample(prompt="a", tokens=[1])


def test_save_weights_and_alias() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["body"] = sent(request)
        return httpx.Response(200, json={"path": "/data/adapters/my-adapter", "format": "peft"})

    tc = TrainingClient(service(handler), "tc-abc")
    saved = tc.save_weights_and_get_sampling_client(name="my-adapter").result()

    assert seen["path"] == "/v1/training/clients/tc-abc/save_weights"
    assert seen["body"] == {"name": "my-adapter"}
    assert saved.path == "/data/adapters/my-adapter"
    assert saved.format == "peft"

    saved2 = tc.save_weights(name="a", dir="/tmp/x").result()
    assert seen["body"] == {"name": "a", "dir": "/tmp/x"}
    assert saved2.format == "peft"


def test_get_info() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/v1/training/clients/tc-abc"
        return httpx.Response(
            200,
            json=info_json(
                status="ready",
                forward_backward_calls=3,
                optim_steps=2,
                trainable_params=1234,
                last_loss=0.25,
                loss_history=[1.0, 0.5, 0.25],
            ),
        )

    info = TrainingClient(service(handler), "tc-abc").get_info()

    assert info.status == "ready"
    assert info.forward_backward_calls == 3
    assert info.optim_steps == 2
    assert info.trainable_params == 1234
    assert info.last_loss == 0.25
    assert info.loss_history == [1.0, 0.5, 0.25]
    assert info.lora_config.rank == 16
    assert info.lora_config.alpha == 32.0


def test_list_training_clients() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/v1/training/clients"
        return httpx.Response(
            200,
            json={
                "clients": [
                    info_json(id="tc-1", status="ready"),
                    info_json(id="tc-2", status="loading"),
                ]
            },
        )

    infos = service(handler).list_training_clients()

    assert [i.id for i in infos] == ["tc-1", "tc-2"]
    assert infos[0].status == "ready"
    assert isinstance(infos[0].lora_config, LoraConfig)


def test_delete() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        return httpx.Response(200, json={"id": "tc-abc", "deleted": True})

    result = TrainingClient(service(handler), "tc-abc").delete()

    assert result is None
    assert seen["method"] == "DELETE"
    assert seen["path"] == "/v1/training/clients/tc-abc"


def test_error_404() -> None:
    tc = TrainingClient(service(lambda r: httpx.Response(404, text="unknown id")), "tc-missing")

    with pytest.raises(HanzoTrainError) as excinfo:
        tc.get_info()

    assert excinfo.value.status == 404
    assert excinfo.value.message == "unknown id"


def test_error_409_forward_backward() -> None:
    tc = TrainingClient(
        service(lambda r: httpx.Response(409, text="client still loading")), "tc-abc"
    )

    with pytest.raises(HanzoTrainError) as excinfo:
        tc.forward_backward([{"prompt": "a", "completion": "b"}]).result()

    assert excinfo.value.status == 409
    assert "loading" in excinfo.value.message


def test_error_400_optim_step() -> None:
    tc = TrainingClient(service(lambda r: httpx.Response(400, text="bad data")), "tc-abc")

    with pytest.raises(HanzoTrainError) as excinfo:
        tc.optim_step().result()

    assert excinfo.value.status == 400


def test_auth_header_bearer() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json=info_json())

    TrainingClient(service(handler, api_key="secret-token"), "tc-abc").get_info()

    assert seen["auth"] == "Bearer secret-token"


def test_no_auth_header_without_key() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json=info_json())

    TrainingClient(service(handler), "tc-abc").get_info()

    assert seen["auth"] is None


def test_future_result_returns_value() -> None:
    tc = TrainingClient(service(lambda r: httpx.Response(200, json={"optim_steps": 5})), "tc-abc")

    fut = tc.optim_step()

    assert fut.result(timeout=1.0).optim_steps == 5
