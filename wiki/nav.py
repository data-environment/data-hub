from __future__ import annotations

from dataclasses import dataclass

NAV_TREE = {
    "XP": {
        "Positivador": {
            "Contrato": "xp_positivador.py",
            "Documentação": "positivador.md",
        }
    },
    "Parceiros": {
        "Avenue": {
            "Avenue FX": "avenue_fx",
        },
    },
}


@dataclass
class ContractLeaf:
    system_name: str


@dataclass
class DocLeaf:
    doc_path: str


Leaf = ContractLeaf | DocLeaf


def resolve_leaf(value: str, path: list[str]) -> Leaf:
    if value.endswith(".py"):
        return ContractLeaf(system_name=value.removesuffix(".py"))
    if value.endswith(".md"):
        dir_segments = [segment.lower().replace(" ", "_") for segment in path[:-2]]
        return DocLeaf(doc_path="/".join([*dir_segments, value]))
    return ContractLeaf(system_name=value)
