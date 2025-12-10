# Copyright 2025 Zoo Labs Foundation Inc. and the Gym team.
#
# Semantic Extractor for Training-Free GRPO
# Based on Tencent youtu-agent: https://arxiv.org/abs/2510.08191v1
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Trajectory:
    """Single rollout trajectory.

    Attributes:
        query: Input query/problem statement
        output: Model-generated output/response
        reward: Numerical reward score (e.g., 0 for wrong, 1 for correct)
        groundtruth: Optional ground truth answer for supervised learning
        summary: Optional LLM-generated step-by-step summary
    """

    query: str
    output: str
    reward: float
    groundtruth: Optional[str] = None
    summary: Optional[str] = None


class SemanticExtractor:
    """Extracts semantic advantages from groups of trajectories.

    Implements the 3-stage LLM process from Training-Free GRPO paper:
    1. Trajectory Summarization (Figure 11): Analyze each rollout step-by-step
    2. Group Advantage Extraction (Figure 12): Compare G trajectories to identify patterns
    3. Batch Consolidation (Figure 13): Merge/modify/delete experiences across batch

    This replaces numerical advantages with natural language experiences,
    enabling learning without parameter updates.
    """

    def __init__(self, llm_client: Any, max_operations: int = 3):
        """Initialize semantic extractor.

        Args:
            llm_client: LLM client with .chat() method (e.g., OpenAI, DeepSeek)
            max_operations: Max operations per group critique (default: 3)
        """
        self.llm = llm_client
        self.max_operations = max_operations

    # =========================================================================
    # STAGE 1: Trajectory Summarization (Figure 11)
    # =========================================================================

    def summarize_trajectory(self, trajectory: Trajectory, use_groundtruth: bool = True) -> str:
        """Summarize a single trajectory step-by-step.

        This stage analyzes what happened in each step of the trajectory,
        identifies which experiences were used, and highlights any errors
        or detours that occurred.

        Args:
            trajectory: Trajectory to summarize
            use_groundtruth: Whether to include ground truth in prompt

        Returns:
            summary: Step-by-step analysis of the trajectory
        """
        # Determine evaluation status
        evaluation = (
            "This trajectory delivers **correct** answer"
            if trajectory.reward > 0
            else "This trajectory delivers **wrong** answer"
        )

        # Include groundtruth if available and requested
        groundtruth_section = (
            f"\n<groundtruth>{trajectory.groundtruth}</groundtruth>"
            if use_groundtruth and trajectory.groundtruth
            else ""
        )

        prompt = f"""An agent system may be provided with some experiences, and then it produces the following trajectory to solve the given problem. Please summarize the trajectory step-by-step:

1. For each step, describe what action is being taken, and which experience has been used in this step.
2. Given the grading of this rollout and the correct answer, identify and explain any steps that represent detours, errors, or backtracking, highlighting why they might have occurred and what their impact was on the trajectory's progress.
3. Maintain all the core outcome of each step, even if it was part of a flawed process.

<trajectory>
{trajectory.output}
</trajectory>

<evaluation>
{evaluation}
</evaluation>{groundtruth_section}

Only return the trajectory summary of each step, e.g.,
1. what happened in the first step and the core outcomes
2. what happened in the second step and the core outcomes
3. ..."""

        response = self.llm.chat(prompt)
        return response

    # =========================================================================
    # STAGE 2: Group Advantage Extraction (Figure 12)
    # =========================================================================

    def extract_group_advantage(
        self, trajectories: List[Trajectory], experiences: str, use_groundtruth: bool = True
    ) -> List[Dict]:
        """Extract semantic advantage from a group of trajectories.

        This stage compares multiple trajectories (both correct and incorrect)
        to identify patterns, extract insights, and propose updates to the
        experience library.

        Args:
            trajectories: List of G trajectories for the same query
            experiences: Formatted experience library string
            use_groundtruth: Whether to include ground truth in prompt

        Returns:
            operations: List of operations to apply to experience library
                Example: [
                    {"option": "add", "experience": "When solving..."},
                    {"option": "modify", "experience": "...", "modified_from": "G17"}
                ]
        """
        # Check if group has variation (std > 0)
        rewards = [t.reward for t in trajectories]
        if len(set(rewards)) <= 1:
            return []  # Skip homogeneous groups

        # Format trajectories with summaries
        formatted_trajectories = []
        for i, traj in enumerate(trajectories):
            status = "correct" if traj.reward > 0 else "wrong"
            content = traj.summary or traj.output
            formatted_trajectories.append(f"Attempt {i + 1} (Answer {status}):\n{content}")

        trajectories_text = "\n\n".join(formatted_trajectories)

        # Include groundtruth if available
        groundtruth_section = (
            f"\n<groundtruth>{trajectories[0].groundtruth}</groundtruth>"
            if use_groundtruth and trajectories[0].groundtruth
            else ""
        )

        prompt = f"""An agent system is provided with a set of experiences and has tried to solve the problem multiple times with both successful and wrong solutions. Review these problem-solving attempt and extract generalizable experiences. Follow these steps:

1. Trajectory Analysis:
   - For successful steps: Identify key correct decisions and insights
   - For errors: Pinpoint where and why the reasoning went wrong
   - Note any important patterns or strategies used/missed
   - Review why some trajectories fail? Is there any existing experiences are missed, or experiences do not provide enough guidance?

2. Update Existing Experiences
   - Some trajectories may be correct and others may be wrong, you should ensure there are experiences can help to run correctly
   - You have three options: [modify, add, delete]
      * modify: You can modify current experiences to make it helpful
      * add: You can introduce new experiences to improve future performance
      * delete: You can delete existing experiences
   - You can update at most {self.max_operations} clear, generalizable lessons for this case
   - Before updating each experience, you need to:
      * Specify when it would be most relevant
      * List key problem features that make this experience applicable
      * Identify similar problem patterns where this advice applies

3. Requirements for each experience that is modified or added.
   - Begin with general background with several words in the experience
   - Focus on strategic thinking patterns, not specific calculations
   - Emphasize decision points that could apply to similar problems

Please provide reasoning in details under the guidance of the above 3 steps. After the step-by-step reasoning, you will finish by returning in this JSON format as follows:

```json
[
    {{
        "option": "modify",
        "experience": "the modified experience",
        "modified_from": "G17"
    }},
    {{
        "option": "add",
        "experience": "the added experience"
    }},
    {{
        "option": "delete",
        "delete_id": "G5"
    }}
]
```

Note that your updated experiences may not need to cover all the options.

<problem>
{trajectories[0].query}
</problem>

<trajectories>
{trajectories_text}
</trajectories>{groundtruth_section}

<experience>
{experiences}
</experience>"""

        response = self.llm.chat(prompt)

        # Parse JSON operations
        return self._parse_json_operations(response, max_ops=self.max_operations)

    # =========================================================================
    # STAGE 3: Batch Consolidation (Figure 13)
    # =========================================================================

    def consolidate_batch(self, all_group_operations: List[List[Dict]], experiences: str) -> List[Dict]:
        """Consolidate all group advantages into final experience updates.

        This stage merges operations from all groups in the batch, ensuring:
        - Experiences are ≤32 words
        - No redundancy between experiences
        - Strategic focus (not specific calculations)
        - Generalizable insights

        Args:
            all_group_operations: List of operations from each group
            experiences: Current formatted experience library

        Returns:
            final_operations: Consolidated list of operations to apply
        """
        # Flatten all operations
        all_ops = []
        for group_ops in all_group_operations:
            all_ops.extend(group_ops)

        if not all_ops:
            return []

        prompt = f"""An agent system is provided with a set of experiences and has tried to solve the problem multiple times. From the reflections, some suggestions on the existing experiences have been posed. Your task is to collect and think for the final experience revision plan. Each final experience must satisfy the following requirements:

1. It must be clear, generalizable lessons for this case, with no more than 32 words
2. Begin with general background with several words in the experience
3. Focus on strategic thinking patterns, not specific calculations
4. Emphasize decision points that could apply to similar problems
5. Avoid repeating saying similar experience in multiple different experiences

<experience>
{experiences}
</experience>

<suggested_updates>
{json.dumps(all_ops, indent=2)}
</suggested_updates>

Please provide reasoning in each of the suggestions, and think for how to update existing experiences. You have three update options: [modify, merge, delete]

- modify: You can modify current experiences to make it helpful
- merge: You can merge some similar experiences into a more general forms to reduce duplication
- delete: You can delete an experience

After generating the step-by-step reasoning, you need to give the final experience revision details by returning in this JSON format as follows:

```json
[
    {{
        "option": "modify",
        "experience": "the modified experience",
        "modified_from": "G17"
    }},
    {{
        "option": "merge",
        "experience": "the merged experience",
        "merged_from": ["C1", "C3", "S4"]
    }},
    {{
        "option": "delete",
        "delete_id": "G5"
    }}
]
```"""

        response = self.llm.chat(prompt)

        # Parse JSON operations
        return self._parse_json_operations(response)

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _parse_json_operations(self, response: str, max_ops: Optional[int] = None) -> List[Dict]:
        """Parse JSON operations from LLM response.

        Extracts JSON block from markdown code fence and validates format.

        Args:
            response: LLM response text
            max_ops: Optional limit on number of operations

        Returns:
            operations: List of operation dictionaries
        """
        # Extract JSON block from markdown code fence
        json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)

        if json_match:
            try:
                operations = json.loads(json_match.group(1))
                if max_ops:
                    return operations[:max_ops]
                return operations
            except json.JSONDecodeError as e:
                # Log error and return empty list
                print(f"JSON parse error: {e}")
                return []

        # Also try to find plain JSON arrays (without code fence)
        try:
            # Look for array pattern
            array_match = re.search(r"\[\s*\{.*?\}\s*\]", response, re.DOTALL)
            if array_match:
                operations = json.loads(array_match.group(0))
                if max_ops:
                    return operations[:max_ops]
                return operations
        except json.JSONDecodeError:
            pass

        return []


class LLMClient:
    """Simple wrapper for LLM API clients.

    Provides a unified .chat() interface for various LLM providers.
    Supports OpenAI-compatible APIs (OpenAI, DeepSeek, etc.).
    """

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com/v1", model: str = "deepseek-chat"):
        """Initialize LLM client.

        Args:
            api_key: API key for the LLM service
            base_url: Base URL for the API endpoint
            model: Model name to use (default: deepseek-chat)
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("OpenAI package not found. Install with: pip install openai")

        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def chat(self, prompt: str, temperature: float = 0.7, max_tokens: int = 4096) -> str:
        """Send chat request to LLM.

        Args:
            prompt: User prompt
            temperature: Sampling temperature (default: 0.7)
            max_tokens: Max tokens to generate (default: 4096)

        Returns:
            response: LLM response text
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content
