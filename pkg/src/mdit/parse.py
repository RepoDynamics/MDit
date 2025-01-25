from __future__ import annotations
import re as _re

import pyserials as _ps


def frontmatter(file_content: str) -> dict:
    match = _re.match(r'^---+\s*\n(.*?)(?=\n---+\s*(\n|$))', file_content, _re.DOTALL)
    if not match:
        return {}
    frontmatter_text = match.group(1).strip()
    frontmatter_dict = _ps.read.yaml_from_string(frontmatter_text)
    return frontmatter_dict


def title(file_content: str) -> str | None:
    match = _re.search(r"^# (.*)", file_content, _re.MULTILINE)
    return match.group(1) if match else ""


def toctree(file_content: str) -> tuple[str, ...] | None:
    matches = _re.findall(r"(:{3,}){toctree}\s((.|\s)*?)\s\1", file_content, _re.DOTALL)
    if not matches:
        return
    toctree_str = matches[0][1]
    toctree_entries = []
    for line in toctree_str.splitlines():
        entry = line.strip()
        if entry and not entry.startswith(":"):
            toctree_entries.append(entry)
    return tuple(toctree_entries)
