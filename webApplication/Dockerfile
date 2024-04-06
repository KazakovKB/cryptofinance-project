FROM python:latest

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY frontend.py .

COPY backend.py .

RUN mkdir assets

COPY style.css ./assets

COPY wait.sh .
RUN chmod +x ./wait.sh

# CMD ["python", "./frontend.py"]