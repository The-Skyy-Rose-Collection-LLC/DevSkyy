"""Unit tests for scripts/remediation/register_webhooks.py.

`diff_webhooks` is pure and takes already-fetched JSON — no network there.
The `main()` tests mock every `requests` call so this suite never touches
live WooCommerce.
"""

import sys
from unittest.mock import MagicMock, patch

from scripts.remediation.register_webhooks import diff_webhooks, main

DELIVERY_URL = "https://www.devskyy.app/api/webhooks/woocommerce"

REQUIRED_ENV = {
    "WP_BASE_URL": "https://example.test",
    "WC_CONSUMER_KEY": "ck_test",
    "WC_CONSUMER_SECRET": "cs_test",
    "WP_WEBHOOK_SECRET": "whsecret",
}


class TestDiffWebhooks:
    def test_all_desired_missing_when_none_exist(self):
        to_create, already_ok = diff_webhooks([], {"product.created": DELIVERY_URL})
        assert to_create == [{"topic": "product.created", "delivery_url": DELIVERY_URL}]
        assert already_ok == []

    def test_active_exact_match_counts_as_already_ok(self):
        existing = [{"topic": "product.created", "delivery_url": DELIVERY_URL, "status": "active"}]
        to_create, already_ok = diff_webhooks(existing, {"product.created": DELIVERY_URL})
        assert to_create == []
        assert already_ok == [{"topic": "product.created", "delivery_url": DELIVERY_URL}]

    def test_inactive_match_does_not_block_a_create(self):
        existing = [
            {"topic": "product.created", "delivery_url": DELIVERY_URL, "status": "inactive"}
        ]
        to_create, already_ok = diff_webhooks(existing, {"product.created": DELIVERY_URL})
        assert to_create == [{"topic": "product.created", "delivery_url": DELIVERY_URL}]
        assert already_ok == []

    def test_same_topic_different_url_is_recreated(self):
        existing = [
            {
                "topic": "product.created",
                "delivery_url": "https://old.example/hook",
                "status": "active",
            }
        ]
        to_create, already_ok = diff_webhooks(existing, {"product.created": DELIVERY_URL})
        assert to_create == [{"topic": "product.created", "delivery_url": DELIVERY_URL}]
        assert already_ok == []

    def test_multiple_topics_split_correctly(self):
        existing = [{"topic": "order.created", "delivery_url": DELIVERY_URL, "status": "active"}]
        desired = {"product.created": DELIVERY_URL, "order.created": DELIVERY_URL}
        to_create, already_ok = diff_webhooks(existing, desired)
        assert {e["topic"] for e in to_create} == {"product.created"}
        assert {e["topic"] for e in already_ok} == {"order.created"}


class TestMainNeverHitsLiveNetwork:
    def test_dry_run_default_refuses_without_execute(self, monkeypatch):
        for var, val in REQUIRED_ENV.items():
            monkeypatch.setenv(var, val)
        monkeypatch.delenv("STOPSHOW_ACK", raising=False)
        monkeypatch.setattr(sys, "argv", ["register_webhooks.py"])

        fake_response = MagicMock()
        fake_response.json.return_value = []
        fake_response.raise_for_status.return_value = None

        with (
            patch(
                "scripts.remediation.register_webhooks.requests.get", return_value=fake_response
            ) as mock_get,
            patch("scripts.remediation.register_webhooks.requests.post") as mock_post,
        ):
            exit_code = main()

        assert exit_code == 1  # STOPSHOW gate — no --execute
        mock_get.assert_called_once()
        mock_post.assert_not_called()

    def test_execute_without_ack_still_refuses(self, monkeypatch):
        for var, val in REQUIRED_ENV.items():
            monkeypatch.setenv(var, val)
        monkeypatch.delenv("STOPSHOW_ACK", raising=False)
        monkeypatch.setattr(sys, "argv", ["register_webhooks.py", "--execute"])

        fake_response = MagicMock()
        fake_response.json.return_value = []
        fake_response.raise_for_status.return_value = None

        with (
            patch("scripts.remediation.register_webhooks.requests.get", return_value=fake_response),
            patch("scripts.remediation.register_webhooks.requests.post") as mock_post,
        ):
            exit_code = main()

        assert exit_code == 1
        mock_post.assert_not_called()

    def test_execute_with_ack_posts_the_batch_create(self, monkeypatch):
        for var, val in REQUIRED_ENV.items():
            monkeypatch.setenv(var, val)
        monkeypatch.setenv("STOPSHOW_ACK", "1")
        monkeypatch.setattr(sys, "argv", ["register_webhooks.py", "--execute"])

        fake_list_response = MagicMock()
        fake_list_response.json.return_value = []  # nothing registered yet
        fake_list_response.raise_for_status.return_value = None

        fake_batch_response = MagicMock()
        fake_batch_response.json.return_value = {
            "create": [{"id": 1, "topic": "product.created"}],
        }
        fake_batch_response.raise_for_status.return_value = None

        with (
            patch(
                "scripts.remediation.register_webhooks.requests.get",
                return_value=fake_list_response,
            ),
            patch(
                "scripts.remediation.register_webhooks.requests.post",
                return_value=fake_batch_response,
            ) as mock_post,
        ):
            exit_code = main()

        assert exit_code == 0
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        created_topics = {entry["topic"] for entry in kwargs["json"]["create"]}
        assert created_topics == {
            "product.created",
            "product.updated",
            "product.deleted",
            "order.created",
            "order.updated",
        }
        # The webhook secret travels in the request body, never printed.
        assert all(entry["secret"] == "whsecret" for entry in kwargs["json"]["create"])

    def test_missing_env_exits_before_any_request(self, monkeypatch):
        for var in REQUIRED_ENV:
            monkeypatch.delenv(var, raising=False)
        monkeypatch.setattr(sys, "argv", ["register_webhooks.py"])

        with patch("scripts.remediation.register_webhooks.requests.get") as mock_get:
            try:
                main()
            except SystemExit:
                pass
        mock_get.assert_not_called()
