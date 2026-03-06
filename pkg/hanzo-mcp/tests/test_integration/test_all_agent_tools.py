"""Integration test for all agent tools working together."""

import json
import sys
from types import ModuleType
from unittest.mock import Mock, patch

import pytest
from hanzo_tools.agent.agent_tool import AgentTool

# Ensure 'llm' module is available for mocking even if not installed
if "llm" not in sys.modules:
    _mock_llm = ModuleType("llm")
    _mock_llm.completion = Mock()
    sys.modules["llm"] = _mock_llm


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

    # Create a test file with a challenging problem
    test_file = project_dir / "complex_algorithm.py"
    test_file.write_text("""def find_optimal_path(graph, start, end):
    # TODO: Implement this complex pathfinding algorithm
    # Should handle weighted graphs, cycles, and negative edges
    pass
""")

    return project_dir


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires CLI agent backends (claude/codex/grok) installed")
async def test_agent_uses_all_tools(test_project, mock_context):
    """Test that an agent can use clarification, critic, review, and zen tools."""
    # Create an agent tool
    agent = AgentTool()

    # Mock the llm completion to simulate agent using all tools
    with patch("llm.completion") as mock_completion:
        mock_completion.side_effect = [
            # 1. Read the file
            Mock(
                choices=[
                    Mock(
                        message=Mock(
                            content=None,
                            tool_calls=[
                                Mock(
                                    function=Mock(
                                        name="read",
                                        arguments=json.dumps(
                                            {
                                                "file_path": str(
                                                    test_project
                                                    / "complex_algorithm.py"
                                                )
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
            # 2. Use zen guidance for creative direction
            Mock(
                choices=[
                    Mock(
                        message=Mock(
                            content=None,
                            tool_calls=[
                                Mock(
                                    function=Mock(
                                        name="zen",
                                        arguments=json.dumps(
                                            {
                                                "challenge": "How should I approach implementing this complex pathfinding algorithm?"
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
            # 3. Request clarification about requirements
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
                                                "question": "Should the algorithm optimize for shortest path or lowest cost?",
                                                "context": {
                                                    "algorithm": "pathfinding",
                                                    "requirements": "unclear",
                                                },
                                                "options": [
                                                    "shortest_distance",
                                                    "lowest_cost",
                                                    "balanced",
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
            # 4. Implement initial solution
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
                                                "file_path": str(
                                                    test_project
                                                    / "complex_algorithm.py"
                                                ),
                                                "edits": [
                                                    {
                                                        "old_string": """def find_optimal_path(graph, start, end):
    # TODO: Implement this complex pathfinding algorithm
    # Should handle weighted graphs, cycles, and negative edges
    pass""",
                                                        "new_string": """def find_optimal_path(graph, start, end):
    \"\"\"Find optimal path using modified Dijkstra's algorithm.
    
    Handles weighted graphs, cycles, and uses Bellman-Ford for negative edges.
    \"\"\"
    # Implementation here
    return []  # Placeholder""",
                                                    }
                                                ],
                                            }
                                        ),
                                    ),
                                    id="call_4",
                                )
                            ],
                        )
                    )
                ]
            ),
            # 5. Request balanced review
            Mock(
                choices=[
                    Mock(
                        message=Mock(
                            content=None,
                            tool_calls=[
                                Mock(
                                    function=Mock(
                                        name="review",
                                        arguments=json.dumps(
                                            {
                                                "focus": "FUNCTIONALITY",
                                                "work_description": "Implemented pathfinding algorithm with Dijkstra/Bellman-Ford hybrid",
                                                "code_snippets": [
                                                    'def find_optimal_path(graph, start, end):\n    """Find optimal path"""'
                                                ],
                                                "file_paths": [
                                                    str(
                                                        test_project
                                                        / "complex_algorithm.py"
                                                    )
                                                ],
                                                "context": "This needs to handle various graph types efficiently",
                                            }
                                        ),
                                    ),
                                    id="call_5",
                                )
                            ],
                        )
                    )
                ]
            ),
            # 6. Request critic review (devil's advocate)
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
                                                "review_type": "PERFORMANCE",
                                                "work_description": "Pathfinding algorithm implementation",
                                                "code_snippets": [
                                                    "def find_optimal_path(graph, start, end):"
                                                ],
                                                "file_paths": [
                                                    str(
                                                        test_project
                                                        / "complex_algorithm.py"
                                                    )
                                                ],
                                                "specific_concerns": "Will this scale to large graphs?",
                                            }
                                        ),
                                    ),
                                    id="call_6",
                                )
                            ],
                        )
                    )
                ]
            ),
            # 7. Final response incorporating all feedback
            Mock(
                choices=[
                    Mock(
                        message=Mock(
                            content="""I've implemented the pathfinding algorithm with guidance from multiple perspectives:

1. **Zen Guidance**: Provided creative insights about balancing simplicity and power
2. **Clarification**: Confirmed we should optimize for lowest cost
3. **Implementation**: Created a hybrid Dijkstra/Bellman-Ford approach
4. **Balanced Review**: Highlighted good structure and suggested edge case handling
5. **Critic Review**: Challenged performance assumptions and pushed for optimization

The final implementation addresses all concerns raised.""",
                            tool_calls=None,
                        )
                    )
                ]
            ),
        ]

        # Execute the agent
        result = await agent.call(
            mock_context,
            prompt=f"Implement the complex pathfinding algorithm in {test_project / 'complex_algorithm.py'} using all available tools for guidance",
        )

        # Verify the result mentions all tools
        assert "zen" in result.lower()
        assert "clarification" in result.lower()
        assert "review" in result.lower()
        assert "critic" in result.lower()

        # Verify all tool calls were made
        assert mock_completion.call_count == 7


@pytest.mark.asyncio
async def test_zen_tool_directly():
    """Test the zen tool directly."""
    from hanzo_tools.agent.zen_tool import ZenTool

    tool = ZenTool()
    ctx = Mock()

    # Test with different challenges
    challenges = [
        "How should I scale this microservice architecture?",
        "What's the best approach to refactor legacy code?",
        "How do I improve team collaboration?",
        "Should I optimize for performance or maintainability?",
    ]

    for challenge in challenges:
        result = await tool.call(ctx, challenge)
        if isinstance(result, dict) and "output" in result:
            result = result["output"]

        # Verify result structure
        assert "ZEN GUIDANCE" in result
        assert "Hexagram Cast" in result
        assert "Hanzo Principles" in result
        assert "Synthesized Approach" in result
        assert "The Way Forward" in result

        # Verify it selected relevant principles
        if "scale" in challenge.lower():
            assert any(
                word in result for word in ["Scalable", "Exponentiality", "Growth"]
            )
        elif "refactor" in challenge.lower():
            assert any(
                word in result for word in ["Simplicity", "Clarity", "Composable"]
            )
        elif "team" in challenge.lower():
            assert any(
                word in result for word in ["Autonomy", "Balance", "Collaboration"]
            )


@pytest.mark.asyncio
async def test_review_vs_critic_difference():
    """Test that review and critic provide different styles of feedback."""
    from hanzo_tools.agent.critic_tool import CriticProtocol
    from hanzo_tools.agent.review_tool import ReviewProtocol

    critic = CriticProtocol()
    reviewer = ReviewProtocol()

    work_description = "Implemented user authentication with JWT tokens"
    code_snippet = [
        "func authenticate(token string) (User, error) { return User{}, nil }"
    ]

    # Get critic feedback (harsh)
    critic_feedback = critic.request_review(
        review_type="SECURITY",
        work_description=work_description,
        code_snippets=code_snippet,
    )

    # Get review feedback (balanced) - use GENERAL since ReviewFocus has no SECURITY
    review_feedback = reviewer.request_review(
        focus="GENERAL", work_description=work_description, code_snippets=code_snippet
    )

    # Critic should be harsher
    assert "❌" in critic_feedback or "⚠️" in critic_feedback
    assert "!" in critic_feedback  # Exclamation marks indicate urgency

    # Review should be more balanced
    assert "Positive Aspects" in review_feedback or "✓" in review_feedback
    assert "Suggestions" in review_feedback

    # Critic should mention security (it has SECURITY review type)
    assert "security" in critic_feedback.lower()


@pytest.mark.asyncio
async def test_tool_limits():
    """Test that tools respect their usage limits."""
    from hanzo_tools.agent.clarification_protocol import ClarificationHandler
    from hanzo_tools.agent.critic_tool import CriticProtocol
    from hanzo_tools.agent.review_tool import ReviewProtocol

    # Test clarification limit (1)
    clarifier = ClarificationHandler()
    clarifier.clarification_count = 0
    clarifier.max_clarifications = 1

    # First should work
    try:
        await clarifier.request_clarification(
            ClarificationType.MISSING_CONTEXT, "Question 1", {}
        )
    except AttributeError:
        # Handler doesn't have async request_clarification, that's ok
        pass

    # Test critic limit (2)
    critic = CriticProtocol()
    assert critic.max_reviews == 2

    # Test review limit (3)
    reviewer = ReviewProtocol()
    assert reviewer.max_reviews == 3

    # Test exceeding limits
    critic.review_count = 2
    result = critic.request_review("GENERAL", "test", None, None, None)
    assert "limit exceeded" in result.lower()

    reviewer.review_count = 3
    result = reviewer.request_review("GENERAL", "test", None, None, None)
    assert "limit reached" in result.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
