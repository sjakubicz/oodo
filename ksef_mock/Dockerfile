FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /usr/local/bin/uv
ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"
WORKDIR /workspace
COPY pyproject.toml uv.lock ./
COPY app/pyproject.toml app/
COPY ksef_mock/pyproject.toml ksef_mock/
RUN uv sync --frozen --package ksef-mock --no-dev
WORKDIR /workspace/ksef_mock
COPY ksef_mock/ ./
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
