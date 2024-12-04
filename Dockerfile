# Dockerfile

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create models directory
RUN mkdir -p /app/models

# Ensure the models directory is writable
VOLUME /app/models

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80"]
