# --- Build stage ---
FROM python:3.11-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# --- Runtime stage ---
FROM python:3.11-slim

RUN groupadd -r promptguard && useradd -r -g promptguard promptguard

WORKDIR /app

COPY --from=builder /root/.local /home/promptguard/.local
ENV PATH=/home/promptguard/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

COPY app ./app
COPY entrypoint.sh .
RUN mkdir -p /app/data && chmod +x entrypoint.sh && chown -R promptguard:promptguard /app

USER promptguard

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
