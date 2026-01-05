"""Comprehensive tests for Shellflow DSL parser and execution."""

import time
import asyncio
from typing import Any

import pytest
from hanzo_tools.shell.shellflow import (
    parse,
    compile,
    to_sexp,
    _tokenize,
    from_sexp,
    _normalize,
    to_commands,
    render_ascii,
)


class TestTokenizer:
    """Tests for shellflow tokenization."""

    def test_simple_command(self):
        assert _tokenize("ls -la") == ["ls -la"]

    def test_sequential_commands(self):
        tokens = _tokenize("A ; B ; C")
        assert tokens == ["A", ";", "B", ";", "C"]

    def test_parallel_block(self):
        tokens = _tokenize("{ A & B & C }")
        assert tokens == ["{ A & B & C }"]

    def test_mixed_syntax(self):
        tokens = _tokenize("A ; { B & C } ; D")
        assert tokens == ["A", ";", "{ B & C }", ";", "D"]

    def test_nested_braces(self):
        tokens = _tokenize("A ; { B ; { C & D } } ; E")
        assert tokens == ["A", ";", "{ B ; { C & D } }", ";", "E"]

    def test_empty_input(self):
        assert _tokenize("") == []
        assert _tokenize("   ") == []

    def test_commands_with_semicolons_in_strings(self):
        # Commands containing semicolons in quoted strings
        tokens = _tokenize('echo "a;b" ; echo c')
        assert len(tokens) == 3  # echo "a;b", ;, echo c

    def test_commands_with_pipes(self):
        tokens = _tokenize("cat file | grep pattern ; echo done")
        assert tokens == ["cat file | grep pattern", ";", "echo done"]

    def test_commands_with_and_or(self):
        tokens = _tokenize("cmd1 && cmd2 || cmd3 ; cmd4")
        assert tokens == ["cmd1 && cmd2 || cmd3", ";", "cmd4"]


class TestParser:
    """Tests for shellflow parsing to AST."""

    def test_simple_command(self):
        ast = parse("ls -la")
        assert ast == {"type": "do", "steps": ["ls -la"]}

    def test_sequential(self):
        ast = parse("A ; B ; C")
        assert ast == {"type": "do", "steps": ["A", "B", "C"]}

    def test_parallel(self):
        ast = parse("{ A & B & C }")
        assert ast == {"type": "all", "steps": ["A", "B", "C"]}

    def test_mixed_dag(self):
        ast = parse("setup ; { task1 & task2 } ; cleanup")
        assert ast == {
            "type": "do",
            "steps": [
                "setup",
                {"type": "all", "steps": ["task1", "task2"]},
                "cleanup",
            ],
        }

    def test_complex_dag(self):
        ast = parse("A ; { B & C & D } ; { E & F } ; G")
        assert ast == {
            "type": "do",
            "steps": [
                "A",
                {"type": "all", "steps": ["B", "C", "D"]},
                {"type": "all", "steps": ["E", "F"]},
                "G",
            ],
        }

    def test_empty_input(self):
        ast = parse("")
        assert ast == {"type": "do", "steps": []}

    def test_whitespace_handling(self):
        ast = parse("  A  ;  B  ;  C  ")
        assert ast == {"type": "do", "steps": ["A", "B", "C"]}

    def test_single_parallel_task(self):
        ast = parse("{ A }")
        # Single item in parallel should be normalized
        assert ast["steps"] == ["A"] or ast == "A"

    def test_real_world_example(self):
        src = "mkdir -p dist ; { cp a.txt dist/ & cp b.txt dist/ & cp c.txt dist/ } ; zip -r out.zip dist/"
        ast = parse(src)
        assert ast["type"] == "do"
        assert len(ast["steps"]) == 3
        assert ast["steps"][0] == "mkdir -p dist"
        assert ast["steps"][1]["type"] == "all"
        assert len(ast["steps"][1]["steps"]) == 3
        assert ast["steps"][2] == "zip -r out.zip dist/"


class TestNormalization:
    """Tests for AST normalization."""

    def test_flatten_nested_do(self):
        ast = {"type": "do", "steps": [{"type": "do", "steps": ["A", "B"]}, "C"]}
        normalized = _normalize(ast)
        assert normalized == {"type": "do", "steps": ["A", "B", "C"]}

    def test_flatten_nested_all(self):
        ast = {"type": "all", "steps": [{"type": "all", "steps": ["A", "B"]}, "C"]}
        normalized = _normalize(ast)
        assert normalized == {"type": "all", "steps": ["A", "B", "C"]}

    def test_singleton_do(self):
        ast = {"type": "do", "steps": ["A"]}
        normalized = _normalize(ast)
        # Singleton should be kept as-is for consistency
        assert "A" in str(normalized)

    def test_empty_steps(self):
        ast = {"type": "do", "steps": []}
        normalized = _normalize(ast)
        assert normalized == {"type": "do", "steps": []}

    def test_deeply_nested(self):
        ast = {
            "type": "do",
            "steps": [
                {"type": "do", "steps": [{"type": "do", "steps": ["A"]}]},
                "B",
            ],
        }
        normalized = _normalize(ast)
        assert "A" in str(normalized)
        assert "B" in str(normalized)


