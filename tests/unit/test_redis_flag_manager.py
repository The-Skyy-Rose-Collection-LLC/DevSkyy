"""Unit tests for RedisFlagManager."""
import json
import pytest
from unittest.mock import MagicMock, patch
from core.feature_flags.flag_manager import FlagManager, FeatureFlag


class TestRedisFlagManager:
    def test_fallback_to_memory_when_no_redis(self):
        """Should work as regular FlagManager when Redis is unavailable."""
        from core.feature_flags.flag_manager import RedisFlagManager
        mgr = RedisFlagManager(redis_url="")
        flag = FeatureFlag(name="test", enabled=True)
        mgr.set_flag(flag)
        assert mgr.is_enabled("test") is True

    def test_set_flag_persists_to_redis(self):
        """set_flag should write to Redis when available."""
        from core.feature_flags.flag_manager import RedisFlagManager
        mgr = RedisFlagManager(redis_url="redis://localhost:6379")
        mock_redis = MagicMock()
        mgr._redis = mock_redis

        flag = FeatureFlag(name="new_feature", enabled=True, rollout_percentage=50)
        mgr.set_flag(flag)

        mock_redis.hset.assert_called_once()
        call_args = mock_redis.hset.call_args
        assert call_args[0][0] == "feature_flags"
        assert call_args[0][1] == "new_feature"

    def test_is_enabled_loads_from_redis(self):
        """is_enabled should load flag from Redis if not in memory."""
        from core.feature_flags.flag_manager import RedisFlagManager
        mgr = RedisFlagManager(redis_url="redis://localhost:6379")
        mock_redis = MagicMock()
        mock_redis.hget.return_value = json.dumps({
            "name": "cached_flag",
            "enabled": True,
            "rollout_percentage": 100,
            "enabled_for_users": [],
            "disabled_for_users": [],
            "kill_switch": False,
        })
        mgr._redis = mock_redis

        result = mgr.is_enabled("cached_flag")
        assert result is True
        mock_redis.hget.assert_called_once_with("feature_flags", "cached_flag")

    def test_delete_flag_removes_from_redis(self):
        """delete_flag should remove from both memory and Redis."""
        from core.feature_flags.flag_manager import RedisFlagManager
        mgr = RedisFlagManager(redis_url="redis://localhost:6379")
        mock_redis = MagicMock()
        mgr._redis = mock_redis

        flag = FeatureFlag(name="to_delete", enabled=True)
        mgr._flags["to_delete"] = flag
        mgr.delete_flag("to_delete")

        assert "to_delete" not in mgr._flags
        mock_redis.hdel.assert_called_once_with("feature_flags", "to_delete")
