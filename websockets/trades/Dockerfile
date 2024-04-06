FROM python:latest

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY trades_ws.py .

COPY wait.sh .
RUN chmod +x ./wait.sh

# CMD ["python", "./trades_ws.py"]