import datetime as dt
from pathlib import Path

import pytest

from aireg import classify, load_register, triage, validate

ROOT = Path(__file__).resolve().parents[1]
TODAY = dt.date(2026, 10, 23)


def base(**over):
    uc = {
        "id": "AI-100", "name": "Test", "owner": "Owner", "purpose": "A purpose long enough to pass validation.",
        "status": "live", "users": ["staff"], "decision_role": "assists", "domain": "general", "practices": [],
        "model": {"source": "vendor-api", "name": "m"}, "data": {"personal_data": False},
        "human_oversight": {"level": "every-output"}, "evals": {"in_place": True},
        "transparency": {"people_told": True}, "review": {"last_reviewed": "2026-10-01", "next_review": "2027-01-01"},
    }
    uc.update(over)
    return uc


def test_sample_register_is_valid():
    assert validate(load_register(ROOT / "register")) == []


def test_schema_catches_mistakes():
    bad = base(status="launched", id="AI-1")
    errors = validate([(Path("bad.yaml"), bad)])
    assert any("status" in e for e in errors) and any("id" in e for e in errors)


def test_prohibited_practice():
    cat, basis, applies = classify(base(practices=["emotion-recognition-at-work-or-school"]))
    assert cat == "prohibited" and "Article 5" in basis and applies == "2 February 2025"


@pytest.mark.parametrize("domain", ["employment", "credit", "education", "insurance"])
def test_annex_iii_domains_are_high_risk_from_december_2027(domain):
    cat, _, applies = classify(base(domain=domain))
    assert cat == "high-risk" and applies == "2 December 2027"


def test_assisting_in_a_high_risk_area_mentions_the_exemption():
    _, basis, _ = classify(base(domain="employment", decision_role="assists"))
    assert "6(3)" in basis


def test_product_safety_components_from_august_2028():
    assert classify(base(domain="safety-component"))[2] == "2 August 2028"


def test_chatbots_have_transparency_duties():
    assert classify(base(practices=["chatbot"]))[0] == "transparency"


def test_ordinary_tools_are_minimal():
    assert classify(base())[0] == "minimal"


def test_gaps():
    t = triage(base(domain="credit", decision_role="decides", human_oversight={"level": "none"},
                    data={"personal_data": True, "dpia_done": False}, evals={"in_place": False},
                    review={"last_reviewed": "2026-01-01", "next_review": "2026-06-01"}), TODAY)
    messages = " ".join(m for _, m in t.gaps)
    assert "Article 14" in messages and "Article 15" in messages and "impact assessment" in messages and "overdue" in messages


def test_below_target_evals():
    t = triage(base(evals={"in_place": True, "pass_rate_target": 0.9, "last_pass_rate": 0.8}), TODAY)
    assert any("below" in m for _, m in t.gaps)


def test_a_well_run_use_case_has_no_gaps():
    assert triage(base(), TODAY).gaps == []
