from __future__ import annotations

from importlib import resources


def read_doc(path: str) -> str | None:
    resource = resources.files("data_docs").joinpath(path)
    if not resource.is_file():
        return None
    return resource.read_text(encoding="utf-8")
