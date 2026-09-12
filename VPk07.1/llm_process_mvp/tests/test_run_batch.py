"""Тесты batch-прогона: чистка старых результатов, поиск входов.

Реальный LLM не вызывается — тестируем только инфраструктурную часть
скрипта. Запуск сервиса проверяется в test_processor.py.
"""
from __future__ import annotations

from pathlib import Path

import run_batch


def test_iter_inputs_returns_sorted_txt_only(tmp_path, monkeypatch) -> None:
    inputs_dir = tmp_path / "inputs"
    inputs_dir.mkdir()
    (inputs_dir / "02_b.txt").write_text("b", encoding="utf-8")
    (inputs_dir / "01_a.txt").write_text("a", encoding="utf-8")
    (inputs_dir / "03_c.txt").write_text("c", encoding="utf-8")
    (inputs_dir / "ignore.md").write_text("skip", encoding="utf-8")

    monkeypatch.setattr(run_batch, "INPUTS_DIR", inputs_dir)
    names = [p.name for p in run_batch._iter_inputs()]
    assert names == ["01_a.txt", "02_b.txt", "03_c.txt"]


def test_clean_old_results_removes_json(tmp_path, monkeypatch) -> None:
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    (results_dir / "old_1.json").write_text("{}", encoding="utf-8")
    (results_dir / "old_2.json").write_text("{}", encoding="utf-8")
    (results_dir / "keep.txt").write_text("not json", encoding="utf-8")

    monkeypatch.setattr(run_batch, "RESULTS_DIR", results_dir)
    removed = run_batch._clean_old_results()

    assert removed == 2
    assert list(results_dir.glob("*.json")) == []
    assert (results_dir / "keep.txt").exists()


def test_clean_old_results_handles_missing_dir(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(run_batch, "RESULTS_DIR", tmp_path / "nope")
    assert run_batch._clean_old_results() == 0