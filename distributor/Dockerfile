# ---- build React ----------
FROM node:18 AS dashboard_builder
WORKDIR /dashboard
COPY dashboard/package*.json ./
RUN npm ci --silent
COPY dashboard/ ./
RUN npm run build

# ---- Python runtime ----
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# deps
COPY distributor/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# copy distributor source code
COPY distributor /app

# copy React build
COPY --from=dashboard_builder /dashboard/dist /app/static

ENV STATIC_DIR=/app/static
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
