FROM python:latest

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY orderbook_ws.py .

COPY wait.sh .
RUN chmod +x ./wait.sh

# CMD ["python", "./orderbook_ws.py"]