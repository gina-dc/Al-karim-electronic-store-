$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$dbPassword = [IO.File]::ReadAllText((Join-Path $projectRoot '.runtime/postgres-password'))
$env:TEST_DATABASE_URL = "postgres://shop:${dbPassword}@127.0.0.1:55432/shop_test"
Push-Location (Join-Path $projectRoot 'backend')
try { uv run pytest; if ($LASTEXITCODE -ne 0) { throw 'Backend tests failed.' } }
finally { Pop-Location; Remove-Item Env:TEST_DATABASE_URL }
