from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Any

import pandas as pd
from data_contracts.model import CSV
from data_contracts.model.data_ingestion.file_format import XLSX, FileFormat
from data_contracts.model.data_quality.data_quality import check_no_duplicates
from pydantic import BaseModel, ValidationError


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


def validate_schema(
    df: pd.DataFrame, model: type[BaseModel]
) -> tuple[list[dict[str, Any]], list[SchemaError]]:
    """Valida cada linha do arquivo (indexada pelos aliases do schema) contra o
    modelo pydantic do contrato. Retorna os registros já convertidos para nome
    de campo (não alias) e a lista de erros, um por (linha, campo)."""
    records: list[dict[str, Any]] = []
    errors: list[SchemaError] = []
    for i, row in enumerate(df.to_dict(orient="records")):
        try:
            parsed = model.model_validate(row)
        except ValidationError as exc:
            for error in exc.errors():
                campo = ".".join(str(loc) for loc in error["loc"]) or "-"
                errors.append(
                    SchemaError(linha=i + 2, campo=campo, mensagem=error["msg"])
                )
        else:
            records.append(parsed.model_dump())
    return records, errors


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
