#!/usr/bin/env python3
"""
Docstring-based semantic extractor for graphify.
Reads all .py files in the project, extracts module/class/function docstrings,
and produces semantic nodes + edges that enrich the AST-based graph.

Output: graphify-out/.graphify_semantic_docstrings.json
Merge with existing graph: cat .graphify_semantic_docstrings.json → build()
"""

from __future__ import annotations

import ast
import json
import os
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".venv", "__pycache__", ".git", "Icon", "voice", "logs", "SFX", "Fonts", "helpers", "graphify-out", ".omo"}
OUTPUT = ROOT / "graphify-out" / ".graphify_semantic_docstrings.json"


def _is_code_file(path: Path) -> bool:
    return path.suffix == ".py" and not any(p.startswith(".") for p in path.parts)


def _safe_id(name: str) -> str:
    """Normalize a name to a graph node ID."""
    cleaned = re.sub(r"[^\w]+", "_", name, flags=re.UNICODE)
    cleaned = re.sub(r"_+", "_", cleaned)
    return cleaned.strip("_").casefold()


def extract_docstrings(filepath: Path) -> list[dict]:
    """Parse a .py file and extract docstrings from modules, classes, and functions."""
    nodes: list[dict] = []
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return nodes

    rel_path = filepath.relative_to(ROOT).as_posix()

    # Module docstring
    module_doc = ast.get_docstring(tree)
    if module_doc:
        nodes.append({
            "id": _safe_id(f"{rel_path}_module"),
            "label": rel_path,
            "file_type": "code",
            "source_file": rel_path,
            "source_location": None,
            "docstring": module_doc[:200],  # Truncate long docstrings
        })

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            doc = ast.get_docstring(node)
            if doc:
                node_id = _safe_id(f"{rel_path}_{node.name}")
                nodes.append({
                    "id": node_id,
                    "label": node.name,
                    "file_type": "code",
                    "source_file": rel_path,
                    "source_location": node.lineno,
                    "docstring": doc[:200],
                })
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node)
            if doc and len(doc) > 20:  # Only meaningful docstrings
                node_id = _safe_id(f"{rel_path}_{node.name}")
                # Check if parent is a class
                parent_class = None
                for p in ast.walk(tree):
                    if isinstance(p, ast.ClassDef) and node in ast.walk(p) and p != node:
                        parent_class = p.name
                        break
                label = f"{parent_class}.{node.name}()" if parent_class else f"{node.name}()"
                nodes.append({
                    "id": node_id,
                    "label": label,
                    "file_type": "code",
                    "source_file": rel_path,
                    "source_location": node.lineno,
                    "docstring": doc[:200],
                })

    return nodes


def find_module_edges(nodes: list[dict]) -> list[dict]:
    """Create contains edges between files and their documented entities."""
    edges: list[dict] = []
    # Group nodes by source file
    by_file: dict[str, list[dict]] = {}
    for n in nodes:
        sf = n.get("source_file", "")
        by_file.setdefault(sf, []).append(n)

    for sf, file_nodes in by_file.items():
        file_id = _safe_id(f"{sf}_module")
        for n in file_nodes:
            if n["id"] != file_id:
                edges.append({
                    "source": file_id,
                    "target": n["id"],
                    "relation": "contains",
                    "confidence": "EXTRACTED",
                    "source_file": sf,
                })

    # Create cross-file edges for shared docstring concepts
    # Look for import relationships and cross-references
    concept_keywords = {
        "vad": "VAD",
        "wake word": "WakeWord",
        "noise": "NoiseSuppression",
        "stt": "STT",
        "tts": "TTS",
        "memory": "Memory",
        "skill": "SkillManager",
        "tool": "ToolRegistry",
        "provider": "Provider",
        "gemini": "GeminiProvider",
        "ollama": "OllamaProvider",
        "ui": "JarvisUI",
        "audio": "AudioPipeline",
        "calendar": "Calendar",
        "weather": "Weather",
        "whatsapp": "WhatsApp",
        "youtube": "YouTube",
        "cron": "CronSystem",
        "process": "ProcessManager",
        "network": "NetworkMonitor",
    }

    concept_refs: dict[str, list[str]] = {}
    for n in nodes:
        doc = n.get("docstring", "").lower()
        for keyword, concept in concept_keywords.items():
            if keyword in doc:
                concept_refs.setdefault(concept, []).append(n["id"])

    for concept, refs in concept_refs.items():
        if len(refs) >= 2:
            # Create edges between nodes referring to the same concept
            for i in range(len(refs) - 1):
                edges.append({
                    "source": refs[i],
                    "target": refs[i + 1],
                    "relation": "semantically_similar_to",
                    "confidence": "INFERRED",
                    "confidence_score": 0.65,
                    "source_file": "docstring_extraction",
                })

    return edges


def main():
    all_nodes: list[dict] = []
    all_edges: list[dict] = []
    stats = {"files_parsed": 0, "nodes_extracted": 0, "errors": 0}

    for pyfile in sorted(ROOT.rglob("*.py")):
        # Skip excluded dirs
        if any(p in SKIP_DIRS for p in pyfile.parts):
            continue
        if pyfile.parent.name.startswith(".") or pyfile.name.startswith("."):
            continue

        try:
            nodes = extract_docstrings(pyfile)
            if nodes:
                all_nodes.extend(nodes)
                stats["files_parsed"] += 1
                stats["nodes_extracted"] += len(nodes)
        except Exception:
            stats["errors"] += 1

    all_edges = find_module_edges(all_nodes)

    result = {
        "nodes": all_nodes,
        "edges": all_edges,
        "hyperedges": [],
        "input_tokens": 0,
        "output_tokens": 0,
        "_stats": stats,
    }

    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✅ Docstring extraction complete:")
    print(f"   Files parsed: {stats['files_parsed']}")
    print(f"   Nodes extracted: {stats['nodes_extracted']}")
    print(f"   Edges created: {len(all_edges)}")
    print(f"   Output: {OUTPUT}")


if __name__ == "__main__":
    main()
