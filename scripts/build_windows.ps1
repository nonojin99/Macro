# Build MacroStudio Windows one-folder dist (run on Windows / CI)
# Usage: powershell -ExecutionPolicy Bypass -File scripts/build_windows.ps1

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

Write-Host "==> Python:" (python --version)
python -m pip install --upgrade pip
python -m pip install -r requirements-build.txt

if (Test-Path build) { Remove-Item -Recurse -Force build }
if (Test-Path dist) { Remove-Item -Recurse -Force dist }

Write-Host "==> PyInstaller (one-folder: dist/MacroStudio/)"
python -m PyInstaller --noconfirm --clean macro_studio.spec

$out = Join-Path (Get-Location) "dist\MacroStudio\MacroStudio.exe"
if (-not (Test-Path $out)) {
    Write-Error "Build failed: missing $out"
    exit 1
}
Write-Host "==> OK: $out"
Write-Host "    macros/ will be created next to the exe on first run."
