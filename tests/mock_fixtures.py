# Mock fixtures for integration tests
import json

import respx
import pytest
from httpx import Response


@pytest.fixture
def mock_api(request):
    """Mock API responses for integration tests"""
    # Don't set up mocks if the test is using respx_mock directly
    if "respx_mock" in request.fixturenames:
        yield None
        return

    with respx.mock(base_url="http://127.0.0.1:4010", assert_all_called=False) as respx_mock:
        # Audio endpoints
        respx_mock.post("/audio/speech").mock(return_value=Response(200, json={}))
        respx_mock.post("/audio/transcriptions").mock(return_value=Response(200, json={}))

        # Batch endpoints
        respx_mock.post("/batch/cancel").mock(return_value=Response(200, json={}))
        respx_mock.post("/batches").mock(return_value=Response(200, json={"id": "batch-123"}))
        respx_mock.get("/batches").mock(return_value=Response(200, json={"data": []}))
        respx_mock.route(method="GET", path__regex=r"/batches/.*").mock(
            return_value=Response(200, json={"id": "batch-123"})
        )
        respx_mock.route(method="POST", path__regex=r"/batches/.*/cancel").mock(return_value=Response(200, json={}))

        # Cache endpoints
        respx_mock.get("/cache/ping").mock(
            return_value=Response(
                200,
                json={
                    "status": "healthy",
                    "cache_type": "redis",
                    "ping_response": True,
                    "set_cache_response": None,
                    "llm_cache_params": None,
                    "health_check_cache_params": None,
                },
            )
        )
        respx_mock.post("/cache/delete").mock(return_value=Response(200, json={}))
        respx_mock.post("/cache/flushall").mock(return_value=Response(200, json={}))
        respx_mock.get("/cache/redis/ping").mock(return_value=Response(200, json={"status": "ok"}))
        respx_mock.delete("/cache").mock(return_value=Response(200, json={}))
        respx_mock.get("/cache/flush").mock(return_value=Response(200, json={}))

        # Chat completions
        respx_mock.post("/chat/completions").mock(
            return_value=Response(
                200,
                json={
                    "id": "chatcmpl-123",
                    "object": "chat.completion",
                    "created": 1677652288,
                    "model": "gpt-3.5-turbo",
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": "Hello!"},
                            "finish_reason": "stop",
                        }
                    ],
                },
            )
        )

        # Config endpoints
        respx_mock.post("/config/pass_through_endpoints").mock(return_value=Response(200, json={}))
        respx_mock.post("/config/pass_through_endpoint").mock(return_value=Response(200, json={}))
        respx_mock.route(method="PUT", path__regex=r"/config/pass_through_endpoints/.*").mock(
            return_value=Response(200, json={})
        )
        respx_mock.get("/config/pass_through_endpoints").mock(return_value=Response(200, json={"data": []}))
        respx_mock.get("/config/pass_through_endpoint").mock(return_value=Response(200, json={"endpoints": []}))
        respx_mock.delete("/config/pass_through_endpoint").mock(return_value=Response(200, json={"endpoints": []}))
        respx_mock.route(method="DELETE", path__regex=r"/config/pass_through_endpoints/.*").mock(
            return_value=Response(200, json={})
        )

        # Engine endpoints
        respx_mock.route(method="POST", path__regex=r"/engines/.*/chat/completions").mock(
            return_value=Response(200, json={})
        )

        # Files
        respx_mock.route(method="GET", path__regex=r"/files/.*/content").mock(
            return_value=Response(200, json="file content")
        )
        respx_mock.route(method="GET", path__regex=r"/.*/v1/files/.*/content").mock(
            return_value=Response(200, json="file content")
        )
        respx_mock.post("/files").mock(return_value=Response(200, json={"id": "file-123"}))
        respx_mock.get("/files").mock(return_value=Response(200, json={"data": []}))
        respx_mock.route(method="DELETE", path__regex=r"/files/.*").mock(return_value=Response(200, json={}))

        # Fine-tuning
        respx_mock.post("/fine_tuning/jobs").mock(return_value=Response(200, json={"id": "ft-123"}))
        respx_mock.get("/fine_tuning/jobs").mock(return_value=Response(200, json={"data": []}))
        respx_mock.route(method="GET", path__regex=r"/fine_tuning/jobs/[^/]+$").mock(
            return_value=Response(200, json={"id": "ft-123"})
        )
        respx_mock.route(method="POST", path__regex=r"/fine_tuning/jobs/.*/cancel").mock(
            return_value=Response(200, json={})
        )

        # Global spend
        respx_mock.get("/global/spend/tags").mock(return_value=Response(200, json=[]))
        respx_mock.post("/global/spend/reset").mock(return_value=Response(200, json={}))
        respx_mock.get("/global/spend/report").mock(return_value=Response(200, json=[]))

        # Guardrails
        respx_mock.get("/guardrails/list").mock(return_value=Response(200, json={"guardrails": []}))

        # Images
        respx_mock.post("/images/generations").mock(return_value=Response(200, json={"data": []}))

        # Models
        respx_mock.get("/model/info").mock(return_value=Response(200, json={"data": []}))
        respx_mock.put("/models/update").mock(return_value=Response(200, json={}))
        respx_mock.route(method="PATCH", path__regex=r"/models/.*").mock(return_value=Response(200, json={}))
        respx_mock.post("/models").mock(return_value=Response(200, json={}))
        respx_mock.get("/models").mock(return_value=Response(200, json={"data": []}))
        respx_mock.route(method="DELETE", path__regex=r"/models/.*").mock(return_value=Response(200, json={}))

        # OpenAI deployments
        respx_mock.route(method="POST", path__regex=r"/openai/deployments/.*/chat/completions").mock(
            return_value=Response(200, json={})
        )
        respx_mock.route(method="POST", path__regex=r"/openai/deployments/.*/completions").mock(
            return_value=Response(200, json={})
        )
        respx_mock.route(method="POST", path__regex=r"/openai/deployments/.*/embeddings").mock(
            return_value=Response(200, json={})
        )

        # Organization
        org_response = {
            "budget_id": "budget-123",
            "created_at": "2024-01-01T00:00:00Z",
            "created_by": "user-123",
            "models": ["gpt-3.5-turbo"],
            "organization_id": "org-123",
            "updated_at": "2024-01-01T00:00:00Z",
            "updated_by": "user-123",
        }
        respx_mock.get("/organization/info").mock(
            return_value=Response(
                200,
                json={
                    "budget_id": "budget-123",
                    "created_at": "2024-01-01T00:00:00Z",
                    "created_by": "user-123",
                    "models": ["gpt-3.5-turbo"],
                    "updated_at": "2024-01-01T00:00:00Z",
                    "updated_by": "user-123",
                },
            )
        )
        respx_mock.get("/organization/info/deprecated").mock(return_value=Response(200, json={}))
        respx_mock.post("/organization/new").mock(return_value=Response(200, json=org_response))
        respx_mock.post("/organization").mock(return_value=Response(200, json={}))
        respx_mock.get("/organization/list").mock(return_value=Response(200, json=[]))
        respx_mock.get("/organization").mock(return_value=Response(200, json=[]))
        org_update_response = {
            "budget_id": "budget-123",
            "created_at": "2024-01-01T00:00:00Z",
            "created_by": "user-123",
            "models": ["gpt-3.5-turbo"],
            "updated_at": "2024-01-01T00:00:00Z",
            "updated_by": "user-123",
            "organization_id": "org-123",
            "members": [],
            "teams": [],
        }
        respx_mock.patch("/organization/update").mock(return_value=Response(200, json=org_update_response))
        respx_mock.put("/organization/update").mock(return_value=Response(200, json=org_update_response))
        respx_mock.put("/organization").mock(return_value=Response(200, json={}))
        respx_mock.delete("/organization/delete").mock(return_value=Response(200, json=[org_response]))
        respx_mock.delete("/organization").mock(return_value=Response(200, json={}))
        org_member_response = {
            "organization_id": "org-123",
            "updated_organization_memberships": [],
            "updated_users": [],
        }
        respx_mock.post("/organization/member_add").mock(return_value=Response(200, json=org_member_response))
        respx_mock.post("/organization/members").mock(return_value=Response(200, json={}))
        respx_mock.delete("/organization/member_delete").mock(return_value=Response(200, json=org_response))
        respx_mock.delete("/organization/members").mock(return_value=Response(200, json={}))
        org_update_member_response = {
            "created_at": "2024-01-01T00:00:00Z",
            "organization_id": "org-123",
            "updated_at": "2024-01-01T00:00:00Z",
            "user_id": "user-123",
        }
        respx_mock.patch("/organization/member_update").mock(
            return_value=Response(200, json=org_update_member_response)
        )
        respx_mock.put("/organization/member_update").mock(return_value=Response(200, json=org_update_member_response))
        respx_mock.put("/organization/members").mock(return_value=Response(200, json={}))

        # Responses
        respx_mock.route(method="GET", path__regex=r"/responses/.*/input_items").mock(
            return_value=Response(200, json={"data": []})
        )

        # Team
        team_response = {
            "team_id": "team-123",
            "models": [],
            "members": [],
            "admins": [],
        }
        respx_mock.route(method="GET", path__regex=r"/team/.*/callback").mock(return_value=Response(200, json={}))
        respx_mock.route(method="POST", path__regex=r"/team/.*/callback").mock(return_value=Response(200, json={}))
        respx_mock.post("/team/model").mock(return_value=Response(200, json={}))
        respx_mock.delete("/team/model").mock(return_value=Response(200, json={}))
        respx_mock.post("/team/new").mock(return_value=Response(200, json=team_response))
        respx_mock.post("/team").mock(return_value=Response(200, json={}))
        respx_mock.get("/team/list").mock(return_value=Response(200, json=[]))
        respx_mock.get("/team").mock(return_value=Response(200, json=[]))
        respx_mock.get("/team/info").mock(return_value=Response(200, json=team_response))
        respx_mock.patch("/team/update").mock(return_value=Response(200, json=team_response))
        respx_mock.put("/team/update").mock(return_value=Response(200, json=team_response))
        respx_mock.put("/team").mock(return_value=Response(200, json={}))
        respx_mock.delete("/team/delete").mock(return_value=Response(200, json=[team_response]))
        respx_mock.delete("/team").mock(return_value=Response(200, json={}))
        team_add_member_response = {
            "team_id": "team-123",
            "updated_team_memberships": [],
            "updated_users": [],
        }
        team_update_member_response = {"team_id": "team-123", "user_id": "user-123"}
        respx_mock.post("/team/member_add").mock(return_value=Response(200, json=team_add_member_response))
        respx_mock.post("/team/members").mock(return_value=Response(200, json={}))
        respx_mock.delete("/team/member_delete").mock(return_value=Response(200, json=team_response))
        respx_mock.delete("/team/members").mock(return_value=Response(200, json={}))
        respx_mock.post("/team/member_update").mock(return_value=Response(200, json=team_update_member_response))
        respx_mock.patch("/team/member_update").mock(return_value=Response(200, json=team_update_member_response))
        respx_mock.put("/team/member_update").mock(return_value=Response(200, json=team_update_member_response))
        respx_mock.put("/team/members").mock(return_value=Response(200, json={}))
        respx_mock.post("/team/block").mock(return_value=Response(200, json=team_response))
        respx_mock.post("/team/unblock").mock(return_value=Response(200, json=team_response))

        # Other endpoints
        respx_mock.get("/active/callbacks").mock(return_value=Response(200, json={"data": []}))
        respx_mock.post("/add/allowed_ip").mock(return_value=Response(200, json={}))
        respx_mock.post("/delete/allowed_ip").mock(return_value=Response(200, json={}))

        # Provider endpoints (anthropic, azure, bedrock, etc.)
        for provider in [
            "anthropic",
            "azure",
            "bedrock",
            "cohere",
            "gemini",
            "openai",
            "vertex_ai",
            "assemblyai",
            "eu_assemblyai",
        ]:
            respx_mock.post(f"/{provider}").mock(return_value=Response(200, json={}))
            respx_mock.get(f"/{provider}").mock(return_value=Response(200, json={"data": []}))
            respx_mock.route(method="GET", path__regex=rf"/{provider}/.*").mock(return_value=Response(200, json={}))
            respx_mock.put(f"/{provider}").mock(return_value=Response(200, json={}))
            respx_mock.route(method="PUT", path__regex=rf"/{provider}/.*").mock(return_value=Response(200, json={}))
            respx_mock.patch(f"/{provider}").mock(return_value=Response(200, json={}))
            respx_mock.route(method="PATCH", path__regex=rf"/{provider}/.*").mock(return_value=Response(200, json={}))
            respx_mock.delete(f"/{provider}").mock(return_value=Response(200, json={}))
            respx_mock.route(method="DELETE", path__regex=rf"/{provider}/.*").mock(return_value=Response(200, json={}))
            respx_mock.post(f"/{provider}/modify").mock(return_value=Response(200, json={}))
            respx_mock.post(f"/{provider}/call").mock(return_value=Response(200, json={}))

        # Assistants
        respx_mock.post("/assistants").mock(return_value=Response(200, json={}))
        respx_mock.get("/assistants").mock(return_value=Response(200, json={"data": []}))
        respx_mock.route(method="DELETE", path__regex=r"/assistants/.*").mock(return_value=Response(200, json={}))

        # Budget
        respx_mock.post("/budget").mock(return_value=Response(200, json={}))
        respx_mock.put("/budget").mock(return_value=Response(200, json={}))
        respx_mock.get("/budget").mock(return_value=Response(200, json={"data": []}))
        respx_mock.delete("/budget").mock(return_value=Response(200, json={}))
        respx_mock.get("/budget/info").mock(return_value=Response(200, json={}))
        respx_mock.get("/budget/settings").mock(return_value=Response(200, json={}))

        # Completions
        respx_mock.post("/completions").mock(return_value=Response(200, json={}))

        # Credentials
        respx_mock.post("/credentials").mock(return_value=Response(200, json={}))
        respx_mock.put("/credentials").mock(return_value=Response(200, json={}))

        # Customer
        respx_mock.post("/customer").mock(return_value=Response(200, json={}))
        respx_mock.get("/customer").mock(return_value=Response(200, json={"data": []}))
        respx_mock.get("/customer/list").mock(return_value=Response(200, json=[]))
        respx_mock.get("/customer/info").mock(
            return_value=Response(200, json={"blocked": False, "user_id": "user-123"})
        )
        respx_mock.put("/customer").mock(return_value=Response(200, json={}))
        respx_mock.delete("/customer").mock(return_value=Response(200, json={}))
        respx_mock.post("/customer/block").mock(return_value=Response(200, json={}))
        respx_mock.post("/customer/unblock").mock(return_value=Response(200, json={}))

        # Embeddings
        respx_mock.post("/embeddings").mock(return_value=Response(200, json={"data": []}))

        # Guardrails
        respx_mock.get("/guardrails").mock(return_value=Response(200, json={"data": []}))

        # Health
        respx_mock.get("/health").mock(return_value=Response(200, json={"status": "healthy"}))
        respx_mock.get("/health/services").mock(return_value=Response(200, json={}))

        # Key management
        respx_mock.post("/key").mock(return_value=Response(200, json={}))
        respx_mock.get("/key").mock(return_value=Response(200, json={"data": []}))
        respx_mock.get("/key/info").mock(return_value=Response(200, json={}))
        respx_mock.put("/key").mock(return_value=Response(200, json={}))
        respx_mock.delete("/key").mock(return_value=Response(200, json={}))
        respx_mock.post("/key/generate").mock(return_value=Response(200, json={"key": "sk-123"}))
        respx_mock.post("/key/regenerate").mock(return_value=Response(200, json={"key": "sk-456"}))
        respx_mock.post("/key/key/regenerate").mock(return_value=Response(200, json={"key": "sk-789"}))
        respx_mock.post("/key/block").mock(return_value=Response(200, json={}))
        respx_mock.post("/key/unblock").mock(return_value=Response(200, json={}))
        respx_mock.get("/key/health").mock(return_value=Response(200, json={"status": "ok"}))

        # Langfuse
        respx_mock.post("/langfuse").mock(return_value=Response(200, json={}))

        # Model group
        respx_mock.get("/model_group/info").mock(return_value=Response(200, json={}))

        # Moderations
        respx_mock.post("/moderations").mock(return_value=Response(200, json={}))

        # Provider
        respx_mock.get("/provider/budgets").mock(return_value=Response(200, json={"data": []}))

        # Rerank
        respx_mock.post("/rerank").mock(return_value=Response(200, json={}))

        # Routes
        respx_mock.get("/routes").mock(return_value=Response(200, json={"data": []}))

        # Settings
        respx_mock.get("/settings").mock(return_value=Response(200, json={}))

        # Spend
        respx_mock.get("/spend/calculate").mock(return_value=Response(200, json={}))
        respx_mock.get("/spend/logs").mock(return_value=Response(200, json=[]))
        respx_mock.get("/spend/tags").mock(return_value=Response(200, json=[]))

        # Test
        respx_mock.get("/test").mock(return_value=Response(200, json={}))

        # Root endpoint for client tests
        respx_mock.get("/").mock(return_value=Response(200, json={}))

        # Threads
        respx_mock.post("/threads").mock(return_value=Response(200, json={}))
        respx_mock.get("/threads").mock(return_value=Response(200, json={"data": []}))
        respx_mock.route(method="GET", path__regex=r"/threads/[^/]+$").mock(return_value=Response(200, json={}))
        respx_mock.route(method="PUT", path__regex=r"/threads/.*").mock(return_value=Response(200, json={}))
        respx_mock.route(method="DELETE", path__regex=r"/threads/.*").mock(return_value=Response(200, json={}))
        respx_mock.route(method="POST", path__regex=r"/threads/.*/messages").mock(return_value=Response(200, json={}))
        respx_mock.route(method="GET", path__regex=r"/threads/.*/messages").mock(
            return_value=Response(200, json={"data": []})
        )
        respx_mock.route(method="POST", path__regex=r"/threads/.*/runs").mock(return_value=Response(200, json={}))
        respx_mock.route(method="GET", path__regex=r"/threads/.*/runs").mock(
            return_value=Response(200, json={"data": []})
        )

        # User
        user_response = {"key": "sk-user-123", "user_id": "user-123"}
        respx_mock.post("/user/new").mock(return_value=Response(200, json=user_response))
        respx_mock.post("/user").mock(return_value=Response(200, json={}))
        respx_mock.get("/user/list").mock(return_value=Response(200, json=[]))
        respx_mock.get("/user").mock(return_value=Response(200, json=[]))
        respx_mock.get("/user/info").mock(return_value=Response(200, json=user_response))
        respx_mock.put("/user/update").mock(return_value=Response(200, json=user_response))
        respx_mock.put("/user").mock(return_value=Response(200, json={}))
        respx_mock.delete("/user/delete").mock(return_value=Response(200, json=user_response))
        respx_mock.delete("/user").mock(return_value=Response(200, json={}))

        # Utils
        respx_mock.get("/utils/supported_openai_params").mock(return_value=Response(200, json={}))
        respx_mock.post("/utils/token_counter").mock(
            return_value=Response(
                200,
                json={
                    "model_used": "gpt-3.5-turbo",
                    "request_model": "gpt-3.5-turbo",
                    "tokenizer_type": "cl100k_base",
                    "total_tokens": 10,
                },
            )
        )
        respx_mock.post("/utils/transform_request").mock(return_value=Response(200, json={}))

        # Home/client
        respx_mock.get("/").mock(return_value=Response(200, json={"message": "Welcome"}))

        # Catch-all for any unmocked endpoints
        respx_mock.route().mock(return_value=Response(200, json={}))

        yield respx_mock
