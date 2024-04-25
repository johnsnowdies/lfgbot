FROM python:3.10

ENV PYTHONPATH /app
ENV APP_DIR /app

COPY ./app /app

WORKDIR $APP_DIR
RUN pip install -r /app/requirements.txt

CMD ["python3", "/app/main.py"]
