"""Deterministic fraud / chargeback risk scorer (advisory only).

Closes agent gap #4 (Fraud/Chargeback), which previously existed only as a prompt
bullet in ``agents/commerce_agent.py`` and ``agents/support_agent.py`` — no implementation.

Design (mirrors ``monitoring/fleet_observer.py``):
- **Pure + deterministic.** Same order in → same assessment out. No LLM, no network, no clock
  except an explicit fallback when an order omits its own ``date_created`` for velocity.
- **Never raises.** Every field read is defensive; the scoring body is fully guarded so a
  malformed order yields a safe ``score == 0`` assessment rather than an exception.
- **Advisory.** It returns a score, a level, and a recommended action ("approve" / "review" /
  "hold"). It NEVER cancels, refunds, or writes to WooCommerce. A human (or a STOP-AND-SHOW
  gated action) acts on the recommendation.
- **Founder-tunable.** Every threshold and the disposable-domain list are constructor args.
- **PII-careful.** Signal details mask email/IP and omit full customer names; the assessment
  payload is internal-only but still avoids embedding raw PII.

Signals are industry-standard chargeback predictors: AVS/CVV mismatch, billing↔shipping
country mismatch, order velocity, disposable email, guest high-value, recipient-name mismatch.
Weights sum, clamp to 100, and map to a level band.
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import IntEnum
from typing import Any

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Public types
# --------------------------------------------------------------------------- #


class RiskLevel(IntEnum):
    """Ordered risk bands. Higher = more likely fraudulent."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass(frozen=True)
class RiskSignal:
    """One triggered rule and the points it contributed."""

    rule: str
    weight: int
    detail: str


@dataclass(frozen=True)
class FraudAssessment:
    """The verdict for a single order. Immutable, JSON-serializable via ``as_dict``."""

    order_id: str | None
    score: int  # 0-100
    level: RiskLevel
    signals: tuple[RiskSignal, ...]
    recommended_action: str  # "approve" | "review" | "hold"

    def as_dict(self) -> dict[str, Any]:
        return {
            "order_id": self.order_id,
            "score": self.score,
            "level": self.level.name,
            "recommended_action": self.recommended_action,
            "signals": [
                {"rule": s.rule, "weight": s.weight, "detail": s.detail} for s in self.signals
            ],
        }


# --------------------------------------------------------------------------- #
# Defaults
# --------------------------------------------------------------------------- #

# Per-rule point weights. Summed, then clamped to 100. Calibrated so that a benign
# international gift (country mismatch + name mismatch + guest + high value) lands at 45
# (MEDIUM/approve), while any gateway-verified signal (AVS/CVV) pushes to HIGH/CRITICAL.
_WEIGHTS: dict[str, int] = {
    "cvv_failure": 35,
    "avs_mismatch": 30,
    "disposable_email": 30,
    "velocity_email": 25,
    "velocity_ip": 20,
    "billing_shipping_country_mismatch": 15,
    "guest_high_value": 10,
    "high_value_order": 10,
    "mismatched_recipient_name": 10,
    "address_mismatch": 8,
    "email_gibberish": 8,
}

# Score band edges → level. Kept module-level so ``level_for`` is a pure staticmethod.
_LEVEL_BANDS: tuple[tuple[int, RiskLevel], ...] = (
    (80, RiskLevel.CRITICAL),
    (50, RiskLevel.HIGH),
    (20, RiskLevel.MEDIUM),
    (0, RiskLevel.LOW),
)

_ACTION_BY_LEVEL: dict[RiskLevel, str] = {
    RiskLevel.LOW: "approve",
    RiskLevel.MEDIUM: "approve",
    RiskLevel.HIGH: "review",
    RiskLevel.CRITICAL: "hold",
}

