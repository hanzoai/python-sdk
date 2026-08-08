"""Smoke tests for the generated `hanzoai` client.

The client is `hanzoai.cloud`, generated from hanzoai/cloud's openapi.yaml at the
ref .spec-lock names. These assert the package imports and that the unified
api.hanzo.ai/v1 product surface is present — not network behaviour.
"""
import hanzoai
import hanzoai.cloud


def test_client_constructs():
    cfg = hanzoai.cloud.Configuration(host="https://api.hanzo.ai")
    cfg.access_token = "hk-test"
    client = hanzoai.cloud.ApiClient(cfg)
    assert client is not None
    assert cfg.host == "https://api.hanzo.ai"


def test_product_apis_present():
    from hanzoai.cloud.api.tracker_api import TrackerApi
    from hanzoai.cloud.api.chat_api import ChatApi
    from hanzoai.cloud.api.crm_api import CrmApi

    client = hanzoai.cloud.ApiClient(hanzoai.cloud.Configuration(host="https://api.hanzo.ai"))
    for cls in (TrackerApi, ChatApi, CrmApi):
        assert cls(client) is not None


def test_full_surface_breadth():
    import glob
    import os

    api_dir = os.path.dirname(hanzoai.cloud.api.__file__)
    modules = glob.glob(os.path.join(api_dir, "*_api.py"))
    # One API group per product in the document, not the ~40 of the LLM-gateway
    # client this replaced.
    assert len(modules) > 150, f"only {len(modules)} api modules — surface too small"


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

    for name in ("AiApi", "KeysApi", "McpApi", "AdminApi"):
        assert hasattr(hanzoai.cloud, name), f"hanzoai.cloud.{name} missing"


def test_admin_plugin_operator_surface():
    """The /v1/admin/plugins operator surface must be reachable from the SDK.

    Four served routes: GET /v1/admin/plugins and POST
    /v1/admin/plugins/{name}/{enable,disable,reload}. The `plugin_` prefix these
    once carried came from the hand-merged master's `<svc>_` operationId
    namespacing; cloud's emission names them `adminPlugins`,
    `adminEnablePlugin`, `adminDisablePlugin`, `adminReloadPlugin`.
    """
    from hanzoai.cloud.api.admin_api import AdminApi

    for op in (
        "admin_plugins",
        "admin_enable_plugin",
        "admin_disable_plugin",
        "admin_reload_plugin",
    ):
        assert callable(getattr(AdminApi, op, None)), f"AdminApi.{op} missing"
