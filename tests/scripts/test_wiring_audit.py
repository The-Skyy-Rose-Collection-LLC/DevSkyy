"""Unit tests for scripts/remediation/wiring_audit.py.

The check_* functions are pure — no network. `run()` is tested with every
`requests` call mocked so this suite never touches live WordPress/WooCommerce.
"""

import base64
import hashlib
import hmac
from unittest.mock import MagicMock, patch

import scripts.remediation.wiring_audit as wiring_audit


def _reference_signature(body: str, secret: str) -> str:
    digest = hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest()
    return base64.b64encode(digest).decode()


class TestComputeSignature:
    def test_matches_reference_hmac_sha256_base64(self):
        assert wiring_audit.compute_signature("hello", "s3cr3t") == _reference_signature(
            "hello", "s3cr3t"
        )

    def test_different_body_yields_different_signature(self):
        assert wiring_audit.compute_signature("a", "s") != wiring_audit.compute_signature("b", "s")

    def test_different_secret_yields_different_signature(self):
        assert wiring_audit.compute_signature("a", "s1") != wiring_audit.compute_signature(
            "a", "s2"
        )


class TestCheckSignatureRoundtrip:
    def test_passes_for_a_real_secret(self):
        ok, note = wiring_audit.check_signature_roundtrip("a-real-secret")
        assert ok is True
        assert "correct" in note


class TestCheckCategoryTotalsSane:
    def test_passes_when_categorized_subset_of_total(self):
        ok, _note = wiring_audit.check_category_totals_sane(
            {"black-rose": 14, "love-hurts": 4, "signature": 11, "kids-capsule": 2}, 33
        )
        assert ok is True

    def test_fails_when_a_fetch_failed(self):
        ok, note = wiring_audit.check_category_totals_sane({"black-rose": -1}, 33)
        assert ok is False
        assert "black-rose" in note

    def test_fails_when_sum_exceeds_grand_total(self):
        ok, _note = wiring_audit.check_category_totals_sane({"black-rose": 50}, 33)
        assert ok is False


class TestFindLeakedSecrets:
    # Real WooCommerce keys are ck_/cs_ + 40 lowercase hex chars.
    REAL_CK = "ck_" + "a1b2c3d4e5" * 4
    REAL_CS = "cs_" + "0f9e8d7c6b" * 4

    def test_finds_consumer_key_fragment(self):
        leaked = wiring_audit.find_leaked_secrets(f"const x = '{self.REAL_CK}';")
        assert len(leaked) == 1

    def test_finds_consumer_secret_fragment(self):
        leaked = wiring_audit.find_leaked_secrets(self.REAL_CS)
        assert len(leaked) == 1

    def test_clean_bundle_finds_nothing(self):
        assert wiring_audit.find_leaked_secrets("export function foo() { return 1; }") == []

    def test_ui_placeholder_does_not_false_positive(self):
        # Admin settings inputs ship literal placeholders in client chunks
        # (bug-223): 'x' is not a hex digit, so these must NOT match.
        text = 'placeholder:"ck_xxxxxxxxxxxxx",placeholder:"cs_xxxxxxxxxxxxx"'
        assert wiring_audit.find_leaked_secrets(text) == []


class TestCheckBurstTiming:
    def test_passes_when_paced_at_500ms(self):
        ok, _note = wiring_audit.check_burst_timing([0, 0.5, 1.0, 1.5])
        assert ok is True

    def test_fails_when_gap_too_tight(self):
        ok, _note = wiring_audit.check_burst_timing([0, 0.01, 0.5])
        assert ok is False

    def test_single_timestamp_is_trivially_ok(self):
        ok, _note = wiring_audit.check_burst_timing([0])
        assert ok is True


