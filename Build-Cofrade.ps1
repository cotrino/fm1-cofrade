[CmdletBinding()]
param(
    [switch]$Installer,   # genera dist\FM1_COFRADE_Instalador.html (workbench con el firmware integrado)
    [string]$SourceUrl = 'https://github.com/cotrino/fm1-cofrade',
    [switch]$Web   # tambien compila el simulador web (requiere WASI SDK 27 en .tools\wasi-sdk-27.0-x86_64-windows)
)
# Compila FM1 Cofrade: SDK oficial FM1 Open (vendor\fm1_open, intacto) + overlay\.
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$cache = Join-Path $root '.tools'
$work = Join-Path $root 'build\work'
$dist = Join-Path $root 'dist'
$utf8 = New-Object Text.UTF8Encoding $false

# 1. Toolchain JieLi 2.5.3 (PI32v2 clang 4.0.1); Build.ps1 del SDK verifica sus hashes.
if (!$env:FM1_PI32_TOOLCHAIN) {
    $env:FM1_PI32_TOOLCHAIN = Join-Path $cache 'jieli-2.5.3\C$\JL\pi32'
}
if (!(Test-Path -LiteralPath (Join-Path $env:FM1_PI32_TOOLCHAIN 'bin\clang.exe'))) {
    throw 'Falta la toolchain JieLi 2.5.3: instalala (o extraela) segun vendor\fm1_open\README.md y define FM1_PI32_TOOLCHAIN.'
}

# 2. Tablas de marchas.
& python (Join-Path $root 'tools\gen_marchas.py')
if ($LASTEXITCODE) { throw 'gen_marchas.py fallo' }

# 3. Copia de trabajo = SDK oficial + overlay.
if (Test-Path -LiteralPath $work) { Remove-Item -Recurse -Force -LiteralPath $work }
[IO.Directory]::CreateDirectory($work) | Out-Null
& robocopy (Join-Path $root 'vendor\fm1_open') $work /E /XD build /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { throw 'robocopy (SDK) fallo' }
& robocopy (Join-Path $root 'overlay') $work /E /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { throw 'robocopy (overlay) fallo' }

# 4. Parches puntuales de pantalla (cada ancla se comprueba).
$screenPath = Join-Path $work 'app\screen.c'
$screen = [IO.File]::ReadAllText($screenPath)
function Patch([string]$pattern, [string]$replacement) {
    if (![regex]::IsMatch($script:screen, $pattern)) { throw "El SDK cambio, ancla no encontrada: $pattern" }
    $script:screen = [regex]::Replace($script:screen, $pattern, { param($m) $replacement }, 1)
}
Patch 'text\(81, 98, "OFFICIAL OPEN", 1, ACCENT, BACK\);' 'text(84, 98, "MODO COFRADE", 1, ACCENT, BACK);'
Patch 'text\(\(240 - 12 \* \(sizeof FM1_RELEASE_VERSION - 1\)\) / 2, 120,\s*FM1_RELEASE_VERSION, 2, TEXT, BACK\);' @'
text(48, 120, "SEMANA SANTA", 2, TEXT, BACK);
        text(48, 136, "QUE VIENE EL PASO, ILLO!", 1, DIM, BACK);
'@
Patch 'text\(86, 35, "OPEN " FM1_RELEASE_VERSION, 1, DIM, BACK\);' 'text(86, 35, "COFRADE", 1, DIM, BACK);'
[IO.File]::WriteAllText($screenPath, $screen, $utf8)

# 5. Compilacion y empaquetado oficial del firmware.
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $work 'sdk\Build.ps1') -FirmwareOnly
if ($LASTEXITCODE) { throw 'Build.ps1 del SDK fallo' }
$gen = Join-Path $work 'build\dx7'
$report = Get-Content (Join-Path $gen 'firmware-report.json') -Raw | ConvertFrom-Json
$layout = Get-Content (Join-Path $gen 'package-report.json') -Raw | ConvertFrom-Json
if (!$report.passed -or !$layout.fits) { throw 'La validacion oficial del firmware fallo' }
[IO.Directory]::CreateDirectory($dist) | Out-Null
Copy-Item (Join-Path $gen 'generated\FM1_OFFICIAL_OPEN.fwsc') (Join-Path $dist 'FM1_COFRADE.fwsc') -Force
foreach ($n in 'firmware-report.json', 'package-report.json', 'build-identity.json') {
    Copy-Item (Join-Path $gen $n) $dist -Force
}
$hash = (Get-FileHash (Join-Path $dist 'FM1_COFRADE.fwsc') -Algorithm SHA256).Hash.ToLower()
[IO.File]::WriteAllText((Join-Path $dist 'SHA256SUMS.txt'), "$hash  FM1_COFRADE.fwsc`n", $utf8)
Write-Host "Firmware listo: $dist\FM1_COFRADE.fwsc ($hash)"

if ($Installer) {
    # Instalador local: pagina del workbench oficial con ESTE firmware integrado (el workbench online solo flashea el oficial).
    $env:FM1_WASI_SDK = Join-Path $cache 'wasi-sdk-27.0-x86_64-windows'
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $work 'sdk\Build.ps1') -Package -SourceUrl $SourceUrl
    if ($LASTEXITCODE) { throw 'Build.ps1 -Package fallo' }
    Copy-Item (Join-Path $work 'build\official-web\FM1-Official-Open-Source.html') (Join-Path $dist 'FM1_COFRADE_Instalador.html') -Force
    Write-Host "Instalador: $dist\FM1_COFRADE_Instalador.html"
}

if ($Web) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $work 'tools\Build-Web.ps1') -WasiSdk (Join-Path $cache 'wasi-sdk-27.0-x86_64-windows') -LocalPreview
    if ($LASTEXITCODE) { throw 'Build-Web.ps1 fallo' }
}
