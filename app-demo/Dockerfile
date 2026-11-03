FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY core ./core
COPY migrations ./migrations
EXPOSE 8000
# Apply pending migrations, then serve. Same behavior against Supabase or a self-hosted Postgres.
CMD ["sh", "-c", "python -m core.migrate && uvicorn core.api:app --host 0.0.0.0 --port 8000"]
