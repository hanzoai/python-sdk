"""Plan usage: the refusal classes, the header reader, and where the client raises them.

The bodies are the AI router's own, as api.hanzo.ai answers them. The client
tests answer over a real socket, so the refusal is raised from the same code
path a caller runs: :meth:`Client.send` and a generated operation.
"""

import json
import threading
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

import pytest
from urllib3 import HTTPHeaderDict

from hanzoai import (
    Fault,
    Usage,
    ModelCapError,
    UsageLimitError,
    FreePlanCapError,
    PaidPlanRequiredError,
    UsageCapExceededError,
    PlanAllowanceUsedError,
    InsufficientBalanceError,
    read_usage,
)
from hanzoai.wire import Reply
from hanzoai.usage import Action, refusal

#: Measured: POST /v1/decisions, model kai, org on the free plan.
FREE_PLAN_CAP = {
    "error": {
        "message": "Free plan: today's Kai requests are used. Upgrade for more: https://hanzo.ai/pay",
        "type": "rate_limit_error",
        "code": "free_plan_cap",
        "class": "ours",
        "resets_at": "2026-10-05T00:00:00Z",
        "upgrade_url": "https://hanzo.ai/pay/cart?plan=dev",
        "actions": [
            {
                "kind": "upgrade",
                "label": "Upgrade your plan",
                "url": "https://hanzo.ai/pay/cart?plan=dev",
                "plan": "dev",
            },
            {"kind": "topup", "label": "Add prepaid credit", "url": "https://hanzo.ai/pay"},
        ],
    }
}

MODEL_CAP = {
    "error": {
        "message": "This model has used its share of your plan for now. Enso answers until it resets.",
        "type": "billing_error",
        "code": "model_cap",
        "class": "premium",
        "model": "anthropic/claude-opus-4.1",
        "fallback": "enso",
        "resets_at": "2026-10-05T05:00:00Z",
        "actions": [
            {"kind": "switch", "label": "Try Enso", "model": "enso"},
            {
                "kind": "upgrade",
                "label": "Upgrade to Max",
                "url": "https://hanzo.ai/pay/cart?plan=max-5x",
                "plan": "max-5x",
            },
        ],
    }
}

PLAN_ALLOWANCE_USED = {
    "error": {
        "message": "Your plan's included premium usage is used for this period.",
        "type": "billing_error",
        "code": "plan_allowance_used",
        "class": "premium",
        "resets_at": "2026-11-01T00:00:00Z",
        "actions": [
            {"kind": "credits", "label": "Continue with credits", "url": "/v1/ai/limits"},
            {"kind": "topup", "label": "Add prepaid credit", "url": "https://hanzo.ai/pay"},
        ],
    }
}

PAID_PLAN_REQUIRED = {
    "error": {
        "message": "This model needs a paid plan or prepaid credit.",
        "type": "billing_error",
        "code": "paid_plan_required",
        "class": "premium",
        "model": "anthropic/claude-sonnet-4.5",
        "upgrade_url": "https://hanzo.ai/pay/cart?plan=dev",
        "actions": [
            {"kind": "upgrade", "label": "Upgrade to Pro", "url": "https://hanzo.ai/pay/cart?plan=dev", "plan": "dev"}
        ],
    }
}

USAGE_CAP_EXCEEDED = {
    "error": {
        "message": "You've used session requests on your plan. They reset at 2026-10-04T23:30:00Z.",
        "type": "rate_limit_error",
        "code": "usage_cap_exceeded",
        "limit": "session",
        "resets_at": "2026-10-04T23:30:00Z",
    }
}

#: The wallet refusal carries only the three members.
INSUFFICIENT_BALANCE = {
    "error": {
        "message": "Insufficient balance for this request.",
        "type": "billing_error",
        "code": "insufficient_balance",
    }
}


def reply(status, body, request="req_9", retry_after=0):
    return Reply(status=status, body=body, request=request, retry_after=retry_after)


# --------------------------------------------------------------------------
# One class per code
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "status, body, cls",
    [
        (402, PLAN_ALLOWANCE_USED, PlanAllowanceUsedError),
        (402, PAID_PLAN_REQUIRED, PaidPlanRequiredError),
        (429, FREE_PLAN_CAP, FreePlanCapError),
        (402, MODEL_CAP, ModelCapError),
        (429, USAGE_CAP_EXCEEDED, UsageCapExceededError),
        (402, INSUFFICIENT_BALANCE, InsufficientBalanceError),
    ],
)
def test_each_code_raises_its_own_class_under_one_base(status, body, cls):
    e = refusal(reply(status, body))
    assert type(e) is cls
    assert isinstance(e, UsageLimitError) and isinstance(e, Fault)
    assert (e.status, e.code, e.message, e.type) == (
        status,
        body["error"]["code"],
        body["error"]["message"],
        body["error"]["type"],
    )
    assert e.code == cls.CODE
    assert e.request == "req_9"


