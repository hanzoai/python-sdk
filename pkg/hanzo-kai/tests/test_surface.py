"""The public surface is a contract shared with @hanzo/kai; a rename here is a break there."""

import inspect

import hanzo_kai
from hanzo_kai import Kai, Models, AsyncKai, AsyncModels, constants

NAMES = [
    "APIConnectionError",
    "APIError",
    "APIResponseValidationError",
    "APITimeoutError",
    "Answer",
    "AsyncKai",
    "AsyncModels",
    "AuthenticationError",
    "BadRequestError",
    "Choice",
    "ChoiceAnswer",
    "ChoiceModel",
    "Decision",
    "InternalServerError",
    "JSONContent",
    "JSONValue",
    "Kai",
    "KaiError",
    "Model",
    "Models",
    "NotFoundError",
    "Noul",
    "NoulAnswer",
    "NoulCriteria",
    "NoulModel",
    "PaymentRequiredError",
    "PermissionDeniedError",
    "Pricing",
    "Question",
    "QuestionModel",
    "Questions",
    "RateLimitError",
    "RetryPolicy",
    "Score",
    "ScoreAnswer",
    "ScoreModel",
    "UnprocessableEntityError",
    "Usage",
    "__version__",
    "constants",
]


def parameters(function: object) -> list[tuple[str, str]]:
    return [(p.name, p.kind.name) for p in inspect.signature(function).parameters.values()]  # type: ignore[arg-type]


def test_names() -> None:
    assert hanzo_kai.__all__ == NAMES
    for name in NAMES:
        assert getattr(hanzo_kai, name) is not None


def test_client_signatures() -> None:
    for kind in (Kai, AsyncKai):
        assert parameters(kind.__init__) == [
            ("self", "POSITIONAL_OR_KEYWORD"),
            ("api_key", "POSITIONAL_OR_KEYWORD"),
            ("model", "KEYWORD_ONLY"),
            ("retry", "KEYWORD_ONLY"),
            ("timeout", "KEYWORD_ONLY"),
            ("headers", "KEYWORD_ONLY"),
            ("transport", "KEYWORD_ONLY"),
            ("http_client", "KEYWORD_ONLY"),
            ("base_url", "KEYWORD_ONLY"),
        ]
        assert parameters(kind.decide) == [
            ("self", "POSITIONAL_OR_KEYWORD"),
            ("state", "POSITIONAL_OR_KEYWORD"),
            ("questions", "POSITIONAL_OR_KEYWORD"),
            ("model", "KEYWORD_ONLY"),
            ("retry", "KEYWORD_ONLY"),
            ("timeout", "KEYWORD_ONLY"),
            ("extra_headers", "KEYWORD_ONLY"),
            ("extra_body", "KEYWORD_ONLY"),
            ("response_model", "KEYWORD_ONLY"),
        ]
    for resource in (Models, AsyncModels):
        assert parameters(resource.list) == [
            ("self", "POSITIONAL_OR_KEYWORD"),
            ("retry", "KEYWORD_ONLY"),
            ("timeout", "KEYWORD_ONLY"),
            ("extra_headers", "KEYWORD_ONLY"),
        ]
    assert inspect.iscoroutinefunction(AsyncKai.decide) and inspect.iscoroutinefunction(AsyncModels.list)
    assert inspect.iscoroutinefunction(AsyncKai.aclose) and callable(Kai.close)


def test_constants() -> None:
    assert (constants.API_KEY_ENV, constants.BASE_URL_ENV, constants.DEFAULT_MODEL_ENV, constants.LOG_LEVEL_ENV) == (
        "HANZO_API_KEY",
        "HANZO_BASE_URL",
        "KAI_MODEL",
        "KAI_LOG_LEVEL",
    )


def test_decision_fields() -> None:
    fields = set(hanzo_kai.Decision.model_fields)
    assert fields == {"id", "model", "provider", "answers", "usage", "routing", "state_hash", "latency_ms"}
    for name in ("choices", "nouls", "scores", "raw_http_response", "request_id"):
        assert isinstance(inspect.getattr_static(hanzo_kai.Decision, name), property)
