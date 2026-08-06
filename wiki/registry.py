"""Descobre e indexa todos os DataContracts publicados em data_contracts.

Lê `data_contracts.definitions.registry` dinamicamente, então qualquer novo
contrato adicionado lá aparece aqui sem precisar tocar neste arquivo.
"""

from __future__ import annotations

from data_contracts.definitions import registry as _registry
from data_contracts.model import DataContract


def _discover() -> dict[str, DataContract]:
    contracts: dict[str, DataContract] = {}
    for name in getattr(_registry, "__all__", dir(_registry)):
        obj = getattr(_registry, name, None)
        if isinstance(obj, DataContract):
            contracts[obj.general.system_name] = obj
    return contracts


CONTRACTS: dict[str, DataContract] = _discover()


def list_contracts() -> list[DataContract]:
    return sorted(CONTRACTS.values(), key=lambda c: c.general.display_name)


def get_contract(system_name: str) -> DataContract:
    return CONTRACTS[system_name]


def all_tags() -> list[str]:
    tags = {tag for c in CONTRACTS.values() for tag in (c.general.tags or [])}
    return sorted(tags)
