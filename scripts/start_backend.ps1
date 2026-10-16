param([switch]$Fixture)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if ($Fixture) {
    $privateConfig = Join-Path $projectRoot '.runtime/local-env.json'
    if (-not (Test-Path -LiteralPath $privateConfig)) { throw 'Falta configuración local. Consulta README.md.' }
    $configuration = Get-Content -LiteralPath $privateConfig -Raw | ConvertFrom-Json
    foreach ($property in $configuration.PSObject.Properties) {
        [Environment]::SetEnvironmentVariable($property.Name, [string]$property.Value, 'Process')
    }
    Write-Host 'Pruebas: PostgreSQL con datos ficticios, modelo local real.'
}
Push-Location (Join-Path $projectRoot 'backend')
try {
    uv run --frozen --python 3.12 python -m app.run
    if ($LASTEXITCODE -ne 0) { throw "API terminó con código $LASTEXITCODE" }
} finally { Pop-Location }
