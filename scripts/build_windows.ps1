$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "Building Vue frontend..."
Push-Location frontend
pnpm build
Pop-Location

Write-Host "Installing desktop build dependencies..."
uv sync --group desktop

Write-Host "Generating application icon..."
uv run --group desktop python scripts/generate_icon.py

Write-Host "Building CrossRead.exe..."
uv run --group desktop pyinstaller --clean --noconfirm packaging/CrossRead.spec

$isccCandidates = @(
  "$env:LOCALAPPDATA\Programs\Inno Setup 7\ISCC.exe",
  "$env:ProgramFiles\Inno Setup 7\ISCC.exe",
  "$env:ProgramFiles(x86)\Inno Setup 7\ISCC.exe",
  "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
  "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
  "$env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe"
)
$iscc = $isccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) {
  throw "找不到 Inno Setup 的 ISCC.exe。请安装 Inno Setup 7 或 6 后重新运行此脚本。"
}

Write-Host "Building CrossRead-Setup.exe..."
& $iscc packaging/CrossRead.iss
Write-Host "Installer created at dist/installer/CrossRead-Setup.exe"
