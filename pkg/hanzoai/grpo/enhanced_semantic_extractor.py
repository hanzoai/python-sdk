# Copyright 2025 Zoo Labs Foundation Inc. and the Gym team.
#
# Enhanced Semantic Extractor for Training-Free GRPO with Full Feature Parity
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

import asyncio
import copy
import json
import os
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    # Fallback progress indicator
    class tqdm:
        def __init__(self, iterable=None, total=None, desc=None, **kwargs):
            self.iterable = iterable
            self.total = total
            self.desc = desc
            self.n = 0
        
        def __iter__(self):
            return iter(self.iterable) if self.iterable else iter([])
        
        def update(self, n=1):
            self.n += n
            if self.desc and self.total:
                print(f"{self.desc}: {self.n}/{self.total}", end="\r")


@dataclass
class Trajectory:
    """Single rollout trajectory with full feature support.

    Attributes:
        query: Input query/problem statement
        output: Model-generated output/response
        reward: Numerical reward score (e.g., 0 for wrong, 1 for correct)
        groundtruth: Optional ground truth answer for supervised learning
        summary: Optional LLM-generated step-by-step summary
        reasoning: Optional reasoning content (for o1 models)
        retry_count: Number of retries attempted
        task_time: Time taken for this trajectory in seconds
    """
    query: str
    output: str
    reward: float
    groundtruth: Optional[str] = None
    summary: Optional[str] = None
    reasoning: Optional[str] = None
    retry_count: int = 0
    task_time: Optional[float] = None