class TestRunNeverHitsLiveNetwork:
    def _set_env(self, monkeypatch):
        for var, val in {
            "WP_BASE_URL": "https://example.test",
            "WC_CONSUMER_KEY": "ck_test",
            "WC_CONSUMER_SECRET": "cs_test",
            "WP_APP_USER": "svc",
            "WP_APP_PASSWORD": "pw",
            "WP_WEBHOOK_SECRET": "whsecret",
        }.items():
            monkeypatch.setenv(var, val)

    def test_run_read_only_uses_mocked_requests_only(self, monkeypatch):
        self._set_env(monkeypatch)

        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.headers = {"X-WP-Total": "1"}
        fake_response.json.return_value = {}
        fake_response.raise_for_status.return_value = None

        with (
            patch(
                "scripts.remediation.wiring_audit.requests.get", return_value=fake_response
            ) as mock_get,
            patch("scripts.remediation.wiring_audit.requests.put") as mock_put,
            patch("scripts.remediation.wiring_audit.requests.patch") as mock_patch,
            patch("scripts.remediation.wiring_audit.time.sleep"),
        ):
            exit_code = wiring_audit.run(write=False)

        assert isinstance(exit_code, int)
        assert mock_get.called
        mock_put.assert_not_called()  # write checks are skipped when write=False
        mock_patch.assert_not_called()

    def test_missing_wp_base_url_returns_1_without_any_request(self, monkeypatch):
        for var in (
            "WP_BASE_URL",
            "WC_CONSUMER_KEY",
            "WC_CONSUMER_SECRET",
            "WP_APP_USER",
            "WP_APP_PASSWORD",
            "WP_WEBHOOK_SECRET",
        ):
            monkeypatch.delenv(var, raising=False)

        with patch("scripts.remediation.wiring_audit.requests.get") as mock_get:
            exit_code = wiring_audit.run(write=False)

        assert exit_code == 1
        mock_get.assert_not_called()

    def test_write_true_invokes_both_write_gated_helpers(self, monkeypatch):
        self._set_env(monkeypatch)

        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.headers = {"X-WP-Total": "1"}
        fake_response.json.return_value = {}
        fake_response.raise_for_status.return_value = None

        with (
            patch("scripts.remediation.wiring_audit.requests.get", return_value=fake_response),
            patch("scripts.remediation.wiring_audit.time.sleep"),
            patch(
                "scripts.remediation.wiring_audit._product_meta_roundtrip",
                return_value=("product meta_data write round-trip", True, "ok"),
            ) as mock_product_check,
            patch(
                "scripts.remediation.wiring_audit._settings_roundtrip",
                return_value=("settings PATCH round-trip", True, "ok"),
            ) as mock_settings_check,
        ):
            wiring_audit.run(write=True)

        mock_product_check.assert_called_once()
        mock_settings_check.assert_called_once()

    def test_write_false_never_invokes_the_write_gated_helpers(self, monkeypatch):
        self._set_env(monkeypatch)

        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.headers = {"X-WP-Total": "1"}
        fake_response.json.return_value = {}
        fake_response.raise_for_status.return_value = None

        with (
            patch("scripts.remediation.wiring_audit.requests.get", return_value=fake_response),
            patch("scripts.remediation.wiring_audit.time.sleep"),
            patch("scripts.remediation.wiring_audit._product_meta_roundtrip") as mock_product_check,
            patch("scripts.remediation.wiring_audit._settings_roundtrip") as mock_settings_check,
        ):
            wiring_audit.run(write=False)

        mock_product_check.assert_not_called()
        mock_settings_check.assert_not_called()


class TestProductMetaRoundtrip:
    def test_writes_reads_back_and_cleans_up(self):
        wc_auth = ("ck_test", "cs_test")
        listing_response = MagicMock()
        listing_response.raise_for_status.return_value = None
        listing_response.json.return_value = [{"id": 42}]

        get_response = MagicMock()
        get_response.raise_for_status.return_value = None
        get_response.json.return_value = {
            "meta_data": [{"key": "devskyy_wiring_check", "value": "wiring-audit-1000"}]
        }

        put_response = MagicMock()
        put_response.raise_for_status.return_value = None

        with (
            patch(
                "scripts.remediation.wiring_audit.requests.get",
                side_effect=[listing_response, get_response],
            ),
            patch(
                "scripts.remediation.wiring_audit.requests.put", return_value=put_response
            ) as mock_put,
            patch("scripts.remediation.wiring_audit.time.time", return_value=1000.0),
        ):
            name, ok, note = wiring_audit._product_meta_roundtrip("https://example.test", wc_auth)

        assert name == "product meta_data write round-trip"
        assert ok is True
        assert "42" in note
        assert mock_put.call_count == 2  # write the marker, then clear it

    def test_marker_mismatch_reports_failure(self):
        wc_auth = ("ck_test", "cs_test")
        listing_response = MagicMock()
        listing_response.raise_for_status.return_value = None
        listing_response.json.return_value = [{"id": 42}]
        get_response = MagicMock()
        get_response.raise_for_status.return_value = None
        get_response.json.return_value = {"meta_data": []}  # marker never landed
        put_response = MagicMock()
        put_response.raise_for_status.return_value = None

        with (
            patch(
                "scripts.remediation.wiring_audit.requests.get",
                side_effect=[listing_response, get_response],
            ),
            patch("scripts.remediation.wiring_audit.requests.put", return_value=put_response),
        ):
            _name, ok, note = wiring_audit._product_meta_roundtrip("https://example.test", wc_auth)

        assert ok is False
        assert "mismatch" in note

    def test_no_products_returns_failure_without_writing(self):
        wc_auth = ("ck_test", "cs_test")
        listing_response = MagicMock()
        listing_response.raise_for_status.return_value = None
        listing_response.json.return_value = []

        with (
            patch("scripts.remediation.wiring_audit.requests.get", return_value=listing_response),
            patch("scripts.remediation.wiring_audit.requests.put") as mock_put,
        ):
            _name, ok, note = wiring_audit._product_meta_roundtrip("https://example.test", wc_auth)

        assert ok is False
        assert "no products" in note
        mock_put.assert_not_called()


