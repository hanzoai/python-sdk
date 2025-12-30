# Zen Coder Training Documentation

This document describes the training infrastructure and methodology for the Zen Coder model family.

## Overview

Zen Coder is a code-specialized LLM trained on the **Zen Agentic Dataset** - a curated collection of:
- Git commit history and diffs from 1,452+ repositories
- Claude Code debug sessions (agentic interactions)
- Code review and documentation examples
- Multi-language programming samples

## Dataset Statistics

| Metric | Value |
|--------|-------|
| Total Tokens | ~8.47B |
| Training Samples | 1.44M |
| Validation Samples | 75K |
| Prepared Data Size | 4 GB |
| Source Repositories | 1,452+ |

### Data Sources

1. **Git History** (~12GB)
   - Commit messages and diffs
   - Full source files at each commit
   - Author metadata

2. **Claude Debug Sessions** (~12GB)
   - Real agentic coding interactions
   - Tool usage patterns
   - Multi-turn problem solving

3. **Claude Full Conversations** (~2GB)
   - Extended coding sessions
   - Architecture discussions
   - Code review examples

4. **Additional Sources** (~4GB)
   - Internal development logs
   - Documentation examples
   - Test cases

## Training Configuration

### Base Model
- **Model**: `Qwen/Qwen3-4B-Instruct-2507`
- **Parameters**: 4B
- **Architecture**: Qwen3 transformer

### LoRA Configuration

```yaml
fine_tune_type: lora
num_layers: -1          # ALL layers
batch_size: 1
grad_accumulation: 8    # Effective batch = 8
learning_rate: 1e-5
optimizer: adamw
max_seq_length: 4096
mask_prompt: true       # Train on completions only
grad_checkpoint: true   # Memory optimization
```

### Training Parameters

| Parameter | Value |
|-----------|-------|
| Total Iterations | 50,000 |
| Checkpoint Every | 1,000 iters |
| Eval Every | 500 iters |
| Estimated Time | ~3 days |

## Data Preparation

### Chunking Strategy

Long sequences are chunked to fit within the 4096 token context:

```python
MAX_CHARS_PER_CHUNK = 12000  # ~3K tokens per chunk

def chunk_messages(messages, max_chars):
    """Split long message sequences into manageable chunks."""
    # Split on paragraph boundaries when possible
    # Each chunk gets system prompt prepended
    # Maintains conversation context
```

### Format Conversion

All data is converted to the `messages` format:

```json
{
  "messages": [
    {"role": "system", "content": "You are Zen Coder..."},
    {"role": "user", "content": "Explain this code..."},
    {"role": "assistant", "content": "This code..."}
  ]
}
```

### Supported Input Formats

The pipeline handles multiple source formats:

1. **Messages format** - Direct passthrough
2. **Conversations format** - OpenAI-style with `from`/`value`
3. **Prompt/Completion** - Simple pairs
4. **Git content** - Commits, diffs, files
5. **Debug sessions** - Claude Code format

## Training Infrastructure

### Hardware
- Apple Silicon (M-series)
- MLX framework for Apple GPU acceleration
- 64GB unified memory

### Software Stack
- `mlx-lm` - MLX language model training
- `tiktoken` - Token counting (cl100k_base)
- Custom data preparation pipeline

## Checkpoints

Checkpoints are saved every 1,000 iterations:

```
adapters/
├── 0001000_adapters.safetensors  (63MB)
├── 0002000_adapters.safetensors
├── ...
├── 0050000_adapters.safetensors
└── adapters.safetensors          (latest)
```

## Usage

### Training

```bash
cd /path/to/zen-coder/training

# Start training
python train_full.py

# Resume from checkpoint
python train_full.py --resume

# Check status
python train_full.py --status
```

### Monitoring

```bash
# Watch training progress
tail -f full_training.log

# Check status JSON
cat training_status.json
```

### Inference with Adapter

```python
from mlx_lm import load, generate

model, tokenizer = load(
    "Qwen/Qwen3-4B-Instruct-2507",
    adapter_path="./adapters"
)

response = generate(
    model, tokenizer,
    prompt="Explain this Python code:\n\ndef fibonacci(n):\n    ...",
    max_tokens=500
)
```

## HuggingFace

- **Private dataset**: `zenlm/zen-agentic-dataset`
- **Public card**: `hanzoai/zen-agentic-dataset`
- **Model**: `zenlm/zen-coder-4b-instruct` (after training)

## Best Practices Applied

1. **Train on completions only** (`--mask-prompt`)
   - Loss computed only on assistant responses
   - User/system tokens masked

2. **LoRA on ALL layers** (`--num-layers -1`)
   - Better adaptation than attention-only
   - Moderate rank for regularization

3. **Gradient accumulation**
   - Effective batch size 8 with batch=1
   - Memory efficient

4. **Gradient checkpointing**
   - Reduces memory footprint
   - Enables longer sequences

5. **Data chunking**
   - Samples split to fit context
   - Preserves conversation structure

## Training Progress

Track training metrics:

| Iteration | Train Loss | Notes |
|-----------|------------|-------|
| 1 | 2.19 | Initial |
| 1,000 | 1.5x | First checkpoint |
| 10,000 | 1.3x | Steady improvement |
| 50,000 | TBD | Final |

## References

- [MLX-LM Documentation](https://github.com/ml-explore/mlx-examples/tree/main/llms)
- [LoRA Paper](https://arxiv.org/abs/2106.09685)
- [Qwen3 Technical Report](https://qwenlm.github.io/blog/qwen3/)
