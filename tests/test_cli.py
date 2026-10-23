from pathlib import Path

from aireg.cli import main

ROOT = Path(__file__).resolve().parents[1]


def test_validate(capsys):
    assert main(["validate", str(ROOT / "register")]) == 0


def test_report_writes_files_and_fails_on_prohibited(tmp_path):
    code = main(["report", str(ROOT / "register"), "--out", str(tmp_path), "--today", "2026-10-23"])
    assert code == 1  # the sample register contains a prohibited idea, on purpose
    assert (tmp_path / "index.html").read_text().count('class="card"') == 7
    assert "Gaps to Close" in (tmp_path / "register.md").read_text()


def test_report_can_be_told_not_to_fail(tmp_path):
    assert main(["report", str(ROOT / "register"), "--out", str(tmp_path), "--fail-on", "never"]) == 0
