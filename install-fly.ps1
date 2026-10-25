$flyPath = Join-Path $env:USERPROFILE '.fly'
New-Item -ItemType Directory -Force -Path $flyPath | Out-Null

# Get the latest release info from GitHub API
Write-Host 'Getting latest release info...'
$releaseInfo = Invoke-RestMethod -Uri 'https://api.github.com/repos/superfly/flyctl/releases/latest'
$version = $releaseInfo.tag_name -replace '^v', ''
Write-Host "Latest version: $version"

$url = "https://github.com/superfly/flyctl/releases/download/v$version/flyctl_${version}_Windows_x86_64.zip"
$zipPath = Join-Path $env:TEMP 'flyctl.zip'

Write-Host "Downloading flyctl from: $url"
Invoke-WebRequest -Uri $url -OutFile $zipPath

Write-Host 'Extracting...'
Expand-Archive -Path $zipPath -DestinationPath $flyPath -Force
Remove-Item $zipPath

Write-Host "Done! Installed to: $flyPath"
$exePath = Join-Path $flyPath 'flyctl.exe'
Write-Host "flyctl.exe location: $exePath"

# Verify installation
if (Test-Path $exePath) {
    Write-Host "Verifying installation..."
    & $exePath version
}
