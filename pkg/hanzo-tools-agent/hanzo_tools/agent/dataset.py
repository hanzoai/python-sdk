"""Dataset collection for agent telemetry.

Captures prompts, responses, and full telemetry data for training dataset annotation.

Usage:
    from hanzo_tools.agent.dataset import DatasetCollector

    collector = DatasetCollector("my_dataset.jsonl")

    # Collect single sample
    await collector.collect("claude", "Explain quicksort")

    # Collect batch
    await collector.collect_batch([
        ("claude", "What is recursion?"),
        ("gemini", "Explain binary search"),
    ])

    # Save dataset
    collector.save()
"""

import json
import time
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple, Any, Dict
from dataclasses import dataclass, asdict, field

from hanzo_async import append_file, write_file

from .agent_tool import AgentTool, Result, Telemetry


@dataclass
class DatasetSample:
    """Single dataset sample with full telemetry."""
    # Core fields
    id: str
    timestamp: str
    agent: str
    prompt: str
    response: str

    # Status
    ok: bool
    error: Optional[str] = None

    # Timing
    latency_ms: int = 0

    # Token usage
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0

    # Cost
    cost_usd: float = 0.0

    # Model info
    model: Optional[str] = None
    service_name: Optional[str] = None
    service_version: Optional[str] = None

    # Full telemetry for annotation
    telemetry_raw: Optional[Dict[str, Any]] = None

    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class DatasetCollector:
    """Collect dataset samples from agent runs."""

    def __init__(self, output_path: str = "dataset.jsonl", auto_save: bool = True):
        """Initialize collector.

        Args:
            output_path: Path to output JSONL file
            auto_save: Auto-save after each sample
        """
        self.output_path = Path(output_path)
        self.auto_save = auto_save
        self.samples: List[DatasetSample] = []
        self.tool = AgentTool()
        self._sample_count = 0

        # Load existing samples if file exists
        if self.output_path.exists():
            self._load_existing()

    def _load_existing(self):
        """Load existing samples from file."""
        try:
            with open(self.output_path, "r") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        self.samples.append(DatasetSample(**data))
            self._sample_count = len(self.samples)
            print(f"Loaded {len(self.samples)} existing samples from {self.output_path}")
        except Exception as e:
            print(f"Could not load existing samples: {e}")

    def _generate_id(self) -> str:
        """Generate unique sample ID."""
        self._sample_count += 1
        return f"sample_{self._sample_count:06d}_{int(time.time())}"

    async def collect(
        self,
        agent: str,
        prompt: str,
        timeout: int = 60,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DatasetSample:
        """Collect a single dataset sample.

        Args:
            agent: Agent to use (claude, gemini, etc.)
            prompt: Prompt to send
            timeout: Timeout in seconds
            tags: Optional tags for categorization
            metadata: Optional additional metadata

        Returns:
            DatasetSample with full telemetry
        """
        result = await self.tool._exec(agent, prompt, None, timeout)

        sample = DatasetSample(
            id=self._generate_id(),
            timestamp=datetime.utcnow().isoformat() + "Z",
            agent=result.agent,
            prompt=prompt,
            response=result.output,
            ok=result.ok,
            error=result.error,
            latency_ms=result.ms,
            tags=tags or [],
            metadata=metadata or {},
        )

        # Add telemetry if available
        if result.telemetry:
            t = result.telemetry
            sample.input_tokens = t.input_tokens
            sample.output_tokens = t.output_tokens
            sample.cache_read_tokens = t.cache_read_input_tokens
            sample.cache_creation_tokens = t.cache_creation_input_tokens
            sample.cost_usd = t.cost_usd
            sample.model = t.model
            sample.service_name = t.service_name
            sample.service_version = t.service_version
            sample.telemetry_raw = t.raw

        self.samples.append(sample)

        if self.auto_save:
            await self._append_sample_async(sample)

        return sample

    async def collect_batch(
        self,
        prompts: List[Tuple[str, str]],
        timeout: int = 60,
        max_concurrent: int = 5,
        tags: Optional[List[str]] = None,
    ) -> List[DatasetSample]:
        """Collect batch of samples with concurrency control.

        Args:
            prompts: List of (agent, prompt) tuples
            timeout: Timeout per sample
            max_concurrent: Max concurrent requests
            tags: Tags to apply to all samples

        Returns:
            List of DatasetSamples
        """
        sem = asyncio.Semaphore(max_concurrent)

        async def collect_one(agent: str, prompt: str, idx: int) -> DatasetSample:
            async with sem:
                sample = await self.collect(
                    agent, prompt, timeout,
                    tags=tags,
                    metadata={"batch_index": idx}
                )
                print(f"[{idx+1}/{len(prompts)}] {agent}: {len(sample.response)} chars, ${sample.cost_usd:.4f}")
                return sample

        tasks = [
            collect_one(agent, prompt, i)
            for i, (agent, prompt) in enumerate(prompts)
        ]

        return await asyncio.gather(*tasks)

    async def _append_sample_async(self, sample: DatasetSample):
        """Append single sample to file (non-blocking)."""
        await append_file(self.output_path, json.dumps(asdict(sample)) + "\n")

    def _append_sample(self, sample: DatasetSample):
        """Append single sample to file (sync version for compatibility)."""
        with open(self.output_path, "a") as f:
            f.write(json.dumps(asdict(sample)) + "\n")

    async def save_async(self):
        """Save all samples to file asynchronously (overwrites)."""
        content = "\n".join(json.dumps(asdict(sample)) for sample in self.samples)
        if content:
            content += "\n"
        await write_file(self.output_path, content)
        print(f"Saved {len(self.samples)} samples to {self.output_path}")

    def save(self):
        """Save all samples to file (sync version, overwrites)."""
        with open(self.output_path, "w") as f:
            for sample in self.samples:
                f.write(json.dumps(asdict(sample)) + "\n")
        print(f"Saved {len(self.samples)} samples to {self.output_path}")

    def stats(self) -> Dict[str, Any]:
        """Get dataset statistics."""
        if not self.samples:
            return {"count": 0}

        total_cost = sum(s.cost_usd for s in self.samples)
        total_input = sum(s.input_tokens for s in self.samples)
        total_output = sum(s.output_tokens for s in self.samples)
        total_cache = sum(s.cache_read_tokens for s in self.samples)
        avg_latency = sum(s.latency_ms for s in self.samples) / len(self.samples)

        agents = {}
        models = {}
        for s in self.samples:
            agents[s.agent] = agents.get(s.agent, 0) + 1
            if s.model:
                models[s.model] = models.get(s.model, 0) + 1

        return {
            "count": len(self.samples),
            "total_cost_usd": total_cost,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_cache_read_tokens": total_cache,
            "avg_latency_ms": avg_latency,
            "success_rate": sum(1 for s in self.samples if s.ok) / len(self.samples),
            "agents": agents,
            "models": models,
        }


async def build_dataset(
    prompts: List[str],
    agents: List[str] = ["claude"],
    output: str = "dataset.jsonl",
    max_concurrent: int = 3,
    timeout: int = 60,
) -> DatasetCollector:
    """Build a dataset from prompts.

    Args:
        prompts: List of prompts to collect
        agents: Agents to use (will cycle through)
        output: Output JSONL path
        max_concurrent: Max concurrent requests
        timeout: Timeout per request

    Returns:
        DatasetCollector with collected samples
    """
    collector = DatasetCollector(output, auto_save=True)

    # Create prompt-agent pairs, cycling through agents
    pairs = [
        (agents[i % len(agents)], prompt)
        for i, prompt in enumerate(prompts)
    ]

    print(f"Collecting {len(prompts)} samples across {len(agents)} agents...")
    start = time.time()

    await collector.collect_batch(pairs, timeout=timeout, max_concurrent=max_concurrent)

    elapsed = time.time() - start
    stats = collector.stats()

    print(f"\n=== Dataset Stats ===")
    print(f"Samples: {stats['count']}")
    print(f"Total cost: ${stats['total_cost_usd']:.4f}")
    print(f"Total tokens: {stats['total_input_tokens']}→{stats['total_output_tokens']}")
    print(f"Cache reads: {stats['total_cache_read_tokens']}")
    print(f"Avg latency: {stats['avg_latency_ms']:.0f}ms")
    print(f"Success rate: {stats['success_rate']*100:.1f}%")
    print(f"Time: {elapsed:.1f}s")
    print(f"Agents: {stats['agents']}")
    print(f"Models: {stats['models']}")
    print(f"\nSaved to: {output}")

    return collector


# Export
__all__ = ["DatasetCollector", "DatasetSample", "build_dataset"]
