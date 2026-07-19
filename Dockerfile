FROM node:22-alpine AS frontend
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt
COPY backend/ /app/backend/
COPY --from=frontend /build/frontend/dist /app/frontend/dist
COPY data/ /app/data/
ENV PYTHONPATH=/app/backend
EXPOSE 8000
CMD ["sh", "-c", "cd /app/backend && alembic upgrade head && exec uvicorn app.main:app --app-dir /app/backend --host 0.0.0.0 --port 8000"]
