from __future__ import annotations

import json
from pathlib import Path

from audit_trace import finalize_governance_artifacts


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs" / "gate3_development"


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def main() -> int:
    updated = 0
    failures: list[str] = []
    for run_result_path in sorted(RUN_ROOT.glob("*-*/DEV-*/run_result.json")):
        base = run_result_path.parent
        workspace = base / "workspace"
        run_result = load_json(run_result_path)
        run_manifest = load_json(workspace / "run_manifest.json")
        try:
            finalize_governance_artifacts(
                workspace=workspace,
                task_id=str(run_result["task_id"]),
                experiment_group=str(run_result["group"]),
                timeout_seconds=int(run_manifest["timeout_seconds"]),
                elapsed_seconds=float(run_result["elapsed_seconds"]),
            )
            updated += 1
        except Exception as exc:
            failures.append(f"{run_result_path.relative_to(ROOT).as_posix()}: {exc}")

    print(json.dumps({"updated": updated, "failures": failures}, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
