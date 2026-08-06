# data-hub

Documentação automática dos [DataContracts](https://github.com/data-environment/data-contracts) em Streamlit.

## Rodando local

### Com uv

Requer [uv](https://docs.astral.sh/uv/) e Python 3.12+ (a versão é fixada em `.python-version`).

```bash
uv sync
uv run streamlit run wiki/screen.py
```

Acesse http://localhost:8501.

### Com Docker

Requer Docker e Docker Compose.

```bash
docker compose up --build
```

Acesse http://localhost:8501.
