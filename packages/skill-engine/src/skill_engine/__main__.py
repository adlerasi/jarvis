"""
CLI interface for skill-engine.

Usage:
    python -m skill_engine list [--json]
    python -m skill_engine info <skill_id>
    python -m skill_engine reload

Conforms to Principle VI:
    - Accepts text as input (arguments, stdin)
    - Produces text as output (stdout)
    - Supports JSON format for structured data exchange (--json flag)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from skill_engine import SkillEngine


def _get_engine() -> SkillEngine:
    """Create a SkillEngine instance, honouring SKILL_ENGINE_SKILLS_DIR env var."""
    skills_dir = os.environ.get(
        "SKILL_ENGINE_SKILLS_DIR",
        str(Path.cwd() / "skills"),
    )
    return SkillEngine(skills_dir=skills_dir, auto_reload=False)


def cmd_list(args: list[str]) -> int:
    """List all loaded skills."""
    use_json = "--json" in args
    engine = _get_engine()
    skills = engine.list_skills()
    if use_json:
        data = [engine.get_skill_info(s).to_dict() for s in skills if engine.get_skill_info(s)]
        json.dump(data, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
    else:
        if not skills:
            print("No skills loaded.")
            return 0
        print(f"Loaded skills ({len(skills)}):\n")
        for sid in skills:
            info = engine.get_skill_info(sid)
            if info:
                print(f"  {sid:30s} v{info.version:8s}  {info.name}")
    return 0


def cmd_info(args: list[str]) -> int:
    """Show detailed info for a single skill."""
    if not args or args[0].startswith("--"):
        print("Usage: skill-engine info <skill_id>", file=sys.stderr)
        return 1
    skill_id = args[0]
    engine = _get_engine()
    info = engine.get_skill_info(skill_id)
    if info is None:
        print(f"Skill not found: {skill_id}", file=sys.stderr)
        return 1
    print(f"  Skill ID:    {info.skill_id}")
    print(f"  Name:        {info.name}")
    print(f"  Version:     {info.version}")
    print(f"  Folder:      {info.folder}")
    print(f"  Module:      {info.module_path}")
    print(f"  Active:      {'yes' if info.is_active else 'no'}")
    print(f"  Load count:  {info.load_count}")
    print(f"  Error count: {info.error_count}")
    print(f"  Loaded at:   {info.loaded_at.isoformat()}")
    if info.last_error:
        print(f"  Last error:  {info.last_error}")
    return 0


def cmd_reload(args: list[str]) -> int:
    """Reload all skills."""
    engine = _get_engine()
    engine.reload_all()
    print(f"Reloaded {len(engine.list_skills())} skills.")
    return 0


def main() -> int:
    args = sys.argv[1:] if len(sys.argv) > 1 else ["list"]
    command = args[0]

    # Allow "skill-engine <subcommand>" or "python -m skill_engine <subcommand>"
    if command in ("list", "ls"):
        return cmd_list(args[1:])
    elif command in ("info", "show"):
        return cmd_info(args[1:])
    elif command in ("reload", "rl"):
        return cmd_reload(args[1:])
    elif command in ("--help", "-h", "help"):
        print(__doc__)
        return 0
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        print(__doc__)
        return 1


if __name__ == "__main__":
    sys.exit(main())
