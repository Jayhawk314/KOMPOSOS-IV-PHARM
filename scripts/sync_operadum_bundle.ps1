param(
    [string]$SourceRoot,
    [switch]$NoBackup
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

if (-not $SourceRoot) {
    $SourceRoot = Join-Path $RepoRoot "..\operadum"
}

$SourceRoot = (Resolve-Path $SourceRoot).Path
$DestRoot = Join-Path $RepoRoot "vendor\operadum"

if (-not (Test-Path (Join-Path $SourceRoot "pronoia"))) {
    throw "SourceRoot does not look like the consolidated OPERADUM/PRONOIA stack: $SourceRoot"
}

if ((Test-Path $DestRoot) -and (-not $NoBackup)) {
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backup = Join-Path $RepoRoot "vendor\operadum.BACKUP_$stamp"
    Copy-Item -LiteralPath $DestRoot -Destination $backup -Recurse -Force
    Write-Host "Backed up existing bundle to $backup"
}

robocopy $SourceRoot $DestRoot /E /XD .pytest_cache .claude __pycache__ /XF *.pyc /R:1 /W:1
$code = $LASTEXITCODE
if ($code -gt 7) {
    exit $code
}

Write-Host "Synced OPERADUM/PRONOIA bundle from $SourceRoot to $DestRoot"
exit 0
