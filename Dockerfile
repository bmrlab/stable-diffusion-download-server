FROM python:3.9

WORKDIR /app
COPY main.py /app

ENV PORT=8000
EXPOSE $PORT


CMD uvicorn main:app --reload --port ${PORT}