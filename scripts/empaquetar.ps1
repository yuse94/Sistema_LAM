# Genera dist_portable\SistemaLAM y dist_portable\SistemaLAM.zip para usar la app en otro equipo.
# Uso (PowerShell, desde la carpeta del proyecto):  powershell -ExecutionPolicy Bypass -File scripts\empaquetar.ps1
# En el otro equipo: descomprimir y hacer doble clic en "Iniciar LAM.bat".
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$dist = Join-Path $root "dist_portable"
$out = Join-Path $dist "SistemaLAM"

Write-Host "1/4 Compilando la interfaz (npm run build)..."
Push-Location (Join-Path $root "frontend")
npm run build
$code = $LASTEXITCODE
Pop-Location
if ($code -ne 0) { throw "Fallo npm run build" }

Write-Host "2/4 Copiando archivos..."
if (Test-Path $dist) { Remove-Item -Recurse -Force $dist }
New-Item -ItemType Directory -Force -Path $out | Out-Null
robocopy (Join-Path $root "backend") (Join-Path $out "backend") /E /XD .venv data __pycache__ .pytest_cache .ruff_cache validation tests /XF .env *.pyc /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { throw "Fallo la copia del backend" }
robocopy (Join-Path $root "frontend\dist") (Join-Path $out "frontend\dist") /E /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { throw "Fallo la copia de la interfaz" }
Copy-Item (Join-Path $root "Iniciar LAM.bat") $out
foreach ($doc in @("GUIA_DE_USO.md", "GUIA_DE_USO.pdf")) {
  $file = Join-Path $root "docs\$doc"
  if (Test-Path $file) { Copy-Item $file $out }
}
$guide = Join-Path $root "docs\guia"
if (Test-Path $guide) { Copy-Item -Recurse $guide (Join-Path $out "guia") }

Write-Host "3/4 Comprimiendo..."
Compress-Archive -Path $out -DestinationPath (Join-Path $dist "SistemaLAM.zip") -Force

$size = [math]::Round((Get-Item (Join-Path $dist "SistemaLAM.zip")).Length / 1MB, 1)
Write-Host "4/4 Listo: dist_portable\SistemaLAM.zip ($size MB)"
