"""App Streamlit que documenta automaticamente os DataContracts do data-contracts.

Rodar com: streamlit run screen.py
"""

from __future__ import annotations

from typing import Any

import registry
import streamlit as st
from engine import ContractDoc, SchemaField, build_doc

STATUS_ICON = {"Active": "🟢", "Inactive": "⚪"}


def render_kv_table(data: dict[str, Any], exclude: set[str] = frozenset()) -> None:
    rows = [
        {"Campo": key.replace("_", " ").capitalize(), "Valor": _format_scalar(value)}
        for key, value in data.items()
        if key not in exclude and not isinstance(value, (dict, list))
    ]
    if rows:
        st.dataframe(rows, hide_index=True, width="stretch")

    for key, value in data.items():
        if key in exclude:
            continue
        if isinstance(value, dict) and value:
            st.caption(key.replace("_", " ").capitalize())
            render_kv_table(value)
        elif isinstance(value, list) and value:
            st.caption(key.replace("_", " ").capitalize())
            render_list_table(value)


def _flatten_item(data: dict[str, Any], prefix: str = "") -> dict[str, str]:
    flat: dict[str, str] = {}
    for key, value in data.items():
        label = f"{prefix}{key.replace('_', ' ').capitalize()}"
        if isinstance(value, dict):
            flat.update(_flatten_item(value, prefix=f"{label} · "))
        else:
            flat[label] = _format_scalar(value)
    return flat


def render_list_table(items: list[Any]) -> None:
    if not items:
        st.caption("Nenhum item.")
        return
    if all(isinstance(item, dict) for item in items):
        rows = [_flatten_item(item) for item in items]
        st.dataframe(rows, hide_index=True, width="stretch")
    else:
        for item in items:
            st.markdown(f"- {_format_scalar(item)}")


def _format_scalar(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "Sim" if value else "Não"
    if isinstance(value, list):
        return ", ".join(str(v) for v in value) if value else "—"
    return str(value)


def render_general(doc: ContractDoc) -> None:
    general = doc.general
    icon = STATUS_ICON.get(general.get("status"), "⚪")
    st.title(general.get("display_name", ""))
    st.caption(
        f"`{general.get('system_name')}` · pipeline `{general.get('pipeline_id')}`"
    )

    cols = st.columns(4)
    cols[0].metric("Status", f"{icon} {general.get('status')}")
    cols[1].metric("Versão", general.get("version"))
    cols[2].metric("Exige CNPJ", "Sim" if general.get("cnpj_needed") else "Não")
    cols[3].metric("Tags", ", ".join(general.get("tags") or []) or "—")

    st.markdown("**Descrição**")
    st.write(general.get("description") or "—")
    st.markdown("**Justificativa de negócio**")
    st.write(general.get("business_justification") or "—")

    approved_by = general.get("approved_by")
    approved_at = general.get("approved_at")
    if approved_by or approved_at:
        st.caption(f"Aprovado por {approved_by or '—'} em {approved_at or '—'}")
    else:
        st.caption("Ainda não aprovado por nenhuma área de negócio.")


def render_schema(schema_fields: list[SchemaField]) -> None:
    if not schema_fields:
        st.caption("Contrato sem schema definido.")
        return

    rows = [
        {
            "Campo": f.name,
            "Alias na fonte": f.alias or "—",
            "Tipo": f.type,
            "Obrigatório": "Sim" if f.required else "Não",
            "Default": "—" if f.default is None else str(f.default),
            "Chave única": "🔑" if f.unique_key else "",
            "Sensível (PII)": "🔒" if f.sensitive else "",
            "Descrição": f.description or "—",
        }
        for f in schema_fields
    ]
    st.dataframe(rows, hide_index=True, width="stretch")

    unique_key_fields = [f.name for f in schema_fields if f.unique_key]
    sensitive_fields = [f.name for f in schema_fields if f.sensitive]
    cols = st.columns(2)
    cols[0].caption(
        f"🔑 Chave única: {', '.join(unique_key_fields) or 'nenhuma marcada'}"
    )
    cols[1].caption(
        f"🔒 Dados sensíveis (LGPD): {', '.join(sensitive_fields) or 'nenhum marcado'}"
    )


def render_data_quality(data_quality: dict[str, Any]) -> None:
    checks = data_quality.get("checks") or {}
    if not checks:
        st.caption("Nenhum check de qualidade definido.")
        return
    rows = [
        {"Check": name, "Parâmetros": _format_scalar(params)}
        for name, params in checks.items()
    ]
    st.dataframe(rows, hide_index=True, width="stretch")


def render_contract(doc: ContractDoc) -> None:
    render_general(doc)

    tabs = st.tabs(
        [
            "Fonte & Extração",
            "Schema",
            "Qualidade",
            "Ingestão",
            "Distribuição",
            "Transformação",
            "Regras de negócio",
        ]
    )

    with tabs[0]:
        st.subheader("Fonte de dados")
        render_kv_table(doc.data_source)
        st.divider()
        st.subheader("Extração")
        render_kv_table(doc.data_extraction)

    with tabs[1]:
        st.subheader("Schema")
        render_schema(doc.schema_fields)

    with tabs[2]:
        st.subheader("Qualidade de dados")
        render_data_quality(doc.data_quality)

    with tabs[3]:
        st.subheader("Ingestão")
        render_kv_table(doc.data_ingestion)

    with tabs[4]:
        st.subheader("Consumidores")
        render_list_table(doc.distribution.get("consumers", []))

    with tabs[5]:
        st.subheader("Funções de transformação")
        render_list_table(doc.transformation.get("functions", []))

    with tabs[6]:
        st.subheader("Regras de negócio")
        render_list_table(doc.business_rules.get("rules", []))


def main() -> None:
    st.set_page_config(page_title="Data Hub · Contratos de Dados", layout="wide")

    contracts = registry.list_contracts()
    if not contracts:
        st.warning(
            "Nenhum DataContract encontrado em data_contracts.definitions.registry."
        )
        return

    with st.sidebar:
        st.header("Contratos de Dados")
        tags = registry.all_tags()
        selected_tags = st.multiselect("Filtrar por tag", tags)
        filtered = [
            c
            for c in contracts
            if not selected_tags or set(c.general.tags or []) & set(selected_tags)
        ]
        options = [c.general.system_name for c in filtered] or [
            c.general.system_name for c in contracts
        ]
        selected = st.radio(
            "Contrato",
            options,
            format_func=lambda name: registry.get_contract(name).general.display_name,
        )

    doc = build_doc(registry.get_contract(selected))
    render_contract(doc)


main()
