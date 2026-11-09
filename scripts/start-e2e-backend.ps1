$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$dbPassword=[IO.File]::ReadAllText((Join-Path $projectRoot '.runtime/postgres-password'))
$pgBin=Join-Path $projectRoot '.tools/pgsql/bin'
$env:PGPASSWORD=$dbPassword
try {
    $exists=& (Join-Path $pgBin 'psql.exe') -h 127.0.0.1 -p 55432 -U shop -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='shop_e2e_test'"
    if ($LASTEXITCODE -ne 0) { throw 'Local database is unavailable.' }
    if ($exists -ne '1') { & (Join-Path $pgBin 'createdb.exe') -h 127.0.0.1 -p 55432 -U shop shop_e2e_test; if ($LASTEXITCODE -ne 0) { throw 'Test database creation failed.' } }
} finally { Remove-Item Env:PGPASSWORD }
$env:DATABASE_URL="postgres://shop:${dbPassword}@127.0.0.1:55432/shop_e2e_test"
$env:FRONTEND_ORIGIN='http://127.0.0.1:5174'
Push-Location (Join-Path $projectRoot 'backend')
try {
    uv run python tests/seed_e2e.py
    if ($LASTEXITCODE -ne 0) { throw 'Test setup failed.' }
    uv run uvicorn app.main:app --host 127.0.0.1 --port 8001
} finally { Pop-Location; Remove-Item Env:DATABASE_URL; Remove-Item Env:FRONTEND_ORIGIN }
