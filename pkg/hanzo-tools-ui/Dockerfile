FROM python:3.12-slim AS builder

WORKDIR /build
COPY pkg/hanzo-tools-ui/ ./pkg/hanzo-tools-ui/
COPY pkg/hanzo-tools-core/ ./pkg/hanzo-tools-core/

RUN pip install --no-cache-dir \
    ./pkg/hanzo-tools-core \
    "./pkg/hanzo-tools-ui[server]"

FROM python:3.12-slim

RUN useradd -m -r hanzo
WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/hanzo-ui-registry /usr/local/bin/

USER hanzo
EXPOSE 8787

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8787/api/health')"

ENV REGISTRY_HOST=0.0.0.0 \
    REGISTRY_PORT=8787

CMD ["python", "-m", "uvicorn", "hanzo_tools.ui.registry.server:app", "--host", "0.0.0.0", "--port", "8787"]