class EnhancedLLMClient:
    """Enhanced LLM client with retry logic, reasoning support, and env config.
    
    Features:
    - Automatic retry with exponential backoff
    - Reasoning content support (for OpenAI o1 models)
    - Environment variable configuration
    - Max retries and timeout control
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: Optional[float] = None,
    ):
        """Initialize LLM client with env var fallback.
        
        Environment variables (if parameters not provided):
        - HANZO_GRPO_API_KEY or DEEPSEEK_API_KEY
        - HANZO_GRPO_BASE_URL
        - HANZO_GRPO_MODEL
        """
        from openai import OpenAI
        
        # Use env vars as fallback
        self.api_key = api_key or os.getenv("HANZO_GRPO_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = base_url or os.getenv("HANZO_GRPO_BASE_URL", "https://api.deepseek.com/v1")
        self.model = model or os.getenv("HANZO_GRPO_MODEL", "deepseek-chat")
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        
        if not self.api_key:
            raise ValueError("API key required. Set HANZO_GRPO_API_KEY or pass api_key parameter.")
        
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=timeout)
    
    def chat(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        return_reasoning: bool = False,
    ) -> str | tuple[str, Optional[str]]:
        """Call LLM with automatic retry logic.
        
        Args:
            prompt: User prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            return_reasoning: If True, return (response, reasoning) tuple
        
        Returns:
            Response string, or (response, reasoning) tuple if return_reasoning=True
        """
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                
                response_text = response.choices[0].message.content.strip()
                
                if return_reasoning:
                    # For OpenAI o1 models or models with reasoning_content
                    reasoning = getattr(response.choices[0].message, "reasoning_content", None)
                    return response_text, reasoning
                
                return response_text
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    print(f"LLM call failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                    print(f"Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    raise Exception(f"LLM call failed after {self.max_retries} attempts: {e}")


class EnhancedSemanticExtractor:
    """Enhanced semantic extractor with full Tencent feature parity.
    
    New Features:
    - File caching for intermediate results (single_rollout_summary.json, etc.)
    - Parallel processing with ThreadPoolExecutor
    - Automatic retry logic with exponential backoff
    - Partial correct filtering (0 < avg_score < 1)
    - Progress tracking with tqdm
    - Async support for rollouts with timeout
    - Reasoning content support for o1 models
    - Environment-based configuration
    """
    
    def __init__(
        self,
        llm_client: EnhancedLLMClient,
        max_operations: int = 3,
        max_workers: int = 16,
        cache_dir: Optional[str] = None,
        enable_caching: bool = True,
        enable_parallel: bool = True,
        filter_partial_correct: bool = True,
    ):
        """Initialize enhanced semantic extractor.
        
        Args:
            llm_client: Enhanced LLM client with retry logic
            max_operations: Max operations per group critique
            max_workers: Max parallel workers for ThreadPoolExecutor
            cache_dir: Directory for caching intermediate results
            enable_caching: Whether to enable file caching
            enable_parallel: Whether to enable parallel processing
            filter_partial_correct: Only process groups with 0 < avg_score < 1
        """
        self.llm = llm_client
        self.max_operations = max_operations
        self.max_workers = max_workers
        self.cache_dir = cache_dir
        self.enable_caching = enable_caching
        self.enable_parallel = enable_parallel
        self.filter_partial_correct = filter_partial_correct
    
    def _get_cache_path(self, filename: str) -> Optional[Path]:
        """Get cache file path if caching enabled."""
        if not self.enable_caching or not self.cache_dir:
            return None
        return Path(self.cache_dir) / filename
    
    def _load_cache(self, filename: str) -> Optional[Any]:
        """Load from cache if exists."""
        cache_path = self._get_cache_path(filename)
        if cache_path and cache_path.exists():
            with open(cache_path) as f:
                data = json.load(f)
                if len(data) > 0:
                    print(f"Loaded from cache: {cache_path}")
                    return data
        return None
    
    def _save_cache(self, filename: str, data: Any):
        """Save to cache."""
        cache_path = self._get_cache_path(filename)
        if cache_path:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, "w") as f:
                json.dump(data, f, indent=2)
            print(f"Saved to cache: {cache_path}")
    
    def summarize_trajectories(
        self,
        trajectories: List[Trajectory],
        use_groundtruth: bool = True,
    ) -> Dict[str, List[Trajectory]]:
        """Stage 1: Summarize trajectories step-by-step with caching and parallel processing.
        
        Args:
            trajectories: List of trajectories to summarize
            use_groundtruth: Whether to use ground truth in summarization
        
        Returns:
            Dict mapping query to list of summarized trajectories
        """
        # Try to load from cache
        cached = self._load_cache("single_rollout_summary.json")
        if cached:
            # Convert back to Trajectory objects
            result = defaultdict(list)
            for query, trajs in cached.items():
                result[query] = [Trajectory(**t) for t in trajs]
            return result
        
        # Group by query
        query_to_trajectories = defaultdict(list)
        for traj in trajectories:
            query_to_trajectories[traj.query].append(traj)
        
        # Filter to partial correct groups if enabled
        all_trajectories_to_process = []
        for trajs in query_to_trajectories.values():
            if self.filter_partial_correct and use_groundtruth:
                scores = [t.reward for t in trajs]
                avg_score = sum(scores) / len(scores)
                if 0 < avg_score < 1:  # Partial correct
                    all_trajectories_to_process.extend(trajs)
            else:
                all_trajectories_to_process.extend(trajs)
        
        def process_trajectory(traj: Trajectory) -> Optional[Trajectory]:
            """Process single trajectory with LLM."""
            try:
                if use_groundtruth and traj.groundtruth:
                    prompt = f"""An agent system may be provided with some experiences, and then it produces the following trajectory to solve the given problem. Please summarize the trajectory step-by-step:

1. For each step, describe what action is being taken, and which experience has been used in this step.
2. Given the grading of this rollout and the correct answer, identify and explain any steps that represent detours, errors, or backtracking...
3. Maintain all the core outcome of each step, even if it was part of a flawed process.

<trajectory>
{traj.output}
</trajectory>

<evaluation>
This trajectory delivers **{"correct" if traj.reward > 0 else "wrong"}** answer
</evaluation>

<groundtruth>{traj.groundtruth}</groundtruth>

Only return the trajectory summary of each step, e.g.,
1. what happened in the first step and the core outcomes
2. what happened in the second step and the core outcomes
3. ..."""
                else:
                    prompt = f"""An agent system produces the following trajectory. Please summarize the trajectory step-by-step:

<trajectory>
{traj.output}
</trajectory>

