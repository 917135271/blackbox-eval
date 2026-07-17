# Oh My Pi source build

The upstream source is pinned as the `candidates/oh-my-pi` Git submodule. Initialize it after cloning:

```powershell
git submodule update --init --recursive candidates/oh-my-pi
```

Build the locked source tree with the project-owned Dockerfile:

```powershell
docker build --progress=plain `
  --file candidates/oh-my-pi-build/Dockerfile.source `
  --tag blackbox-eval/oh-my-pi-source:17.0.1 `
  candidates/oh-my-pi
```

The exact upstream commit, Bun lock hash, Dockerfile hash, image identifier, and DeepSeek canary result are recorded in `config/source_eval_lock.yaml`.
