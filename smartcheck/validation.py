from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from io import BytesIO
from typing import Any, get_args

import pandas as pd
from data_contracts.model import CSV
from data_contracts.model.data_ingestion.file_format import XLSX, FileFormat
from data_contracts.model.data_quality.data_quality import check_no_duplicates
from pydantic import BaseModel, TypeAdapter, ValidationError


class FileReadError(Exception):
    """Erro tratado ao ler o arquivo enviado (formato/encoding incompatível)."""


@dataclass
class SchemaError:
    linha: int
    campo: str
    mensagem: str


@dataclass
class QualityError:
    check: str
    mensagem: str


def read_uploaded_file(uploaded_file, file_format: FileFormat) -> pd.DataFrame:
    """Lê o arquivo enviado como texto puro — a coerção de tipo é responsabilidade
    do schema pydantic do contrato, não do pandas."""
    raw = uploaded_file.getvalue()
    try:
        if isinstance(file_format, CSV):
            return pd.read_csv(
                BytesIO(raw),
                sep=file_format.separator,
                encoding=file_format.encoding,
                header=0 if file_format.header else None,
                quotechar=file_format.quote_char,
                escapechar=file_format.escape_char,
                na_values=(
                    [file_format.null_value]
                    if file_format.null_value is not None
                    else None
                ),
                keep_default_na=False,
                dtype=str,
            )
        if isinstance(file_format, XLSX):
            return pd.read_excel(
                BytesIO(raw),
                sheet_name=file_format.sheet_name,
                header=file_format.header_row - 1,
                dtype=str,
            )
    except Exception as exc:
        raise FileReadError(
            f"Não foi possível ler o arquivo no formato esperado "
            f"({file_format.type}): {exc}"
        ) from exc
    raise FileReadError(f"Formato de arquivo não suportado: {file_format.type}")


def _decimal_aliases(model: type[BaseModel]) -> list[str]:
    aliases = []
    for name, field in model.model_fields.items():
        if field.annotation is Decimal or Decimal in get_args(field.annotation):
            aliases.append(field.alias or name)
    return aliases


def _normalize_brazilian_decimals(
    rows: list[dict[str, Any]], model: type[BaseModel]
) -> None:
    """Converte valores decimais no formato BR ("1.234,56") para o formato
    aceito por `decimal.Decimal` ("1234.56"), e células vazias ("") para
    `None`, só nas colunas tipadas como `Decimal` no schema — os arquivos de
    origem usam vírgula como separador decimal e string vazia para ausência
    de valor, e o Python `Decimal` não entende nenhum dos dois."""
    for alias in _decimal_aliases(model):
        for row in rows:
            value = row.get(alias)
            if isinstance(value, str):
                if value == "":
                    row[alias] = None
                elif "," in value:
                    row[alias] = value.replace(".", "").replace(",", ".")


def validate_schema(
    df: pd.DataFrame, model: type[BaseModel]
) -> tuple[list[dict[str, Any]], list[SchemaError]]:
    """Valida o arquivo inteiro (indexado pelos aliases do schema) contra o
    modelo pydantic do contrato numa única passada. Retorna os registros já
    convertidos para nome de campo (não alias) e a lista de erros, um por
    (linha, campo). Se qualquer linha falhar, nenhum registro é retornado —
    só a lista de erros."""
    rows = df.to_dict(orient="records")
    _normalize_brazilian_decimals(rows, model)
    try:
        parsed = TypeAdapter(list[model]).validate_python(rows)
    except ValidationError as exc:
        errors = []
        for error in exc.errors():
            linha, *resto = error["loc"]
            campo = ".".join(str(loc) for loc in resto) or "-"
            errors.append(
                SchemaError(linha=linha + 2, campo=campo, mensagem=error["msg"])
            )
        return [], errors
    return [record.model_dump() for record in parsed], []


def run_data_quality_checks(
    records: list[dict[str, Any]], checks: dict[Any, Any]
) -> tuple[list[QualityError], list[str]]:
    """Roda os checks de qualidade declarados no contrato. Só reconhece
    `check_no_duplicates` hoje — checks desconhecidos são reportados como
    `unknown` em vez de silenciosamente ignorados, para não esconder lacuna
    de cobertura."""
    errors: list[QualityError] = []
    unknown: list[str] = []
    for check, params in checks.items():
        if check is check_no_duplicates:
            columns = params
            seen: dict[tuple[Any, ...], int] = {}
            for i, record in enumerate(records):
                key = tuple(record.get(c) for c in columns)
                if key in seen:
                    errors.append(
                        QualityError(
                            check="check_no_duplicates",
                            mensagem=(
                                f"Linha {i + 2} duplica a chave "
                                f"{dict(zip(columns, key))} já vista na linha "
                                f"{seen[key]}."
                            ),
                        )
                    )
                else:
                    seen[key] = i + 2
        else:
            unknown.append(getattr(check, "__name__", str(check)))
    return errors, unknown
