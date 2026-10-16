$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$env:PGPASSFILE = Join-Path $projectRoot '.runtime/reader-pgpass'
$psqlPath = 'C:/Program Files/PostgreSQL/18/bin/psql.exe'
$connection = @('-w', '-h', '127.0.0.1', '-p', '55432', '-U', 'chatbot_fixture', '-d', 'correos_sandbox_fixture')
$results = & $psqlPath @connection -v ON_ERROR_STOP=1 -Atc "BEGIN READ ONLY; SELECT count(*)=0 FROM chatbot.v_tracking; SET LOCAL chatbot.access_scope='global_internal'; SELECT count(*)=5 FROM chatbot.v_tracking; SELECT count(*)=1 FROM chatbot.v_offices; COMMIT; SELECT count(*)=0 FROM chatbot.v_tracking;"
if ($LASTEXITCODE -ne 0 -or @($results | Where-Object { $_ -eq 't' }).Count -ne 4) { throw 'Projection or scope cleanup failed' }
$null = & $psqlPath @connection -Atc 'SELECT * FROM public.paquetes_certi' 2>&1
if ($LASTEXITCODE -eq 0) { throw 'Unexpected raw-table access' }
$null = & $psqlPath @connection -Atc "INSERT INTO public.estados VALUES(99,'forbidden')" 2>&1
if ($LASTEXITCODE -eq 0) { throw 'Unexpected write access' }
Write-Output 'PASS: scoped projection, scope cleanup, raw-table denial, write denial.'
