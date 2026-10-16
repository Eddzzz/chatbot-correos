param([ValidateRange(1,16)][int]$Threads = 4)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$server = Get-ChildItem -LiteralPath (Join-Path $projectRoot '.runtime/llama-cpu') -Filter llama-server.exe -Recurse | Select-Object -First 1
if (-not $server) { throw 'Ejecuta python scripts/setup_inference.py primero.' }
$model = Join-Path $projectRoot 'models/Qwen3.5-2B-Q4_K_M.gguf'
if (-not (Test-Path -LiteralPath $model)) { throw 'Falta modelo verificado. Ejecuta scripts/setup_inference.py.' }
& $server.FullName --model $model --host 127.0.0.1 --port 8081 --n-gpu-layers 0 --no-op-offload --ctx-size 4096 --parallel 1 --threads $Threads --reasoning off --jinja --no-webui --cors-origins http://127.0.0.1:8081 --no-cors-credentials
if ($LASTEXITCODE -ne 0) { throw "llama-server terminó con código $LASTEXITCODE" }
