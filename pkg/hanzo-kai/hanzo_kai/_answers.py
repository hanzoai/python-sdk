"""What the API returns: typed answers, usage, the decision that holds them, and models."""

import json
from typing import Any, Literal, Annotated
from datetime import UTC, datetime

import httpx
from pydantic import Field, BaseModel, ConfigDict, PrivateAttr, ValidationError, field_validator

from hanzo_kai._log import logger
from hanzo_kai._errors import KaiError, APIResponseValidationError
from hanzo_kai._version import __version__
from hanzo_kai._questions import JSONContent

KINDS = frozenset({"noul", "choice", "score"})


class _Answer(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)


class NoulAnswer(_Answer):
    """The answer to a yes/no question."""

    type: Literal["noul"] = "noul"
    noul: float
    """Probability that the answer is yes, from 0 to 1."""
    confidence: float | None = None
    """How far the noul leans from even, |2·noul - 1|; `/v1/decisions` sends it."""
    answer_confidence: float | None = None
    """Probability of the answer the noul leans to: the larger of p(yes) and p(no)."""


class ChoiceAnswer(_Answer):
    """The label chosen, with a probability for every label."""

    type: Literal["choice"] = "choice"
    choice: str
    """The most probable label."""
    confidence: float
    """How far the top label stands above a uniform guess over n labels: (n·p_max - 1)/(n - 1)."""
    probabilities: dict[str, float]
    """Probability of each label; they sum to 1."""
    answer_confidence: float | None = None
    """Probability of the chosen label."""


class ScoreAnswer(_Answer):
    """The expected level on an ordered rubric, with a probability for every level."""

    type: Literal["score"] = "score"
    score: float
    """Expected level, Σ level · p(level); it may fall between levels."""
    confidence: float
    """How far the top level stands above a uniform guess over n levels: (n·p_max - 1)/(n - 1)."""
    legend: dict[int, JSONContent]
    """Each level's description, keyed by level, lowest first."""
    probabilities: dict[int, float]
    """Probability of each level, keyed by level, lowest first; they sum to 1."""
    answer_confidence: float | None = None
    """Probability of the most probable level."""

    @field_validator("legend", "probabilities")
    @classmethod
    def _ordered(cls, levels: dict[int, Any]) -> dict[int, Any]:
        return dict(sorted(levels.items()))


type Answer = Annotated[NoulAnswer | ChoiceAnswer | ScoreAnswer, Field(discriminator="type")]
"""An answer, told apart by its `type`."""


class Usage(BaseModel):
    """Tokens a decision counted."""

    model_config = ConfigDict(extra="allow", frozen=True)

    input_tokens: int | None = None
    """Input tokens billed."""
    output_tokens: int | None = None
    """Output tokens; a decision generates none."""


class _Read(BaseModel):
    """A body read from an HTTP response, which stays reachable."""

    model_config = ConfigDict(extra="allow", frozen=True)

    _response: httpx.Response | None = PrivateAttr(default=None)

    @property
    def raw_http_response(self) -> httpx.Response:
        """The `httpx.Response` this was read from."""
        if self._response is None:
            raise KaiError("this was not read from an HTTP response")
        return self._response

    @property
    def request_id(self) -> str | None:
        """The response's `x-request-id`."""
        return None if self._response is None else self._response.headers.get("x-request-id")


class Response(_Read):
    """Answers keyed by question name, with the model and usage: the body `/v1/systemone` returns.

    Subclass it to type answers by name: a field named after a question is filled with that
    question's answer.
    """

    model: str
    """The model that answered."""
    answers: dict[str, Answer] = Field(default_factory=dict)
    """Every answer, keyed by question name."""
    usage: Usage = Field(default_factory=Usage)
    """Tokens the request counted."""

    @property
    def nouls(self) -> dict[str, NoulAnswer]:
        """The yes/no answers, keyed by question name."""
        return {name: answer for name, answer in self.answers.items() if isinstance(answer, NoulAnswer)}

    @property
    def choices(self) -> dict[str, ChoiceAnswer]:
        """The choice answers, keyed by question name."""
        return {name: answer for name, answer in self.answers.items() if isinstance(answer, ChoiceAnswer)}

    @property
    def scores(self) -> dict[str, ScoreAnswer]:
        """The score answers, keyed by question name."""
        return {name: answer for name, answer in self.answers.items() if isinstance(answer, ScoreAnswer)}


class Decision(Response):
    """Kai's answers to one request, keyed by question name, with usage and routing: the body `/v1/decisions` returns.

    Subclass it to type answers by name: a field named after a question is filled with that
    question's answer.

    Examples:
        ```python
        class Ticket(Decision):
            team: ChoiceAnswer


        ticket = kai.decide(state, questions, response_model=Ticket)
        ticket.team.choice
        ```
    """

    id: str
    """The decision's id, `dec_` and 32 hex digits."""
    provider: str | None = None
    """Who served the decision."""
    routing: dict[str, Any] | None = None
    """The checkpoint, weights digest, calibration and device that answered."""
    state_hash: str | None = None
    """`sha256:` digest of the state as the server read it."""
    latency_ms: float | None = None
    """Milliseconds the server spent deciding."""