class TestSettingsRoundtrip:
    # The endpoint whitelists its keys, so the round-trip uses the real
    # `fastapi_url` key and the PATCH response echoes accepted keys in
    # `updated` (see skyyrose_see_rest_update_settings).
    MARKER = "https://wiring-check-1000.invalid"

    def test_writes_reads_back_and_restores(self):
        wp_auth = ("svc", "pw")
        before_response = MagicMock()
        before_response.raise_for_status.return_value = None
        before_response.json.return_value = {"fastapi_url": "https://api.devskyy.app"}

        after_response = MagicMock()
        after_response.raise_for_status.return_value = None
        after_response.json.return_value = {"fastapi_url": self.MARKER}

        patch_response = MagicMock()
        patch_response.raise_for_status.return_value = None
        patch_response.json.return_value = {"updated": ["fastapi_url"]}

        with (
            patch(
                "scripts.remediation.wiring_audit.requests.get",
                side_effect=[before_response, after_response],
            ),
            patch(
                "scripts.remediation.wiring_audit.requests.patch", return_value=patch_response
            ) as mock_patch,
            patch("scripts.remediation.wiring_audit.time.time", return_value=1000.0),
        ):
            name, ok, note = wiring_audit._settings_roundtrip("https://example.test", wp_auth)

        assert name == "settings PATCH round-trip"
        assert ok is True
        assert "restored" in note
        assert mock_patch.call_count == 2  # write the marker, then restore
        _, restore_kwargs = mock_patch.call_args
        assert restore_kwargs["json"] == {"fastapi_url": "https://api.devskyy.app"}

    def test_marker_mismatch_reports_failure(self):
        wp_auth = ("svc", "pw")
        before_response = MagicMock()
        before_response.raise_for_status.return_value = None
        before_response.json.return_value = {"fastapi_url": ""}
        after_response = MagicMock()
        after_response.raise_for_status.return_value = None
        after_response.json.return_value = {"fastapi_url": ""}  # PATCH didn't take
        patch_response = MagicMock()
        patch_response.raise_for_status.return_value = None
        patch_response.json.return_value = {"updated": ["fastapi_url"]}

        with (
            patch(
                "scripts.remediation.wiring_audit.requests.get",
                side_effect=[before_response, after_response],
            ),
            patch(
                "scripts.remediation.wiring_audit.requests.patch", return_value=patch_response
            ) as mock_patch,
        ):
            _name, ok, note = wiring_audit._settings_roundtrip("https://example.test", wp_auth)

        assert ok is False
        assert "mismatch" in note
        assert mock_patch.call_count == 2  # restore still runs on failure

    def test_unaccepted_key_reports_failure_and_restores(self):
        wp_auth = ("svc", "pw")
        before_response = MagicMock()
        before_response.raise_for_status.return_value = None
        before_response.json.return_value = {"fastapi_url": "https://api.devskyy.app"}
        patch_response = MagicMock()
        patch_response.raise_for_status.return_value = None
        patch_response.json.return_value = {"updated": []}  # whitelist rejected the key

        with (
            patch(
                "scripts.remediation.wiring_audit.requests.get",
                return_value=before_response,
            ),
            patch(
                "scripts.remediation.wiring_audit.requests.patch", return_value=patch_response
            ) as mock_patch,
        ):
            _name, ok, note = wiring_audit._settings_roundtrip("https://example.test", wp_auth)

        assert ok is False
        assert "did not accept" in note
        assert mock_patch.call_count == 2  # restore still runs


class TestMainGate:
    def test_write_without_ack_refuses_before_run(self, monkeypatch):
        monkeypatch.delenv("STOPSHOW_ACK", raising=False)
        monkeypatch.setattr("sys.argv", ["wiring_audit.py", "--write"])

        with patch("scripts.remediation.wiring_audit.run") as mock_run:
            exit_code = wiring_audit.main()

        assert exit_code == 1
        mock_run.assert_not_called()

    def test_write_with_ack_calls_run_write_true(self, monkeypatch):
        monkeypatch.setenv("STOPSHOW_ACK", "1")
        monkeypatch.setattr("sys.argv", ["wiring_audit.py", "--write"])

        with patch("scripts.remediation.wiring_audit.run", return_value=0) as mock_run:
            exit_code = wiring_audit.main()

        assert exit_code == 0
        mock_run.assert_called_once_with(write=True)
