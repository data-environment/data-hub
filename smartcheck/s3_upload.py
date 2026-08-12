from __future__ import annotations

from datetime import date

import boto3
import streamlit as st
from botocore.exceptions import BotoCoreError, ClientError
from data_contracts.model import DataContract


class S3UploadError(Exception):
    """Erro tratado ao subir o arquivo para o S3."""


def build_s3_key(contract: DataContract, reference_date: date) -> str:
    s3_ingestion = contract.data_ingestion.s3_ingestion
    return f"{s3_ingestion.s3_path}/{reference_date.isoformat()}/{s3_ingestion.s3_file}"


def _s3_client():
    try:
        aws_secrets = st.secrets["aws"]
    except KeyError as exc:
        raise S3UploadError(
            "Credenciais da AWS não configuradas (.streamlit/secrets.toml)."
        ) from exc
    return boto3.client(
        "s3",
        aws_access_key_id=aws_secrets["access_key_id"],
        aws_secret_access_key=aws_secrets["secret_access_key"],
        region_name=aws_secrets.get("region", "us-east-1"),
    )


def upload_file(contract: DataContract, reference_date: date, file_bytes: bytes) -> str:
    """Sobe os bytes originais do arquivo (não o DataFrame transformado) para o
    bucket/caminho definidos no contrato. Retorna o caminho final no S3."""
    bucket = contract.data_ingestion.s3_ingestion.s3_bucket
    key = build_s3_key(contract, reference_date)
    client = _s3_client()
    try:
        client.put_object(Bucket=bucket, Key=key, Body=file_bytes)
    except (ClientError, BotoCoreError) as exc:
        raise S3UploadError(f"Falha ao enviar o arquivo para o S3: {exc}") from exc
    return f"s3://{bucket}/{key}"
