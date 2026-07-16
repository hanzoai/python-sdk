"""Tinker-shaped client for the Hanzo Engine training API.

The engine exposes a small LoRA training surface under ``/v1/training``. This
client mirrors the shapes of Thinking Machines' ``tinker`` SDK -- so training
loops written against tinker port across unchanged -- using Hanzo-canonical
field names and a single synchronous HTTP path (httpx, no retries).

Usage::

    from hanzo_train import ServiceClient, LoraConfig, AdamParams, SamplingParams

    sc = ServiceClient("http://localhost:1234")
    tc = sc.create_lora_training_client("HuggingFaceTB/SmolLM2-135M", LoraConfig(rank=16))
    tc.forward_backward([{"prompt": "2+2=", "completion": "4"}]).result()
    tc.optim_step(AdamParams(lr=1e-4)).result()
"""

from __future__ import annotations

from collections.abc import Iterable
from concurrent.futures import Future
from dataclasses import dataclass, field
from time import monotonic, sleep
from typing import Any

import httpx

_TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]


class HanzoTrainError(Exception):
    """A non-2xx response from the training API, carrying its status and message."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"[{status}] {message}")
        self.status = status
        self.message = message


@dataclass(frozen=True)
class ModelInput:
    """Pre-tokenized model input."""

    tokens: list[int]


@dataclass(frozen=True)
class Datum:
    """One tokenized example: input tokens, target tokens, and per-token weights."""

    model_input: ModelInput
    target_tokens: list[int]
    weights: list[float]


@dataclass(frozen=True)
class LoraConfig:
    """LoRA adapter configuration; defaults match the engine wire defaults."""

    rank: int = 16
    alpha: float = 32.0
    target_modules: list[str] = field(default_factory=lambda: list(_TARGET_MODULES))


@dataclass(frozen=True)
class AdamParams:
    """Adam optimizer parameters for one step; defaults match the wire defaults."""

    lr: float = 1e-4
    beta1: float = 0.9
    beta2: float = 0.95
    eps: float = 1e-8
    weight_decay: float = 0.0


@dataclass(frozen=True)
class SamplingParams:
    """Sampling parameters; defaults match the engine wire defaults."""

    max_tokens: int = 64
    temperature: float = 1.0
    top_k: int = -1
    top_p: float = 1.0
    seed: int = 0
    stop_tokens: list[int] = field(default_factory=list)


@dataclass(frozen=True)
class ForwardBackwardResult:
    """Loss and token count returned by a forward-backward pass."""

    loss: float
    num_tokens: int
    metrics: dict[str, float]


@dataclass(frozen=True)
class OptimResult:
    """Cumulative optimizer step count after an optim step."""

    optim_steps: int


@dataclass(frozen=True)
class Sequence:
    """One sampled sequence: token ids and decoded text."""

    tokens: list[int]
    text: str


@dataclass(frozen=True)
class SampleResult:
    """Sequences produced by a sample call."""

    sequences: list[Sequence]


@dataclass(frozen=True)
class SaveResult:
    """Where a saved adapter lives and in what format."""

    path: str
    format: str


@dataclass(frozen=True)
class TrainingClientInfo:
    """Server-side state of a training client."""

    id: str
    base_model: str
    status: str
    lora_config: LoraConfig
    forward_backward_calls: int
    optim_steps: int
    error: str | None = None
    trainable_params: int | None = None
    last_loss: float | None = None
    loss_history: list[float] = field(default_factory=list)


def _future[T](value: T) -> Future[T]:
    fut: Future[T] = Future()
    fut.set_result(value)
    return fut


def _datum_wire(datum: Datum | dict[str, Any]) -> dict[str, Any]:
    if isinstance(datum, Datum):
        return {
            "model_input": {"tokens": list(datum.model_input.tokens)},
            "target_tokens": list(datum.target_tokens),
            "weights": list(datum.weights),
        }
    return datum


def _info(data: dict[str, Any]) -> TrainingClientInfo:
    cfg = data["lora_config"]
    return TrainingClientInfo(
        id=data["id"],
        base_model=data["base_model"],
        status=data["status"],
        lora_config=LoraConfig(
            rank=cfg["rank"], alpha=cfg["alpha"], target_modules=list(cfg["target_modules"])
        ),
        forward_backward_calls=data["forward_backward_calls"],
        optim_steps=data["optim_steps"],
        error=data.get("error"),
        trainable_params=data.get("trainable_params"),
        last_loss=data.get("last_loss"),
        loss_history=list(data.get("loss_history", [])),
    )


class ServiceClient:
    """Entry point to the Hanzo Engine training API."""

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._http = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers=headers,
            transport=transport,
            timeout=httpx.Timeout(None, connect=10.0),
        )

    def _request(self, method: str, path: str, body: Any = None) -> Any:
        resp = self._http.request(method, path, json=body)
        if resp.status_code >= 400:
            raise HanzoTrainError(resp.status_code, resp.text)
        return resp.json()

    def create_lora_training_client(
        self,
        base_model: str,
        lora_config: LoraConfig | None = None,
        wait: bool = True,
        timeout: float = 600.0,
        poll_interval: float = 1.0,
    ) -> TrainingClient:
        cfg = lora_config or LoraConfig()
        data = self._request(
            "POST",
            "/v1/training/clients",
            {
                "base_model": base_model,
                "lora_config": {
                    "rank": cfg.rank,
                    "alpha": cfg.alpha,
                    "target_modules": list(cfg.target_modules),
                },
            },
        )
        tc = TrainingClient(self, data["id"], poll_interval)
        if wait:
            tc._wait_ready(timeout)
        return tc

    def list_training_clients(self) -> list[TrainingClientInfo]:
        data = self._request("GET", "/v1/training/clients")
        return [_info(c) for c in data["clients"]]

    def close(self) -> None:
        self._http.close()


class TrainingClient:
    """A handle to one LoRA training client on the engine."""

    def __init__(self, service: ServiceClient, id: str, poll_interval: float = 1.0) -> None:
        self.id = id
        self._service = service
        self._poll_interval = poll_interval

    def _path(self, suffix: str = "") -> str:
        return f"/v1/training/clients/{self.id}{suffix}"

    def forward_backward(
        self, data: Iterable[Datum | dict[str, Any]]
    ) -> Future[ForwardBackwardResult]:
        result = self._service._request(
            "POST", self._path("/forward_backward"), {"data": [_datum_wire(d) for d in data]}
        )
        return _future(
            ForwardBackwardResult(
                loss=result["loss"], num_tokens=result["num_tokens"], metrics=result["metrics"]
            )
        )

    def optim_step(self, adam_params: AdamParams | None = None) -> Future[OptimResult]:
        adam = adam_params or AdamParams()
        result = self._service._request(
            "POST",
            self._path("/optim_step"),
            {
                "adam_params": {
                    "lr": adam.lr,
                    "beta1": adam.beta1,
                    "beta2": adam.beta2,
                    "eps": adam.eps,
                    "weight_decay": adam.weight_decay,
                }
            },
        )
        return _future(OptimResult(optim_steps=result["optim_steps"]))

    def sample(
        self,
        prompt: str | None = None,
        tokens: list[int] | None = None,
        sampling_params: SamplingParams | None = None,
        num_samples: int = 1,
    ) -> Future[SampleResult]:
        if (prompt is None) == (tokens is None):
            raise ValueError("pass exactly one of prompt or tokens")
        sp = sampling_params or SamplingParams()
        body: dict[str, Any] = {
            "sampling_params": {
                "max_tokens": sp.max_tokens,
                "temperature": sp.temperature,
                "top_k": sp.top_k,
                "top_p": sp.top_p,
                "seed": sp.seed,
                "stop_tokens": list(sp.stop_tokens),
            },
            "num_samples": num_samples,
        }
        if prompt is not None:
            body["prompt"] = prompt
        else:
            body["tokens"] = tokens
        result = self._service._request("POST", self._path("/sample"), body)
        return _future(
            SampleResult(
                sequences=[
                    Sequence(tokens=s["tokens"], text=s["text"]) for s in result["sequences"]
                ]
            )
        )

    def save_weights_and_get_sampling_client(
        self, name: str, dir: str | None = None
    ) -> Future[SaveResult]:
        body: dict[str, Any] = {"name": name}
        if dir is not None:
            body["dir"] = dir
        result = self._service._request("POST", self._path("/save_weights"), body)
        return _future(SaveResult(path=result["path"], format=result["format"]))

    save_weights = save_weights_and_get_sampling_client

    def get_info(self) -> TrainingClientInfo:
        return _info(self._service._request("GET", self._path()))

    def delete(self) -> None:
        self._service._request("DELETE", self._path())

    def _wait_ready(self, timeout: float) -> None:
        deadline = monotonic() + timeout
        while True:
            info = self.get_info()
            if info.status == "ready":
                return
            if info.status == "failed":
                raise HanzoTrainError(409, info.error or "training client failed to load")
            if monotonic() >= deadline:
                raise HanzoTrainError(408, f"training client {self.id} not ready after {timeout}s")
            sleep(self._poll_interval)
