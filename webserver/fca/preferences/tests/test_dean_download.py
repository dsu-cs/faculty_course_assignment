from __future__ import annotations

from pathlib import Path

import pytest
from django.urls import reverse

from fca.preferences import exporters


pytestmark = pytest.mark.django_db


def test_refresh_bim_sections_csv_passes_term_to_scraper(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    captured: dict[str, object] = {}

    class ScraperModule:
        @staticmethod
        def run(*, term=None, output_path=None):
            captured["term"] = term
            captured["output_path"] = output_path
            return output_path

    monkeypatch.setattr(exporters, "_load_module", lambda module_name, module_path: ScraperModule)

    output_path = tmp_path / "sections.csv"
    result = exporters.refresh_bim_sections_csv(output_path, term="2026 Fall")

    assert result == output_path
    assert captured == {
        "term": "2026 Fall",
        "output_path": output_path,
    }


def test_dean_download_get_includes_available_terms(client, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("fca.views.get_available_bim_terms", lambda: ["2026 Summer", "2026 Fall"])
    monkeypatch.setattr("fca.views.get_default_bim_term", lambda terms: "2026 Fall")

    response = client.get(reverse("dean_download"))

    assert response.status_code == 200
    assert response.context["available_terms"] == ["2026 Summer", "2026 Fall"]
    assert response.context["selected_term"] == "2026 Fall"


def test_dean_download_post_passes_selected_term_into_export(client, monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    workbook_path = tmp_path / "faculty_assignment_workbook.xlsx"
    workbook_path.write_bytes(b"test workbook")
    captured: dict[str, object] = {}

    class Artifacts:
        def __init__(self, path: Path):
            self.workbook_path = path

    monkeypatch.setattr("fca.views.get_available_bim_terms", lambda: ["2026 Fall"])
    monkeypatch.setattr("fca.views.get_default_bim_term", lambda terms: "2026 Fall")

    def fake_build_dean_download_artifacts(*, term=None):
        captured["term"] = term
        return Artifacts(workbook_path)

    monkeypatch.setattr("fca.views.build_dean_download_artifacts", fake_build_dean_download_artifacts)

    response = client.post(reverse("dean_download"), data={"bim_term": "2026 Fall"})

    assert response.status_code == 200
    assert captured["term"] == "2026 Fall"
    assert response.get("Content-Disposition") is not None
