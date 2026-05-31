FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# El código será montado como volumen mediante docker-compose
COPY . .

EXPOSE 8000
