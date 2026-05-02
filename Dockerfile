FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock* README.md config.toml ./
COPY src ./src

RUN uv sync --frozen --no-dev || uv sync --no-dev

ENTRYPOINT ["uv", "run", "gmail-tool"]
