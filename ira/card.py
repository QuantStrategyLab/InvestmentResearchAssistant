"""Deterministic checks for a public research card.

The card clock is `as_of`. `now` is accepted so callers can pass a test clock,
and the result does not depend on the wall clock.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

ABSENCE_NOT_PROOF_MARKERS = (
    "不能证明没有新闻",
    "not proof that no news exists",
)

MAX_SUPPORTED_AGE_DAYS = 14

REQUIRED_FIELDS = (
    "as_of",
    "source_times",
    "ticker",
    "exchange",
    "claim",
    "evidence_state",
    "primary_evidence",
    "counter_evidence",
    "confidence_reason",
    "missing_data",
    "invalidation",
    "next_review",
    "execution_allowed",
)

OPTIONAL_FIELDS = (
    "financial_figures",
    "canonical_url",
    "synthetic",
)

EVIDENCE_STATES = frozenset(
    {
        "supported",
        "unavailable",
        "blocked",
        "stale",
        "rumor",
        "duplicate",
        "contradicted",
        "abstain",
    }
)

SOURCED_STATES = frozenset(
    {"supported", "stale", "rumor", "duplicate", "contradicted"}
)

OPEN_STATES = frozenset({"unavailable", "blocked", "abstain"})

FORBIDDEN_KEYS = frozenset(
    {
        "account",
        "account_id",
        "broker",
        "holdings",
        "limit_price",
        "notional",
        "order",
        "orders",
        "position",
        "positions",
        "quantity",
        "shares",
        "side",
        "stop_price",
        "target_shares",
    }
)

PLACEHOLDER_VALUES = frozenset(
    {"", "tbd", "todo", "placeholder", "n/a", "na", "...", "xxx"}
)

_BARE_PROBABILITY = re.compile(
    r"(?:\d+(?:\.\d+)?%?|high|medium|low|概率\s*[:：]\s*\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
_AFFIRMATIVE_VERIFIED = re.compile(r"\b(verified|confirmed)\b", re.IGNORECASE)
_ENGLISH_NEGATION = re.compile(r"\b(not|never|no|without)\b|n't\s*$", re.IGNORECASE)
_CHINESE_VERIFIED = re.compile(r"已验证|已核实|已证实")
_CHINESE_NEGATION = ("未", "不能", "不是", "并非", "没有", "不可", "不算")


def instrument_id(ticker: str, exchange: str) -> str:
    """Return the exchange-qualified identity. Case does not make a new symbol."""
    return f"{ticker.strip().upper()}@{exchange.strip().upper()}"


def validate_card(card: Any, now: datetime | None = None) -> list[str]:
    """Return human-readable errors. An empty list means the card is accepted."""
    del now  # Freshness is measured from as_of so a later rerun stays stable.
    if not isinstance(card, dict):
        return ["card must be an object"]

    errors: list[str] = []
    errors.extend(_forbidden_keys(card, "$"))
    for key in sorted(card):
        if key not in REQUIRED_FIELDS and key not in OPTIONAL_FIELDS:
            if key.lower() not in FORBIDDEN_KEYS:
                errors.append(f"unknown field: {key}")

    for field in REQUIRED_FIELDS:
        if field not in card:
            errors.append(f"missing field: {field}")
    if errors:
        return errors

    as_of = _parse_time(card["as_of"], "as_of", errors)
    next_review = _parse_date(card["next_review"], "next_review", errors)
    if as_of and next_review and next_review < as_of.date():
        errors.append("next_review is before as_of")

    if card["execution_allowed"] is not False:
        errors.append("execution_allowed must be boolean false")

    ticker = card["ticker"]
    exchange = card["exchange"]
    if not isinstance(ticker, str) or not ticker.strip():
        errors.append("ticker must be a non-empty string")
    if not isinstance(exchange, str) or not exchange.strip():
        errors.append("exchange must be a non-empty string")

    claim = card["claim"]
    if not isinstance(claim, str) or not claim.strip():
        errors.append("claim must be a non-empty string")

    state = card["evidence_state"]
    if not isinstance(state, str) or state not in EVIDENCE_STATES:
        errors.append("evidence_state is not a known state")
        return errors

    times = _source_times(card["source_times"], errors)
    primary = _evidence_list(card["primary_evidence"], "primary_evidence", errors)
    counter = _evidence_list(card["counter_evidence"], "counter_evidence", errors)
    _confidence(card["confidence_reason"], state, errors)
    missing = _string_list(card["missing_data"], "missing_data", errors)
    if not isinstance(card["invalidation"], str) or not card["invalidation"].strip():
        errors.append("invalidation must be a non-empty string")

    if state in SOURCED_STATES:
        if not any(item["role"] == "published" for item in times):
            errors.append("source_times must include a published time")
        if not any(item["role"] == "retrieved" for item in times):
            errors.append("source_times must include a retrieved time")
        if not primary:
            errors.append("primary_evidence requires an exact https URL")
    elif state in OPEN_STATES:
        if not any(item["role"] == "retrieved" for item in times):
            errors.append("source_times must include a retrieved time")
        if not primary and not any(marker in " ".join(missing) for marker in ABSENCE_NOT_PROOF_MARKERS):
            errors.append(
                "missing primary source is not proof that no news exists; "
                "missing_data must say so"
            )

    if state == "supported" and counter:
        errors.append("counter_evidence contradicts a supported state")
    if state == "contradicted" and not counter:
        errors.append("contradicted state requires counter_evidence")

    canonical = card.get("canonical_url")
    primary_urls = {item["url"] for item in primary}
    if canonical is not None:
        if not _https_url(canonical):
            errors.append("canonical_url must be an exact https URL")
        elif primary_urls and canonical not in primary_urls and state != "duplicate":
            errors.append("syndication must use evidence_state duplicate")
    elif state == "duplicate":
        errors.append("duplicate state requires canonical_url")

    if state == "supported":
        _primary_freshness(primary_urls, times, as_of, errors)

    for item in times:
        if as_of is not None and item["at"] > as_of and item["role"] == "retrieved":
            errors.append("retrieved time is after as_of")

    if "financial_figures" in card:
        _figures(card["financial_figures"], errors)
    if "synthetic" in card and card["synthetic"] is not True:
        errors.append("synthetic must be true when present")

    return errors


def _forbidden_keys(value: Any, path: str) -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if isinstance(key, str) and key.lower() in FORBIDDEN_KEYS:
                errors.append(f"forbidden field: {path}.{key}")
            errors.extend(_forbidden_keys(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_forbidden_keys(child, f"{path}[{index}]"))
    return errors


def _parse_time(value: Any, label: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str):
        errors.append(f"{label} must be an ISO-8601 time")
        return None
    text = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        errors.append(f"{label} must be an ISO-8601 time")
        return None
    if parsed.tzinfo is None:
        errors.append(f"{label} must include a timezone")
        return None
    return parsed.astimezone(timezone.utc)


def _parse_date(value: Any, label: str, errors: list[str]):
    if not isinstance(value, str):
        errors.append(f"{label} must be a date")
        return None
    try:
        if len(value) == 10:
            return datetime.fromisoformat(value).date()
        parsed = _parse_time(value, label, errors)
        return None if parsed is None else parsed.date()
    except ValueError:
        errors.append(f"{label} must be a date")
        return None


def _https_url(value: Any) -> bool:
    if not isinstance(value, str) or any(char.isspace() for char in value):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def _source_times(value: Any, errors: list[str]) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        errors.append("source_times must be a list")
        return []
    items: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        label = f"source_times[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        role = item.get("role")
        if role not in {"published", "retrieved"}:
            errors.append(f"{label} role must be published or retrieved")
            continue
        at = _parse_time(item.get("at"), f"{label}.at", errors)
        url = item.get("url")
        if not _https_url(url):
            errors.append(f"{label}.url must be an exact https URL")
            continue
        if at is not None:
            items.append({"role": role, "at": at, "url": url})
    return items


def _evidence_list(value: Any, label: str, errors: list[str]) -> list[dict[str, str]]:
    if not isinstance(value, list):
        errors.append(f"{label} must be a list")
        return []
    items: list[dict[str, str]] = []
    for index, item in enumerate(value):
        item_label = f"{label}[{index}]"
        if not isinstance(item, dict) or not _https_url(item.get("url")):
            errors.append(f"{item_label} requires an exact https URL")
            continue
        note = item.get("note")
        if note is not None and not isinstance(note, str):
            errors.append(f"{item_label}.note must be a string")
            continue
        items.append({"url": item["url"]})
    return items


def _string_list(value: Any, label: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        errors.append(f"{label} must be a list of strings")
        return []
    return value


def _confidence(value: Any, state: str, errors: list[str]) -> None:
    if not isinstance(value, str) or len(value.strip()) < 20:
        errors.append("confidence_reason must explain the evidence in words")
        return
    if _BARE_PROBABILITY.fullmatch(value.strip()):
        errors.append("confidence_reason must not be a bare probability or score")
    if state == "rumor" and _affirms_verification(value):
        errors.append("rumor state cannot be described as verified")


def _affirms_verification(text: str) -> bool:
    for match in _AFFIRMATIVE_VERIFIED.finditer(text):
        prefix = text[max(0, match.start() - 32) : match.start()]
        if _ENGLISH_NEGATION.search(prefix):
            continue
        return True
    for match in _CHINESE_VERIFIED.finditer(text):
        prefix = text[max(0, match.start() - 16) : match.start()]
        if any(token in prefix for token in _CHINESE_NEGATION):
            continue
        return True
    return False


def _primary_freshness(
    primary_urls: set[str],
    times: list[dict[str, Any]],
    as_of: datetime | None,
    errors: list[str],
) -> None:
    for url in sorted(primary_urls):
        published = [
            item["at"]
            for item in times
            if item["role"] == "published" and item["url"] == url
        ]
        retrieved = [
            item["at"]
            for item in times
            if item["role"] == "retrieved" and item["url"] == url
        ]
        if not published:
            errors.append(f"primary_evidence {url} has no published time")
        if not retrieved:
            errors.append(f"primary_evidence {url} has no retrieved time")
        if not published or as_of is None:
            continue
        newest = max(published)
        age_days = (as_of.date() - newest.date()).days
        if age_days > MAX_SUPPORTED_AGE_DAYS:
            errors.append(f"published source is stale: {age_days} days before as_of")
        if newest > as_of:
            errors.append("published time is after as_of")


def _figures(value: Any, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append("financial_figures must be a list")
        return
    required = ("name", "value", "unit", "source_url", "published_at", "retrieved_at")
    for index, figure in enumerate(value):
        label = f"financial_figures[{index}]"
        if not isinstance(figure, dict):
            errors.append(f"{label} must be an object")
            continue
        for key in figure:
            if key not in required:
                errors.append(f"unknown field: {label}.{key}")
        for key in required:
            if key not in figure:
                errors.append(f"{label} missing {key}")
        if "value" in figure:
            rendered = str(figure["value"]).strip().lower()
            if rendered in PLACEHOLDER_VALUES:
                errors.append(f"{label} value is a placeholder")
        if "source_url" in figure and not _https_url(figure["source_url"]):
            errors.append(f"{label}.source_url must be an exact https URL")
        published = (
            _parse_time(figure["published_at"], f"{label}.published_at", errors)
            if "published_at" in figure
            else None
        )
        retrieved = (
            _parse_time(figure["retrieved_at"], f"{label}.retrieved_at", errors)
            if "retrieved_at" in figure
            else None
        )
        if published and retrieved and published > retrieved:
            errors.append(f"{label} published_at is after retrieved_at")
