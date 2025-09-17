"""Integration test for agent clarification and critic features."""

import json
from unittest.mock import Mock, patch

import pytest
from hanzo_mcp.tools.agent.agent_tool import AgentTool
from hanzo_mcp.tools.agent.critic_tool import ReviewType
from hanzo_mcp.tools.common.permissions import PermissionManager
from hanzo_mcp.tools.agent.clarification_protocol import ClarificationType


@pytest.fixture
def mock_context():
    """Create a mock MCP context."""
    ctx = Mock()
    ctx.session_id = "test-session"
    return ctx


@pytest.fixture
def test_project(tmp_path):
    """Create a test project structure."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Create a test file with import issues
    test_file = project_dir / "main.go"
    test_file.write_text(
        """package main

import (
    "fmt"
)

func main() {
    logger := common.GetLogger()
    logger.Info("Starting application")
    
    config := common.LoadConfig()
    fmt.Printf("Config: %v\\n", config)
}
"""
    )

    return project_dir


@pytest.mark.asyncio
async def test_agent_clarification_flow(test_project, mock_context):
    """Test that agents can request clarification from main loop."""
    permission_manager = PermissionManager(allowed_paths=[str(test_project)])

    # Create an agent tool with test model
    agent = AgentTool(permission_manager=permission_manager, model="test-model", max_iterations=5)

    # Mock the litellm completion to simulate agent requesting clarification
    with patch("litellm.completion") as mock_completion:
        # First call - agent reads file and asks for clarification
        mock_completion.side_effect = [
            # First iteration - read file and request clarification
            Mock(
                choices=[
                    Mock(
                        message=Mock(
                            content=None,
                            tool_calls=[
                                Mock(
                                    function=Mock(
                                        name="read",
                                        arguments=json.dumps({"file_path": str(test_project / "main.go")}),
                                    ),
                                    id="call_1",
                                )
                            ],
                        )
                    )
                ]
            ),
            # Second iteration - process file content and request clarification
            Mock(
                choices=[
                    Mock(
                        message=Mock(
                            content=None,
                            tool_calls=[
                                Mock(
                                    function=Mock(
                                        name="request_clarification",
                                        arguments=json.dumps(
                                            {
                                                "type": "MISSING_CONTEXT",
                                                "question": "What is the correct import path for the common package?",
                                                "context": {
                                                    "file_path": str(test_project / "main.go"),
                                                    "undefined_symbols": ["common"],
                                                },
                                                "options": [
                                                    "github.com/project/common",
                                                    "github.com/company/common",
                                                    "../common",
                                                ],
                                            }
                                        ),
                                    ),
                                    id="call_2",
                                )
                            ],
                        )
                    )
                ]
            ),
            # Third iteration - use clarification to fix the file
            Mock(
                choices=[
                    Mock(
                        message=Mock(
                            content=None,
                            tool_calls=[
                                Mock(
                                    function=Mock(
                                        name="multi_edit",
                                        arguments=json.dumps(
                                            {
                                                "file_path": str(test_project / "main.go"),
                                                "edits": [
                                                    {
                                                        "old_string": 'import (\n    "fmt"\n)',
                                                        "new_string": 'import (\n    "fmt"\n    "github.com/project/common"\n)',
                                                    }
                                                ],
                                            }
                                        ),
                                    ),
                                    id="call_3",
                                )
                            ],
                        )
                    )
                ]
            ),
            # Final response
            Mock(
                choices=[
                    Mock(
                        message=Mock(
                            content="I've successfully added the missing import for the common package based on the clarification received.",
                            tool_calls=None,
                        )
                    )
                ]
            ),
        ]

        # Execute the agent
        result = await agent.call(
            mock_context,
            prompts=f"Fix the undefined 'common' import in {test_project / 'main.go'}",
        )

        # Verify the result
        tool_helper.assert_in_result("successfully added the missing import", result)
        assert "clarification" in result.lower()

        # Verify the agent made the expected tool calls
        assert mock_completion.call_count == 4

        # Check file was modified
        content = (test_project / "main.go").read_text()
        assert "github.com/project/common" in content


@pytest.mark.asyncio
async def test_agent_critic_flow(test_project, mock_context):
    """Test that agents can request critical review."""
    permission_manager = PermissionManager(allowed_paths=[str(test_project)])

    # Create an agent tool
    agent = AgentTool(permission_manager=permission_manager, model="test-model", max_iterations=5)

    # Mock the litellm completion to simulate agent requesting critic review
    with patch("litellm.completion") as mock_completion:
        mock_completion.side_effect = [
            # First iteration - read file
            Mock(
                choices=[
                    Mock(
                        message=Mock(
                            content=None,
                            tool_calls=[
                                Mock(
                                    function=Mock(
                                        name="read",
                                        arguments=json.dumps({"file_path": str(test_project / "main.go")}),
                                    ),
                                    id="call_1",
                                )
                            ],
                        )
                    )
                ]
            ),
            # Second iteration - make initial fix
            Mock(
                choices=[
                    Mock(
                        message=Mock(
                            content=None,
                            tool_calls=[
                                Mock(
                                    function=Mock(
                                        name="multi_edit",
                                        arguments=json.dumps(
                                            {
                                                "file_path": str(test_project / "main.go"),
                                                "edits": [
                                                    {
                                                        "old_string": 'import (\n    "fmt"\n)',
                                                        "new_string": 'import (\n    "fmt"\n    "github.com/project/common"\n)',
                                                    }
                                                ],
                                            }
                                        ),
                                    ),
                                    id="call_2",
                                )
                            ],
                        )
                    )
                ]
            ),
            # Third iteration - request critic review
            Mock(
                choices=[
                    Mock(
                        message=Mock(
                            content=None,
                            tool_calls=[
                                Mock(
                                    function=Mock(
                                        name="critic",
                                        arguments=json.dumps(
                                            {
                                                "review_type": "CODE_QUALITY",
                                                "work_description": "Added missing import for common package",
                                                "code_snippets": [
                                                    'import (\n    "fmt"\n    "github.com/project/common"\n)'
                                                ],
                                                "file_paths": [str(test_project / "main.go")],
                                                "specific_concerns": "Is the import in the correct format and position?",
                                            }
                                        ),
                                    ),
                                    id="call_3",
                                )
                            ],
                        )
                    )
                ]
            ),
            # Final response after critic review
            Mock(
                choices=[
                    Mock(
                        message=Mock(
                            content="Fixed the import issue. The critic confirmed the import is properly formatted and in the correct position.",
                            tool_calls=None,
                        )
                    )
                ]
            ),
        ]

        # Execute the agent
        result = await agent.call(
            mock_context,
            prompts=f"Fix the undefined 'common' import in {test_project / 'main.go'} and verify the fix with critic review",
        )

        # Verify the result
        assert "critic confirmed" in result.lower()
        assert mock_completion.call_count == 4


@pytest.mark.asyncio
async def test_clarification_limits(test_project, mock_context):
    """Test that clarification requests are limited."""
    permission_manager = PermissionManager(allowed_paths=[str(test_project)])

    agent = AgentTool(permission_manager=permission_manager, model="test-model", max_iterations=5)

    # Test that only one clarification is allowed
    with patch("litellm.completion") as mock_completion:
        mock_completion.side_effect = [
            # First clarification request
            Mock(
                choices=[
                    Mock(
                        message=Mock(
                            content=None,
                            tool_calls=[
                                Mock(
                                    function=Mock(
                                        name="request_clarification",
                                        arguments=json.dumps(
                                            {
                                                "type": "MISSING_CONTEXT",
                                                "question": "First question",
                                                "context": {},
                                            }
                                        ),
                                    ),
                                    id="call_1",
                                )
                            ],
                        )
                    )
                ]
            ),
            # Try second clarification (should fail)
            Mock(
                choices=[
                    Mock(
                        message=Mock(
                            content=None,
                            tool_calls=[
                                Mock(
                                    function=Mock(
                                        name="request_clarification",
                                        arguments=json.dumps(
                                            {
                                                "type": "MISSING_CONTEXT",
                                                "question": "Second question",
                                                "context": {},
                                            }
                                        ),
                                    ),
                                    id="call_2",
                                )
                            ],
                        )
                    )
                ]
            ),
            # Final response
            Mock(
                choices=[
                    Mock(
                        message=Mock(
                            content="Completed with clarification limit error.",
                            tool_calls=None,
                        )
                    )
                ]
            ),
        ]

        result = await agent.call(mock_context, prompts="Test clarification limits")

        # The second clarification should fail
        assert "limit" in result.lower()


@pytest.mark.asyncio
async def test_critic_limits(test_project, mock_context):
    """Test that critic reviews are limited."""
    permission_manager = PermissionManager(allowed_paths=[str(test_project)])

    agent = AgentTool(permission_manager=permission_manager, model="test-model", max_iterations=6)

    # Test that only two critic reviews are allowed
    with patch("litellm.completion") as mock_completion:
        review_args = json.dumps(
            {
                "review_type": "GENERAL",
                "work_description": "Test work",
                "code_snippets": None,
                "file_paths": None,
                "specific_concerns": None,
            }
        )

        mock_completion.side_effect = [
            # First review
            Mock(
                choices=[
                    Mock(
                        message=Mock(
                            content=None,
                            tool_calls=[
                                Mock(
                                    function=Mock(name="critic", arguments=review_args),
                                    id="call_1",
                                )
                            ],
                        )
                    )
                ]
            ),
            # Second review
            Mock(
                choices=[
                    Mock(
                        message=Mock(
                            content=None,
                            tool_calls=[
                                Mock(
                                    function=Mock(name="critic", arguments=review_args),
                                    id="call_2",
                                )
                            ],
                        )
                    )
                ]
            ),
            # Third review (should fail)
            Mock(
                choices=[
                    Mock(
                        message=Mock(
                            content=None,
                            tool_calls=[
                                Mock(
                                    function=Mock(name="critic", arguments=review_args),
                                    id="call_3",
                                )
                            ],
                        )
                    )
                ]
            ),
            # Final response
            Mock(
                choices=[
                    Mock(
                        message=Mock(
                            content="Completed with review limit exceeded.",
                            tool_calls=None,
                        )
                    )
                ]
            ),
        ]

        result = await agent.call(mock_context, prompts="Test critic review limits")

        # The third review should fail
        assert "limit exceeded" in result.lower()


@pytest.mark.asyncio
async def test_clarification_protocol_types():
    """Test all clarification types work correctly."""
    from hanzo_mcp.tools.agent.clarification_protocol import ClarificationHandler

    handler = ClarificationHandler()

    # Test each clarification type
    types_to_test = [
        (ClarificationType.AMBIGUOUS_INSTRUCTION, {"file_path": "test.go"}),
        (ClarificationType.MISSING_CONTEXT, {}),
        (ClarificationType.MULTIPLE_OPTIONS, {}),
        (ClarificationType.CONFIRMATION_NEEDED, {}),
        (ClarificationType.ADDITIONAL_INFO, {}),
    ]

    for clarification_type, context in types_to_test:
        request_id = handler.create_request(
            agent_id="test-agent",
            request_type=clarification_type,
            question=f"Test question for {clarification_type.value}",
            context=context,
            options=(["option1", "option2"] if clarification_type == ClarificationType.MULTIPLE_OPTIONS else None),
        )

        assert request_id.startswith("clarify_")
        assert len(handler.pending_requests) > 0

        # Get the request and handle it
        request = handler.pending_requests[request_id]
        response = handler.handle_request(request)

        assert response.answer
        assert len(response.answer) > 0


@pytest.mark.asyncio
async def test_critic_review_types():
    """Test all review types work correctly."""
    from hanzo_mcp.tools.agent.critic_tool import AutoCritic

    critic = AutoCritic()

    # Test each review type
    for review_type in ReviewType:
        review = critic.review(
            review_type=review_type,
            work_description="Test work for review",
            code_snippets=["import fmt", "if err != nil { return err }"],
            file_paths=["test.go"],
            specific_concerns="Is this correct?",
        )

        assert review
        assert "REVIEW" in review
        assert len(review) > 50  # Ensure substantial feedback


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
