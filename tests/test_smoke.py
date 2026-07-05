"""Smoke tests for the generated `hanzoai` client.

The client is generated from hanzoai/openapi `hanzo.yaml` (openapi-generator,
urllib3). These assert the package imports and the unified api.hanzo.ai/v1
product surface is present — not network behaviour.
"""
import hanzoai


def test_client_constructs():
    cfg = hanzoai.Configuration(host="https://api.hanzo.ai")
    cfg.access_token = "hk-test"
    client = hanzoai.ApiClient(cfg)
    assert client is not None
    assert cfg.host == "https://api.hanzo.ai"


def test_product_apis_present():
    from hanzoai.api.tracker_projects_api import TrackerProjectsApi
    from hanzoai.api.chat_agents_api import ChatAgentsApi
    from hanzoai.api.crm_opportunities_api import CrmOpportunitiesApi

    client = hanzoai.ApiClient(hanzoai.Configuration(host="https://api.hanzo.ai"))
    for cls in (TrackerProjectsApi, ChatAgentsApi, CrmOpportunitiesApi):
        assert cls(client) is not None


def test_full_surface_breadth():
    import glob
    import os

    api_dir = os.path.dirname(hanzoai.api.__file__)
    modules = glob.glob(os.path.join(api_dir, "*_api.py"))
    # The full unified surface is hundreds of API groups, not the ~40 of the
    # legacy LLM-gateway-only client.
    assert len(modules) > 300, f"only {len(modules)} api modules — surface too small"
