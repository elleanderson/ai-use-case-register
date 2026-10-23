"""Indicative EU AI Act triage and governance gap checks.

This is a first-pass sort to help a team see where to look first. It is not
legal advice, and a real classification needs someone qualified to read the
use case against the Act itself.

Dates reflect the AI Act as amended by the Digital Omnibus, Regulation (EU)
2026/1744: Annex III high-risk duties apply from 2 December 2027, high-risk AI
in regulated products from 2 August 2028, and the Article 50 transparency
duties have applied since 2 August 2026.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

PROHIBITED = {
    "subliminal-manipulation": "manipulative or deceptive techniques that cause significant harm",
    "exploits-vulnerabilities": "exploiting vulnerabilities due to age, disability or circumstances",
    "social-scoring": "social scoring that leads to unfair treatment",
    "emotion-recognition-at-work-or-school": "emotion recognition in the workplace or in education",
    "biometric-categorisation-sensitive": "biometric categorisation that infers sensitive traits",
    "untargeted-face-scraping": "untargeted scraping of facial images for recognition databases",
    "predictive-policing-profiling": "predicting crime from profiling alone",
    "realtime-remote-biometric-id": "real-time remote biometric identification in public spaces",
}
ANNEX_III = {
    "biometrics": "Biometrics",
    "critical-infrastructure": "Critical infrastructure",
    "education": "Education and vocational training",
    "employment": "Employment and workers management",
    "essential-services": "Access to essential public and private services",
    "credit": "Access to essential services: creditworthiness",
    "insurance": "Access to essential services: life and health insurance",
    "law-enforcement": "Law enforcement",
    "migration": "Migration, asylum and border control",
    "justice": "Administration of justice",
    "democratic-processes": "Democratic processes",
}
TRANSPARENCY = {"chatbot", "generates-synthetic-media", "deepfakes", "emotion-recognition"}

CATEGORY_ORDER = ["prohibited", "high-risk", "transparency", "minimal"]
CATEGORY_LABEL = {
    "prohibited": "Prohibited Practice",
    "high-risk": "High Risk",
    "transparency": "Transparency Duties",
    "minimal": "Minimal Risk",
}


@dataclass
class Triage:
    category: str
    basis: str
    applies_from: str
    gaps: list[tuple[str, str]] = field(default_factory=list)  # (severity, message)

    @property
    def label(self) -> str:
        return CATEGORY_LABEL[self.category]


def classify(uc: dict) -> tuple[str, str, str]:
    practices = set(uc.get("practices", []))
    banned = sorted(practices & set(PROHIBITED))
    if banned:
        return "prohibited", "Article 5: " + "; ".join(PROHIBITED[p] for p in banned), "2 February 2025"
    domain = uc.get("domain", "general")
    if domain == "safety-component":
        return "high-risk", "Article 6(1): safety component of a regulated product", "2 August 2028"
    if domain in ANNEX_III:
        basis = f"Article 6(2) and Annex III: {ANNEX_III[domain]}"
        if uc["decision_role"] == "assists":
            basis += ". It may qualify for the Article 6(3) exemption if it only performs a narrow preparatory task, so record your reasoning."
        return "high-risk", basis, "2 December 2027"
    if practices & TRANSPARENCY:
        return "transparency", "Article 50: people must know when they're dealing with AI or AI-made content", "2 August 2026"
    return "minimal", "No specific AI Act duties beyond AI literacy, though good practice still applies", "2 February 2025 (AI literacy)"


def gaps(uc: dict, category: str, today: dt.date) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    live = uc["status"] in {"pilot", "live"}
    practices = set(uc.get("practices", []))
    data, oversight, evals, tr = uc["data"], uc["human_oversight"], uc["evals"], uc["transparency"]

    if category == "prohibited":
        out.append(("stop", "This practice is banned in the EU. Stop or redesign before any further work."))
    if category == "high-risk":
        if oversight["level"] in {"none", "flagged-only"} and uc["decision_role"] == "decides":
            out.append(("high", "Automated decisions in a high-risk area need meaningful human oversight (Article 14)."))
        if not evals.get("in_place"):
            out.append(("high", "High-risk systems need documented accuracy and robustness testing (Article 15). Set up evals."))
        if not tr.get("people_told"):
            out.append(("high", "Tell the people affected that AI is involved in decisions about them."))
    if category == "transparency" and not tr.get("people_told"):
        out.append(("high", "Article 50: make it clear that people are dealing with AI or AI-made content."))
    if "generates-synthetic-media" in practices and not tr.get("content_marked"):
        out.append(("medium", "Mark generated images, audio or video in a machine-readable way (Article 50(2))."))
    if data.get("personal_data") and not data.get("dpia_done"):
        severity = "high" if data.get("special_category") or category in {"high-risk", "prohibited"} else "medium"
        out.append((severity, "Personal data with no data protection impact assessment on record (UK GDPR and EU GDPR Article 35)."))
    if live and not evals.get("in_place") and category != "high-risk":
        out.append(("medium", "Live or in pilot with no evals. Nobody can show it's working as intended."))
    target, last = evals.get("pass_rate_target"), evals.get("last_pass_rate")
    if target is not None and last is not None and last < target:
        out.append(("medium", f"Eval pass rate {last:.0%} is below its {target:.0%} target."))
    if live and oversight["level"] == "none" and set(uc["users"]) & {"customers", "public", "children", "patients", "job-applicants"}:
        out.append(("medium", "No human oversight on something people outside the organisation rely on."))
    next_review = dt.date.fromisoformat(str(uc["review"]["next_review"]))
    if next_review < today and uc["status"] != "retired":
        out.append(("low", f"Review overdue since {next_review.day} {next_review:%B %Y}."))
    return out


def triage(uc: dict, today: dt.date | None = None) -> Triage:
    category, basis, applies = classify(uc)
    return Triage(category, basis, applies, gaps(uc, category, today or dt.date.today()))
