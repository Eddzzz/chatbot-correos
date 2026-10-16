param([switch]$Fixture)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$institutionalConfig = Join-Path $projectRoot '.runtime/institutional-env.json'
if ($Fixture -or (Test-Path -LiteralPath $institutionalConfig)) {
    $privateConfig = if ($Fixture) { Join-Path $projectRoot '.runtime/local-env.json' } else { $institutionalConfig }
    if (-not (Test-Path -LiteralPath $privateConfig)) { throw 'Falta configuración local. Consulta README.md.' }
    $configuration = Get-Content -LiteralPath $privateConfig -Raw | ConvertFrom-Json
    foreach ($property in $configuration.PSObject.Properties) {
        [Environment]::SetEnvironmentVariable($property.Name, [string]$property.Value, 'Process')
    }
    if ($Fixture) {
        [Environment]::SetEnvironmentVariable('CHATBOT_DATA_SNAPSHOT', '', 'Process')
        Write-Host 'Pruebas: PostgreSQL con datos ficticios, modelo local real.'
    } else { Write-Host 'Datos reales del respaldo local; conexión de solo lectura.' }
}
Push-Location (Join-Path $projectRoot 'backend')
try {
    uv run --frozen --python 3.12 python -m app.run
    if ($LASTEXITCODE -ne 0) { throw "API terminó con código $LASTEXITCODE" }
} finally { Pop-Location }
