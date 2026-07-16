"""Hanzo Train -- Tinker-shaped client for the Hanzo Engine training API.

Mirrors the shapes of Thinking Machines' ``tinker`` SDK so training loops port
across unchanged. Synchronous httpx under the hood; the four training ops return
a completed future exposing ``.result(timeout=None)``.

Usage::

    from hanzo_train import ServiceClient, LoraConfig, AdamParams, SamplingParams

    sc = ServiceClient("http://localhost:1234")
    tc = sc.create_lora_training_client("HuggingFaceTB/SmolLM2-135M", LoraConfig(rank=16))
    out = tc.forward_backward([{"prompt": "2+2=", "completion": "4"}]).result()
    tc.optim_step(AdamParams(lr=1e-4)).result()
    resp = tc.sample(prompt="2+2=", sampling_params=SamplingParams(max_tokens=8)).result()
"""

from hanzo_train.client import (
    AdamParams,
    Datum,
    ForwardBackwardResult,
    HanzoTrainError,
    LoraConfig,
    ModelInput,
    OptimResult,
    SampleResult,
    SamplingParams,
    SaveResult,
    Sequence,
    ServiceClient,
    TrainingClient,
    TrainingClientInfo,
)

__version__ = "0.1.0"

__all__ = [
    "ServiceClient",
    "TrainingClient",
    "TrainingClientInfo",
    "LoraConfig",
    "AdamParams",
    "SamplingParams",
    "Datum",
    "ModelInput",
    "ForwardBackwardResult",
    "OptimResult",
    "SampleResult",
    "Sequence",
    "SaveResult",
    "HanzoTrainError",
]
