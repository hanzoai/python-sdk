"""Questions: the three kinds Kai answers, as models or as plain dicts."""

from typing import Any, Literal, TypedDict, NotRequired
from collections.abc import Mapping, Sequence

from pydantic import BaseModel, ConfigDict, with_config

from hanzo_kai._errors import KaiError

type JSONValue = str | int | float | bool | Sequence[JSONValue] | Mapping[str, JSONValue] | None
"""Any JSON value, nested to any depth."""

type JSONContent = str | Mapping[str, JSONValue] | Sequence[JSONValue]
"""Text, a JSON object or a JSON array: what state, instructions and descriptions accept."""


@with_config(ConfigDict(extra="forbid"))
class NoulCriteria(TypedDict, total=False):
    """What a yes and a no each mean; either may be left out."""

    true: JSONContent | None
    """When the answer is yes."""
    false: JSONContent | None
    """When the answer is no."""


@with_config(ConfigDict(extra="forbid"))
class NoulLabels(TypedDict):
    """The words a noul's two sides go by in the text Kai reads; their meaning stays yes and no."""

    true: str
    false: str


class NoulModel(TypedDict):
    """A yes/no question as a dict."""

    type: Literal["noul"]
    instructions: NotRequired[JSONContent | None]
    criteria: NotRequired[NoulCriteria | None]
    labels: NotRequired[NoulLabels]


class ChoiceModel(TypedDict):
    """A choice question as a dict."""

    type: Literal["choice"]
    instructions: NotRequired[JSONContent | None]
    criteria: Mapping[str, JSONContent | None] | Sequence[str]


class ScoreModel(TypedDict):
    """A score question as a dict."""

    type: Literal["score"]
    instructions: NotRequired[JSONContent | None]
    criteria: Sequence[JSONContent]


class _Question(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Noul(_Question):
    """A yes/no question; its answer is the probability of yes.

    Examples:
        ```python
        Noul(
            instructions="Is this about billing?",
            criteria={"true": "it concerns charges, invoices or refunds", "false": "it concerns something else"},
        )
        ```
    """

    type: Literal["noul"] = "noul"
    instructions: JSONContent | None = None
    """The question, as text, a JSON object or an array; optional."""
    criteria: NoulCriteria | None = None
    """What a yes and a no each mean."""
    labels: NoulLabels | None = None
    """Words for the two sides, such as `{"true": "refund", "false": "no refund"}`; `/v1/decisions` only."""


class Choice(_Question):
    """A question whose answer is one of a set of labels.

    Examples:
        ```python
        Choice(instructions="Which team handles this?", criteria={"billing": "charges", "tech": "bugs"})
        Choice(instructions="Which team handles this?", criteria=["billing", "tech"])
        ```
    """

    type: Literal["choice"] = "choice"
    instructions: JSONContent | None = None
    """The question, as text, a JSON object or an array; optional."""
    criteria: Mapping[str, JSONContent | None] | Sequence[str]
    """Each label mapped to when it applies (None leaves it to the label's name), or a list of labels; at least 2."""


class Score(_Question):
    """A question rated on an ordered rubric; its answer is the expected level.

    Examples:
        ```python
        Score(instructions="How urgent is this?", criteria=["can wait", "this week", "today"])
        ```
    """

    type: Literal["score"] = "score"
    instructions: JSONContent | None = None
    """The question, as text, a JSON object or an array; optional."""
    criteria: Sequence[JSONContent]
    """One description per level, level 0 first; at least 1, none null."""


type QuestionModel = NoulModel | ChoiceModel | ScoreModel
"""A question as a dict, told apart by its `type`."""

type Question = Noul | Choice | Score | QuestionModel
"""A question as a model or as a dict."""

type Questions = Mapping[str, Question]
"""Questions keyed by the names their answers come back under."""


def encode(questions: Questions) -> dict[str, Any]:
    """The questions as the wire takes them, after the checks only a client can make.

    Every other rule (how many questions, labels and levels, levels not null, a state that fits)
    is the server's, and its 422 says which one a request broke.
    """
    if not isinstance(questions, Mapping) or not questions:
        raise KaiError("questions must map at least one name to a question")
    wire: dict[str, Any] = {}
    for name, question in questions.items():
        if isinstance(question, Noul | Choice | Score):
            wire[name] = {key: value for key, value in question.model_dump().items() if value is not None}
        elif isinstance(question, Mapping):
            kind, criteria = question.get("type"), question.get("criteria")
            if kind == "score" and not listed(criteria):
                raise KaiError(f"question {name!r}: a score question's criteria is a list of levels, level 0 first")
            if kind == "choice" and not (isinstance(criteria, Mapping) or listed(criteria)):
                raise KaiError(
                    f"question {name!r}: a choice question's criteria maps labels to descriptions, or lists labels"
                )
            wire[name] = question
        else:
            raise KaiError(
                f"question {name!r} is a {type(question).__name__}; ask a Noul, Choice or Score, or a dict with a 'type'"
            )
    return wire


def listed(value: object) -> bool:
    """Whether a value is a JSON array: a sequence other than text or bytes."""
    return isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray)
