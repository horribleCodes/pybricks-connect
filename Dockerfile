FROM python:3.14-alpine

COPY --from=docker.io/astral/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY server/ ./
COPY server_data/ ./server_data/

EXPOSE 5000

CMD ["uv", "run", "--no-dev", "python", "app.py"]
