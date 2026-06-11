"""
CLI interface for memory-store.

Usage:
    python -m memory_store get <category> [key]
    python -m memory_store set <category> <key> <value>
    python -m memory_store delete <category> [key]
    python -m memory_store search <text>
    python -m memory_store preview
    python -m memory_store clear

All commands support --json for structured output.

Conforms to Principle VI:
    - Accepts text as input (arguments, stdin)
    - Produces text as output (stdout)
    - Supports JSON format (--json flag)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from memory_store import MemoryStore


def _get_store() -> MemoryStore:
    file_path = os.environ.get(
        "MEMORY_STORE_FILE",
        str(Path.cwd() / "memory.json"),
    )
    return MemoryStore(file_path=file_path)


def cmd_get(args: list[str], use_json: bool) -> int:
    if not args:
        print("Usage: memory-store get <category> [key]", file=sys.stderr)
        return 1
    store = _get_store()
    key = ".".join(args)
    value = store.get(key)
    if value is None:
        if use_json:
            json.dump({"error": "not_found", "key": key}, sys.stdout)
            sys.stdout.write("\n")
        else:
            print(f"Kayit bulunamadi: {key}", file=sys.stderr)
        return 1
    if use_json:
        json.dump({"key": key, "value": value}, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
    else:
        print(value)
    return 0


def cmd_set(args: list[str], use_json: bool) -> int:
    if len(args) < 2:
        print("Usage: memory-store set <category> <key> <value>", file=sys.stderr)
        return 1
    key = ".".join(args[:-1])
    value = args[-1]
    # Try parsing as JSON
    try:
        parsed = json.loads(value)
        value = parsed
    except (json.JSONDecodeError, ValueError):
        pass
    store = _get_store()
    store.set(key, value)
    if use_json:
        json.dump({"key": key, "value": value}, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
    else:
        print(f"Kaydedildi: {key} = {value}")
    return 0


def cmd_delete(args: list[str], use_json: bool) -> int:
    if not args:
        print("Usage: memory-store delete <category> [key]", file=sys.stderr)
        return 1
    store = _get_store()
    if len(args) == 1:
        msg = store.delete(category=args[0])
    else:
        msg = store.delete(category=args[0], key=args[1])
    if use_json:
        json.dump({"message": msg}, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
    else:
        print(msg)
    return 0 if "kaldirildi" in msg else 1


def cmd_search(args: list[str], use_json: bool) -> int:
    if not args:
        print("Usage: memory-store search <text>", file=sys.stderr)
        return 1
    store = _get_store()
    results = store.search(" ".join(args))
    if use_json:
        json.dump(results, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        if not results:
            print("Eslesme bulunamadi.")
            return 0
        for r in results:
            print(f"  {r['category']}/{r['key']}: {r['value']}")
    return 0


def cmd_preview(args: list[str], use_json: bool) -> int:
    store = _get_store()
    output = store.format()
    if use_json:
        json.dump({"preview": output}, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
    else:
        print(output if output else "(empty)")
    return 0


def cmd_clear(args: list[str], use_json: bool) -> int:
    store = _get_store()
    store.clear()
    if use_json:
        json.dump({"status": "cleared"}, sys.stdout)
        sys.stdout.write("\n")
    else:
        print("Hafiza temizlendi.")
    return 0


def main() -> int:
    args = sys.argv[1:] if len(sys.argv) > 1 else ["preview"]
    use_json = "--json" in args
    args = [a for a in args if a != "--json"]

    command = args[0] if args else "preview"

    commands = {
        "get": cmd_get,
        "set": cmd_set,
        "delete": cmd_delete,
        "search": cmd_search,
        "preview": cmd_preview,
        "clear": cmd_clear,
    }

    handler = commands.get(command)
    if handler is None:
        print(f"Bilinmeyen komut: {command}", file=sys.stderr)
        print(__doc__)
        return 1
    return handler(args[1:], use_json)


if __name__ == "__main__":
    sys.exit(main())
