<#
Runs the T7 OpenCode formal experiment, writes the analysis and report, then
shuts the computer down after a grace period.

The shutdown is skipped unless every run finished (or -ForceShutdown is used),
so a crashed or partial run does not leave the machine off with no chance to
resume. Re-running the script resumes the run (`--resume` is used internally).

Example (detached):
  Start-Process powershell -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass',
    '-File','scripts\run_formal_shutdown.ps1'
#>
param(
    [string]$OutDir = "qa_reports/formal-opencode",
    [string]$Model = "opencode-go/deepseek-v4.1-flash",
    [string]$Reps = "1,2,3",
    [int]$Timeout = 900,
    [int]$ShutdownDelayMinutes = 5,
    [switch]$ForceShutdown,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo
New-Item -ItemType Directory -Force -Path (Join-Path $repo $OutDir) | Out-Null
$log = Join-Path $repo (Join-Path $OutDir "formal_run.log")
$analysisPath = Join-Path $repo (Join-Path $OutDir "analysis.json")
$reportPath = Join-Path $repo "docs/research/formal-results-opencode.md"
$summaryPath = Join-Path $repo (Join-Path $OutDir "SUMMARY.txt")

function Write-Log([string]$message) {
    $line = "{0} {1}" -f (Get-Date -Format "o"), $message
    Add-Content -LiteralPath $log -Value $line
    Write-Output $line
}

Write-Log "start model=$Model out=$OutDir reps=$Reps timeout=$Timeout"

& python experiments/tasks/formal_all.py --runner opencode --model $Model --reps $Reps `
    --out-dir $OutDir --timeout $Timeout 2>&1 | Out-File -FilePath $log -Append -Encoding utf8
Write-Log "formal_all exit=$LASTEXITCODE"

& python experiments/tasks/formal_analysis.py --dir (Join-Path $repo $OutDir) `
    --out $analysisPath 2>&1 | Out-File -FilePath $log -Append -Encoding utf8
& python experiments/tasks/formal_report.py --analysis $analysisPath `
    --out $reportPath 2>&1 | Out-File -FilePath $log -Append -Encoding utf8

$complete = $false
if (Test-Path -LiteralPath $analysisPath) {
    $analysis = Get-Content -LiteralPath $analysisPath -Raw | ConvertFrom-Json
    Write-Log ("analysis runs={0} finished={1} invalid={2}" -f $analysis.runs, $analysis.finished, $analysis.invalid)
    $lines = @(
        "T7 OpenCode formal run",
        "model: $Model",
        "runs: $($analysis.runs)  finished: $($analysis.finished)  invalid: $($analysis.invalid)",
        "",
        "arms:"
    )
    foreach ($arm in $analysis.arms.PSObject.Properties) {
        $values = $arm.Value
        $lines += ("  {0}: n={1} hidden={2} semgrep={3} confirmed={4} behavioral={5} latent={6} clean={7} gate_rounds={8}" -f `
            $arm.Name, $values.n, $values.hidden_pass, $values.oracle_findings, `
            $values.outcomes.confirmed_violation, $values.outcomes.behavioral_failure, `
            $values.outcomes.latent_risk, $values.outcomes.clean, $values.gate_rounds)
    }
    $lines += @(
        "",
        "paired: n=$($analysis.paired.n) mean=$($analysis.paired.delta_compliance_mean) sd=$($analysis.paired.delta_compliance_sd)",
        "mcnemar_hidden: $($analysis.paired.mcnemar_hidden | ConvertTo-Json -Compress)",
        "mcnemar_confirmed: $($analysis.paired.mcnemar_confirmed | ConvertTo-Json -Compress)",
        "",
        "report: $reportPath"
    )
    Set-Content -LiteralPath $summaryPath -Value $lines -Encoding utf8
    $complete = ([int]$analysis.finished -eq [int]$analysis.runs)
} else {
    Write-Log "analysis.json missing; the run did not produce results"
}

if (-not $complete -and -not $ForceShutdown) {
    Write-Log "run incomplete; NOT shutting down. Rerun the script to resume, or pass -ForceShutdown."
    exit 1
}

Write-Log "shutting down in $ShutdownDelayMinutes minute(s)"
Start-Sleep -Seconds ($ShutdownDelayMinutes * 60)

if ($DryRun) {
    Write-Log "dry run: skipping shutdown"
    exit 0
}

Write-Log "shutting down"
Stop-Computer -Force
