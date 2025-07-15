# --- Builder image (optional) ---
FROM python:3.12-slim AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Install deps
COPY distributor/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY distributor /app

# Expose & run
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
