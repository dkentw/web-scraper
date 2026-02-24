#!/bin/sh
BUS_STATUS="$(cd "$(dirname "$0")/.." && pwd)/bus_status.py"

uv run python -m scraper --url "https://ebus.gov.taipei/EBus/VsSimpleMap?routeid=0100067200&gb=1" --category "bus"
uv run python "$BUS_STATUS" --stop "基隆長興街口"
