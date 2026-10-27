FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

ENV MCP_HOST=0.0.0.0 \
    MCP_PORT=8000 \
    NODEGRID_BASE_URL=https://127.0.0.1 \
    NODEGRID_VERIFY_TLS=0

EXPOSE 8000

CMD ["python", "-u", "server.py"]
