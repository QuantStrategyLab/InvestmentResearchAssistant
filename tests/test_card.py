"""Research-card contract tests. Inputs are synthetic and are not market data."""

import unittest
from datetime import datetime, timezone

from ira.card import (
    ABSENCE_NOT_PROOF_MARKERS,
    instrument_id,
    validate_card,
)


def _time(day: str) -> str:
    return f"{day}T00:00:00Z"


def valid_card(**overrides):
    card = {
        "as_of": _time("2026-11-20"),
        "source_times": [
            {
                "role": "published",
                "at": _time("2026-11-18"),
                "url": "https://example.test/issuer/release",
            },
            {
                "role": "retrieved",
                "at": _time("2026-11-20"),
                "url": "https://example.test/issuer/release",
            },
        ],
        "ticker": "SYNTH",
        "exchange": "XNAS",
        "claim": "Synthetic issuer page states a fact used only by this contract test.",
        "evidence_state": "supported",
        "primary_evidence": [
            {
                "url": "https://example.test/issuer/release",
                "note": "synthetic primary page",
            }
        ],
        "counter_evidence": [],
        "confidence_reason": (
            "The synthetic primary page was retrieved and no contrary source was supplied."
        ),
        "missing_data": [],
        "invalidation": "A later synthetic primary page that contradicts the claim.",
        "next_review": "2026-11-27",
        "execution_allowed": False,
    }
    card.update(overrides)
    return card


