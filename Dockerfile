FROM mcr.microsoft.com/playwright/python:v1.54.0-jammy

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY reserve_docker.py .

ENV PYTHONUNBUFFERED=1

CMD ["python", "reserve_docker.py"]
