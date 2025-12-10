"""Training-Free GRPO implementation for Hanzo AI.

This module provides Training-Free Group Relative Policy Optimization (GRPO)
from Tencent's youtu-agent paper (arXiv:2510.08191v1).

Training-Free GRPO improves LLM performance via context expansion rather than
parameter updates, using semantic advantages extracted via LLM introspection.

Key components:
- ExperienceManager: Manages the experience library (E) with CRUD operations
- SemanticExtractor: Implements 3-stage LLM process for semantic advantage extraction
- Trajectory: Data class for rollout trajectories
- LLMClient: Wrapper for LLM API clients (DeepSeek, OpenAI)
- APIModelAdapter: Use API-hosted models as target model
- DeepSeekAdapter: Convenience wrapper for DeepSeek models
- OpenAIAdapter: Convenience wrapper for OpenAI models

Example usage:
    ```python
    from hanzoai.grpo import DeepSeekAdapter, ExperienceManager, SemanticExtractor, LLMClient

    # Initialize components
    target_model = DeepSeekAdapter(api_key="your-api-key")
    semantic_llm = LLMClient(api_key="your-api-key", base_url="https://api.deepseek.com/v1")
    exp_manager = ExperienceManager(checkpoint_path="./experiences/experiences.json")
    extractor = SemanticExtractor(semantic_llm, max_operations=5)

    # Generate rollouts with experience injection
    query = "Solve: 2x + 5 = 13"
    group_size = 5
    trajectories = []

    for i in range(group_size):
        experiences_text = exp_manager.format_for_prompt()
        response = target_model.generate_with_experiences(
            query=query, experiences=experiences_text, temperature=0.7 + (i * 0.1)
        )
        # Evaluate and create trajectory
        # trajectories.append(Trajectory(query=query, output=response, reward=score))

    # Extract semantic advantages and update experience library
    group_operations = extractor.extract_group_advantage(trajectories, exp_manager.format_for_prompt())
    exp_manager.apply_operations(group_operations)
    exp_manager.save()
    ```

For more details, see the Training-Free GRPO paper:
https://arxiv.org/abs/2510.08191
"""

# Basic implementations
from .api_model_adapter import (
    OpenAIAdapter,
    APIModelConfig,
    APIModelAdapter,
    DeepSeekAdapter,
)
from .experience_manager import ExperienceManager
from .semantic_extractor import LLMClient, Trajectory, SemanticExtractor
from .enhanced_api_model_adapter import (
    EnhancedOpenAIAdapter,
    EnhancedAPIModelConfig,
    EnhancedAPIModelAdapter,
    EnhancedDeepSeekAdapter,
)

# Enhanced implementations with full Tencent feature parity
from .enhanced_semantic_extractor import (
    Trajectory as EnhancedTrajectory,
    EnhancedLLMClient,
    EnhancedSemanticExtractor,
    rollout_with_timeout,
)

__all__ = [
    # Basic
    "ExperienceManager",
    "SemanticExtractor",
    "Trajectory",
    "LLMClient",
    "APIModelAdapter",
    "APIModelConfig",
    "DeepSeekAdapter",
    "OpenAIAdapter",
    # Enhanced (recommended for production use)
    "EnhancedSemanticExtractor",
    "EnhancedLLMClient",
    "EnhancedTrajectory",
    "EnhancedAPIModelAdapter",
    "EnhancedAPIModelConfig",
    "EnhancedDeepSeekAdapter",
    "EnhancedOpenAIAdapter",
    "rollout_with_timeout",
]