# Throwaway-email providers. Conservative, well-known set; founder can extend per-instance.
_DEFAULT_DISPOSABLE_DOMAINS: frozenset[str] = frozenset(
    {
        "mailinator.com",
        "guerrillamail.com",
        "10minutemail.com",
        "trashmail.com",
        "yopmail.com",
        "temp-mail.org",
        "tempmail.com",
        "getnada.com",
        "throwawaymail.com",
        "sharklasers.com",
        "maildrop.cc",
        "dispostable.com",
        "fakeinbox.com",
        "mailnesia.com",
        "mintemail.com",
    }
)

_GIBBERISH_MIN_LEN = 8


# --------------------------------------------------------------------------- #
# Defensive field helpers (never raise)
# --------------------------------------------------------------------------- #


def _section(order: dict, key: str) -> dict:
    """Return ``order[key]`` if it is a dict, else an empty dict."""
    value = order.get(key)
    return value if isinstance(value, dict) else {}


def _to_float(value: Any) -> float | None:
    """Parse a money-ish value to a finite float, or None when not parseable/non-finite."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        result = float(value)
    elif isinstance(value, str):
        try:
            result = float(value.strip())
        except (ValueError, AttributeError):
            return None
    else:
        return None
    return result if math.isfinite(result) else None


def _parse_dt(value: Any) -> datetime | None:
    """Parse an ISO-8601 timestamp defensively. Naive timestamps are normalized to UTC so
    aware/naive subtraction never raises (real WooCommerce mixes +00:00 and bare timestamps)."""
    if not isinstance(value, str):
        return None
    raw = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def _email_domain(email: Any) -> str:
    if not isinstance(email, str) or "@" not in email:
        return ""
    return email.rsplit("@", 1)[-1].strip().lower()


def _email_local(email: Any) -> str:
    if not isinstance(email, str) or "@" not in email:
        return ""
    return email.rsplit("@", 1)[0].strip().lower()


def _mask_email(email: str) -> str:
    """Mask an email for logging: keep the domain, redact the local-part."""
    domain = _email_domain(email)
    return f"***@{domain}" if domain else "***"


def _mask_ip(ip: str) -> str:
    """Mask an IP for logging: keep the /24 prefix for IPv4, else fully redact."""
    octets = ip.split(".")
    if len(octets) == 4 and all(o.isdigit() for o in octets):
        return f"{octets[0]}.{octets[1]}.{octets[2]}.x"
    return "***"


def _full_name(section: dict) -> str:
    first = str(section.get("first_name") or "").strip().lower()
    last = str(section.get("last_name") or "").strip().lower()
    return f"{first} {last}".strip()


def _scan_meta(order: dict, needle: str) -> str | None:
    """Search ``meta_data`` (WooCommerce list-of-{key,value}) for a key containing ``needle``."""
    meta = order.get("meta_data")
    if not isinstance(meta, list):
        return None
    for item in meta:
        if not isinstance(item, dict):
            continue
        key = str(item.get("key", "")).lower()
        if needle in key:
            value = item.get("value")
            return str(value) if value is not None else None
    return None


# AVS/CVV result codes that indicate a mismatch / failure (lowercased).
_AVS_BAD = {"n", "no_match", "nomatch", "mismatch", "fail", "failed"}
_CVV_BAD = {"n", "no_match", "nomatch", "fail", "failed", "mismatch"}


def _looks_gibberish(local: str) -> bool:
    """Heuristic: long local-part that is mostly digits reads as machine-generated."""
    if len(local) < _GIBBERISH_MIN_LEN:
        return False
    digits = sum(c.isdigit() for c in local)
    return digits / len(local) >= 0.5


_WS = re.compile(r"\s+")


def _norm_addr(section: dict) -> str:
    parts = [
        str(section.get("address_1") or ""),
        str(section.get("postcode") or ""),
        str(section.get("city") or ""),
    ]
    return _WS.sub(" ", " ".join(parts)).strip().lower()


def _md_cell(value: Any) -> str:
    """Escape a value for a GitHub-flavored-Markdown table cell (no pipe/newline breakout)."""
    return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


# --------------------------------------------------------------------------- #
# Scorer
# --------------------------------------------------------------------------- #


class FraudScorer:
    """Score an order's fraud/chargeback risk from deterministic signals (read-only)."""

    def __init__(
        self,
        *,
        high_value_threshold: float = 500.0,
        mid_value_threshold: float = 250.0,
        velocity_count: int = 3,
        velocity_window_hours: int = 24,
        extra_disposable_domains: tuple[str, ...] = (),
        weights: dict[str, int] | None = None,
    ) -> None:
        self.high_value_threshold = high_value_threshold
        self.mid_value_threshold = mid_value_threshold
        self.velocity_count = velocity_count
        self.velocity_window_hours = velocity_window_hours
        self.disposable_domains = _DEFAULT_DISPOSABLE_DOMAINS | {
            d.lower() for d in extra_disposable_domains
        }
        self.weights = {**_WEIGHTS, **(weights or {})}

    # -- level / action mapping (pure) ------------------------------------- #

    @staticmethod
    def level_for(score: int) -> RiskLevel:
        for edge, level in _LEVEL_BANDS:
            if score >= edge:
                return level
        return RiskLevel.LOW

    @staticmethod
    def action_for(level: RiskLevel) -> str:
        return _ACTION_BY_LEVEL.get(level, "review")

    # -- main entry point -------------------------------------------------- #

    def assess(
        self, order: dict[str, Any], history: list[dict[str, Any]] | None = None
    ) -> FraudAssessment:
        """Return a :class:`FraudAssessment` for ``order``. Never raises."""
        if not isinstance(order, dict):
            return FraudAssessment(None, 0, RiskLevel.LOW, (), "approve")

        order_id = order.get("id")
        order_id_str = str(order_id) if order_id is not None else None

        try:
            signals = self._signals(order, history or [])
            raw = sum(int(s.weight) for s in signals)
        except Exception as exc:  # defense-in-depth: a buggy rule must not break checkout review
            logger.warning("fraud assess fell back to score=0 (order_id=%s): %s", order_id_str, exc)
            signals, raw = (), 0

        score = max(0, min(100, raw))
        level = self.level_for(score)
        return FraudAssessment(
            order_id=order_id_str,
            score=score,
            level=level,
            signals=signals,
            recommended_action=self.action_for(level),
        )

    # -- rules ------------------------------------------------------------- #

    def _signals(self, order: dict, history: list[dict]) -> tuple[RiskSignal, ...]:
        billing = _section(order, "billing")
        shipping = _section(order, "shipping")
        out: list[RiskSignal] = []

        def add(rule: str, detail: str) -> None:
            out.append(RiskSignal(rule=rule, weight=self.weights.get(rule, 0), detail=detail))

        # --- payment-gateway signals --------------------------------------
        if self._cvv_failed(order):
            add("cvv_failure", "CVV/CVC check did not pass")
        if self._avs_mismatch(order):
            add("avs_mismatch", "Address Verification System reported a mismatch")

        # --- email signals -------------------------------------------------
        email = billing.get("email")
        domain = _email_domain(email)
        if domain and domain in self.disposable_domains:
            add("disposable_email", f"Disposable email domain: {domain}")
        elif _looks_gibberish(_email_local(email)):
            add("email_gibberish", "Email local-part looks machine-generated")

        # --- velocity ------------------------------------------------------
        self._velocity_signals(order, billing, history, add)

        # --- geography -----------------------------------------------------
        bill_country = str(billing.get("country") or "").strip().upper()
        ship_country = str(shipping.get("country") or "").strip().upper()
        countries_mismatch = bool(bill_country and ship_country and bill_country != ship_country)
        if countries_mismatch:
            add(
                "billing_shipping_country_mismatch",
                f"Billing {bill_country} != shipping {ship_country}",
            )
        elif bill_country and ship_country:
            # Same country but different street/zip/city.
            bill_addr = _norm_addr(billing)
            ship_addr = _norm_addr(shipping)
            if bill_addr and ship_addr and bill_addr != ship_addr:
                add("address_mismatch", "Billing and shipping addresses differ")

        # --- recipient name (redacted — names are PII) --------------------
        bill_name = _full_name(billing)
        ship_name = _full_name(shipping)
        if bill_name and ship_name and bill_name != ship_name:
            add("mismatched_recipient_name", "Billing name does not match shipping name")

        # --- order value ---------------------------------------------------
        total = _to_float(order.get("total"))
        # Guest only when the gateway explicitly says customer_id == 0. A missing/None id is
        # "unknown", not "guest" — avoids false-positives on partial webhook payloads.
        is_guest = str(order.get("customer_id", "")).strip() == "0"
        if total is not None:
            if total >= self.high_value_threshold:
                add(
                    "high_value_order",
                    f"Order total {total:.2f} >= {self.high_value_threshold:.2f}",
                )
            if is_guest and total >= self.mid_value_threshold:
                add(
                    "guest_high_value",
                    f"Guest checkout with total {total:.2f} >= {self.mid_value_threshold:.2f}",
                )

        return tuple(out)

    def _cvv_failed(self, order: dict) -> bool:
        value = order.get("cvv_result")
        if value is None:
            value = _scan_meta(order, "cvv")
        return isinstance(value, str) and value.strip().lower() in _CVV_BAD

    def _avs_mismatch(self, order: dict) -> bool:
        value = order.get("avs_result")
        if value is None:
            value = _scan_meta(order, "avs")
        return isinstance(value, str) and value.strip().lower() in _AVS_BAD

    def _velocity_signals(self, order, billing, history, add) -> None:
        if not history:
            return
        ref = _parse_dt(order.get("date_created"))
        window = timedelta(hours=self.velocity_window_hours)
        current_id = order.get("id")

        def eligible(hist: dict) -> bool:
            if not isinstance(hist, dict):
                return False
            if current_id is not None and hist.get("id") == current_id:
                return False  # never count the order against itself
            if ref is None:
                return True  # no reference time → count all provided history
            ts = _parse_dt(hist.get("date_created"))
            return ts is not None and timedelta(0) <= (ref - ts) <= window

        window_phrase = "in window" if ref is not None else "(no order timestamp — all counted)"
        order_email = str(billing.get("email") or "").strip().lower()
        order_ip = str(order.get("customer_ip_address") or "").strip()

        if order_email:
            same_email = sum(
                1
                for h in history
                if eligible(h)
                and str(_section(h, "billing").get("email") or "").strip().lower() == order_email
            )
            if same_email >= self.velocity_count:
                add(
                    "velocity_email",
                    f"{same_email} prior orders from {_mask_email(order_email)} {window_phrase}",
                )

        if order_ip:
            same_ip = sum(
                1
                for h in history
                if eligible(h) and str(h.get("customer_ip_address") or "").strip() == order_ip
            )
            if same_ip >= self.velocity_count:
                add(
                    "velocity_ip",
                    f"{same_ip} prior orders from IP {_mask_ip(order_ip)} {window_phrase}",
                )


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #


def format_assessment(assessment: FraudAssessment) -> str:
    """Render a :class:`FraudAssessment` as a markdown summary (for the MCP tool / logs)."""
    lines = [
        f"## Fraud Risk — order {assessment.order_id or 'n/a'}",
        f"Score: **{assessment.score}/100** | Level: **{assessment.level.name}** | "
        f"Action: **{assessment.recommended_action}**",
        "",
    ]
    if not assessment.signals:
        lines.append("No risk signals triggered.")
        return "\n".join(lines)

    lines.append("| Rule | Weight | Detail |")
    lines.append("|------|--------|--------|")
    for s in sorted(assessment.signals, key=lambda x: -x.weight):
        lines.append(f"| {_md_cell(s.rule)} | {_md_cell(s.weight)} | {_md_cell(s.detail)} |")
    return "\n".join(lines)


__all__ = [
    "FraudAssessment",
    "FraudScorer",
    "RiskLevel",
    "RiskSignal",
    "format_assessment",
]