class Pricing(BaseModel):
    """List prices in US dollars, per token and per million tokens."""

    model_config = ConfigDict(extra="allow", frozen=True)

    prompt: str | None = None
    """Per input token, as a decimal string (OpenRouter's key and unit)."""
    completion: str | None = None
    """Per output token, as a decimal string."""
    input_per_million: float | None = None
    output_per_million: float | None = None


class Model(BaseModel):
    """A model that answers decisions; pass its `id` as `model`."""

    model_config = ConfigDict(extra="allow", frozen=True)

    id: str
    owned_by: str | None = None
    created: int | None = None
    """Unix time the model was listed."""
    pricing: Pricing | None = None


class ModelMetadata(BaseModel):
    """A decision model in Jev's shape: its name, a description and its release date."""

    model_config = ConfigDict(extra="allow", frozen=True)

    name: str
    """The id to pass as `model`."""
    description: str = ""
    release_date: str | None = None
    """YYYY-MM-DD, the day the listing dates the model."""


class ListModelsResponse(_Read):
    """The decision models of `GET /v1/models`, in Jev's shape."""

    models: tuple[ModelMetadata, ...] = ()


def read[R: BaseModel](response: httpx.Response, kind: type[R]) -> R:
    """The body of a successful decision, read as `kind`.

    A `Response` keeps the answer types it knows and skips newer ones with a warning; any other
    model reads the body as sent.
    """
    if not issubclass(kind, Response):
        try:
            return kind.model_validate_json(response.content)
        except ValidationError as error:
            raise invalid(response, where(error)) from error
    data = parse(response)
    if not isinstance(data, dict):
        raise invalid(response, "")
    answers = data.get("answers")
    if isinstance(answers, dict):
        known: dict[str, Any] = {}
        for name, answer in answers.items():
            tag = answer.get("type") if isinstance(answer, dict) else None
            if not isinstance(tag, str):
                raise invalid(response, f"answers.{name}.type")
            if tag in KINDS:
                known[name] = answer
            else:
                logger.warning("skipping answer %r: hanzo-kai %s does not know type %r", name, __version__, tag)
        data["answers"] = known
        base = Decision if issubclass(kind, Decision) else Response
        for field in kind.model_fields.keys() - base.model_fields.keys():
            if field in known:
                data[field] = known[field]
    try:
        result = kind.model_validate(data)
    except ValidationError as error:
        raise invalid(response, where(error)) from error
    result._response = response
    return result


def models(response: httpx.Response) -> list[Model]:
    """The models `GET /v1/models` lists whose outputs include decisions."""
    data = parse(response)
    rows = data.get("data") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        raise invalid(response, "data")
    found = []
    for index, row in enumerate(rows):
        outputs = row.get("outputs") if isinstance(row, dict) else None
        if isinstance(outputs, list) and "decision" in outputs:
            try:
                found.append(Model.model_validate(row))
            except ValidationError as error:
                raise invalid(response, f"data.{index}.{where(error)}") from error
    return found


def catalog(response: httpx.Response) -> ListModelsResponse:
    """The decision models `GET /v1/models` lists under `data`, in Jev's shape.

    The name is the model's id, the description is empty, and the release date is the day of its
    `created` time; the listing's own `models` key stays empty on api.hanzo.ai.
    """
    listing = ListModelsResponse(
        models=tuple(
            ModelMetadata(
                name=model.id,
                release_date=None
                if model.created is None
                else datetime.fromtimestamp(model.created, UTC).date().isoformat(),
            )
            for model in models(response)
        )
    )
    listing._response = response
    return listing


def parse(response: httpx.Response) -> Any:
    """The JSON body, or None when the body is not JSON."""
    try:
        return json.loads(response.content)
    except ValueError:
        return None


def invalid(response: httpx.Response, path: str) -> APIResponseValidationError:
    """The error for a success body that does not fit at `path`."""
    body = parse(response)
    return APIResponseValidationError(
        response.status_code,
        response.text if body is None else body,
        response.headers,
        path,
        endpoint(response),
    )


def where(error: ValidationError) -> str:
    """The dotted path of a validation error's first failure, without the answer-type tag."""
    loc = list(error.errors(include_url=False)[0]["loc"])
    if len(loc) > 2 and loc[0] == "answers" and loc[2] in KINDS:
        del loc[2]
    return ".".join(str(part) for part in loc if part != "[key]")


def endpoint(response: httpx.Response) -> str | None:
    """Method and URL of the request a response answers."""
    try:
        request = response.request
    except RuntimeError:
        return None
    return f"{request.method} {request.url.copy_with(query=None, fragment=None)}"
