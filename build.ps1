# Decision Canvas Desktop Build Script
# =====================================
# This script builds the complete desktop application:
# 1. Backend (PyInstaller)
# 2. Frontend (Next.js static export)
# 3. Desktop App (Tauri)
#
# Prerequisites:
# - Python 3.11+
# - Node.js 18+
# - Rust (for Tauri)
# - PyInstaller (pip install pyinstaller)

param(
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$TauriOnly,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-Step { param($Message) Write-Host "`n=== $Message ===" -ForegroundColor Cyan }
function Write-Success { param($Message) Write-Host "[OK] $Message" -ForegroundColor Green }
function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Yellow }

$RootDir = $PSScriptRoot
$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "frontend"
$TauriDir = Join-Path $RootDir "src-tauri"
$TauriBinDir = Join-Path $TauriDir "binaries"

# Clean build artifacts
if ($Clean) {
    Write-Step "Cleaning build artifacts"

    if (Test-Path (Join-Path $BackendDir "dist")) {
        Remove-Item -Recurse -Force (Join-Path $BackendDir "dist")
    }
    if (Test-Path (Join-Path $BackendDir "build")) {
        Remove-Item -Recurse -Force (Join-Path $BackendDir "build")
    }
    if (Test-Path (Join-Path $FrontendDir "out")) {
        Remove-Item -Recurse -Force (Join-Path $FrontendDir "out")
    }
    if (Test-Path (Join-Path $FrontendDir ".next")) {
        Remove-Item -Recurse -Force (Join-Path $FrontendDir ".next")
    }
    if (Test-Path $TauriBinDir) {
        Remove-Item -Recurse -Force $TauriBinDir
    }

    Write-Success "Clean complete"
    if (-not ($BackendOnly -or $FrontendOnly -or $TauriOnly)) {
        exit 0
    }
}

# Build Backend
if (-not ($FrontendOnly -or $TauriOnly)) {
    Write-Step "Building Backend with PyInstaller"

    Push-Location $BackendDir

    # Install dependencies if needed
    if (-not (Test-Path ".venv")) {
        Write-Info "Creating virtual environment..."
        python -m venv .venv
    }

    # Activate venv and install
    & ".venv\Scripts\Activate.ps1"
    pip install -e ".[dev]" --quiet

    # Run PyInstaller
    Write-Info "Running PyInstaller..."
    pyinstaller decisiongpt.spec --clean --noconfirm

    # Create binaries directory for Tauri
    if (-not (Test-Path $TauriBinDir)) {
        New-Item -ItemType Directory -Path $TauriBinDir | Out-Null
    }

    # Copy executable to Tauri binaries
    # Note: Tauri expects platform-specific naming
    $ExePath = Join-Path (Join-Path $BackendDir "dist") "decisiongpt-backend.exe"
    $TargetPath = Join-Path $TauriBinDir "decisiongpt-backend-x86_64-pc-windows-msvc.exe"

    if (Test-Path $ExePath) {
        Copy-Item $ExePath $TargetPath -Force
        Write-Success "Backend built: $TargetPath"
    } else {
        Write-Error "Backend build failed - executable not found"
        exit 1
    }

    Pop-Location
}

# Build Frontend
if (-not ($BackendOnly -or $TauriOnly)) {
    Write-Step "Building Frontend (Next.js static export)"

    Push-Location $FrontendDir

    # Install dependencies
    if (-not (Test-Path "node_modules")) {
        Write-Info "Installing npm dependencies..."
        npm ci
    }

    # Build static export
    Write-Info "Building Next.js static export..."
    npm run build

    if (Test-Path "out") {
        Write-Success "Frontend built: $FrontendDir\out"
    } else {
        Write-Error "Frontend build failed - out directory not found"
        exit 1
    }

    Pop-Location
}

# Build Tauri App
if (-not ($BackendOnly -or $FrontendOnly)) {
    Write-Step "Building Tauri Desktop App"

    Push-Location $TauriDir

    # Check if backend binary exists
    $BackendBin = Join-Path $TauriBinDir "decisiongpt-backend-x86_64-pc-windows-msvc.exe"
    if (-not (Test-Path $BackendBin)) {
        Write-Error "Backend binary not found. Run build without -TauriOnly first."
        exit 1
    }

    # Check if frontend is built
    $FrontendOut = Join-Path $FrontendDir "out"
    if (-not (Test-Path $FrontendOut)) {
        Write-Error "Frontend not built. Run build without -TauriOnly first."
        exit 1
    }

    # Build Tauri
    Write-Info "Building Tauri application..."
    cargo tauri build

    # Find the output
    $InstallerDir = Join-Path $TauriDir "target" "release" "bundle"

    if (Test-Path $InstallerDir) {
        Write-Success "Tauri build complete!"
        Write-Info "Installers located at: $InstallerDir"

        # List generated installers
        Get-ChildItem -Path $InstallerDir -Recurse -Include "*.exe", "*.msi" | ForEach-Object {
            Write-Host "  - $($_.FullName)" -ForegroundColor White
        }
    } else {
        Write-Error "Tauri build failed"
        exit 1
    }

    Pop-Location
}

Write-Step "Build Complete!"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Install Ollama from https://ollama.ai"
Write-Host "2. Pull a model: ollama pull llama3.2"
Write-Host "3. Run the installer from src-tauri/target/release/bundle/"
Write-Host ""
