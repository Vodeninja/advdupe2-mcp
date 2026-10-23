param(
    [string]$GameDir = $env:ADV2MCP_GAME_DIR
)
$ErrorActionPreference = 'Stop'
if (-not $GameDir) {
    if ($env:ADV2MCP_DUPE_DIR) {
        $GameDir = Split-Path -Parent (Split-Path -Parent $env:ADV2MCP_DUPE_DIR)
    } else {
        $steamRoot = ${env:ProgramFiles(x86)}
        if (-not $steamRoot) { $steamRoot = 'C:\Program Files (x86)' }
        $GameDir = Join-Path $steamRoot 'Steam\steamapps\common\GarrysMod\garrysmod'
    }
}
if (-not (Test-Path -LiteralPath $GameDir -PathType Container)) {
    throw "Game directory does not exist: $GameDir"
}
$sourceFile = Join-Path $PSScriptRoot 'gmod_addon\adv2mcp_export\lua\autorun\client\adv2mcp_export.lua'
$targetDir = Join-Path $GameDir 'addons\adv2mcp_export\lua\autorun\client'
$null = New-Item -ItemType Directory -Path $targetDir -Force
Copy-Item -LiteralPath $sourceFile -Destination (Join-Path $targetDir 'adv2mcp_export.lua') -Force
Write-Output 'Exporter installed. Restart GMod, join the server, and open the Q menu.'
Write-Output 'Console: adv2mcp_export_props (or adv2mcp_capture_props for custom tabs).'

