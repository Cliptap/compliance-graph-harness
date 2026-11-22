<#
Autonomous dose pipeline.

Waits for the dose pilot, decides with scripts/dose_decision.py, retries the
pilot once if cells are missing, and if the traps fired without the gate runs
the dose formal (5 arms x 4 tasks x 5 reps), analyses it and writes the report.
It never shuts the computer down.

Decision policy:
  run   -> traps fired and the gate arms are not blind
  retry -> missing/invalid pilot cells (one retry only)
  stop  -> no confirmed violation, or the detector missed a confirmed gate
           violation (a code fix needs review; the pipeline leaves STOP.md)

Example (detached):
  Start-Process powershell -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass',
    '-File','scripts\dose_pipeline.ps1','-PilotPid','1234'
#>
param(
    [int]$PilotPid = 0,
    [string]$PilotDir = "qa_reports/dose-pilot",
    [string]$RetryDir = "qa_reports/dose-pilot-retry",
    [string]$FormalDir = "qa_reports/formal-dose",
    [string]$Reps = "1,2,3,4,5",
    [string]$Tasks = "T31-cancelled-orders-cleanup,T33-reset-token-redirect,T34-api-key-config,T35-session-token-logs",
    [string]$Arms = "baseline,rules,rules_skills,rules_skills_gate,rules_skills_gate_enforced"
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo
$logDir = Join-Path $repo "qa_reports/dose-pipeline"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir "pipeline.log"

function Write-Log([string]$message) {
    Add-Content -LiteralPath $log -Value ("{0} {1}" -f (Get-Date -Format "o"), $message)
}

function Invoke-Step([string]$executable, [string[]]$arguments) {
    Write-Log ("run: {0} {1}" -f $executable, ($arguments -join " "))
    & $executable @arguments 2>&1 | Out-File -FilePath $log -Append -Encoding utf8
    return $LASTEXITCODE
}

Write-Log "pipeline start pilot=$PilotDir formal=$FormalDir"
if ($PilotPid -gt 0) {
    Write-Log "waiting for pilot pid $PilotPid"
    while (Get-Process -Id $PilotPid -ErrorAction SilentlyContinue) {
        Start-Sleep -Seconds 60
    }
    Write-Log "pilot process ended"
}

$pilotAggregate = Join-Path $repo (Join-Path $PilotDir "cost_pilot.json")
if (-not (Test-Path -LiteralPath $pilotAggregate)) {
    Write-Log "pilot aggregate missing; stop"
    exit 1
}

$decisionPath = Join-Path $repo (Join-Path $PilotDir "decision.json")
$code = Invoke-Step "python" @("scripts/dose_decision.py", "--pilot", $pilotAggregate,
    "--dir", (Join-Path $repo $PilotDir), "--out", $decisionPath)
Write-Log "decision exit=$code"

if ($code -eq 3) {
    Write-Log "retrying pilot once in $RetryDir"
    $retryAggregate = Join-Path $repo (Join-Path $RetryDir "cost_pilot.json")
    Invoke-Step "python" @("experiments/tasks/cost_pilot.py", "--runner", "opencode",
        "--tasks", $Tasks, "--arms", $Arms, "--out-dir", $RetryDir,
        "--out", $retryAggregate, "--timeout", "900") | Out-Null
    $decisionPath = Join-Path $repo (Join-Path $RetryDir "decision.json")
    $code = Invoke-Step "python" @("scripts/dose_decision.py", "--pilot", $retryAggregate,
        "--dir", (Join-Path $repo $RetryDir), "--out", $decisionPath)
    Write-Log "retry decision exit=$code"
    if ($code -eq 0) { $PilotDir = $RetryDir }
}

if ($code -eq 4) {
    $autofixLog = Join-Path $logDir "autofix.log"
    $autofixCode = Invoke-Step "python" @("scripts/autofix_detector.py", "--decision", $decisionPath,
        "--repo", $repo, "--log", $autofixLog, "--timeout", "1800")
    Write-Log "autofix exit=$autofixCode"
    if ($autofixCode -ne 0) {
        Write-Log "autofix failed; stopping for review"
        $decisionMd = [System.IO.Path]::ChangeExtension($decisionPath, ".md")
        if (Test-Path -LiteralPath $decisionMd) {
            Copy-Item -LiteralPath $decisionMd -Destination (Join-Path $repo (Join-Path $PilotDir "STOP.md")) -Force
        }
        exit 1
    }
    $code = 0
}

if ($code -ne 0) {
    Write-Log "stopping: decision exit=$code"
    $decisionMd = [System.IO.Path]::ChangeExtension($decisionPath, ".md")
    if (Test-Path -LiteralPath $decisionMd) {
        Copy-Item -LiteralPath $decisionMd -Destination (Join-Path $repo (Join-Path $PilotDir "STOP.md")) -Force
    }
    exit 1
}

$decision = Get-Content -LiteralPath $decisionPath -Raw | ConvertFrom-Json
$taskList = ($decision.tasks -join ",")
$armList = ($decision.arms -join ",")
Write-Log "formal start tasks=$taskList arms=$armList reps=$Reps"

$formalCode = Invoke-Step "python" @("experiments/tasks/formal_all.py", "--runner", "opencode",
    "--reps", $Reps, "--arms", $armList, "--tasks", $taskList,
    "--out-dir", $FormalDir, "--timeout", "900")
Write-Log "formal exit=$formalCode"

$analysisPath = Join-Path $repo (Join-Path $FormalDir "analysis.json")
Invoke-Step "python" @("experiments/tasks/formal_analysis.py", "--dir", $FormalDir,
    "--out", $analysisPath) | Out-Null
Invoke-Step "python" @("experiments/tasks/formal_report.py", "--analysis", $analysisPath,
    "--out", "docs/research/formal-results-dose.md") | Out-Null

if (Test-Path -LiteralPath $analysisPath) {
    $analysis = Get-Content -LiteralPath $analysisPath -Raw | ConvertFrom-Json
    $lines = @(
        "Dose formal",
        "runs=$($analysis.runs) finished=$($analysis.finished) invalid=$($analysis.invalid)",
        ""
    )
    foreach ($arm in $analysis.arms.PSObject.Properties) {
        $values = $arm.Value
        $lines += ("{0}: n={1} hidden={2} semgrep={3} confirmed={4} behavioral={5} clean={6}" -f `
            $arm.Name, $values.n, $values.hidden_pass, $values.oracle_findings,
            $values.outcomes.confirmed_violation, $values.outcomes.behavioral_failure,
            $values.outcomes.clean)
    }
    $lines += ""
    foreach ($arm in $analysis.contrasts.PSObject.Properties) {
        $values = $arm.Value
        $lines += ("{0} vs baseline: n={1} delta={2} mcnemar_confirmed={3} any={4}" -f `
            $arm.Name, $values.n, $values.delta_mean,
            ($values.mcnemar_confirmed | ConvertTo-Json -Compress),
            ($values.mcnemar_any_failure | ConvertTo-Json -Compress))
    }
    $lines += "", "report: docs/research/formal-results-dose.md"
    Set-Content -LiteralPath (Join-Path $repo (Join-Path $FormalDir "SUMMARY.txt")) `
        -Value $lines -Encoding utf8
}
Write-Log "pipeline done"
