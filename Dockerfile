# ── Stage 1: build frontend ───────────────────────────────────────────────
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ── Stage 2: backend + frontend dist ──────────────────────────────────────
FROM python:3.11-slim
WORKDIR /app

# Dependências Python
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Código backend
COPY backend/ ./backend

# CSV de jogos (necessário para o sistema)
COPY jogos.csv ./jogos.csv

# Frontend buildado
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Pasta de dados persistente (Railway volume ou pasta local)
RUN mkdir -p /app/dados

ENV DADOS_DIR=/app/dados
ENV JOGOS_CSV=/app/jogos.csv
ENV PORT=8000

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
