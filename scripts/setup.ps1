param(
    [switch]$Install,
    [switch]$Strict
)

$ErrorActionPreference = 'Stop'
$scriptFolder = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExecutable = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonExecutable) {
    $pythonExecutable = Get-Command py -ErrorAction SilentlyContinue
}
if (-not $pythonExecutable) {
    Write-Host 'Python 3 is needed for this starter.'
    if ($Install -and (Get-Command winget -ErrorAction SilentlyContinue)) {
        $answer = Read-Host 'Install Python 3 with winget? (y/N)'
        if ($answer -eq 'y' -or $answer -eq 'yes') {
            winget install --id Python.Python.3.13 --exact --source winget
            $pythonExecutable = Get-Command python -ErrorAction SilentlyContinue
            if (-not $pythonExecutable) { $pythonExecutable = Get-Command py -ErrorAction SilentlyContinue }
        }
    }
}
if (-not $pythonExecutable) {
    Write-Error 'Please install Python 3 and reopen your terminal; then rerun this script.'
    exit 2
}
$arguments = @((Join-Path $scriptFolder 'doctor.py'))
if ($Install) { $arguments += '--install' }
if ($Strict) { $arguments += '--strict' }
& $pythonExecutable.Source @arguments
exit $LASTEXITCODE

