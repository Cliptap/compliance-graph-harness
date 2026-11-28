param(
    [int]$BatchPid = 17360,
    [int]$GraceSeconds = 60,
    [string]$Root = "C:\Users\andre\Documents\VSC Projects\Gentle-AI\vibecoding"
)

# Watches the experiment batch, writes the comparison when it ends and shuts the
# machine down. Cancel the shutdown by creating qa_reports/clean-env/CANCEL_SHUTDOWN
# before the grace period ends, or run: shutdown /a

$ErrorActionPreference = "Continue"
$Out = Join-Path $Root "qa_reports\clean-env"
$Log = Join-Path $Out "shutdown.log"
$Cancel = Join-Path $Out "CANCEL_SHUTDOWN"

function Write-Log([string]$Message) {
    $line = "{0}  {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Add-Content -Path $Log -Value $line
}

Set-Location $Root
Write-Log "watcher start; batch pid $BatchPid"

$deadline = (Get-Date).AddHours(6)
while ((Get-Date) -lt $deadline) {
    $process = Get-Process -Id $BatchPid -ErrorAction SilentlyContinue
    if (-not $process) { break }
    Start-Sleep -Seconds 30
}

$runs = (Get-ChildItem $Out -Filter "rep*_*.json" -ErrorAction SilentlyContinue | Measure-Object).Count
Write-Log "batch finished; run files: $runs"

$python = "python"
if (Test-Path (Join-Path $Root ".venv\Scripts\python.exe")) {
    $python = Join-Path $Root ".venv\Scripts\python.exe"
}

& $python -m harness.eval.arm_comparison --root $Out --left baseline --right gate_only `
    --json (Join-Path $Out "comparison_baseline_gate.json") *>> $Log
& $python -m harness.eval.arm_comparison --root $Out --left baseline --right rules_skills_gate `
    --json (Join-Path $Out "comparison_baseline_full.json") *>> $Log

$summary = & $python -m harness.eval.arm_comparison --root $Out --left baseline --right gate_only 2>&1
$summary | Set-Content -Path (Join-Path $Out "SUMMARY.txt") -Encoding UTF8
Write-Log "summary written"

if (Test-Path $Cancel) {
    Write-Log "shutdown cancelled by CANCEL_SHUTDOWN"
    "shutdown cancelled" | Out-File -FilePath (Join-Path $Out "DONE.txt") -Encoding UTF8
    exit 0
}

Write-Log "shutting down in $GraceSeconds seconds"
"Apagado programado. Cancelar con: shutdown /a" | Out-File -FilePath (Join-Path $Out "DONE.txt") -Encoding UTF8
& shutdown.exe /s /t $GraceSeconds /c "Experimento terminado. Apagado en $GraceSeconds s. Cancelar: shutdown /a"
Write-Log "shutdown issued"
