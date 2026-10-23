$ErrorActionPreference = 'Stop'
$localConfig = Join-Path $PSScriptRoot 'mcp.config.json'
if (Test-Path -LiteralPath $localConfig) {
    $config = Get-Content -LiteralPath $localConfig -Raw | ConvertFrom-Json
    foreach ($setting in $config.mcpServers.adv2mcp.env.PSObject.Properties) {
        if (-not [Environment]::GetEnvironmentVariable($setting.Name, 'Process')) {
            [Environment]::SetEnvironmentVariable($setting.Name, [string]$setting.Value, 'Process')
        }
    }
}
$pythonPath = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Run python -m venv .venv and .\.venv\Scripts\python.exe -m pip install -e . first.'
}
& $pythonPath -m adv2mcp @args
exit $LASTEXITCODE

