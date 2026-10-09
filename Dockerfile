FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY lacan_agent ./lacan_agent
RUN pip install --no-cache-dir .
ENV LACAN_DB_PATH=/data/lacan.db LACAN_STORAGE_PATH=/data/storage
EXPOSE 8000
CMD ["uvicorn", "lacan_agent.api:app", "--host", "0.0.0.0", "--port", "8000"]
