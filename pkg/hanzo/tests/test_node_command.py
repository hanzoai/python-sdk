"""Tests for hanzo node command integration with hanzo/net."""

import sys
from unittest.mock import MagicMock, patch

import pytest
from hanzo.cli import start_compute_node
from hanzo.utils.net_check import check_net_installation, get_missing_dependencies


class TestNetCheck:
    """Test hanzo/net availability checking."""

    def test_check_net_installation_with_venv(self, tmp_path):
        """Test checking net installation with venv present."""
        # Create mock net directory with venv
        net_path = tmp_path / "net"
        net_path.mkdir()
        venv_path = net_path / ".venv" / "bin"
        venv_path.mkdir(parents=True)
        (venv_path / "python").touch()

        with patch("hanzo.utils.net_check.Path") as mock_path:
            mock_path.home.return_value = tmp_path.parent
            mock_path.return_value.exists.return_value = True

            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0

                is_available, path, python = check_net_installation()

                assert is_available is True
                assert path is not None
                assert "python" in python

    def test_check_net_installation_no_venv(self):
        """Test checking net installation without venv."""
        with patch("hanzo.utils.net_check.Path") as mock_path:
            mock_path.return_value.exists.return_value = False

            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 1

                is_available, path, python = check_net_installation()

                assert is_available is False

    def test_get_missing_dependencies(self):
        """Test checking for missing dependencies."""
        with patch("subprocess.run") as mock_run:
            # Mock some packages as installed, others as missing
            def side_effect(cmd, **kwargs):
                result = MagicMock()
                if "scapy" in cmd[2] or "aiohttp" in cmd[2]:
                    result.returncode = 0
                else:
                    result.returncode = 1
                return result

            mock_run.side_effect = side_effect

            missing = get_missing_dependencies()

            assert "scapy" not in missing
            assert "aiohttp" not in missing
            assert "mlx" in missing
            assert "transformers" in missing


class TestNodeCommand:
    """Test hanzo node command."""

    @pytest.mark.asyncio
    async def test_start_compute_node_missing_net(self):
        """Test starting compute node when net is not available."""
        ctx = MagicMock()
        ctx.obj = {"console": MagicMock()}

        with patch("hanzo.cli.check_net_installation") as mock_check:
            mock_check.return_value = (False, None, None)

            await start_compute_node(ctx)

            # Should print error and return early
            ctx.obj["console"].print.assert_any_call(
                "[red]Error:[/red] hanzo/net is not properly configured"
            )

    @pytest.mark.asyncio
    async def test_start_compute_node_with_net_venv(self):
        """Test starting compute node with net venv available."""
        ctx = MagicMock()
        ctx.obj = {"console": MagicMock()}

        with patch("hanzo.cli.check_net_installation") as mock_check:
            mock_check.return_value = (
                True,
                "/path/to/net",
                "/path/to/net/.venv/bin/python",
            )

            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0

                with patch("os.chdir"):
                    await start_compute_node(ctx, models=("llama-3.2-3b",))

                    # Should use venv python
                    mock_run.assert_called_once()
                    assert (
                        "/path/to/net/.venv/bin/python" in mock_run.call_args[0][0][0]
                    )

    @pytest.mark.asyncio
    async def test_start_compute_node_with_models(self):
        """Test starting compute node with specific models."""
        ctx = MagicMock()
        ctx.obj = {"console": MagicMock()}

        with patch("hanzo.cli.check_net_installation") as mock_check:
            mock_check.return_value = (True, "/path/to/net", sys.executable)

            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0

                with patch("os.chdir"):
                    await start_compute_node(
                        ctx,
                        models=("llama-3.2-3b", "gpt-4"),
                        name="test-node",
                        port=8080,
                    )

                    # Check environment variables were set
                    env = mock_run.call_args[1]["env"]
                    assert env["NET_MODELS"] == "llama-3.2-3b,gpt-4"
                    assert env["NET_NODE_NAME"] == "test-node"

    @pytest.mark.asyncio
    async def test_start_compute_node_keyboard_interrupt(self):
        """Test graceful shutdown on keyboard interrupt."""
        ctx = MagicMock()
        ctx.obj = {"console": MagicMock()}

        with patch("hanzo.cli.check_net_installation") as mock_check:
            mock_check.return_value = (True, "/path/to/net", sys.executable)

            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = KeyboardInterrupt()

                with patch("os.chdir"):
                    await start_compute_node(ctx)

                    # Should print shutdown message
                    ctx.obj["console"].print.assert_any_call(
                        "\n[yellow]Shutting down node...[/yellow]"
                    )


def test_cli_imports():
    """Test that CLI modules can be imported."""
    from hanzo import cli
    from hanzo.utils import net_check

    assert hasattr(cli, "start_compute_node")
    assert hasattr(net_check, "check_net_installation")
    assert hasattr(net_check, "get_missing_dependencies")
