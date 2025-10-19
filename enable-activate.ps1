# enable-activate.ps1
# Installs a small 'activate' function in the user's PowerShell profile that runs the project's activate.ps1
# Run once to enable typing 'activate' in this project folder's PowerShell sessions.

$profilePath = $PROFILE.CurrentUserAllHosts
if (-not (Test-Path $profilePath)) {
    New-Item -ItemType File -Path $profilePath -Force | Out-Null
}

$scriptRoot = $PSScriptRoot
$activateScript = Join-Path $scriptRoot 'activate.ps1'
$functionText = @"
function activate {
    param()
    Set-Location -Path '$scriptRoot'
    . '$activateScript'
}
"@

# Append the function if not already present
$profileContent = Get-Content $profilePath -Raw -ErrorAction SilentlyContinue
if ($profileContent -notmatch "function activate") {
    Add-Content -Path $profilePath -Value "`n# activate helper for this project`n$functionText`n"
    Write-Host "Added 'activate' function to your PowerShell profile ($profilePath). Restart PowerShell or run `. $profilePath` to use it." -ForegroundColor Green
} else {
    Write-Host "Your profile already contains an 'activate' function. No changes made." -ForegroundColor Yellow
}
