"""Batch-прогон 10 контрольных входов через реальный LLM.

Читает inputs/*.txt, обрабатывает каждый файл через ProcessingService,
пишет:
    - data/results.csv         — сводка по всем кейсам
    - data/processing.db       — журнал аудита (пишется самим сервисом)
    - data/results/<name>.json — полный JSON-результат по каждому кейсу

Сборка сервиса — через src.bootstrap.build_service (единый composition root
с FastAPI-путём). Перед прогоном старые JSON в data/results/ удаляются,
чтобы не оставалось мусора от удалённых кейсов.

Запуск:
    python run_batch.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from src.bootstrap import build_service
from src.config import BASE_DIR, get_settings
from src.services.processor import ProcessingService


INPUTS_DIR: Path = BASE_DIR / "inputs"
RESULTS_DIR: Path = BASE_DIR / "data" / "results"
CSV_PATH: Path = BASE_DIR / "data" / "results.csv"


def _iter_inputs() -> list[Path]:
    return sorted(p for p in INPUTS_DIR.glob("*.txt") if p.is_file())


def _clean_old_results() -> int:
    """Удалить старые JSON-результаты. Возвращает количество удалённых."""
    if not RESULTS_DIR.is_dir():
        return 0
    removed = 0
    for old in RESULTS_DIR.glob("*.json"):
        old.unlink()
        removed += 1
    return removed


def _build_processing_service() -> ProcessingService:
    """Тонкая обёртка для тестируемости: легко подменить в тестах."""
    return build_service(get_settings())


def main() -> int:
    if not INPUTS_DIR.is_dir():
        print(f"[error] Папка с входами не найдена: {INPUTS_DIR}")
        return 2

    files = _iter_inputs()
    if not files:
        print(f"[error] В {INPUTS_DIR} нет .txt файлов")
        return 2

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)

    removed = _clean_old_results()
    if removed:
        print(f"[clean] Удалено старых результатов: {removed}")

    service = _build_processing_service()
    rows: list[dict[str, object]] = []

    print(f"[batch] Найдено входов: {len(files)}")
    for path in files:
        text = path.read_text(encoding="utf-8")
        record = service.process(text)
        result = record.result

        # Полный JSON по кейсу — для демонстрации и отчёта
        case_json = {
            "file": path.name,
            "record_id": record.id,
            "status": record.status.value,
            "error": record.error,
            "model": record.model,
            "raw_input": text,
            "result": result.model_dump(mode="json") if result else None,
        }
        (RESULTS_DIR / f"{path.stem}.json").write_text(
            json.dumps(case_json, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        rows.append(
            {
                "file": path.name,
                "record_id": record.id,
                "status": record.status.value,
                "category": result.category.value if result else "",
                "priority": result.priority.value if result else "",
                "confidence": result.confidence.value if result else "",
                "escalate": bool(result.escalate) if result else True,
                "error": record.error or "",
            }
        )
        flag = "ESCALATED" if rows[-1]["escalate"] else "OK"
        print(f"  [{flag:9}] {path.name:32} id={record.id}")

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    processed = sum(1 for r in rows if r["status"] == "processed")
    escalated = sum(1 for r in rows if r["status"] == "escalated")
    errored = sum(1 for r in rows if r["status"] == "error")

    print()
    print(f"[summary] processed={processed}  escalated={escalated}  error={errored}")
    print(f"[csv]     {CSV_PATH}")
    print(f"[json]    {RESULTS_DIR}")
    print(f"[db]      {get_settings().DB_PATH}")
    return 0 if errored == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())