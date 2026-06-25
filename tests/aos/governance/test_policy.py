"""Tests for PolicyEngine."""

from __future__ import annotations

from aos.governance.policy import PolicyEngine, PolicyRule, PolicyVerdict


class TestEvaluate:
    def test_default_allow(self):
        eng = PolicyEngine()
        d = eng.evaluate({"action": "anything"})
        assert d.verdict == PolicyVerdict.ALLOW
        assert d.matched_rule is None

    def test_default_deny_configurable(self):
        eng = PolicyEngine(default_verdict=PolicyVerdict.DENY)
        d = eng.evaluate({"action": "x"})
        assert d.verdict == PolicyVerdict.DENY

    def test_matching_rule_wins(self):
        eng = PolicyEngine()
        eng.add_rule(
            PolicyRule(
                name="block-prod-writes",
                verdict=PolicyVerdict.DENY,
                match={"target_env": "production", "op": "write"},
                reason="production writes need explicit approval path",
            )
        )
        d = eng.evaluate({"target_env": "production", "op": "write"})
        assert d.verdict == PolicyVerdict.DENY
        assert d.matched_rule == "block-prod-writes"

    def test_non_match_falls_through(self):
        eng = PolicyEngine()
        eng.add_rule(PolicyRule(name="r", verdict=PolicyVerdict.DENY, match={"foo": "bar"}))
        d = eng.evaluate({"foo": "baz"})
        assert d.verdict == PolicyVerdict.ALLOW


class TestPrecedence:
    def test_deny_beats_allow(self):
        eng = PolicyEngine()
        eng.add_rule(PolicyRule(name="allow-all", verdict=PolicyVerdict.ALLOW, match={"x": 1}))
        eng.add_rule(PolicyRule(name="deny-special", verdict=PolicyVerdict.DENY, match={"x": 1}))
        d = eng.evaluate({"x": 1})
        assert d.verdict == PolicyVerdict.DENY
        assert d.matched_rule == "deny-special"

    def test_deny_beats_require_approval(self):
        eng = PolicyEngine()
        eng.add_rule(PolicyRule(name="ra", verdict=PolicyVerdict.REQUIRE_APPROVAL, match={"x": 1}))
        eng.add_rule(PolicyRule(name="d", verdict=PolicyVerdict.DENY, match={"x": 1}))
        d = eng.evaluate({"x": 1})
        assert d.verdict == PolicyVerdict.DENY

    def test_require_approval_beats_allow(self):
        eng = PolicyEngine()
        eng.add_rule(PolicyRule(name="a", verdict=PolicyVerdict.ALLOW, match={"x": 1}))
        eng.add_rule(PolicyRule(name="ra", verdict=PolicyVerdict.REQUIRE_APPROVAL, match={"x": 1}))
        d = eng.evaluate({"x": 1})
        assert d.verdict == PolicyVerdict.REQUIRE_APPROVAL


class TestManagement:
    def test_add_and_remove(self):
        eng = PolicyEngine()
        eng.add_rule(PolicyRule(name="r1", verdict=PolicyVerdict.DENY, match={"a": 1}))
        assert len(eng.rules) == 1
        assert eng.remove_rule("r1")
        assert len(eng.rules) == 0

    def test_remove_missing_returns_false(self):
        eng = PolicyEngine()
        assert not eng.remove_rule("nope")

    def test_rules_immutable_snapshot(self):
        eng = PolicyEngine()
        rule = PolicyRule(name="r", verdict=PolicyVerdict.ALLOW, match={})
        eng.add_rule(rule)
        snap = eng.rules
        eng.add_rule(PolicyRule(name="r2", verdict=PolicyVerdict.ALLOW, match={}))
        assert len(snap) == 1


class TestRuleMatch:
    def test_empty_match_matches_everything(self):
        rule = PolicyRule(name="always", verdict=PolicyVerdict.ALLOW, match={})
        assert rule.matches({"anything": "goes"})

    def test_partial_descriptor_with_full_match_fails(self):
        rule = PolicyRule(name="r", verdict=PolicyVerdict.DENY, match={"a": 1, "b": 2})
        assert not rule.matches({"a": 1})
        assert rule.matches({"a": 1, "b": 2, "c": 3})
