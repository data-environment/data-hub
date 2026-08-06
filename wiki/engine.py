"""Converte um DataContract em uma estrutura de documentação pronta para exibição.

Não depende do Streamlit — a saída é feita só de tipos simples (dict/list/str)
para poder ser testada ou renderizada em qualquer front-end.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from typing import Any

from data_contracts.model import DataContract


def _label(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if callable(value) and not is_dataclass(value):
        return getattr(value, "__name__", str(value))
    return value


def as_plain(value: Any) -> Any:
    """Converte recursivamente valores de um DataContract (dataclasses aninhadas,
    enums, uniões polimórficas como extractor/trigger/inserter, listas e dicts)
    em tipos simples prontos para exibição."""
    value = _label(value)
    if is_dataclass(value) and not isinstance(value, type):
        return {f.name: as_plain(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, (list, tuple)):
        return [as_plain(v) for v in value]
    if isinstance(value, dict):
        return {_label(k): as_plain(v) for k, v in value.items()}
    return value


@dataclass
class SchemaField:
    name: str
    alias: str | None
    type: str
    required: bool
    default: Any
    description: str | None
    unique_key: bool
    sensitive: bool


@dataclass
class ContractDoc:
    contract: DataContract
    general: dict[str, Any]
    data_source: dict[str, Any]
    data_extraction: dict[str, Any]
    schema_fields: list[SchemaField]
    data_quality: dict[str, Any]
    data_ingestion: dict[str, Any]
    distribution: dict[str, Any]
    transformation: dict[str, Any]
    business_rules: dict[str, Any]


def _type_name(annotation: Any) -> str:
    return str(getattr(annotation, "__name__", annotation)).replace("NoneType", "None")


def _schema_fields(contract: DataContract) -> list[SchemaField]:
    model = contract.schema.model
    unique_keys = set(contract.schema.unique_key_columns())
    sensitive = set(contract.schema.sensitive_columns())

    result = []
    for name, info in model.model_fields.items():
        extra = info.json_schema_extra if isinstance(info.json_schema_extra, dict) else {}
        result.append(
            SchemaField(
                name=name,
                alias=info.alias,
                type=_type_name(info.annotation),
                required=info.is_required(),
                default=None if info.is_required() else info.default,
                description=info.description,
                unique_key=name in unique_keys or bool(extra.get("unique_key")),
                sensitive=name in sensitive or bool(extra.get("sensitive")),
            )
        )
    return result


def build_doc(contract: DataContract) -> ContractDoc:
    return ContractDoc(
        contract=contract,
        general=as_plain(contract.general),
        data_source=as_plain(contract.data_source),
        data_extraction=as_plain(contract.data_extraction),
        schema_fields=_schema_fields(contract),
        data_quality=as_plain(contract.data_quality),
        data_ingestion=as_plain(contract.data_ingestion),
        distribution=as_plain(contract.distribution),
        transformation=as_plain(contract.transformation),
        business_rules=as_plain(contract.business_rules),
    )
