"""
Tests for Feature Flag System
==============================

Tests FlagManager evaluation logic, rollout percentages,
user targeting, and A/B test consistency.
"""

import pytest

from core.feature_flags import FeatureFlag, FlagManager


@pytest.fixture
def manager() -> FlagManager:
    """Fresh FlagManager for each test."""
    return FlagManager()


@pytest.mark.unit
class TestFeatureFlag:
    """Tests for FeatureFlag dataclass validation"""

    def test_default_flag_is_enabled_100_percent(self):
        """A flag with no arguments is enabled for all users."""
        flag = FeatureFlag(name="my_feature")
        assert flag.enabled is True
        assert flag.rollout_percentage == 100

    def test_invalid_percentage_raises(self):
        """rollout_percentage outside 0–100 raises ValueError."""
        with pytest.raises(ValueError, match="rollout_percentage"):
            FeatureFlag(name="bad_flag", rollout_percentage=101)

        with pytest.raises(ValueError, match="rollout_percentage"):
            FeatureFlag(name="bad_flag", rollout_percentage=-1)


@pytest.mark.unit
class TestFlagManagerCRUD:
    """Tests for flag creation and management"""

    def test_create_flag_stores_flag(self, manager):
        """create_flag registers the flag so it can be retrieved."""
        manager.create_flag("my_feature", rollout_percentage=50)
        flag = manager.get_flag("my_feature")
        assert flag is not None
        assert flag.rollout_percentage == 50

    def test_get_nonexistent_flag_returns_none(self, manager):
        """get_flag returns None for unknown flags."""
        assert manager.get_flag("nonexistent") is None

    def test_enable_and_disable_toggle_global_switch(self, manager):
        """enable()/disable() control the global kill switch."""
        manager.create_flag("beta_feature", enabled=False)
        assert manager.is_enabled("beta_feature") is False

        manager.enable("beta_feature")
        assert manager.is_enabled("beta_feature") is True

        manager.disable("beta_feature")
        assert manager.is_enabled("beta_feature") is False

    def test_set_rollout_updates_percentage(self, manager):
        """set_rollout() updates rollout_percentage on an existing flag."""
        manager.create_flag("gradual_rollout", rollout_percentage=5)
        manager.set_rollout("gradual_rollout", 50)
        assert manager.get_flag("gradual_rollout").rollout_percentage == 50

    def test_set_rollout_invalid_percentage_raises(self, manager):
        """set_rollout validates 0–100 range."""
        manager.create_flag("my_flag")
        with pytest.raises(ValueError):
            manager.set_rollout("my_flag", 150)

    def test_create_flag_overwrites_existing(self, manager):
        """Creating a flag with the same name replaces it entirely."""
        manager.create_flag("feature", rollout_percentage=25)
        manager.create_flag("feature", rollout_percentage=75)
        assert manager.get_flag("feature").rollout_percentage == 75

    def test_list_flags_returns_all(self, manager):
        """list_flags() returns every registered flag."""
        manager.create_flag("flag_a")
        manager.create_flag("flag_b")
        flags = manager.list_flags()
        names = {f["name"] for f in flags}
        assert "flag_a" in names
        assert "flag_b" in names


@pytest.mark.unit
class TestFlagEvaluation:
    """Tests for is_enabled() evaluation logic"""

    def test_unknown_flag_returns_false(self, manager):
        """Unregistered flags default to False — safe by default."""
        assert manager.is_enabled("unknown_flag", user_id="user-1") is False

    def test_disabled_flag_returns_false_for_all(self, manager):
        """Global kill switch overrides user targeting."""
        manager.create_flag("killed", enabled=False, rollout_percentage=100)
        assert manager.is_enabled("killed", user_id="vip-user") is False

    def test_100_percent_rollout_enabled_for_all(self, manager):
        """100% rollout is enabled for all users without hashing."""
        manager.create_flag("full_rollout", rollout_percentage=100)
        assert manager.is_enabled("full_rollout", user_id="anyone") is True
        assert manager.is_enabled("full_rollout", user_id="someone-else") is True

    def test_0_percent_rollout_disabled_for_all(self, manager):
        """0% rollout is disabled for all users."""
        manager.create_flag("no_rollout", rollout_percentage=0)
        assert manager.is_enabled("no_rollout", user_id="anyone") is False

    def test_enabled_for_users_overrides_rollout(self, manager):
        """Explicitly whitelisted users always get the feature."""
        manager.create_flag(
            "internal_feature",
            rollout_percentage=0,   # Disabled for everyone...
            enabled_for_users=["dev@devskyy.com"],  # ...except this user
        )
        assert manager.is_enabled("internal_feature", user_id="dev@devskyy.com") is True
        assert manager.is_enabled("internal_feature", user_id="customer@example.com") is False

    def test_disabled_for_users_blocks_access(self, manager):
        """Explicitly blacklisted users never get the feature."""
        manager.create_flag(
            "new_checkout",
            rollout_percentage=100,   # Enabled for everyone...
            disabled_for_users=["blocked@example.com"],  # ...except this user
        )
        assert manager.is_enabled("new_checkout", user_id="blocked@example.com") is False
        assert manager.is_enabled("new_checkout", user_id="normal@example.com") is True

    def test_no_user_id_with_partial_rollout_returns_false(self, manager):
        """
        Without a user_id, partial rollouts conservatively return False.
        We can't do sticky assignment without an identity.
        """
        manager.create_flag("partial", rollout_percentage=50)
        assert manager.is_enabled("partial", user_id=None) is False

    def test_consistent_hash_gives_sticky_assignment(self, manager):
        """
        The same user always gets the same flag value — crucial for A/B tests.
        """
        manager.create_flag("ab_test", rollout_percentage=50)
        user_id = "consistent-user-99"

        results = [manager.is_enabled("ab_test", user_id=user_id) for _ in range(10)]
        # All 10 evaluations must agree — no flipping
        assert all(r == results[0] for r in results)

    def test_hash_bucket_distributes_uniformly(self, manager):
        """
        Verify the hash function produces ~50% True for a 50% rollout
        across a large sample of users.
        """
        manager.create_flag("half_rollout", rollout_percentage=50)

        users = [f"user-{i}" for i in range(1000)]
        enabled_count = sum(
            1 for u in users if manager.is_enabled("half_rollout", user_id=u)
        )

        # Expect roughly 50% — allow ±8% tolerance
        assert 420 <= enabled_count <= 580, (
            f"Expected ~500/1000 enabled, got {enabled_count}"
        )

    def test_different_flags_hash_independently(self, manager):
        """
        The same user can be in different buckets for different flags.
        This is the point of including flag_name in the hash key.
        """
        manager.create_flag("flag_x", rollout_percentage=50)
        manager.create_flag("flag_y", rollout_percentage=50)

        # Find a user where the two flags differ
        for i in range(200):
            user_id = f"probe-{i}"
            x = manager.is_enabled("flag_x", user_id=user_id)
            y = manager.is_enabled("flag_y", user_id=user_id)
            if x != y:
                break  # Found a user in different buckets — flags are independent
        else:
            pytest.fail("Could not find a user with different flag_x and flag_y values")


@pytest.mark.unit
class TestBulkLoading:
    """Tests for load_from_dict"""

    def test_load_from_dict_registers_all_flags(self, manager):
        """load_from_dict creates all flags from the config."""
        config = {
            "graphql_products": {"rollout_percentage": 25, "description": "GraphQL layer"},
            "new_checkout": {"enabled": False},
        }
        manager.load_from_dict(config)

        assert manager.get_flag("graphql_products").rollout_percentage == 25
        assert manager.get_flag("new_checkout").enabled is False
