FROM python:latest

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY telegramBot.py .

COPY wait.sh .
RUN chmod +x ./wait.sh

# CMD ["python", "./telegramBot.py"]