class TestSexpConversion:
    """Tests for S-expression conversion."""

    def test_to_sexp_simple(self):
        ast = {"type": "do", "steps": ["A", "B", "C"]}
        sexp = to_sexp(ast)
        assert sexp == ["do", "A", "B", "C"]

    def test_to_sexp_nested(self):
        ast = {
            "type": "do",
            "steps": ["A", {"type": "all", "steps": ["B", "C"]}, "D"],
        }
        sexp = to_sexp(ast)
        assert sexp == ["do", "A", ["all", "B", "C"], "D"]

    def test_from_sexp_simple(self):
        sexp = ["do", "A", "B", "C"]
        ast = from_sexp(sexp)
        assert ast == {"type": "do", "steps": ["A", "B", "C"]}

    def test_from_sexp_nested(self):
        sexp = ["do", "A", ["all", "B", "C"], "D"]
        ast = from_sexp(sexp)
        assert ast == {
            "type": "do",
            "steps": ["A", {"type": "all", "steps": ["B", "C"]}, "D"],
        }

    def test_roundtrip(self):
        original = {
            "type": "do",
            "steps": ["A", {"type": "all", "steps": ["B", "C"]}, "D"],
        }
        sexp = to_sexp(original)
        recovered = from_sexp(sexp)
        assert recovered == original


class TestToCommands:
    """Tests for conversion to executor commands format."""

    def test_sequential(self):
        ast = {"type": "do", "steps": ["A", "B", "C"]}
        cmds = to_commands(ast)
        assert cmds == ["A", "B", "C"]

    def test_parallel(self):
        ast = {"type": "all", "steps": ["A", "B", "C"]}
        cmds = to_commands(ast)
        assert cmds == [["A", "B", "C"]]

    def test_mixed(self):
        ast = {
            "type": "do",
            "steps": ["A", {"type": "all", "steps": ["B", "C"]}, "D"],
        }
        cmds = to_commands(ast)
        assert cmds == ["A", ["B", "C"], "D"]

    def test_complex_dag(self):
        ast = {
            "type": "do",
            "steps": [
                "setup",
                {"type": "all", "steps": ["task1", "task2", "task3"]},
                {"type": "all", "steps": ["cleanup1", "cleanup2"]},
                "done",
            ],
        }
        cmds = to_commands(ast)
        assert cmds == [
            "setup",
            ["task1", "task2", "task3"],
            ["cleanup1", "cleanup2"],
            "done",
        ]


class TestCompile:
    """Tests for compile convenience function."""

    def test_compile_to_ast(self):
        result = compile("A ; B ; C", format="ast")
        assert result == {"type": "do", "steps": ["A", "B", "C"]}

    def test_compile_to_sexp(self):
        result = compile("A ; B ; C", format="sexp")
        assert result == ["do", "A", "B", "C"]

    def test_compile_to_commands(self):
        result = compile("A ; { B & C } ; D", format="commands")
        assert result == ["A", ["B", "C"], "D"]

    def test_compile_to_ascii(self):
        result = compile("A ; B", format="ascii")
        assert "[do]" in result
        assert "A" in result
        assert "B" in result

    def test_compile_invalid_format(self):
        with pytest.raises(ValueError):
            compile("A", format="invalid")


class TestRenderAscii:
    """Tests for ASCII rendering."""

    def test_simple(self):
        ast = {"type": "do", "steps": ["A", "B"]}
        output = render_ascii(ast)
        assert "[do]" in output
        assert "A" in output
        assert "B" in output

    def test_nested(self):
        ast = {
            "type": "do",
            "steps": ["A", {"type": "all", "steps": ["B", "C"]}, "D"],
        }
        output = render_ascii(ast)
        assert "[do]" in output
        assert "[all]" in output