def test_free_plan_cap_reads_every_field_the_router_sends():
    e = refusal(reply(429, FREE_PLAN_CAP, retry_after=3032))
    assert e.usage_class == "ours"
    assert e.resets_at == datetime(2026, 10, 5, tzinfo=timezone.utc)
    assert e.upgrade_url == "https://hanzo.ai/pay/cart?plan=dev"
    assert e.model is None and e.fallback is None
    assert e.retry_after == 3032
    assert e.actions == (
        Action(kind="upgrade", label="Upgrade your plan", url="https://hanzo.ai/pay/cart?plan=dev", plan="dev"),
        Action(kind="topup", label="Add prepaid credit", url="https://hanzo.ai/pay"),
    )
    assert "429 free_plan_cap" in str(e) and "today's Kai requests are used" in str(e)


def test_model_cap_names_the_model_its_fallback_and_the_switch():
    e = refusal(reply(402, MODEL_CAP))
    assert (e.model, e.fallback, e.usage_class) == ("anthropic/claude-opus-4.1", "enso", "premium")
    assert e.actions[0] == Action(kind="switch", label="Try Enso", model="enso")


def test_a_spent_window_is_named_never_sized():
    e = refusal(reply(429, USAGE_CAP_EXCEEDED))
    assert (e.window, e.resets_at) == ("session", datetime(2026, 10, 4, 23, 30, tzinfo=timezone.utc))


def test_a_controller_s_v1_envelope_reads_the_same():
    e = refusal(
        reply(429, {"status": "error", "code": "free_plan_cap", "msg": "Free plan: today's Kai requests are used."})
    )
    assert type(e) is FreePlanCapError
    assert (e.message, e.usage_class, e.actions) == ("Free plan: today's Kai requests are used.", None, ())


def test_a_field_the_refusal_did_not_carry_is_none_not_empty():
    e = refusal(reply(402, INSUFFICIENT_BALANCE))
    assert (e.usage_class, e.model, e.fallback, e.window, e.resets_at, e.upgrade_url) == (None,) * 6
    assert e.actions == ()


@pytest.mark.parametrize(
    "status, body",
    [
        # The money gate's flat refusal is Denied's, not this family's.
        (402, {"type": "about:blank", "status": 402, "detail": "the wallet is empty", "code": "insufficient_balance"}),
        (402, {"error": "payment_required", "product": "search", "message": "top up"}),
        # The retryable sibling and the free lane are not usage-limit refusals.
        (503, {"error": {"code": "balance_unavailable", "message": "try again"}}),
        (429, {"error": {"code": "pool_busy", "message": "busy"}}),
        (400, {"status": "error", "code": "bad_request", "msg": "no"}),
        (500, "upstream exploded"),
        (402, None),
        # A success never is one, whatever it carries.
        (200, FREE_PLAN_CAP),
    ],
)
def test_anything_else_is_left_to_the_rule_that_reads_it(status, body):
    assert refusal(reply(status, body)) is None


# --------------------------------------------------------------------------
# The headers
# --------------------------------------------------------------------------


def test_read_usage_matches_without_regard_to_case():
    u = read_usage(
        {
            "X-Hanzo-Usage": "ok",
            "x-hanzo-usage-class": "premium",
            "X-HANZO-PAID-BY": "credits",
            "x-Hanzo-Served": "anthropic/claude-sonnet-4.5",
            "Content-Type": "application/json",
        }
    )
    assert u == Usage(usage="ok", usage_class="premium", paid_by="credits", served="anthropic/claude-sonnet-4.5")


def test_an_absent_header_reads_none_never_empty():
    u = read_usage({"x-hanzo-served": "enso", "x-hanzo-paid-by": "", "x-hanzo-fallback": "  "})
    assert u.served == "enso"
    assert (u.usage, u.usage_class, u.paid_by, u.fallback, u.reason) == (None, None, None, None, None)
    assert read_usage(None) == Usage()
    assert read_usage({}) == Usage()


def test_read_usage_takes_pairs_and_every_header_mapping():
    pairs = [("X-Hanzo-Fallback", "enso"), ("X-Hanzo-Usage-Reason", "model_cap"), ("X-Hanzo-Usage", "limited")]
    assert read_usage(pairs) == Usage(usage="limited", fallback="enso", reason="model_cap")
    assert read_usage(HTTPHeaderDict(pairs)) == read_usage(pairs)


# --------------------------------------------------------------------------
# Where the client raises them
# --------------------------------------------------------------------------


class Minted:
    """A credential that already holds its token, so no call goes to IAM."""

    def token(self):
        return "tok"

    def invalidate(self):
        pass


