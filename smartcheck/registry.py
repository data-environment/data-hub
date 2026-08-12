from __future__ import annotations

from data_contracts.definitions.registry import POSITIVADOR
from data_contracts.model import DataContract

SMARTCHECK_CONTEXT: dict[str, dict[str, DataContract]] = {
    "xp": {
        "positivador": POSITIVADOR,
    },
    "bitrix": {},
}
