# hanzo-train

Tinker-shaped Python client for the Hanzo Engine training API.

It mirrors the shapes of Thinking Machines' [`tinker`](https://github.com/thinking-machines-lab/tinker)
SDK, so training loops written against tinker port across unchanged, while using
Hanzo-canonical field names. The transport is synchronous `httpx` with no retries;
the four training ops return a completed future exposing `.result(timeout=None)`
so `fut.result()` code ports 1:1.

## Install

```bash
pip install hanzo-train
```

## Quickstart

```python
from hanzo_train import ServiceClient, LoraConfig, AdamParams, SamplingParams, Datum, ModelInput

sc = ServiceClient(base_url="http://localhost:1234", api_key=None)   # api_key -> Authorization: Bearer

tc = sc.create_lora_training_client(
    "HuggingFaceTB/SmolLM2-135M", lora_config=LoraConfig(rank=16), wait=True, timeout=600.0
)
# wait=True polls the client until status is ready (raises on failed); wait=False returns immediately.

out = tc.forward_backward([
    {"prompt": "2+2=", "completion": "4"},
    Datum(model_input=ModelInput(tokens=[1, 2, 3]), target_tokens=[2, 3, 4], weights=[0.0, 1.0, 1.0]),
]).result()
# out.loss, out.num_tokens, out.metrics

tc.optim_step(AdamParams(lr=1e-4)).result()

resp = tc.sample(
    prompt="2+2=", sampling_params=SamplingParams(max_tokens=8, temperature=0.0), num_samples=1
).result()
# resp.sequences[0].tokens / .text

saved = tc.save_weights_and_get_sampling_client(name="my-adapter").result()   # .path, .format == "peft"
# alias: tc.save_weights(name="my-adapter")

info = tc.get_info()          # TrainingClientInfo incl. loss_history
sc.list_training_clients()    # list[TrainingClientInfo]
tc.delete()
```

## Errors

Every non-2xx response raises `HanzoTrainError(status, message)`:

- `400` — bad input
- `404` — unknown training client id
- `409` — client still loading, or failed to load

## API

`ServiceClient(base_url, api_key=None)`

- `create_lora_training_client(base_model, lora_config=None, wait=True, timeout=600.0, poll_interval=1.0) -> TrainingClient`
- `list_training_clients() -> list[TrainingClientInfo]`
- `close()`

`TrainingClient`

- `forward_backward(data) -> Future[ForwardBackwardResult]` — `data` items are either
  `{"prompt": str, "completion": str}` dicts or `Datum` values.
- `optim_step(adam_params=None) -> Future[OptimResult]`
- `sample(prompt=None, tokens=None, sampling_params=None, num_samples=1) -> Future[SampleResult]`
  — pass exactly one of `prompt` or `tokens`.
- `save_weights_and_get_sampling_client(name, dir=None) -> Future[SaveResult]` (alias: `save_weights`)
- `get_info() -> TrainingClientInfo`
- `delete()`
