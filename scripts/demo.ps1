$env:PYTHONUTF8 = "1"
[Console]::InputEncoding  = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::Unicode

$busStatus = Join-Path $PSScriptRoot "..\bus_status.py"

uv run python -m scraper --url "https://ebus.gov.taipei/EBus/VsSimpleMap?routeid=0100067200&gb=1" --category "bus"
uv run python $busStatus --stop "基隆長興街口"
