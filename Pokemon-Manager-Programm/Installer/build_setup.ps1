param(
    [switch]$InstallDependencies,
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$versionFile = Join-Path $projectRoot "VERSION.json"
$requirementsFile = Join-Path $PSScriptRoot "requirements-build.txt"
$spec = Join-Path $PSScriptRoot "PokemonManager.spec"
$iss = Join-Path $PSScriptRoot "PokemonManager.iss"
$distRoot = Join-Path $projectRoot "Release\dist"
$workRoot = Join-Path $projectRoot "App\build"
$releaseRoot = Join-Path $projectRoot "Release"

if (-not (Test-Path -LiteralPath $versionFile)) {
    throw "Versionsdatei fehlt: $versionFile"
}
$version = (Get-Content -LiteralPath $versionFile -Raw -Encoding UTF8 | ConvertFrom-Json).app_version
if ([string]::IsNullOrWhiteSpace([string]$version)) {
    throw "VERSION.json enthält keine gültige app_version."
}

$pythonCommand = $env:POKEMON_MANAGER_PYTHON
if ([string]::IsNullOrWhiteSpace($pythonCommand)) {
    $pythonCommand = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
}
if ([string]::IsNullOrWhiteSpace($pythonCommand)) {
    $pythonCommand = (Get-Command python -ErrorAction SilentlyContinue).Source
}
if ([string]::IsNullOrWhiteSpace($pythonCommand)) {
    throw "Python wurde nicht gefunden. Installiere Python 3.11 oder neuer und starte den Build erneut."
}

& $pythonCommand -c "import sys; assert sys.version_info >= (3, 11), sys.version"
if ($LASTEXITCODE -ne 0) {
    throw "Python 3.11 oder neuer wird benötigt."
}

if ($InstallDependencies) {
    & $pythonCommand -m pip install --disable-pip-version-check --requirement $requirementsFile
    if ($LASTEXITCODE -ne 0) {
        throw "Die Build-Abhängigkeiten konnten nicht installiert werden."
    }
}

& $pythonCommand -c "import PyInstaller, PIL; assert PyInstaller.__version__ == '6.22.3', PyInstaller.__version__; assert PIL.__version__ == '13.0.0', PIL.__version__"
if ($LASTEXITCODE -ne 0) {
    throw "Die Build-Abhängigkeiten fehlen oder haben nicht die festgelegten Versionen. Nutze -InstallDependencies."
}

if (-not $SkipTests) {
    & $pythonCommand -m unittest discover -s (Join-Path $projectRoot "tests") -p "test_*.py"
    if ($LASTEXITCODE -ne 0) {
        throw "Automatisierte Tests sind fehlgeschlagen."
    }
}

if (Test-Path -LiteralPath $distRoot) {
    Remove-Item -LiteralPath $distRoot -Recurse -Force
}
if (Test-Path -LiteralPath $workRoot) {
    Remove-Item -LiteralPath $workRoot -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $distRoot, $workRoot, $releaseRoot | Out-Null

& $pythonCommand -m PyInstaller --noconfirm --clean --distpath $distRoot --workpath $workRoot $spec
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller-Build fehlgeschlagen."
}

$innoCandidates = @(
    (Get-Command iscc.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue),
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe",
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe")
)
$iscc = $innoCandidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
if (-not $iscc) {
    throw "Inno Setup 6 fehlt. Bitte auf dem Build-System installieren und erneut ausführen."
}

& $iscc "/DMyAppVersion=$version" $iss
if ($LASTEXITCODE -ne 0) {
    throw "Inno-Setup-Build fehlgeschlagen."
}

$setup = Join-Path $releaseRoot "Pokemon-Manager-Setup.exe"
if (-not (Test-Path -LiteralPath $setup)) {
    throw "Setup-Datei wurde nicht erzeugt: $setup"
}
$hash = (Get-FileHash -LiteralPath $setup -Algorithm SHA256).Hash.ToLowerInvariant()
$hashFile = Join-Path $releaseRoot "Pokemon-Manager-Setup.exe.sha256"
Set-Content -LiteralPath $hashFile -Value ("$hash  Pokemon-Manager-Setup.exe") -Encoding UTF8
$releaseDocs = Join-Path $releaseRoot "Anleitung"
New-Item -ItemType Directory -Force -Path $releaseDocs, (Join-Path $releaseDocs "Projekt") | Out-Null
Copy-Item -LiteralPath (Join-Path $projectRoot "README.md") -Destination (Join-Path $releaseDocs "README.md") -Force
Copy-Item -LiteralPath (Join-Path $projectRoot "Gebrauchsanweisung_Pokemon-Auswahl.html") -Destination (Join-Path $releaseDocs "Gebrauchsanweisung_Pokemon-Auswahl.html") -Force
Get-ChildItem -LiteralPath (Join-Path $projectRoot "docs") -File -Filter "*.md" | Copy-Item -Destination (Join-Path $releaseDocs "Projekt") -Force

$manifest = [ordered]@{
    product = "Pokemon-Manager"
    version = [string]$version
    target = "windows-x64"
    installer = $setup
    installer_sha256 = $hash
    built_at = (Get-Date).ToUniversalTime().ToString("o")
    app_id = "{D2BB7F9A-6E4E-4FC4-8B9A-0E5E0F2E67A9}"
    update_mode = "manual-same-app-id"
    signing = "not-signed"
    documentation = @(
        (Join-Path $releaseRoot "Anleitung\README.md"),
        (Join-Path $releaseRoot "Anleitung\Projekt\PROJEKTDOKUMENTATION.md"),
        (Join-Path $releaseRoot "Anleitung\Projekt\ENTWICKLUNGSFAHRPLAN.md"),
        (Join-Path $releaseRoot "Anleitung\Projekt\RELEASE-CHECKLIST.md"),
        (Join-Path $releaseRoot "RELEASE_NOTES_$version.md")
    )
}
Set-Content -LiteralPath (Join-Path $releaseRoot "release-manifest.json") -Value ($manifest | ConvertTo-Json -Depth 4) -Encoding UTF8

$releaseNotes = @"
# Pokémon-Manager $version

Erstellt: $((Get-Date).ToString("yyyy-MM-dd HH:mm:ss zzz"))

## Enthalten

- deutschsprachige Oberfläche mit optionaler englischer Auswahl
- automatische Sicherung vor Übernahme, Aktualisierung der Druckauswahl und Wiederherstellung
- Wiederherstellungsdialog mit fünf geprüften Sicherungsständen
- Administrator-PIN für geschützte Verwaltungsaktionen
- atomare Ausgabe von Index, JSON und Druckauswahl
- Anleitung und Versionsinformationen im Installationspaket

## Prüfsumme

SHA-256: $hash

## Update-Hinweis

Für ein Update die neue `Pokemon-Manager-Setup.exe` ausführen. Die bestehende AppId bleibt erhalten; Inno Setup aktualisiert die installierte Version. Die App lädt keine Updates automatisch aus dem Internet.

## Signierung

Diese Version ist noch nicht code-signiert. Die SHA-256-Prüfsumme dient als Integritätsnachweis.
"@
Set-Content -LiteralPath (Join-Path $releaseRoot "RELEASE_NOTES_$version.md") -Value $releaseNotes -Encoding UTF8

Write-Output "Setup erstellt: $setup"
Write-Output "SHA-256: $hash"
Write-Output "Manifest: $(Join-Path $releaseRoot 'release-manifest.json')"