class TestEdgeCases:
    """Edge case and error handling tests."""

    def test_many_sequential(self):
        src = " ; ".join([f"cmd{i}" for i in range(100)])
        ast = parse(src)
        assert len(ast["steps"]) == 100

    def test_many_parallel(self):
        src = "{ " + " & ".join([f"cmd{i}" for i in range(100)]) + " }"
        ast = parse(src)
        assert len(ast["steps"]) == 100

    def test_deeply_nested_parallel(self):
        src = "A ; { B & { C & D } } ; E"
        ast = parse(src)
        # Should handle nested parallel blocks
        assert ast["type"] == "do"

    def test_unicode_commands(self):
        ast = parse("echo 你好 ; echo мир ; echo 🚀")
        assert len(ast["steps"]) == 3

    def test_long_commands(self):
        long_cmd = "echo " + "x" * 10000
        ast = parse(long_cmd)
        assert long_cmd in ast["steps"][0] or ast["steps"][0] == long_cmd


class TestPerformance:
    """Performance benchmarks."""

    def test_parse_speed_simple(self):
        """Should parse simple commands very fast."""
        src = "ls -la"
        start = time.perf_counter()
        for _ in range(10000):
            parse(src)
        elapsed = time.perf_counter() - start
        ops_per_sec = 10000 / elapsed
        print(f"\nSimple parse: {ops_per_sec:.0f} ops/sec")
        assert ops_per_sec > 10000  # At least 10k ops/sec

    def test_parse_speed_mixed(self):
        """Should parse mixed DAGs reasonably fast."""
        src = "mkdir -p dist ; { cp a dist/ & cp b dist/ & cp c dist/ } ; zip out.zip dist/"
        start = time.perf_counter()
        for _ in range(1000):
            parse(src)
        elapsed = time.perf_counter() - start
        ops_per_sec = 1000 / elapsed
        print(f"\nMixed DAG parse: {ops_per_sec:.0f} ops/sec")
        assert ops_per_sec > 1000  # At least 1k ops/sec

    def test_compile_speed(self):
        """Should compile to commands fast."""
        src = "A ; { B & C & D } ; E"
        start = time.perf_counter()
        for _ in range(10000):
            compile(src, format="commands")
        elapsed = time.perf_counter() - start
        ops_per_sec = 10000 / elapsed
        print(f"\nFull compile: {ops_per_sec:.0f} ops/sec")
        assert ops_per_sec > 5000  # At least 5k ops/sec

    def test_large_dag(self):
        """Should handle large DAGs efficiently."""
        # 100 sequential with 10 parallel each
        parts = []
        for i in range(100):
            parallel = "{ " + " & ".join([f"task{i}_{j}" for j in range(10)]) + " }"
            parts.append(parallel)
        src = " ; ".join(parts)

        start = time.perf_counter()
        ast = parse(src)
        cmds = to_commands(ast)
        elapsed = time.perf_counter() - start

        print(f"\nLarge DAG (100x10): {elapsed*1000:.2f}ms")
        assert elapsed < 0.1  # Should complete in under 100ms
        assert len(cmds) == 100


@pytest.mark.asyncio
class TestIntegration:
    """Integration tests with actual shell execution."""

    async def test_execute_sequential(self):
        from hanzo_tools.shell import ZshTool

        zsh = ZshTool()
        result = await zsh.call(None, command="echo A ; echo B ; echo C")
        assert "A" in result
        assert "B" in result
        assert "C" in result

    async def test_execute_parallel(self):
        from hanzo_tools.shell import ZshTool

        zsh = ZshTool()
        result = await zsh.call(None, command="{ echo A & echo B & echo C }")
        assert "A" in result
        assert "B" in result
        assert "C" in result

    async def test_execute_mixed(self):
        from hanzo_tools.shell import ZshTool

        zsh = ZshTool()
        result = await zsh.call(
            None, command="echo start ; { echo A & echo B } ; echo end"
        )
        assert "start" in result
        assert "A" in result
        assert "B" in result
        assert "end" in result

    async def test_execute_with_bash(self):
        from hanzo_tools.shell import BashTool

        bash = BashTool()
        # Use proper bash syntax (no zsh-style { } backgrounding)
        result = await bash.call(
            None, command="echo start && echo A && echo B && echo end"
        )
        assert "start" in result
        assert "end" in result

    async def test_parallel_execution_time(self):
        """Parallel should be faster than sequential for sleep commands."""
        from hanzo_tools.shell import ZshTool

        zsh = ZshTool()

        # Parallel: should take ~0.1s
        start = time.perf_counter()
        await zsh.call(None, command="{ sleep 0.1 & sleep 0.1 & sleep 0.1 }")
        parallel_time = time.perf_counter() - start

        # Sequential: should take ~0.3s
        start = time.perf_counter()
        await zsh.call(None, command="sleep 0.1 ; sleep 0.1 ; sleep 0.1")
        sequential_time = time.perf_counter() - start

        print(f"\nParallel: {parallel_time:.2f}s, Sequential: {sequential_time:.2f}s")
        # Parallel should be at least 2x faster
        assert parallel_time < sequential_time * 0.7


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
