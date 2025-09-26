"""Response truncation utilities for MCP tools.

This module provides utilities to ensure MCP tool responses don't exceed token limits.
"""

import tiktoken


def estimate_tokens(text: str, model: str = "gpt-4") -> int:
    """Estimate the number of tokens in a text string.

    Args:
        text: The text to estimate tokens for
        model: The model to use for token estimation (default: gpt-4)

    Returns:
        Estimated number of tokens
    """
    try:
        # Try to get the encoding for the specific model
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # Fall back to cl100k_base which is used by newer models
        encoding = tiktoken.get_encoding("cl100k_base")

    return len(encoding.encode(text))


def truncate_response(
    response: str,
    max_tokens: int = 20000,
    truncation_message: str = "\n\n[Response truncated due to length. Please use pagination, filtering, or limit parameters to see more.]",
) -> str:
    """Truncate a response to fit within token limits.

    Args:
        response: The response text to truncate
        max_tokens: Maximum number of tokens allowed (default: 20000)
        truncation_message: Message to append when truncating

    Returns:
        Truncated response if needed, original response otherwise
    """
    # Quick check - if response is short, no need to count tokens
    if len(response) < max_tokens * 2:  # Rough estimate: 1 token ≈ 2-4 chars
        return response

    # Estimate tokens
    token_count = estimate_tokens(response)

    # If within limit, return as-is
    if token_count <= max_tokens:
        return response

    # Need to truncate
    # Binary search to find the right truncation point
    left, right = 0, len(response)
    truncation_msg_tokens = estimate_tokens(truncation_message)
    target_tokens = max_tokens - truncation_msg_tokens

    while left < right - 1:
        mid = (left + right) // 2
        mid_tokens = estimate_tokens(response[:mid])

        if mid_tokens <= target_tokens:
            left = mid
        else:
            right = mid

    # Find a good break point (newline or space)
    truncate_at = left
    for i in range(min(100, left), -1, -1):
        if response[left - i] in "\n ":
            truncate_at = left - i
            break

    return response[:truncate_at] + truncation_message


def truncate_lines(
    response: str,
    max_lines: int = 1000,
    truncation_message: str = "\n\n[Response truncated to {max_lines} lines. Please use pagination or filtering to see more.]",
) -> str:
    """Truncate a response by number of lines.

    Args:
        response: The response text to truncate
        max_lines: Maximum number of lines allowed (default: 1000)
        truncation_message: Message template to append when truncating

    Returns:
        Truncated response if needed, original response otherwise
    """
    lines = response.split("\n")

    if len(lines) <= max_lines:
        return response

    truncated = "\n".join(lines[:max_lines])
    return truncated + truncation_message.format(max_lines=max_lines)
