param(
    [string]$Source = "C:\Users\Administrator\Documents\research\pilot_experiments",
    [string]$Destination = "D:\research\pilot_experiments",
    [string]$RemoteUrl = "https://github.com/JCZhang2025/bench.git"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $Source)) {
    throw "Source directory does not exist: $Source"
}

if (-not (Test-Path -LiteralPath "D:\research")) {
    New-Item -ItemType Directory -Path "D:\research" | Out-Null
}

if (Test-Path -LiteralPath $Destination) {
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backup = "D:\research\pilot_experiments_backup_$stamp"
    Write-Host "Backing up existing destination to $backup"
    Move-Item -LiteralPath $Destination -Destination $backup
}

Write-Host "Copying project from $Source to $Destination"
New-Item -ItemType Directory -Path $Destination -Force | Out-Null
robocopy $Source $Destination /MIR /XD "__pycache__" /XF "*.pyc" | Out-Host
if ($LASTEXITCODE -gt 7) {
    throw "robocopy failed with exit code $LASTEXITCODE"
}

Set-Location -LiteralPath $Destination

git status --short | Out-Host
git branch -M main

if (git remote get-url origin 2>$null) {
    git remote set-url origin $RemoteUrl
} else {
    git remote add origin $RemoteUrl
}

$gitHelper = "D:\tools\git\mingw64\bin"
if (Test-Path -LiteralPath (Join-Path $gitHelper "git-remote-https.exe")) {
    $env:PATH = "$gitHelper;D:\tools\git\cmd;$env:PATH"
    $env:GIT_EXEC_PATH = $gitHelper
}

Write-Host "Pushing main to $RemoteUrl"
git push -u origin main

Write-Host "Done. Future work directory: $Destination"
