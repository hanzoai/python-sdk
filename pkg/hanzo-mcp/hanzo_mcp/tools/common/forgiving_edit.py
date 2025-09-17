"""Forgiving edit helper for AI-friendly text matching."""

import re
import difflib
from typing import List, Tuple, Optional


class ForgivingEditHelper:
    """Helper class to make text editing more forgiving for AI usage.

    This helper normalizes whitespace, handles partial matches, and provides
    suggestions when exact matches fail.
    """

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Normalize whitespace while preserving structure.

        Args:
            text: Text to normalize

        Returns:
            Text with normalized whitespace
        """
        # Handle the input line by line
        lines = []
        for line in text.split("\n"):
            # Replace tabs with 4 spaces everywhere in the line
            line = line.replace("\t", "    ")

            # Split into indentation and content
            stripped = line.lstrip()
            indent = line[: len(line) - len(stripped)]

            if stripped:
                # For content, normalize multiple spaces to single space
                content = re.sub(r" {2,}", " ", stripped)
                lines.append(indent + content)
            else:
                lines.append(indent)

        return "\n".join(lines)

    @staticmethod
    def find_fuzzy_match(haystack: str, needle: str, threshold: float = 0.85) -> Optional[Tuple[int, int, str]]:
        """Find a fuzzy match for the needle in the haystack.

        Args:
            haystack: Text to search in
            needle: Text to search for
            threshold: Similarity threshold (0-1)

        Returns:
            Tuple of (start_pos, end_pos, matched_text) or None
        """
        # First try exact match
        if needle in haystack:
            start = haystack.index(needle)
            return (start, start + len(needle), needle)

        # Normalize for comparison
        norm_haystack = ForgivingEditHelper.normalize_whitespace(haystack)
        norm_needle = ForgivingEditHelper.normalize_whitespace(needle)

        # Try normalized exact match
        if norm_needle in norm_haystack:
            # Find the match in normalized text
            norm_start = norm_haystack.index(norm_needle)

            # Map back to original text
            # This is approximate but usually good enough
            lines_before = norm_haystack[:norm_start].count("\n")

            # Find corresponding position in original
            original_lines = haystack.split("\n")
            norm_lines = norm_haystack.split("\n")

            start_pos = sum(len(line) + 1 for line in original_lines[:lines_before])

            # Find end position by counting lines in needle
            needle_lines = norm_needle.count("\n") + 1
            end_pos = sum(len(line) + 1 for line in original_lines[: lines_before + needle_lines])

            matched = "\n".join(original_lines[lines_before : lines_before + needle_lines])
            return (start_pos, end_pos - 1, matched)

        # Try fuzzy matching on lines
        haystack_lines = haystack.split("\n")
        needle_lines = needle.split("\n")

        if len(needle_lines) == 1:
            # Single line - find best match
            needle_norm = ForgivingEditHelper.normalize_whitespace(needle)
            best_ratio = 0
            best_match = None

            for i, line in enumerate(haystack_lines):
                line_norm = ForgivingEditHelper.normalize_whitespace(line)
                ratio = difflib.SequenceMatcher(None, line_norm, needle_norm).ratio()

                if ratio > best_ratio and ratio >= threshold:
                    best_ratio = ratio
                    start_pos = sum(len(l) + 1 for l in haystack_lines[:i])
                    best_match = (start_pos, start_pos + len(line), line)

            return best_match

        else:
            # Multi-line - find sequence match
            for i in range(len(haystack_lines) - len(needle_lines) + 1):
                candidate_lines = haystack_lines[i : i + len(needle_lines)]
                candidate = "\n".join(candidate_lines)
                candidate_norm = ForgivingEditHelper.normalize_whitespace(candidate)
                needle_norm = ForgivingEditHelper.normalize_whitespace(needle)

                ratio = difflib.SequenceMatcher(None, candidate_norm, needle_norm).ratio()

                if ratio >= threshold:
                    start_pos = sum(len(l) + 1 for l in haystack_lines[:i])
                    return (start_pos, start_pos + len(candidate), candidate)

        return None

    @staticmethod
    def suggest_matches(haystack: str, needle: str, max_suggestions: int = 3) -> List[Tuple[float, str]]:
        """Suggest possible matches when exact match fails.

        Args:
            haystack: Text to search in
            needle: Text to search for
            max_suggestions: Maximum number of suggestions

        Returns:
            List of (similarity_score, text) tuples
        """
        suggestions = []

        # Normalize needle
        needle_norm = ForgivingEditHelper.normalize_whitespace(needle)
        needle_lines = needle.split("\n")

        if len(needle_lines) == 1:
            # Single line - compare with all lines
            for line in haystack.split("\n"):
                if line.strip():  # Skip empty lines
                    line_norm = ForgivingEditHelper.normalize_whitespace(line)
                    ratio = difflib.SequenceMatcher(None, line_norm, needle_norm).ratio()
                    if ratio > 0.5:  # Only reasonably similar lines
                        suggestions.append((ratio, line))

        else:
            # Multi-line - use sliding window
            haystack_lines = haystack.split("\n")
            window_size = len(needle_lines)

            for i in range(len(haystack_lines) - window_size + 1):
                candidate_lines = haystack_lines[i : i + window_size]
                candidate = "\n".join(candidate_lines)
                candidate_norm = ForgivingEditHelper.normalize_whitespace(candidate)

                ratio = difflib.SequenceMatcher(None, candidate_norm, needle_norm).ratio()
                if ratio > 0.5:
                    suggestions.append((ratio, candidate))

        # Sort by similarity and return top matches
        suggestions.sort(reverse=True, key=lambda x: x[0])
        return suggestions[:max_suggestions]

    @staticmethod
    def create_edit_suggestion(file_content: str, old_string: str, new_string: str) -> dict:
        """Create a helpful edit suggestion when match fails.

        Args:
            file_content: Current file content
            old_string: String that couldn't be found
            new_string: Replacement string

        Returns:
            Dict with error message and suggestions
        """
        # Try fuzzy match
        fuzzy_match = ForgivingEditHelper.find_fuzzy_match(file_content, old_string)

        if fuzzy_match:
            _, _, matched_text = fuzzy_match
            return {
                "error": "Exact match not found, but found similar text",
                "found": matched_text,
                "suggestion": "Use this as old_string instead",
                "confidence": "high",
            }

        # Get suggestions
        suggestions = ForgivingEditHelper.suggest_matches(file_content, old_string)

        if suggestions:
            return {
                "error": "Could not find exact or fuzzy match",
                "suggestions": [{"similarity": f"{score:.0%}", "text": text} for score, text in suggestions],
                "hint": "Try using one of these suggestions as old_string",
            }

        # No good matches - provide general help
        return {
            "error": "Could not find any matches",
            "hints": [
                "Check for whitespace differences (tabs vs spaces)",
                "Ensure you're including complete lines",
                "Try a smaller, more unique portion of text",
                "Use the streaming_command tool to view the file with visible whitespace",
            ],
        }

    @staticmethod
    def prepare_edit_string(text: str) -> str:
        """Prepare a string for editing by handling common issues.

        Args:
            text: Text to prepare

        Returns:
            Cleaned text ready for editing
        """
        # Remove any line number prefixes (common in AI copy-paste)
        lines = []
        for line in text.split("\n"):
            # Remove common line number patterns while preserving indentation
            # Match patterns like "1: ", "123: ", "1| ", "1- ", etc.
            # But preserve the original indentation after the line number
            match = re.match(r"^(\d+[:\|\-])\s(.*)", line)
            if match:
                # Keep only the content part (group 2) which includes any indentation
                lines.append(match.group(2))
            else:
                # No line number pattern found, keep the line as-is
                lines.append(line)

        return "\n".join(lines)
