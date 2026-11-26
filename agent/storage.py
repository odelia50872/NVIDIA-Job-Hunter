import json
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "seen_jobs.json"

def load_seen_ids() -> set[str]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DB_PATH.exists():
        DB_PATH.write_text("[]", encoding="utf-8")
    try:
        data = json.loads(DB_PATH.read_text(encoding="utf-8"))
        return {str(item) for item in data}
    except (json.JSONDecodeError, OSError):
        raise RuntimeError(f"Could not read deduplication file: {DB_PATH}")

def save_seen_ids(ids: set[str]) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    DB_PATH.write_text(
        json.dumps(sorted(ids), ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
