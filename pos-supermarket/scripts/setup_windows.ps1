param(
    [switch]$RunApp
)

$ErrorActionPreference = 'Stop'

Write-Host "[1/6] Vérification Python launcher (py)..." -ForegroundColor Cyan
if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    Write-Host "Le launcher 'py' est introuvable." -ForegroundColor Red
    Write-Host "Installez Python 3.12 depuis https://www.python.org/downloads/windows/" -ForegroundColor Yellow
    Write-Host "Pendant l'installation, cochez 'Add python.exe to PATH'." -ForegroundColor Yellow
    exit 1
}

Write-Host "[2/6] Version Python détectée:" -ForegroundColor Cyan
py -3.12 --version

Write-Host "[3/6] Création venv (.venv)..." -ForegroundColor Cyan
py -3.12 -m venv .venv

Write-Host "[4/6] Installation dépendances..." -ForegroundColor Cyan
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

Write-Host "[5/6] Vérification imports critiques..." -ForegroundColor Cyan
.\.venv\Scripts\python.exe -c "import sqlalchemy, bcrypt, PyQt6; print('OK imports')"

Write-Host "[6/6] Setup terminé." -ForegroundColor Green
Write-Host "Pour activer manuellement l'environnement: .\.venv\Scripts\Activate.ps1" -ForegroundColor Green
Write-Host "Pour lancer l'application: python main.py" -ForegroundColor Green

if ($RunApp) {
    Write-Host "Lancement de l'application..." -ForegroundColor Cyan
    & .\.venv\Scripts\python.exe main.py
}
