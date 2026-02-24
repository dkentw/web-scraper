"""Standalone tool: check if a bus is approaching your target stop.

Reads output/results.json (or a custom path), locates the target stop,
then inspects the stops *before* it for "進站中" (arriving) — each one
found means a bus is on its way to your stop.

Usage:
    python bus_status.py --stop "公館"
    python bus_status.py --stop "公館" --input path/to/results.json
"""

import argparse
import json
import sys
from pathlib import Path

from colorama import Fore, Style, init as colorama_init

ARRIVING = "進站中"
DEFAULT_INPUT = Path(__file__).parent / "output" / "results.json"


def load_result(path: Path) -> dict:
    if not path.exists():
        sys.exit(f"Error: file not found: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def find_stop_index(mapstops: list[list[str]], target: str) -> int | None:
    """Return the list index of the stop whose name matches target, or None."""
    for i, stop in enumerate(mapstops):
        if stop and stop[0] == target:
            return i
    return None


def stop_label(stop: list[str], position: int, total: int) -> str:
    name = stop[0] if stop else "?"
    status = ", ".join(s for s in stop[1:] if s) if len(stop) > 1 else ""
    tag = f"  [{status}]" if status else ""
    return f"[{position}/{total}] {name}{tag}"


def check_bus_status(data: dict, target_stop: str) -> dict:
    """Check whether any bus is approaching the target stop.

    Returns a result dict with the keys:
      - bus_number, direction, total: route metadata
      - target_stop: name of the requested stop
      - target_index: 0-based position of the stop (None if not found)
      - approaching: list of dicts for each approaching bus, each with:
          index, stop, stops_away
      - error: human-readable error string, or None
    """
    mapstops: list[list[str]] = data.get("mapstops", [])

    result = {
        "bus_number": data.get("bus_number", "?"),
        "direction": data.get("direction", "?"),
        "total": len(mapstops),
        "target_stop": target_stop,
        "target_stop_data": None,
        "target_index": None,
        "approaching": [],
        "error": None,
    }

    target_idx = find_stop_index(mapstops, target_stop)
    if target_idx is None:
        result["error"] = f"Stop '{target_stop}' not found on this route."
        return result

    result["target_index"] = target_idx
    result["target_stop_data"] = mapstops[target_idx]

    if target_idx == 0:
        result["error"] = "This is the first stop on the route — no previous stops to check."
        return result

    for i in range(target_idx):
        stop = mapstops[i]
        if ARRIVING in stop:
            result["approaching"].append(
                {"index": i, "stop": stop, "stops_away": target_idx - i}
            )

    return result


def print_status(result: dict) -> None:
    """Print the bus status result produced by check_bus_status()."""
    mapstops_total = result["total"]
    print(f"Bus {result['bus_number']}  |  {result['direction']}\n")

    if result["error"] and result["target_index"] is None:
        print(f"Error: {result['error']}")
        return

    target_idx = result["target_index"]
    print(f"Target stop : {stop_label(result['target_stop_data'], target_idx + 1, mapstops_total)}\n")

    if result["error"]:
        print(result["error"])
        return

    approaching = result["approaching"]
    if not approaching:
        print("No bus is currently approaching your stop.")
        return

    print(f"{'Bus' if len(approaching) == 1 else 'Buses'} approaching ({len(approaching)} found):\n")
    for hit in approaching:
        stops_away = hit["stops_away"]
        label = stop_label(hit["stop"], hit["index"] + 1, mapstops_total)
        proximity = (
            Fore.RED + "next stop is yours — arriving soon!" + Style.RESET_ALL
            if stops_away == 1
            else f"{stops_away} stop{'s' if stops_away > 1 else ''} away"
        )
        print(f"  Currently at {label}")
        print(f"  → {proximity}\n")


def main() -> None:
    colorama_init()
    parser = argparse.ArgumentParser(
        description="Check if a bus is approaching your target stop."
    )
    parser.add_argument("--stop", required=True, help="Target stop name (exact match)")
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Path to results.json (default: {DEFAULT_INPUT})",
    )
    args = parser.parse_args()

    data = load_result(args.input)
    result = check_bus_status(data, args.stop)
    print_status(result)


if __name__ == "__main__":
    main()
