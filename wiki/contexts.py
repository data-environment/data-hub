from __future__ import annotations

from collections.abc import Iterator

type ContextNode = dict[str, "ContextNode"] | str

CONTEXT_TREE: dict[str, ContextNode] = {
    "XP": {
        "Positivador": "xp_positivador",
    },
    "Parceiros": {
        "Avenue": {
            "Avenue FX": "avenue_fx",
        },
    },
}


def resolve(node: ContextNode, path: list[str]) -> ContextNode | None:
    for segment in path:
        if not isinstance(node, dict) or segment not in node:
            return None
        node = node[segment]
    return node


def iter_leaf_values(node: ContextNode) -> Iterator[str]:
    if isinstance(node, str):
        yield node
    else:
        for child in node.values():
            yield from iter_leaf_values(child)


def count_leaves(node: ContextNode) -> int:
    return sum(1 for _ in iter_leaf_values(node))
