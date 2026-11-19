param(
    [string]$Version = "dev",
    [string]$LilyPondVersion = "2.24.4",
    [string]$LilyPondDir = "",
    [string]$Python = "python",
    [string]$SmokeTestWav = ""
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Dist = Join-Path $Root "dist"
$AppDir = Join-Path $Dist "GitarProjekt"
$WorkDir = Join-Path $Root "build\pyinstaller"
$CppBuildDir = Join-Path $Root "build\cpp-release"
$Algos = @("main", "main_plus_viterbi", "viterbi", "pso")

function Invoke-Checked([string]$Exe, [string[]]$Arguments) {
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Sikertelen parancs ($LASTEXITCODE): $Exe $($Arguments -join ' ')" }
}

Write-Host "== 1/5 C++ optimalizalok forditasa =="
Invoke-Checked "cmake" @("-S", (Join-Path $Root "backend\cpp"), "-B", $CppBuildDir, "-DCMAKE_BUILD_TYPE=Release")
Invoke-Checked "cmake" @("--build", $CppBuildDir, "--config", "Release")

Write-Host "== 2/5 PyInstaller =="
if (Test-Path $AppDir) { Remove-Item -Recurse -Force $AppDir }
Invoke-Checked $Python @("-m", "PyInstaller", "--noconfirm", "--clean",
    "--distpath", $Dist, "--workpath", $WorkDir,
    (Join-Path $Root "packaging\gitar_projekt.spec"))

Write-Host "== 3/5 C++ programok, benchmarkok masolasa =="
foreach ($algo in $Algos) {
    $src = Join-Path $Root "backend\cpp\${algo}_fingering_optimization\main.exe"
    if (-not (Test-Path $src)) { throw "Hianyzik a leforditott program: $src" }
    $dst = Join-Path $AppDir "backend\cpp\${algo}_fingering_optimization"
    New-Item -ItemType Directory -Force $dst | Out-Null
    Copy-Item $src $dst
}
Copy-Item -Recurse (Join-Path $Root "benchmarks") (Join-Path $AppDir "benchmarks")
New-Item -ItemType Directory -Force (Join-Path $AppDir "benchmark_results") | Out-Null
Copy-Item (Join-Path $Root "README.md") $AppDir

Write-Host "== 4/5 LilyPond =="
$LilyTarget = Join-Path $AppDir "lilypond"
if ($LilyPondDir) {
    Copy-Item -Recurse $LilyPondDir $LilyTarget
}
else {
    $zipName = "lilypond-$LilyPondVersion-mingw-x86_64.zip"
    $url = "https://gitlab.com/lilypond/lilypond/-/releases/v$LilyPondVersion/downloads/$zipName"
    $zipPath = Join-Path $Root "build\$zipName"
    if (-not (Test-Path $zipPath)) {
        Write-Host "Letoltes: $url"
        Invoke-WebRequest -Uri $url -OutFile $zipPath
    }
    $extractDir = Join-Path $Root "build\lilypond-extract"
    if (Test-Path $extractDir) { Remove-Item -Recurse -Force $extractDir }
    Expand-Archive -Path $zipPath -DestinationPath $extractDir
    $inner = Get-ChildItem $extractDir -Directory | Select-Object -First 1
    Move-Item $inner.FullName $LilyTarget
}
if (-not (Test-Path (Join-Path $LilyTarget "bin\lilypond.exe"))) { throw "Nem talalhato a lilypond.exe a csomagban." }

Write-Host "== 5/5 Zip =="
$ZipOut = Join-Path $Dist "GitarProjekt-$Version-windows-x64.zip"
if (Test-Path $ZipOut) { Remove-Item -Force $ZipOut }
Invoke-Checked "$env:SystemRoot\System32\tar.exe" @("-a", "-c", "-f", $ZipOut, "-C", $Dist, "GitarProjekt")
Write-Host "Kesz: $ZipOut"

if ($SmokeTestWav) {
    Write-Host "== 6/6 Smoke test a kicsomagolt zipbol =="
    $SmokeDir = Join-Path $Root "build\smoke"
    if (Test-Path $SmokeDir) { Remove-Item -Recurse -Force $SmokeDir }
    New-Item -ItemType Directory -Force $SmokeDir | Out-Null
    Invoke-Checked "$env:SystemRoot\System32\tar.exe" @("-x", "-f", $ZipOut, "-C", $SmokeDir)
    Remove-Item Env:LILYPOND_PATH -ErrorAction SilentlyContinue
    $wav = (Resolve-Path $SmokeTestWav).Path
    Invoke-Checked (Join-Path $SmokeDir "GitarProjekt\GitarProjekt.exe") @("--smoke-test", $wav)
}
