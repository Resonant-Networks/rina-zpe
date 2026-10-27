FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir "mcp==1.9.4"  requests uvicorn

COPY nodegrid_readonly_mcp.py .

CMD ["python", "nodegrid_readonly_mcp.py"]
