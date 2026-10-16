param([string]$PostgresBin = 'C:/Program Files/PostgreSQL/18/bin')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$fixtureRuntime = Join-Path $projectRoot '.runtime'
$fixtureData = Join-Path $fixtureRuntime 'postgres-fixture'
if (Test-Path -LiteralPath $fixtureData) { throw 'Fixture already exists. No existing cluster was modified.' }
New-Item -ItemType Directory -Path $fixtureRuntime -Force | Out-Null
function New-FixtureSecret {
    $bytes = New-Object byte[] 32
    $generator = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $generator.GetBytes($bytes) } finally { $generator.Dispose() }
    return -join ($bytes | ForEach-Object { $_.ToString('x2') })
}
$adminSecret = New-FixtureSecret
$readerSecret = New-FixtureSecret
$passwordFile = Join-Path $fixtureRuntime 'initdb-password'
[IO.File]::WriteAllText($passwordFile, $adminSecret)
& "$PostgresBin/initdb.exe" -D $fixtureData -U fixture_admin --pwfile=$passwordFile --auth=scram-sha-256 --encoding=UTF8 --locale=C
if ($LASTEXITCODE -ne 0) { throw 'initdb failed' }
$env:PGPASSFILE = Join-Path $fixtureRuntime 'pgpass'
[IO.File]::WriteAllText($env:PGPASSFILE, "127.0.0.1:55432:*:fixture_admin:$adminSecret")
& "$PostgresBin/pg_ctl.exe" -D $fixtureData -l "$fixtureRuntime/postgres-fixture.log" -o '-p 55432 -h 127.0.0.1' -w start
if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL start failed; check port 55432 availability' }
& "$PostgresBin/createdb.exe" -w -h 127.0.0.1 -p 55432 -U fixture_admin correos_sandbox_fixture
if ($LASTEXITCODE -ne 0) { throw 'createdb failed' }
& "$PostgresBin/psql.exe" -w -h 127.0.0.1 -p 55432 -U fixture_admin -d correos_sandbox_fixture -v ON_ERROR_STOP=1 -f "$projectRoot/database/fixtures/001_synthetic.sql" -f "$projectRoot/database/views/001_projection.sql" -f "$projectRoot/database/policies/002_reader_role.sql"
if ($LASTEXITCODE -ne 0) { throw 'Fixture SQL failed' }
"CREATE ROLE chatbot_fixture LOGIN PASSWORD '$readerSecret' NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT NOBYPASSRLS; GRANT chatbot_reader TO chatbot_fixture; ALTER ROLE chatbot_fixture SET default_transaction_read_only=on;" | & "$PostgresBin/psql.exe" -w -h 127.0.0.1 -p 55432 -U fixture_admin -d correos_sandbox_fixture -v ON_ERROR_STOP=1 -q
if ($LASTEXITCODE -ne 0) { throw 'Reader creation failed' }
[IO.File]::WriteAllText("$fixtureRuntime/fixture-dsn.txt", "postgresql://chatbot_fixture:$readerSecret@127.0.0.1:55432/correos_sandbox_fixture")
[IO.File]::WriteAllText("$fixtureRuntime/reader-pgpass", "127.0.0.1:55432:*:chatbot_fixture:$readerSecret")
Write-Output 'Synthetic fixture ready at 127.0.0.1:55432; private DSN in .runtime/fixture-dsn.txt'
