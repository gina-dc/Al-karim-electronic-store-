$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
& (Join-Path $projectRoot '.tools/pgsql/bin/pg_ctl.exe') stop -D (Join-Path $projectRoot '.runtime/postgres-data') -m fast -w
if ($LASTEXITCODE -ne 0) { throw 'Database stop failed.' }
