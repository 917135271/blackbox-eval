# oh-my-pi Adapter

The GATE3 runner installs the generated business Skills under
`<workspace>/.omp/skills`, copies the three controlled subagent definitions and
the native audit hook from `.omp/`, and mounts `shared/` as the common control
runtime.

The project `.omp/mcp.json` and the user-level `models.yml` are generated per
task so task IDs, experiment groups, paths, and secrets are never baked into
this adapter.

Business behavior comes from the generated `skills/` and `shared/` directories.
Edit the canonical shared core instead of those generated copies.
