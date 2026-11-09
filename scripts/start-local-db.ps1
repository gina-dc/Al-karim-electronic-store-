$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pgBin = Join-Path $projectRoot '.tools/pgsql/bin'
$runtimePath = Join-Path $projectRoot '.runtime'
$pgData = Join-Path $runtimePath 'postgres-data'
if (-not (Test-Path (Join-Path $projectRoot '.tools/pgsql/share/postgres.bki'))) { throw 'PostgreSQL binaries are missing or still extracting.' }
New-Item -ItemType Directory -Force -Path $runtimePath | Out-Null
$pwPath = Join-Path $runtimePath 'postgres-password'
if (-not (Test-Path $pgData)) {
    $randomBytes = New-Object byte[] 32
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($randomBytes)
    $dbPassword = [Convert]::ToBase64String($randomBytes).Replace('+','A').Replace('/','B')
    [IO.File]::WriteAllText($pwPath, $dbPassword)
    & (Join-Path $pgBin 'initdb.exe') -D $pgData -U shop --pwfile=$pwPath --auth=scram-sha-256 --encoding=UTF8 --locale=C
    if ($LASTEXITCODE -ne 0) { throw 'Database initialization failed.' }
}
$dbPassword = [IO.File]::ReadAllText($pwPath)
& (Join-Path $pgBin 'pg_ctl.exe') status -D $pgData | Out-Null
if ($LASTEXITCODE -ne 0) {
    & (Join-Path $pgBin 'pg_ctl.exe') start -D $pgData -l (Join-Path $runtimePath 'postgres.log') -o '-h 127.0.0.1 -p 55432' -w
    if ($LASTEXITCODE -ne 0) { throw 'Database startup failed.' }
}
$env:PGPASSWORD = $dbPassword
try {
    foreach ($dbName in @('shop','shop_test')) {
        $exists = & (Join-Path $pgBin 'psql.exe') -h 127.0.0.1 -p 55432 -U shop -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$dbName'"
        if ($LASTEXITCODE -ne 0) { throw 'Database connection failed.' }
        if ($exists -ne '1') {
            & (Join-Path $pgBin 'createdb.exe') -h 127.0.0.1 -p 55432 -U shop $dbName
            if ($LASTEXITCODE -ne 0) { throw 'Database creation failed.' }
        }
    }
} finally { Remove-Item Env:PGPASSWORD }
$backendEnv = Join-Path $projectRoot 'backend/.env'
if (-not (Test-Path $backendEnv)) {
    [IO.File]::WriteAllText($backendEnv, "DATABASE_URL=postgres://shop:${dbPassword}@127.0.0.1:55432/shop`nFRONTEND_ORIGIN=http://localhost:5173`nCOOKIE_SECURE=false`n")
}
Write-Output 'Local PostgreSQL is ready on 127.0.0.1:55432. Credentials are stored in ignored local files.'
