"""
CLI for notify-core — send notifications from the command line.
"""
from __future__ import annotations

import json
import sys
from typing import NoReturn

from notify_core import notify


def _cmd_send(args: list[str]) -> dict:
    """send <title> <message> [--priority P] [--json]"""
    args = [a for a in args if a != "--json"]

    priority = "normal"
    if "--priority" in args:
        idx = args.index("--priority")
        if idx + 1 < len(args):
            priority = args[idx + 1]
            args = args[:idx] + args[idx + 2:]

    if len(args) < 2:
        return {"error": "Usage: send <title> <message> [--priority low|normal|critical] [--json]"}

    title = args[0]
    message = " ".join(args[1:])
    ok = notify(title, message, priority=priority)
    return {"status": "delivered" if ok else "fallback", "title": title, "message": message}


def main() -> NoReturn:
    if len(sys.argv) < 2:
        print("Usage: python -m notify_core <command> [args...]", file=sys.stderr)
        print("Commands: send", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    rest = sys.argv[2:]

    if command == "send":
        result = _cmd_send(rest)
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

    json_flag = "--json" in sys.argv
    if json_flag:
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        status = result.get("status", "error")
        print(f"[{status.upper()}] {result.get('title', '')}: {result.get('message', '')}")

    sys.exit(0)


if __name__ == "__main__":
    main()
