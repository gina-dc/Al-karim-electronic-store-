FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:0.11.23 /uv /usr/local/bin/uv
WORKDIR /workspace
COPY pyproject.toml uv.lock README.md ./
COPY backend/pyproject.toml backend/README.md backend/
RUN uv sync --locked --package backend --no-dev
COPY backend backend
WORKDIR /workspace/backend
ENV PATH="/workspace/.venv/bin:$PATH"
RUN useradd --create-home appuser
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-proxy-headers"]
