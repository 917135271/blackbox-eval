from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SHARED = ROOT / "shared-audit-core"
CONTROL_MCP = ROOT / "control-mcp"
ADAPTERS = {
    "claude-code-best": ROOT / "adapters" / "claude-code-best" / "securities-expense-audit",
    "codex": ROOT / "adapters" / "codex" / "securities-expense-audit",
    "openclaude": ROOT / "adapters" / "openclaude" / "securities-expense-audit",
    "opencode": ROOT / "adapters" / "opencode" / "securities-expense-audit",
    "oh-my-pi": ROOT / "adapters" / "oh-my-pi" / "securities-expense-audit",
}
GENERATED_NAMES = ("skills", "shared")


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): file_hash(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    }


def safe_remove_generated(adapter: Path, name: str) -> None:
    target = (adapter / name).resolve()
    adapter_root = adapter.resolve()
    if target.parent != adapter_root or target.name not in GENERATED_NAMES:
        raise ValueError(f"refusing to remove unexpected path: {target}")
    if target.exists():
        shutil.rmtree(target)


def build_adapter(name: str, adapter: Path, canonical_hashes: dict[str, str]) -> dict[str, Any]:
    adapter.mkdir(parents=True, exist_ok=True)
    for generated in GENERATED_NAMES:
        safe_remove_generated(adapter, generated)

    shutil.copytree(SHARED / "skills", adapter / "skills")
    shared_target = adapter / "shared"
    for directory in ("routing", "references", "schemas", "scripts"):
        shutil.copytree(SHARED / directory, shared_target / "shared-audit-core" / directory)
    shutil.copytree(CONTROL_MCP, shared_target / "control-mcp")

    built_hashes = tree_hashes(adapter / "skills")
    if canonical_hashes != built_hashes:
        raise ValueError(f"skill copy hash mismatch for {name}")
    manifest = {
        "adapter": name,
        "shared_core_version": "0.1.0",
        "canonical_skill_hashes": canonical_hashes,
        "generated_shared_hashes": tree_hashes(shared_target),
    }
    manifest_path = adapter / "build_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "adapter": name,
        "skill_count": sum(1 for path in (adapter / "skills").iterdir() if path.is_dir()),
        "manifest": manifest_path.relative_to(ROOT).as_posix(),
    }


def main() -> None:
    canonical_hashes = tree_hashes(SHARED / "skills")
    results = [build_adapter(name, path, canonical_hashes) for name, path in ADAPTERS.items()]
    print(json.dumps({"status": "pass", "adapters": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
