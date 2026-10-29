$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$envExampleFile = Join-Path $projectRoot ".env.example"
$rulesFile = Join-Path $projectRoot "automated-print.toml"
$projectPython = Join-Path $projectRoot "env\Scripts\python.exe"
if (Test-Path -LiteralPath $projectPython -PathType Leaf) {
    $pythonExecutable = $projectPython
} else {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCommand) {
        throw "Python tidak ditemukan. Buat virtual environment pada folder env atau pasang Python."
    }
    $pythonExecutable = $pythonCommand.Source
}

if (-not (Test-Path -LiteralPath $envExampleFile -PathType Leaf)) {
    throw "File .env.example tidak ditemukan."
}
if (-not (Test-Path -LiteralPath $rulesFile -PathType Leaf)) {
    throw "File automated-print.toml tidak ditemukan."
}

& $pythonExecutable -c "import tkinter; tkinter.Tcl()"
if ($LASTEXITCODE -ne 0) {
    throw "Runtime Tcl/Tk Python tidak siap. Pasang atau perbaiki Python dengan dukungan Tcl/Tk sebelum membuat EXE."
}

Push-Location $projectRoot
try {
    & $pythonExecutable -m PyInstaller `
        --noconfirm `
        --clean `
        --windowed `
        --onedir `
        --contents-directory . `
        --name IloPrintClient `
        --hidden-import win32timezone `
        --collect-submodules engineio.async_drivers `
        index.py

    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller gagal dengan exit code $LASTEXITCODE."
    }

    $outputDirectory = Join-Path $projectRoot "dist\IloPrintClient"
    Copy-Item -LiteralPath $envExampleFile -Destination (Join-Path $outputDirectory ".env.example") -Force
    Copy-Item -LiteralPath $rulesFile -Destination (Join-Path $outputDirectory "automated-print.toml") -Force
    Write-Host "Build selesai: $outputDirectory\IloPrintClient.exe"
} finally {
    Pop-Location
}
