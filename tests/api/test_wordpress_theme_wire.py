"""Tests for the wordpress/theme/deploy endpoint wire-up.

Verifies flag-mapping logic (production → no --dry-run; non-production →
--dry-run) and returncode-to-success mapping.

The deploy script is NEVER executed — asyncio.create_subprocess_exec is
fully mocked so no network or filesystem contact occurs.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.v1.wordpress_theme import require_admin, router

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_client() -> TestClient:
    """Minimal FastAPI app with the theme router and admin dep overridden."""
    app = FastAPI()
    app.include_router(router)
    # require_admin is a RoleChecker *instance* — override it by identity so
    # the dependency injection system skips JWT verification in tests.
    app.dependency_overrides[require_admin] = lambda: {"sub": "admin", "role": "admin"}
    return TestClient(app)


def _make_fake_proc(returncode: int, stdout: bytes, stderr: bytes = b"") -> MagicMock:
    """Return a fake asyncio.subprocess.Process for subprocess mocking."""
    proc = MagicMock()
    proc.returncode = returncode
    # communicate() must be an AsyncMock so `await proc.communicate()` works
    # and `asyncio.wait_for(proc.communicate(), ...)` gets a real coroutine.
    proc.communicate = AsyncMock(return_value=(stdout, stderr))
    # wait() is awaited in the timeout branch to reap a killed child (no zombie).
    proc.wait = AsyncMock(return_value=returncode)
    return proc


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestDeployThemeWire:
    """Flag-mapping + returncode-mapping for the /wordpress/theme/deploy endpoint."""

    def test_production_success_no_dry_run_flag(self) -> None:
        """returncode=0 + environment='production' → success=True, no --dry-run in call."""
        fake_proc = _make_fake_proc(
            returncode=0,
            stdout=b"Theme uploaded.\nDeploy complete (verified live)\nBackup saved.",
        )

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = fake_proc

            client = _build_client()
            resp = client.post(
                "/wordpress/theme/deploy",
                json={"environment": "production", "backup_first": True},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["returncode"] == 0
        assert body["environment"] == "production"

        # Critical flag-mapping assertion: production MUST NOT include --dry-run
        call_args = mock_exec.call_args
        assert call_args is not None, "create_subprocess_exec was not called"
        positional_args = list(call_args.args)
        assert (
            "--dry-run" not in positional_args
        ), f"production deploy must not receive --dry-run; got args: {positional_args}"

    def test_staging_passes_dry_run_flag(self) -> None:
        """environment != 'production' → --dry-run IS included in the subprocess call."""
        fake_proc = _make_fake_proc(
            returncode=0,
            stdout=b"DRY-RUN: would deploy theme\nNo files transferred.",
        )

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = fake_proc

            client = _build_client()
            resp = client.post(
                "/wordpress/theme/deploy",
                json={"environment": "staging", "backup_first": False},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["environment"] == "staging"

        # Critical flag-mapping assertion: non-production MUST include --dry-run
        call_args = mock_exec.call_args
        assert call_args is not None, "create_subprocess_exec was not called"
        positional_args = list(call_args.args)
        assert (
            "--dry-run" in positional_args
        ), f"non-production deploy must include --dry-run; got args: {positional_args}"
        # dry-run in response message
        assert "dry-run" in body["message"].lower()

    def test_returncode_3_post_verify_failure(self) -> None:
        """exit code 3 (post-deploy verify failure) → success=False, returncode=3."""
        fake_proc = _make_fake_proc(
            returncode=3,
            stdout=b"Theme uploaded but post-deploy verify probe returned non-200.",
            stderr=b"HTTP 502 on verify probe",
        )

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = fake_proc

            client = _build_client()
            resp = client.post(
                "/wordpress/theme/deploy",
                json={"environment": "production", "backup_first": True},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert body["returncode"] == 3
        # Message must indicate failure
        assert "fail" in body["message"].lower() or "3" in body["message"]
        # log_tail should contain lines from stdout/stderr
        assert isinstance(body["log_tail"], list)
        assert len(body["log_tail"]) > 0

    def test_with_maintenance_flag_appended_to_production_deploy(self) -> None:
        """with_maintenance=True → --with-maintenance in the subprocess call (production)."""
        fake_proc = _make_fake_proc(
            returncode=0,
            stdout=b"Maintenance mode on.\nDeploy complete (verified live).",
        )

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = fake_proc

            client = _build_client()
            resp = client.post(
                "/wordpress/theme/deploy",
                json={
                    "environment": "production",
                    "backup_first": True,
                    "with_maintenance": True,
                },
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True

        positional_args = list(mock_exec.call_args.args)
        assert (
            "--with-maintenance" in positional_args
        ), f"with_maintenance=True must pass --with-maintenance; got args: {positional_args}"
        assert "--dry-run" not in positional_args

    def test_with_maintenance_default_omits_flag(self) -> None:
        """with_maintenance defaults to False → --with-maintenance NOT in call."""
        fake_proc = _make_fake_proc(returncode=0, stdout=b"Deploy complete (verified live).")

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = fake_proc

            client = _build_client()
            resp = client.post(
                "/wordpress/theme/deploy",
                json={"environment": "production", "backup_first": True},
            )

        assert resp.status_code == 200
        positional_args = list(mock_exec.call_args.args)
        assert "--with-maintenance" not in positional_args

    def test_timeout_kills_proc_and_returns_timed_out_body(self) -> None:
        """Deploy exceeding the timeout → proc killed AND reaped, 200 body success=False.

        Simulating via communicate() raising TimeoutError reaches the same
        `except TimeoutError` branch as a real wait_for timeout: wait_for awaits
        the coroutine and re-raises the TimeoutError it sees (so the coroutine is
        awaited, not left dangling — no 'never awaited' warning).
        """
        fake_proc = _make_fake_proc(returncode=0, stdout=b"")
        fake_proc.communicate = AsyncMock(side_effect=TimeoutError())

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = fake_proc

            client = _build_client()
            resp = client.post(
                "/wordpress/theme/deploy",
                json={"environment": "production", "backup_first": True},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert body["returncode"] == -1
        assert "timed out" in body["message"].lower()
        assert isinstance(body["log_tail"], list)

        # The leaked child must be killed AND reaped — proves no zombie is left.
        fake_proc.kill.assert_called_once()
        fake_proc.wait.assert_awaited_once()

    def test_cancelled_request_kills_child(self) -> None:
        """Request cancellation (client disconnect / shutdown) must kill the child.

        Calls the handler coroutine directly (TestClient cannot simulate ASGI
        cancellation) and asserts the deploy child is SIGKILL'd before the
        CancelledError propagates — otherwise `bash deploy-theme.sh` leaks.
        """
        import asyncio

        from api.v1.wordpress_theme import ThemeDeployRequest, deploy_theme

        fake_proc = _make_fake_proc(returncode=0, stdout=b"")
        fake_proc.returncode = None  # still running when the request is cancelled
        fake_proc.communicate = AsyncMock(side_effect=asyncio.CancelledError())

        async def _run() -> bool:
            with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = fake_proc
                try:
                    await deploy_theme(
                        ThemeDeployRequest(environment="production"),
                        current_user={"sub": "admin"},
                    )
                except asyncio.CancelledError:
                    return True
                return False

        cancelled = asyncio.run(_run())
        assert cancelled is True, "deploy_theme must propagate CancelledError"
        fake_proc.kill.assert_called_once()