@pytest.fixture
def server():
    """A server on a free port: the base URL and the staged answers."""
    staged = []

    class Handler(BaseHTTPRequestHandler):
        def answer(self):
            n = int(self.headers.get("Content-Length") or 0)
            if n:
                self.rfile.read(n)
            status, headers, body = staged.pop(0)
            data = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            for name, v in headers.items():
                self.send_header(name, v)
            self.end_headers()
            self.wfile.write(data)

        do_GET = do_POST = answer

        def log_message(self, *args):
            pass

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        yield "http://127.0.0.1:{0}".format(httpd.server_address[1]), staged
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_send_raises_the_refusal_with_the_call_s_request_id(server):
    from hanzoai import Client

    base, staged = server
    staged.append((429, {"x-request-id": "req_kai", "Retry-After": "3032"}, FREE_PLAN_CAP))
    c = Client(base=base, credential=Minted())
    with pytest.raises(FreePlanCapError) as raised:
        c.send("POST", "/v1/decisions", body={"model": "kai", "state": "s", "questions": {}})
    assert (raised.value.request, raised.value.retry_after, raised.value.usage_class) == ("req_kai", 3032, "ours")


def test_a_generated_operation_raises_the_same_class(server):
    from hanzoai import Client
    from hanzoai.cloud import AiApi

    base, staged = server
    staged.append((402, {}, PLAN_ALLOWANCE_USED))
    with pytest.raises(PlanAllowanceUsedError) as raised:
        AiApi(Client(base=base, credential=Minted())).ai_limits()
    assert raised.value.actions[0].url == "/v1/ai/limits"


def test_a_generated_answer_s_headers_read_as_usage(server):
    from hanzoai import Client
    from hanzoai.cloud import AiApi

    base, staged = server
    headers = {"X-Hanzo-Usage": "ok", "X-Hanzo-Usage-Class": "premium", "X-Hanzo-Paid-By": "credits"}
    staged.append((200, headers, {"plan": "dev", "state": "ok"}))
    r = AiApi(Client(base=base, credential=Minted())).ai_limits_with_http_info()
    assert r.data.plan == "dev"
    assert read_usage(r.headers) == Usage(usage="ok", usage_class="premium", paid_by="credits")


# --------------------------------------------------------------------------
# Live, against api.hanzo.ai, as the signed-in `hanzo` CLI user
# --------------------------------------------------------------------------


class Bearer:
    """The `hanzo` CLI's live IAM session token, asked for once."""

    def __init__(self):
        import subprocess

        try:
            out = subprocess.run(["hanzo", "auth", "token"], capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.SubprocessError):
            out = None
        self.value = out.stdout.strip() if out and out.returncode == 0 else ""

    def token(self):
        return self.value

    def invalidate(self):
        pass


@pytest.fixture(scope="module")
def live():
    from hanzoai import Client

    bearer = Bearer()
    if not bearer.value:
        pytest.skip("no `hanzo auth token`: sign in with `hanzo auth login`")
    return Client(base="https://api.hanzo.ai", credential=bearer)


@pytest.mark.integration
def test_live_limits_models_and_a_premium_chat_paid_by_credits(live):
    from hanzoai.cloud import AiApi
    from hanzoai.cloud.models import OpenaiChatCompletionRequest

    ai = AiApi(live)

    limits = ai.ai_limits()
    assert limits.state in ("ok", "near", "limited")
    assert limits.plan

    rows = ai.get_models().data or []
    ours = [m for m in rows if m.var_class == "ours"]
    assert {"kai"} <= {m.id for m in ours}
    assert all(m.var_class in ("premium", "ours", "free") for m in rows)
    assert any(m.pricing and m.pricing.variable for m in rows)

    r = ai.post_chat_completions_with_http_info(
        OpenaiChatCompletionRequest.from_dict(
            {
                "model": "anthropic/claude-sonnet-4.5",
                "messages": [{"role": "user", "content": "Say ok"}],
                "max_tokens": 5,
            }
        )
    )
    u = read_usage(r.headers)
    assert (u.usage_class, u.paid_by, u.served) == ("premium", "credits", "anthropic/claude-sonnet-4.5")
    assert u.usage in ("ok", "near")


@pytest.mark.integration
def test_live_a_decision_answers_or_raises_its_typed_refusal(live):
    from hanzoai.cloud import AiApi
    from hanzoai.cloud.models import AiDecisionsRequest

    req = AiDecisionsRequest.from_dict(
        {
            "model": "kai",
            "state": "refund for a double charge",
            "questions": {
                "team": {
                    "type": "choice",
                    "criteria": {"payments": "money moved wrong", "account": "sign-in or profile"},
                }
            },
        }
    )
    try:
        d = AiApi(live).post_decisions(req)
    except UsageLimitError as e:
        # The free plan's daily Kai share, used: the refusal arrives typed.
        assert isinstance(e, FreePlanCapError) and e.usage_class == "ours" and e.resets_at is not None
    else:
        assert "team" in d.answers
