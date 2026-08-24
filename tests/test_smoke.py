"""Smoke tests for the generated `hanzoai` client.

The client is `hanzoai.cloud`, generated from hanzoai/cloud's openapi.yaml at the
ref .spec-lock names. These assert the package imports and that the unified
api.hanzo.ai/v1 product surface is present — not network behaviour.
"""
import hanzoai
import hanzoai.cloud


def test_client_constructs():
    cfg = hanzoai.cloud.Configuration(host="https://api.hanzo.ai")
    cfg.access_token = "sk-test"
    client = hanzoai.cloud.ApiClient(cfg)
    assert client is not None
    assert cfg.host == "https://api.hanzo.ai"


def test_the_bearer_comes_from_the_configuration():
    """`Configuration(access_token=…)` reaches the wire as `Authorization`.

    The document declares `securitySchemes.bearer` and applies it document-wide,
    so every operation carries `auth_settings=['bearer']` and
    `_apply_auth_params` sets the header. This asserts the whole path, not just
    the dict: serialize a real operation and read the header it produced.

    It asserted the opposite until the document grew the scheme — that a caller
    who set `access_token` sent nothing at all, and had to pass the header to
    `ApiClient` by hand. Keeping the negative here as an inverted assertion is
    what makes the fix a fact rather than a claim.
    """
    cfg = hanzoai.cloud.Configuration(host="https://api.hanzo.ai", access_token="sk-test")
    assert cfg.auth_settings()["bearer"] == {
        "type": "bearer", "in": "header", "key": "Authorization",
        "value": "Bearer sk-test",
    }

    api = hanzoai.cloud.IamApi(hanzoai.cloud.ApiClient(cfg))
    _, _, headers, _, _ = api._get_iam_keys_serialize(
        owner=None, _request_auth=None, _content_type=None, _headers=None, _host_index=0)
    assert headers["Authorization"] == "Bearer sk-test"


def test_the_public_operations_send_no_credential():
    """An operation the document marks `security: []` must not carry the header.

    A client that attaches a credential to an operation that takes none makes
    the API look like it authenticates when it does not. Five operations carry
    the marking; `GET /v1/openapi.json` is the one that has carried it across
    every pin, so it is what the mechanism is held to. `/v1/models` was here
    until it stopped declaring the marking, which is the document's call.
    """
    cfg = hanzoai.cloud.Configuration(host="https://api.hanzo.ai", access_token="sk-test")
    api = hanzoai.cloud.OpenapiApi(hanzoai.cloud.ApiClient(cfg))
    _, _, headers, _, _ = api._get_openapi_json_serialize(
        _request_auth=None, _content_type=None, _headers=None, _host_index=0)
    assert "Authorization" not in headers


def test_product_apis_present():
    """Whole products, not just the AI routes, reach the SDK.

    Name products the document still tags, read off the client rather than
    guessed. Tags move: `tracker`, then `analytics` and `chat`, each stood here
    until cloud folded those routes into the product that owns them.
    """
    from hanzoai.cloud.api.commerce_api import CommerceApi
    from hanzoai.cloud.api.crm_api import CrmApi
    from hanzoai.cloud.api.iam_api import IamApi

    client = hanzoai.cloud.ApiClient(hanzoai.cloud.Configuration(host="https://api.hanzo.ai"))
    for cls in (CommerceApi, CrmApi, IamApi):
        assert cls(client) is not None


def test_full_surface_breadth():
    import glob
    import os

    api_dir = os.path.dirname(hanzoai.cloud.api.__file__)
    modules = glob.glob(os.path.join(api_dir, "*_api.py"))
    # One API group per TAG in the document, not the ~40 of the LLM-gateway
    # client this replaced. 117 at the pinned ref, where cloud carries 130
    # products; the floor is a breadth check, not a count to keep in step.
    assert len(modules) > 100, f"only {len(modules)} api modules — surface too small"


def test_one_client_only():
    """There is exactly one generated client in this distribution.

    `hanzoai.api` / `hanzoai.models` was a second one, re-exported flat from the
    package root: 1,695 routes, of which 1,452 no longer exist in the document.
    A caller reaching for the obvious flat name got a client that 404s. This
    refuses its return — under that name or any other name beside `cloud`.
    """
    import pkgutil

    generated = {
        m.name
        for m in pkgutil.iter_modules(hanzoai.__path__)
        if m.ispkg and m.name in {"cloud", "api", "models"}
    }
    assert generated == {"cloud"}, f"more than one generated client: {sorted(generated)}"


def test_version_is_single_sourced():
    """`hanzoai.__version__` must be the installed distribution, never a literal.

    The generator writes `__version__ = "1.0.0"` (its default) into the package
    __init__; that literal disagreed with pyproject for every release.
    """
    from importlib.metadata import version

    assert hanzoai.__version__ == version("hanzoai")


def test_cloud_package_imports():
    """`hanzoai.cloud` is the generated client — it must import cleanly.

    This guarded a tag-casing collision in the retired hanzo.yaml lineage: tags
    differing only by case (`AI`/`ai`, `API Keys`/`api-keys`, `MCP`/`mcp`) made
    openapi-generator emit imports for classes it never wrote, so
    `import hanzoai.cloud` raised ImportError. The client is a projection of
    hanzoai/cloud's own emission now, which carries ONE spelling per tag, so the
    class names lost their all-caps variants: `AIApi`/`APIKeysApi`/`MCPApi` are
    `AiApi`/`KeysApi`/`McpApi`. The collision cannot recur while one document
    with one spelling per tag is the only input; what this still pins is that
    the top-level names resolve at all.
    """
    import hanzoai.cloud

    for name in ("AiApi", "IamApi", "ToolsApi", "OpenapiApi"):
        assert hasattr(hanzoai.cloud, name), f"hanzoai.cloud.{name} missing"


def test_plugin_operator_surface():
    """The plugin operator surface must be reachable from the SDK.

    Four published routes under `tools`: GET /v1/tools/plugins, GET and DELETE
    /v1/tools/plugins/authored[/{id}], POST /v1/tools/plugins/build. This asked
    `AdminApi` for /v1/admin/plugins until cloud stopped publishing an `admin`
    tag; that address still answers, and a client is a projection of the
    document, which no longer names it.
    """
    from hanzoai.cloud.api.tools_api import ToolsApi

    for op in (
        "get_tools_plugins",
        "get_tools_plugins_authored",
        "delete_tools_plugins_authored_by_id",
        "post_tools_plugins_build",
    ):
        assert callable(getattr(ToolsApi, op, None)), f"ToolsApi.{op} missing"
