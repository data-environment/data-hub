from __future__ import annotations

from typing import Any
from urllib.parse import quote, unquote

import streamlit as st

from components.home_page_link import home_page_link
from wiki import contexts, registry
from wiki.contexts import ContextNode
from wiki.engine import ContractDoc, SchemaField, build_doc

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


def render_breadcrumb(path: list[str]) -> None:
    crumbs = ["🏠 Wiki"] + path
    links = [
        f'<a href="?ctx={quote("/".join(path[:i]))}" target="_self">{label}</a>'
        for i, label in enumerate(crumbs[:-1])
    ]
    st.markdown(
        " › ".join([*links, crumbs[-1]]),
        unsafe_allow_html=True,
    )


def render_context_grid(
    node: dict[str, ContextNode], path: list[str], by_name: dict
) -> None:
    render_breadcrumb(path)
    st.divider()

    children = sorted(node.items())
    cols = st.columns(3)
    for i, (label, child) in enumerate(children):
        href = "?ctx=" + quote("/".join([*path, label]))
        if isinstance(child, dict):
            icon = "📁"
            subtitle = f"{contexts.count_leaves(child)} contrato(s)"
        else:
            contract = by_name.get(child)
            icon = "📄"
            subtitle = (
                contract.general.description or contract.general.display_name
                if contract
                else "Contrato não encontrado"
            )
        with cols[i % 3]:
            home_page_link(icon=icon, title=label, subtitle=subtitle, page=href)


def main() -> None:
    contracts = registry.list_contracts()

    by_name = {c.general.system_name: c for c in contracts}

    root: dict[str, ContextNode] = {**contexts.CONTEXT_TREE}

    raw_ctx = st.query_params.get("ctx", "")
    path = [unquote(p) for p in raw_ctx.split("/") if p]

    node = contexts.resolve(root, path)

    if isinstance(node, str):
        contract = by_name.get(node)
        render_breadcrumb(path)
        st.divider()
        render_contract(build_doc(contract))
    else:
        render_context_grid(node, path, by_name)


main()
