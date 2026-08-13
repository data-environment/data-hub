from __future__ import annotations

from datetime import date
from typing import Any
from urllib.parse import quote

import streamlit as st
from data_contracts.model import CSV, DataContract

from components.home_page_link import home_page_link
from smartcheck import s3_upload, validation
from smartcheck.registry import SMARTCHECK_CONTEXT


def render_result(contract: DataContract, result: dict[str, Any]) -> None:
    if result.get("file_error"):
        st.error(result["file_error"])
        return

    unknown_checks = result["unknown_checks"]
    if unknown_checks:
        st.warning(
            "Checks de qualidade sem implementação, não foram executados: "
            + ", ".join(unknown_checks)
        )

    schema_errors = result["schema_errors"]
    if schema_errors:
        st.error(f"{len(schema_errors)} erro(s) de schema encontrado(s).")
        st.dataframe(
            [
                {"Linha": e.linha, "Campo": e.campo, "Erro": e.mensagem}
                for e in schema_errors[:10]
            ],
            hide_index=True,
            width="stretch",
        )
        if len(schema_errors) > 10:
            st.caption(f"Exibindo os 10 primeiros de {len(schema_errors)} erros.")
        return

    quality_errors = result["quality_errors"]
    if quality_errors:
        st.error(f"{len(quality_errors)} erro(s) de qualidade encontrado(s).")
        st.dataframe(
            [{"Check": e.check, "Erro": e.mensagem} for e in quality_errors],
            hide_index=True,
            width="stretch",
        )
        return

    st.success("Arquivo validado com sucesso.")
    if st.button("Enviar para o S3"):
        try:
            path = s3_upload.upload_file(
                contract, result["reference_date"], result["file_bytes"]
            )
        except s3_upload.S3UploadError as exc:
            st.error(str(exc))
        else:
            st.success(f"Arquivo enviado para `{path}`.")


def render_upload_form(contract: DataContract) -> None:
    inserter = contract.data_ingestion.s3_ingestion.inserter
    file_format = inserter.expected_file_format
    system_name = contract.general.system_name

    st.caption(
        f"Formato esperado: `{file_format.type}` · "
        f"[Modelo de referência]({inserter.model_link})"
    )

    accepted_types = ["csv"] if isinstance(file_format, CSV) else ["xlsx"]
    uploaded_file = st.file_uploader(
        "Arquivo", type=accepted_types, key=f"file_{system_name}"
    )
    reference_date = st.date_input(
        "Data de referência", value=date.today(), key=f"date_{system_name}"
    )

    result_key = f"smartcheck_result_{system_name}"

    if st.button("Validar", type="primary", disabled=uploaded_file is None):
        with st.spinner("Validando o tipo do arquivo..."):
            try:
                df = validation.read_uploaded_file(uploaded_file, file_format)
            except validation.FileReadError as exc:
                st.session_state[result_key] = {"file_error": str(exc)}
                df = None

        if df is not None:
            with st.spinner("Validando a estrutura dos dados..."):
                records, schema_errors = validation.validate_schema(
                    df, contract.schema.model
                )

            with st.spinner("Aplicando os checks de qualidade..."):
                quality_errors, unknown_checks = validation.run_data_quality_checks(
                    records, contract.data_quality.checks
                )

            st.session_state[result_key] = {
                "schema_errors": schema_errors,
                "quality_errors": quality_errors,
                "unknown_checks": unknown_checks,
                "file_bytes": uploaded_file.getvalue(),
                "reference_date": reference_date,
            }

    result = st.session_state.get(result_key)
    if result:
        render_result(contract, result)


def render_context_page(context: str) -> None:
    st.title(context.upper())

    contracts = SMARTCHECK_CONTEXT.get(context)

    if not contracts:
        st.info("Nenhum contrato disponível para este contexto ainda.")
        return

    contract_name = st.selectbox(
        "Contrato",
        sorted(contracts),
        index=None,
        placeholder="Selecione um contrato...",
    )

    if contract_name is None:
        return

    render_upload_form(contracts[contract_name])


def render_context_grid() -> None:
    st.title("✅ SmartCheck")

    cols = st.columns(3)
    for i, (context, contracts) in enumerate(sorted(SMARTCHECK_CONTEXT.items())):
        subtitle = (
            f"{len(contracts)} contrato(s)" if contracts else "Nenhum contrato ainda"
        )
        with cols[i % 3]:
            home_page_link(
                icon="",
                title=context.upper(),
                subtitle=subtitle,
                page=f"?ctx={quote(context)}",
            )


def main() -> None:
    context = st.query_params.get("ctx")

    if context:
        render_context_page(context)
    else:
        render_context_grid()


main()