class ResearchCardContractTest(unittest.TestCase):
    def test_valid_synthetic_card_has_no_errors(self):
        self.assertEqual(validate_card(valid_card()), [])

    def test_invalid_inputs_fail_before_any_interpretation(self):
        for bad in (None, [], "card", 3):
            errors = validate_card(bad)
            self.assertTrue(errors)
            self.assertIn("card must be an object", errors)

    def test_missing_required_field_fails(self):
        card = valid_card()
        del card["exchange"]
        errors = validate_card(card)
        self.assertTrue(any("exchange" in error for error in errors))

    def test_execution_allowed_must_be_boolean_false(self):
        for value in (True, "false", "False", 0, None):
            errors = validate_card(valid_card(execution_allowed=value))
            self.assertTrue(errors, value)
            self.assertTrue(
                any("execution_allowed" in error for error in errors),
                errors,
            )

    def test_order_and_account_fields_are_rejected_at_any_depth(self):
        forbidden = (
            {"order": {"side": "buy"}},
            {"account": "synthetic"},
            {"target_shares": 10},
            {"nested": {"broker": "none"}},
            {"meta": {"holdings": []}},
        )
        for extra in forbidden:
            card = valid_card()
            card.update(extra)
            errors = validate_card(card)
            self.assertTrue(errors, extra)
            self.assertTrue(
                any("forbidden" in error or "unknown" in error for error in errors),
                errors,
            )

    def test_same_ticker_on_different_exchanges_are_different_instruments(self):
        nasdaq = instrument_id("synth", "xnas")
        nyse = instrument_id("SYNTH", "XNYS")
        self.assertNotEqual(nasdaq, nyse)
        self.assertEqual(nasdaq, "SYNTH@XNAS")
        first = validate_card(valid_card(exchange="XNAS"))
        second = validate_card(valid_card(exchange="XNYS"))
        self.assertEqual(first, [])
        self.assertEqual(second, [])

    def test_supported_claim_requires_exact_https_primary_url(self):
        errors = validate_card(
            valid_card(primary_evidence=[{"url": "not a url"}])
        )
        self.assertTrue(any("primary_evidence" in error for error in errors))

    def test_missing_primary_source_cannot_become_supported(self):
        errors = validate_card(valid_card(primary_evidence=[]))
        self.assertTrue(any("primary_evidence" in error for error in errors))

    def test_unavailable_card_must_say_absence_is_not_proof(self):
        errors = validate_card(
            valid_card(
                evidence_state="unavailable",
                primary_evidence=[],
                missing_data=["no news exists"],
            )
        )
        self.assertTrue(errors)
        ok = validate_card(
            valid_card(
                evidence_state="unavailable",
                primary_evidence=[],
                source_times=[
                    {
                        "role": "retrieved",
                        "at": _time("2026-11-20"),
                        "url": "https://example.test/search",
                    }
                ],
                missing_data=[
                    "Search was not retrieved. " + ABSENCE_NOT_PROOF_MARKERS[1]
                ],
            )
        )
        self.assertEqual(ok, [])

    def test_blocked_card_abstains_without_fabricating_a_source(self):
        errors = validate_card(
            valid_card(
                evidence_state="blocked",
                primary_evidence=[],
                claim="Connector refused the read.",
                confidence_reason="The public search connector returned a block.",
                missing_data=["Read blocked. " + ABSENCE_NOT_PROOF_MARKERS[0]],
                source_times=[
                    {
                        "role": "retrieved",
                        "at": _time("2026-11-20"),
                        "url": "https://example.test/search",
                    }
                ],
            )
        )
        self.assertEqual(errors, [])

    def test_old_news_cannot_stay_supported(self):
        old = valid_card(
            source_times=[
                {
                    "role": "published",
                    "at": _time("2025-01-01"),
                    "url": "https://example.test/issuer/old",
                },
                {
                    "role": "retrieved",
                    "at": _time("2026-11-20"),
                    "url": "https://example.test/issuer/old",
                },
            ],
            primary_evidence=[{"url": "https://example.test/issuer/old"}],
        )
        self.assertTrue(any("stale" in error for error in validate_card(old)))
        stale = dict(old)
        stale["evidence_state"] = "stale"
        stale["confidence_reason"] = (
            "The only synthetic page is older than the freshness window."
        )
        self.assertEqual(validate_card(stale), [])

    def test_syndicated_copy_cannot_stay_supported(self):
        syndicated = valid_card(
            canonical_url="https://example.test/issuer/release",
            primary_evidence=[
                {"url": "https://example.test/wire/repost", "note": "syndication"}
            ],
            source_times=[
                {
                    "role": "published",
                    "at": _time("2026-11-18"),
                    "url": "https://example.test/issuer/release",
                },
                {
                    "role": "retrieved",
                    "at": _time("2026-11-20"),
                    "url": "https://example.test/wire/repost",
                },
            ],
        )
        self.assertTrue(any("duplicate" in error for error in validate_card(syndicated)))
        syndicated["evidence_state"] = "duplicate"
        syndicated["confidence_reason"] = (
            "This page repeats the synthetic issuer page and is not a new source."
        )
        self.assertEqual(validate_card(syndicated), [])

    def test_counterevidence_prevents_a_supported_state(self):
        conflicted = valid_card(
            counter_evidence=[
                {
                    "url": "https://example.test/issuer/correction",
                    "note": "synthetic correction",
                }
            ]
        )
        self.assertTrue(
            any("contradict" in error for error in validate_card(conflicted))
        )
        conflicted["evidence_state"] = "contradicted"
        conflicted["confidence_reason"] = (
            "The synthetic issuer page and the synthetic correction disagree."
        )
        self.assertEqual(validate_card(conflicted), [])

    def test_rumor_cannot_use_verified_language(self):
        rumor = valid_card(
            evidence_state="rumor",
            primary_evidence=[{"url": "https://example.test/social/post"}],
            source_times=[
                {
                    "role": "published",
                    "at": _time("2026-11-19"),
                    "url": "https://example.test/social/post",
                },
                {
                    "role": "retrieved",
                    "at": _time("2026-11-20"),
                    "url": "https://example.test/social/post",
                },
            ],
            confidence_reason="Verified by the social post.",
        )
        self.assertTrue(any("rumor" in error for error in validate_card(rumor)))
        rumor["confidence_reason"] = (
            "A synthetic social post is unverified until a primary source is retrieved."
        )
        self.assertEqual(validate_card(rumor), [])

    def test_confidence_reason_rejects_a_bare_probability(self):
        for reason in ("0.82", "82%", "HIGH", "概率: 0.8"):
            errors = validate_card(valid_card(confidence_reason=reason))
            self.assertTrue(errors, reason)

    def test_financial_figure_requires_source_and_both_times(self):
        figure = {
            "name": "synthetic_revenue",
            "value": "1",
            "unit": "USD",
            "source_url": "https://example.test/issuer/release",
            "published_at": _time("2026-11-18"),
            "retrieved_at": _time("2026-11-20"),
        }
        self.assertEqual(
            validate_card(valid_card(financial_figures=[figure])),
            [],
        )
        broken = dict(figure)
        del broken["published_at"]
        self.assertTrue(validate_card(valid_card(financial_figures=[broken])))
        placeholder = dict(figure)
        placeholder["value"] = "TBD"
        self.assertTrue(validate_card(valid_card(financial_figures=[placeholder])))

    def test_published_and_retrieved_times_stay_distinct(self):
        card = valid_card(
            source_times=[
                {
                    "role": "retrieved",
                    "at": _time("2026-11-20"),
                    "url": "https://example.test/issuer/release",
                }
            ]
        )
        self.assertTrue(any("published" in error for error in validate_card(card)))

    def test_rumor_allows_an_explicit_denial_of_verification(self):
        denied = valid_card(
            evidence_state="rumor",
            primary_evidence=[{"url": "https://example.test/social/post"}],
            source_times=[
                {
                    "role": "published",
                    "at": _time("2026-11-19"),
                    "url": "https://example.test/social/post",
                },
                {
                    "role": "retrieved",
                    "at": _time("2026-11-20"),
                    "url": "https://example.test/social/post",
                },
            ],
            confidence_reason="This rumor is not confirmed by any primary source.",
        )
        self.assertEqual(validate_card(denied), [])
        denied["confidence_reason"] = "这条传闻尚未获得一手来源支持，不能视为已证实。"
        self.assertEqual(validate_card(denied), [])

    def test_non_string_evidence_state_returns_errors(self):
        for value in ([], {}):
            errors = validate_card(valid_card(evidence_state=value))
            self.assertTrue(errors, value)
            self.assertTrue(any("evidence_state" in error for error in errors), errors)

    def test_unrelated_recent_time_does_not_refresh_the_primary_url(self):
        card = valid_card(
            primary_evidence=[{"url": "https://example.test/issuer/old"}],
            source_times=[
                {
                    "role": "published",
                    "at": _time("2025-01-01"),
                    "url": "https://example.test/issuer/old",
                },
                {
                    "role": "retrieved",
                    "at": _time("2026-11-20"),
                    "url": "https://example.test/issuer/old",
                },
                {
                    "role": "published",
                    "at": _time("2026-11-19"),
                    "url": "https://example.test/other",
                },
                {
                    "role": "retrieved",
                    "at": _time("2026-11-20"),
                    "url": "https://example.test/other",
                },
            ],
        )
        self.assertTrue(any("stale" in error for error in validate_card(card)))

    def test_primary_url_needs_its_own_retrieved_time(self):
        card = valid_card(
            source_times=[
                {
                    "role": "published",
                    "at": _time("2026-11-18"),
                    "url": "https://example.test/issuer/release",
                },
                {
                    "role": "retrieved",
                    "at": _time("2026-11-20"),
                    "url": "https://example.test/other",
                },
            ]
        )
        errors = validate_card(card)
        self.assertTrue(any("retrieved" in error for error in errors), errors)

    def test_abstain_is_allowed_when_the_claim_is_not_asserted(self):
        errors = validate_card(
            valid_card(
                evidence_state="abstain",
                claim="No research conclusion is asserted.",
                primary_evidence=[],
                confidence_reason="Inputs were insufficient, so this card abstains.",
                missing_data=["Primary page missing. " + ABSENCE_NOT_PROOF_MARKERS[1]],
                source_times=[
                    {
                        "role": "retrieved",
                        "at": _time("2026-11-20"),
                        "url": "https://example.test/search",
                    }
                ],
            )
        )
        self.assertEqual(errors, [])


class ClockTest(unittest.TestCase):
    def test_validator_uses_the_card_clock_not_the_wall_clock(self):
        card = valid_card()
        first = validate_card(card, now=datetime(2030, 1, 1, tzinfo=timezone.utc))
        second = validate_card(card, now=datetime(1999, 1, 1, tzinfo=timezone.utc))
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
