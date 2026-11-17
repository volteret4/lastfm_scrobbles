FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# server.py sincroniza cada SYNC_EVERY_HOURS horas y expone POST /api/jobs/run para
# lanzarlo a mano. La base queda en /data para que otros servicios la monten en solo lectura.
EXPOSE 5000
CMD ["python3", "server.py"]