Only return the trajectory summary of each step."""
                
                summary = self.llm.chat(prompt)
                result = copy.copy(traj)
                result.summary = summary
                return result
            except Exception as e:
                print(f"Warning: Failed to summarize trajectory: {e}")
                return None
        
        # Parallel or sequential processing
        results = defaultdict(list)
        
        if self.enable_parallel and self.max_workers > 1:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_traj = {
                    executor.submit(process_trajectory, traj): traj
                    for traj in all_trajectories_to_process
                }
                
                iterator = as_completed(future_to_traj)
                if TQDM_AVAILABLE:
                    iterator = tqdm(iterator, total=len(all_trajectories_to_process), desc="Summarizing trajectories")
                
                for future in iterator:
                    result = future.result()
                    if result:
                        results[result.query].append(result)
        else:
            # Sequential processing with progress bar
            iterator = all_trajectories_to_process
            if TQDM_AVAILABLE:
                iterator = tqdm(iterator, desc="Summarizing trajectories")
            
            for traj in iterator:
                result = process_trajectory(traj)
                if result:
                    results[result.query].append(result)
        
        # Save to cache
        cache_data = {
            query: [{"query": t.query, "output": t.output, "reward": t.reward, 
                    "groundtruth": t.groundtruth, "summary": t.summary} for t in trajs]
            for query, trajs in results.items()
        }
        self._save_cache("single_rollout_summary.json", cache_data)
        
        return results
    
    def extract_group_advantages(
        self,
        query_to_summarized_trajectories: Dict[str, List[Trajectory]],
        experiences: str,
        use_groundtruth: bool = True,
    ) -> List[Dict]:
        """Stage 2: Extract group advantages from summarized trajectories.
        
        Args:
            query_to_summarized_trajectories: Dict of query to summarized trajectories
            experiences: Formatted experiences string
            use_groundtruth: Whether to use ground truth
        
        Returns:
            List of critique dictionaries with operations
        """
        # Try to load from cache
        cached = self._load_cache("single_query_critique.json")
        if cached:
            return cached
        
        # Filter to partial correct groups if enabled
        all_groups = []
        for trajs in query_to_summarized_trajectories.values():
            if self.filter_partial_correct and use_groundtruth:
                scores = [t.reward for t in trajs]
                avg_score = sum(scores) / len(scores)
                if 0 < avg_score < 1:
                    all_groups.append(trajs)
            else:
                all_groups.append(trajs)
        
        def process_group(trajs: List[Trajectory]) -> Optional[Dict]:
            """Process single group of trajectories."""
            try:
                query = trajs[0].query
                groundtruth = trajs[0].groundtruth if use_groundtruth else None
                
                formatted_trajs = "\n\n".join([
                    f"Trajectory {i+1} (Answer {'correct' if t.reward > 0 else 'wrong'}):\n{t.summary}"
                    for i, t in enumerate(trajs)
                ])
                
                if use_groundtruth and groundtruth:
                    prompt = f"""Given the problem and several trajectory summaries with grading, generate semantic experiences that could help future rollouts.

Problem: {query}
Correct Answer: {groundtruth}

Current Experiences:
{experiences}

Trajectories:
{formatted_trajs}

Based on comparing these trajectories, generate up to {self.max_operations} operations to update experiences.
Return a JSON array of operations with format:
[{{"option": "add", "experience": "..."}}, {{"option": "modify", "modified_from": "G0", "experience": "..."}}, ...]

Only return the JSON array."""
                else:
                    prompt = f"""Given the problem and several trajectory summaries, generate semantic experiences.

Problem: {query}

Current Experiences:
{experiences}

Trajectories:
{formatted_trajs}

