"""Tests for git slash commands using a temporary git repo."""

import os
import subprocess
from pathlib import Path

import pytest

from hanzo_dev.git_commands import (
    git_branch,
    git_commit,
    git_diff,
    git_stash,
    git_status,
    git_worktree,
    handle_git_command,
)

_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "test",
    "GIT_AUTHOR_EMAIL": "t@t",
    "GIT_COMMITTER_NAME": "test",
    "GIT_COMMITTER_EMAIL": "t@t",
}


def _run(*args: str, cwd: Path) -> None:
    subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=_ENV, check=True)


@pytest.fixture()
def git_repo(tmp_path: Path) -> Path:
    """Create a temporary git repo with one committed file."""
    _run("git", "init", "-b", "main", cwd=tmp_path)
    (tmp_path / "README.md").write_text("# test\n")
    _run("git", "add", "README.md", cwd=tmp_path)
    _run("git", "commit", "-m", "init", cwd=tmp_path)
    return tmp_path


class TestGitStatus:
    def test_clean_repo(self, git_repo: Path) -> None:
        out = git_status(git_repo)
        assert "nothing to commit" in out.lower() or "clean" in out.lower()

    def test_dirty_repo(self, git_repo: Path) -> None:
        (git_repo / "new.txt").write_text("hello\n")
        out = git_status(git_repo)
        assert "new.txt" in out


class TestGitBranch:
    def test_list_branches(self, git_repo: Path) -> None:
        out = git_branch("", git_repo)
        assert "main" in out

    def test_create_branch(self, git_repo: Path) -> None:
        out = git_branch("feature-x", git_repo)
        assert "feature-x" in out
        listing = git_branch("", git_repo)
        assert "feature-x" in listing


class TestGitCommit:
    def test_commit_staged(self, git_repo: Path) -> None:
        (git_repo / "a.txt").write_text("a\n")
        out = git_commit("add a.txt", git_repo)
        assert "add a.txt" in out or "1 file changed" in out or "create mode" in out

    def test_commit_nothing(self, git_repo: Path) -> None:
        out = git_commit("empty", git_repo)
        assert "nothing" in out.lower() or "no changes" in out.lower()


class TestGitDiff:
    def test_no_diff(self, git_repo: Path) -> None:
        out = git_diff(git_repo)
        assert out.strip() == "" or "no changes" in out.lower()

    def test_has_diff(self, git_repo: Path) -> None:
        (git_repo / "README.md").write_text("# changed\n")
        out = git_diff(git_repo)
        assert "changed" in out


class TestGitStash:
    def test_stash_and_pop(self, git_repo: Path) -> None:
        (git_repo / "README.md").write_text("# stashed\n")
        out = git_stash("", git_repo)
        assert "saved" in out.lower() or "stash" in out.lower()

        list_out = git_stash("list", git_repo)
        assert "stash@" in list_out or "stash" in list_out.lower()

        git_stash("pop", git_repo)
        assert "stashed" in (git_repo / "README.md").read_text()

    def test_stash_nothing(self, git_repo: Path) -> None:
        out = git_stash("", git_repo)
        assert "no local changes" in out.lower() or "nothing" in out.lower() or "no changes" in out.lower()


class TestGitWorktree:
    def test_list_worktrees(self, git_repo: Path) -> None:
        out = git_worktree("", git_repo)
        assert str(git_repo) in out or "main" in out


class TestDispatcher:
    def test_known_command(self, git_repo: Path) -> None:
        out = handle_git_command("status", "", git_repo)
        assert out is not None

    def test_unknown_command(self, git_repo: Path) -> None:
        out = handle_git_command("frobnicate", "", git_repo)
        assert out is None
