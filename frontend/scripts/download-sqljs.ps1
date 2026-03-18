# download-sqljs.ps1
# Downloads sql.js v1.13.0 WASM assets from GitHub releases.
# Run from repo root: powershell -ExecutionPolicy Bypass -File frontend/scripts/download-sqljs.ps1
# Idempotent: skips download if assets already exist.

$Version = "1.14.1"
$AssetsDir = Join-Path $PSScriptRoot "..\src\assets"

$jsFile   = Join-Path $AssetsDir "sql-wasm.js"
$wasmFile = Join-Path $AssetsDir "sql-wasm.wasm"

if ((Test-Path $jsFile) -and (Test-Path $wasmFile)) {
    Write-Host "sql.js assets already exist - skipping download."
    exit 0
}

$zipUrl     = "https://github.com/sql-js/sql.js/releases/download/v$Version/sqljs-wasm.zip"
$zipPath    = Join-Path $env:TEMP "sqljs-$Version.zip"
$extractDir = Join-Path $env:TEMP "sqljs-$Version"

Write-Host "Downloading sql.js v$Version ..."
try {
    Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -UseBasicParsing
} catch {
    Write-Error "Failed to download sql.js: $_"
    exit 1
}

Write-Host "Extracting..."
if (Test-Path $extractDir) { Remove-Item $extractDir -Recurse -Force }
Expand-Archive -Path $zipPath -DestinationPath $extractDir -Force

$srcJs   = Join-Path $extractDir "sql-wasm.js"
$srcWasm = Join-Path $extractDir "sql-wasm.wasm"

if ((-not (Test-Path $srcJs)) -or (-not (Test-Path $srcWasm))) {
    $found = (Get-ChildItem $extractDir).Name -join ", "
    Write-Error "Expected files not found. Contents: $found"
    exit 1
}

New-Item -ItemType Directory -Path $AssetsDir -Force | Out-Null
Copy-Item $srcJs   -Destination $jsFile   -Force
Copy-Item $srcWasm -Destination $wasmFile -Force

Remove-Item $zipPath    -Force -ErrorAction SilentlyContinue
Remove-Item $extractDir -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Done."
Write-Host "  js  : $jsFile"
Write-Host "  wasm: $wasmFile"
