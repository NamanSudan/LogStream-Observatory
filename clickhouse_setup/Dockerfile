FROM python:3.9

WORKDIR /app

COPY setup_clickhouse.py .
COPY requirements.txt .

RUN pip install -r requirements.txt

CMD ["python", "setup_clickhouse.py"]