Generate up to {self.max_operations} operations to update experiences.
Return JSON array: [{{"option": "add", "experience": "..."}}, ...]"""
                
                response = self.llm.chat(prompt)
                response_clean = response.split("```json")[-1].split("```")[0].strip()
                operations = json.loads(response_clean)
                
                return {
                    "trajectories": trajs,
                    "critique": response,
                    "operations": operations[:self.max_operations]
                }
            except Exception as e:
                print(f"Warning: Failed to extract group advantage: {e}")
                return None
        
        # Parallel or sequential processing
        results = []
        
        if self.enable_parallel and self.max_workers > 1:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_group = {
                    executor.submit(process_group, trajs): trajs
                    for trajs in all_groups
                }
                
                iterator = as_completed(future_to_group)
                if TQDM_AVAILABLE:
                    iterator = tqdm(iterator, total=len(all_groups), desc="Extracting group advantages")
                
                for future in iterator:
                    result = future.result()
                    if result:
                        results.append(result)
        else:
            iterator = all_groups
            if TQDM_AVAILABLE:
                iterator = tqdm(iterator, desc="Extracting group advantages")
            
            for trajs in iterator:
                result = process_group(trajs)
                if result:
                    results.append(result)
        
        # Save to cache
        self._save_cache("single_query_critique.json", results)
        
        return results
    
    def consolidate_batch(
        self,
        all_group_operations: List[List[Dict]],
        experiences: Dict[str, str],
    ) -> Dict[str, str]:
        """Stage 3: Consolidate all group operations into final experience updates.
        
        Args:
            all_group_operations: List of operation lists from each group
            experiences: Current experience dictionary
        
        Returns:
            Updated experience dictionary
        """
        # Try to load from cache
        cached = self._load_cache("batch_update.json")
        if cached:
            return cached.get("new_experiences", experiences)
        
        print("Batch consolidation")
        
        # Collect all operations
        all_operations = []
        for ops in all_group_operations:
            all_operations.extend(ops)
        
        print(f"- Total operations to process: {len(all_operations)}")
        
        # Split into add and modify operations
        candidate_experiences = copy.deepcopy(experiences)
        to_modify = []
        max_id = 0
        
        for operation in all_operations:
            if operation.get("option") == "modify":
                if operation.get("modified_from") in candidate_experiences:
                    to_modify.append(operation)
            elif operation.get("option") == "add":
                candidate_experiences[f"C{max_id}"] = operation["experience"]
                max_id += 1
        
        print(f"- Added experiences: {max_id}")
        print(f"- Experiences to modify: {len(to_modify)}")
        print(f"- Candidate experiences: {len(candidate_experiences)}")
        
        # Use LLM to create revision plan
        if len(to_modify) > 0:
            prompt = f"""Given candidate experiences and modification requests, create a revision plan.

Candidate Experiences:
{json.dumps(candidate_experiences, indent=2)}

Modification Requests:
{json.dumps(to_modify, indent=2)}

Create a revision plan as JSON array with operations:
- {{"option": "modify", "modified_from": "ID", "experience": "..."}}
- {{"option": "merge", "merged_from": ["ID1", "ID2"], "experience": "..."}}

Return only the JSON array."""
            
            try:
                response = self.llm.chat(prompt)
                response_clean = response.split("```json")[-1].split("```")[0].strip()
                revision_plan = json.loads(response_clean)
            except Exception as e:
                print(f"Warning: Failed to create revision plan: {e}")
                revision_plan = []
        else:
            revision_plan = []
        
        # Apply revision plan
        new_experiences = copy.deepcopy(candidate_experiences)
        for operation in revision_plan:
            try:
                if operation["option"] == "modify":
                    new_experiences[operation["modified_from"]] = operation["experience"]
                elif operation["option"] == "merge":
                    for exp_id in operation["merged_from"]:
                        if exp_id in new_experiences:
                            del new_experiences[exp_id]
                    new_experiences[f"C{max_id}"] = operation["experience"]
                    max_id += 1
            except Exception as e:
                print(f"Error applying operation {operation}: {e}")
        
        print(f"- Final experiences: {len(new_experiences)}")
        
        # Save to cache
        cache_data = {
            "operations": all_operations,
            "revision_plan": revision_plan,
            "new_experiences": new_experiences,
        }
        self._save_cache("batch_update.json", cache_data)
        
        # Reassign IDs
        final_experiences = {f"G{i}": exp for i, exp in enumerate(new_experiences.values())}
        
        return final_experiences


# Async rollout support with timeout
async def rollout_with_timeout(
    generate_func: Callable,
    query: str,
    timeout: float = 3600,
    max_retries: int = 3,
    **kwargs
) -> Optional[str]:
    """Execute rollout with timeout and retry support.
    
    Args:
        generate_func: Function to call for generation (must be async-compatible)
        query: Query/prompt to generate from
        timeout: Timeout in seconds
        max_retries: Maximum retry attempts
        **kwargs: Additional arguments to pass to generate_func
    
    Returns:
        Generated response or None if failed
    """
    for attempt in range(max_retries):
        try:
            # Wrap sync function in async if needed
            if asyncio.iscoroutinefunction(generate_func):
                coro = generate_func(query, **kwargs)
            else:
                coro = asyncio.to_thread(generate_func, query, **kwargs)
            
            result = await asyncio.wait_for(coro, timeout=timeout)
            return result
            
        except asyncio.TimeoutError:
            print(f"Rollout timeout (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            else:
                print(f"Rollout failed after {max_retries} timeout attempts")
                return None
        except Exception as e:
            print(f"Rollout error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
            else:
                print(f"Rollout failed after {max_retries} attempts")
                return None
