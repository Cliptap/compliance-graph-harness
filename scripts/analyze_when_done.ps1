param(
    [int]$ProcessId = 0,
    [string]$OutDir = "qa_reports/formal-test",
    [string]$Report = "docs/research/formal-results-test.md"
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo
$log = Join-Path $repo (Join-Path $OutDir "analysis.log")
New-Item -ItemType Directory -Force -Path (Join-Path $repo $OutDir) | Out-Null

function Write-Log([string]$message) {
    Add-Content -LiteralPath $log -Value ("{0} {1}" -f (Get-Date -Format "o"), $message)
}

if ($ProcessId -gt 0) {
    Write-Log "waiting for pid $ProcessId"
    while (Get-Process -Id $ProcessId -ErrorAction SilentlyContinue) {
        Start-Sleep -Seconds 60
    }
    Write-Log "pid $ProcessId finished"
}

$analysis = Join-Path $repo (Join-Path $OutDir "analysis.json")
& python experiments/tasks/formal_analysis.py --dir $OutDir --out $analysis *>> $log
& python experiments/tasks/formal_report.py --analysis $analysis --out $Report *>> $log
Write-Log "analysis and report written"
