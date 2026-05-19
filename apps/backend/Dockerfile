FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md alembic.ini ./
COPY migrations ./migrations
COPY src ./src

RUN pip install --no-cache-dir .

COPY start.sh ./
RUN chmod +x start.sh

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["/app/start.sh"]
