param(
    [switch]$SkipCanary
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Invoke-Docker {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)

    & docker @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "docker $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
    }
}

function Get-DockerServerVersion {
    $stdoutPath = [IO.Path]::GetTempFileName()
    $stderrPath = [IO.Path]::GetTempFileName()
    try {
        $process = Start-Process -FilePath "docker" `
            -ArgumentList @("info", "--format", "{{.ServerVersion}}") `
            -RedirectStandardOutput $stdoutPath `
            -RedirectStandardError $stderrPath `
            -WindowStyle Hidden `
            -PassThru
        if (-not $process.WaitForExit(15000)) {
            Stop-Process -Id $process.Id -Force
            throw "Docker daemon health check timed out after 15 seconds"
        }

        $stdoutRaw = Get-Content -LiteralPath $stdoutPath -Raw
        $stderrRaw = Get-Content -LiteralPath $stderrPath -Raw
        $stdout = if ($null -eq $stdoutRaw) { "" } else { $stdoutRaw.Trim() }
        $stderr = if ($null -eq $stderrRaw) { "" } else { $stderrRaw.Trim() }
        if ($stdout -notmatch '^\d+\.\d+') {
            throw "Docker daemon is unavailable: $stdout $stderr"
        }
        return $stdout
    }
    finally {
        Remove-Item -LiteralPath $stdoutPath, $stderrPath -Force -ErrorAction SilentlyContinue
    }
}

$serverVersion = Get-DockerServerVersion
Write-Host "Docker server: $serverVersion"

Push-Location $repoRoot
try {
    Invoke-Docker build --progress=plain `
        --file candidates/opencode/Dockerfile.source `
        --tag blackbox-eval/opencode-source:1.18.1 `
        candidates/opencode/vendor/opencode

    Invoke-Docker build --progress=plain `
        --file candidates/openclaude/Dockerfile.source `
        --tag blackbox-eval/openclaude-source:0.24.0 `
        candidates/openclaude/vendor/openclaude

    $opencodeVersion = (& docker run --rm blackbox-eval/opencode-source:1.18.1 --version).Trim()
    if ($LASTEXITCODE -ne 0 -or $opencodeVersion -ne "1.18.1") {
        throw "Unexpected OpenCode image version: $opencodeVersion"
    }

    $openclaudeVersion = (& docker run --rm blackbox-eval/openclaude-source:0.24.0 --version).Trim()
    if ($LASTEXITCODE -ne 0 -or $openclaudeVersion -notmatch '^0\.24\.0') {
        throw "Unexpected OpenClaude image version: $openclaudeVersion"
    }

    if ($SkipCanary) {
        Write-Host "Image builds and version checks passed; model canaries skipped."
        return
    }

    if (-not $env:LLM_API_KEY) {
        $env:LLM_API_KEY = [Environment]::GetEnvironmentVariable("LLM_API_KEY", "User")
    }
    if ([string]::IsNullOrWhiteSpace($env:LLM_API_KEY)) {
        throw "LLM_API_KEY is unavailable"
    }

    $canaryDir = (Resolve-Path "candidates/opencode/docker-canary").Path
    $opencodeCanary = (& docker run --rm `
        --env LLM_API_KEY `
        --mount "type=bind,src=$canaryDir,dst=/workspace,readonly" `
        blackbox-eval/opencode-source:1.18.1 `
        run --pure --dir /workspace --format json `
        --model deepseek/deepseek-v4-pro `
        "Return exactly OK." 2>&1 | Out-String)
    if ($LASTEXITCODE -ne 0 -or $opencodeCanary -notmatch 'OK') {
        throw "OpenCode DeepSeek Canary failed: $opencodeCanary"
    }

    $previousOpenAIKey = $env:OPENAI_API_KEY
    try {
        $env:OPENAI_API_KEY = $env:LLM_API_KEY
        $openclaudeCanary = (& docker run --rm `
            --env OPENAI_API_KEY `
            --env CLAUDE_CODE_USE_OPENAI=1 `
            --env OPENAI_BASE_URL=https://api.deepseek.com/v1 `
            --env OPENAI_MODEL=deepseek-v4-pro `
            --env OPENCLAUDE_CONFIG_DIR=/tmp/openclaude-config `
            blackbox-eval/openclaude-source:0.24.0 `
            -p "Return exactly OK." --output-format json --bare `
            --no-session-persistence --tools Read 2>&1 | Out-String)
    }
    finally {
        $env:OPENAI_API_KEY = $previousOpenAIKey
    }
    if ($LASTEXITCODE -ne 0 -or $openclaudeCanary -notmatch 'OK') {
        throw "OpenClaude DeepSeek Canary failed: $openclaudeCanary"
    }

    Write-Host "OpenCode and OpenClaude image builds, versions, and DeepSeek canaries passed."
}
finally {
    Pop-Location
}
