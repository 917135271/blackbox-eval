from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SOURCE_ADAPTERS = ROOT / "adapters"
TARGET_ADAPTERS = ROOT / "scripted-adapters"
SCRIPTED_CORE = ROOT / "scripted-audit-core"
SHARED_CORE = ROOT / "shared-audit-core"
BASE_CONTROL_MCP = ROOT / "control-mcp" / "audit_control_mcp.py"
SCRIPTED_CONTROL_MCP = ROOT / "scripted-control-mcp" / "audit_control_mcp.py"
sys.path.insert(0, str(SCRIPTED_CORE / "scripts"))

from scripted_workflow_core import SCRIPTED_WORKFLOW_VERSION  # noqa: E402
FRAMEWORKS = (
    "claude-code-best",
    "codex",
    "openclaude",
    "opencode",
    "oh-my-pi",
    "pi-agent",
)
GENERATED = {"skills", "shared", "build_manifest.json"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): _sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    }


def _safe_reset(target: Path) -> None:
    resolved = target.resolve()
    expected = TARGET_ADAPTERS.resolve()
    if resolved.parent != expected or resolved.name not in FRAMEWORKS:
        raise ValueError(f"refusing to reset unexpected scripted adapter: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)


def _copy_static_adapter(source: Path, target: Path) -> None:
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        if relative.parts and relative.parts[0] in GENERATED:
            continue
        destination = target / relative
        if path.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
        elif path.is_file():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)


def build_adapter(framework: str) -> dict[str, Any]:
    source = SOURCE_ADAPTERS / framework / "securities-expense-audit"
    target_root = TARGET_ADAPTERS / framework
    target = target_root / "securities-expense-audit"
    _safe_reset(target_root)
    target.mkdir(parents=True)
    _copy_static_adapter(source, target)

    shutil.copytree(SCRIPTED_CORE / "skills", target / "skills")
    shared = target / "shared"
    for directory in ("routing", "references", "schemas", "scripts"):
        shutil.copytree(SHARED_CORE / directory, shared / "shared-audit-core" / directory)
    shutil.copytree(SCRIPTED_CORE / "references", shared / "scripted-audit-core" / "references")
    shutil.copytree(SCRIPTED_CORE / "scripts", shared / "scripted-audit-core" / "scripts")
    control_target = shared / "control-mcp"
    control_target.mkdir(parents=True)
    shutil.copy2(BASE_CONTROL_MCP, control_target / "_base_audit_control_mcp.py")
    shutil.copy2(SCRIPTED_CONTROL_MCP, control_target / "audit_control_mcp.py")

    manifest = {
        "adapter": framework,
        "experiment_group": "scripted-enhanced",
        "scripted_workflow_version": SCRIPTED_WORKFLOW_VERSION,
        "skill_count": sum(1 for path in (target / "skills").iterdir() if path.is_dir()),
        "skill_hashes": _tree_hashes(target / "skills"),
        "shared_hashes": _tree_hashes(shared),
    }
    manifest_path = target / "build_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    manifests = [build_adapter(framework) for framework in FRAMEWORKS]
    print(json.dumps({"status": "pass", "adapters": manifests}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
