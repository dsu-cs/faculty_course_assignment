from __future__ import annotations

from pathlib import Path

import pytest

from fca.preferences import services


@pytest.mark.django_db
def test_get_previously_taught_course_keys_reads_archived_section_history(
    monkeypatch: pytest.MonkeyPatch,
    settings,
    tmp_path: Path,
):
    history_root = tmp_path / "BIM Scraper" / "previous_semesters"
    term_dir = history_root / "2025_Fall"
    term_dir.mkdir(parents=True)
    (term_dir / "section_data.csv").write_text(
        "CRN,Sub,Num,Seq,Crd,Desc,Seats,Waitlist,Days,Time,Room,Faculty,workload_if_full,workload_per_student,special_workload\n"
        "10001,CSC,150,D01,3,Computer Science I,20/25,0,MWF,0900-0950,EH 101,Ada Lovelace,3,0.12,\n"
        "10002,MATH,201,D01,3,Calculus I,18/25,0,MWF,1000-1050,SC 201,Grace Hopper,3,0.12,\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        services,
        "SECTION_HISTORY_DIR_CANDIDATES",
        (history_root,),
    )

    assert services.get_previously_taught_course_keys("Ada Lovelace") == {"CSC-150"}
    assert services.get_previously_taught_course_keys("Grace Hopper") == {"MATH-201"}
    assert services.get_previously_taught_course_keys("Unknown Faculty") == set()