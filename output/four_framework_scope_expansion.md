# Four-Framework Scope Expansion

## Decision

The next formal evaluation compares Claude Code Best, Codex, OpenClaude, and OpenCode. Each framework has a baseline and an enhanced group, producing eight groups in total.

The formal task set is reduced from 55 tasks to 15 representative cases. All eight groups run the same 15 cases once, for 120 formal executions. The five case families each retain three complementary cases. Development tasks remain unscored and are used only for tool, routing, and submission debugging.

## Case-By-Case Rubric Contract

Every formal case has its own 100-point rubric with explicit expected facts, record sets, policy evidence, reasoning requirements, partial-credit anchors, and critical score caps. The frozen set contains 85 criterion rows.

| Case family | Cases |
| --- | ---: |
| Policy and version | 3 |
| Record audit | 3 |
| Full-year audit | 3 |
| Clean trap | 3 |
| Retrieval and report | 3 |

The candidate sees only the runnable prompt. The rubric, Ground Truth, judge implementation, and other candidate trajectories remain outside the isolated task workspace.

## Framework Status

| Framework | Source/runtime status | Domain adapter |
| --- | --- | --- |
| Claude Code Best | Existing source GATE3 passed | 7 shared Skills built |
| Codex | Existing source GATE3 passed | 7 shared Skills built |
| OpenClaude | Source image `0.24.0` built; container version and DeepSeek Canary passed | 7 shared Skills built |
| OpenCode | Source-runtime image `1.18.1` built; container version and DeepSeek Canary passed | 7 shared Skills built |
All four adapters are generated from one canonical shared core and have identical Skill hashes. The completed earlier GATE3 artifacts remain historical checkpoints. Formal GATE4 must wait until all newly added frameworks finish the same 12-development-case baseline/enhanced checks.

## Verification

- Formal dataset validator: pass, 15 cases and 85 criteria.
- Formal dataset excludes `ground_truth_lookup`: pass.
- Four adapter build: pass, 7 Skills per adapter with identical hashes.
- Domain enhancement tests: 18 passed.
- Case rubric tests: 3 passed.
- Secret remains environment-only through `LLM_API_KEY`.
