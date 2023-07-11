FROM python:3.9

WORKDIR /app
COPY main.py /app
COPY requirements.txt /app

RUN pip3 install -r requirements.txt

ENV PORT=8000
EXPOSE $PORT


CMD uvicorn main:app --reload --port ${PORT}