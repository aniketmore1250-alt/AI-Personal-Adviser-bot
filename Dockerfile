FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=3000

WORKDIR /app

RUN mkdir -p /app/instance

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY .

EXPOSE 1000

CMD ["sh", "-c", "python -m gunicorn --bind 0.0.0.0:${PORT:-3000} --workers 2 --timeout 120 run:app"]
