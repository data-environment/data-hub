FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# git é necessário para o uv resolver a dependência data-contracts (instalada via git+https).
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Camada de dependências isolada do código para aproveitar o cache do Docker.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project

COPY wiki/ wiki/
RUN uv sync --locked

EXPOSE 8501

HEALTHCHECK CMD uv run python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

CMD ["uv", "run", "streamlit", "run", "wiki/screen.py", "--server.address=0.0.0.0", "--server.port=8501"]
