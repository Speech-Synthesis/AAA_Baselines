$release = Invoke-RestMethod -Uri 'https://api.github.com/repos/superfly/flyctl/releases/latest'
$release.assets | ForEach-Object { Write-Host $_.name }
