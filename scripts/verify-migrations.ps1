$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$dbPassword=[IO.File]::ReadAllText((Join-Path $projectRoot '.runtime/postgres-password'))
$dbName='shop_migrations_'+(Get-Date -Format 'yyyyMMddHHmmss')+'_test'
$env:PGPASSWORD=$dbPassword
try {
    & (Join-Path $projectRoot '.tools/pgsql/bin/createdb.exe') -h 127.0.0.1 -p 55432 -U shop $dbName
    if ($LASTEXITCODE -ne 0) { throw 'Fresh test database creation failed.' }
} finally { Remove-Item Env:PGPASSWORD }
$env:DATABASE_URL="postgres://shop:${dbPassword}@127.0.0.1:55432/$dbName"
Push-Location (Join-Path $projectRoot 'backend')
try {
    uv run aerich upgrade
    if ($LASTEXITCODE -ne 0) { throw 'Fresh migration failed.' }
    uv run aerich upgrade
    if ($LASTEXITCODE -ne 0) { throw 'Repeated migration failed.' }
    Write-Output "Fresh migrations verified in $dbName; database retained for inspection."
} finally { Pop-Location; Remove-Item Env:DATABASE_URL }
