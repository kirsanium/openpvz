FROM python:3.11.4-slim
WORKDIR /opt/openpvz

COPY ./src/telegram_bot/requirements.txt .
COPY ./src/core/requirements.txt ./requirements.core.txt
RUN pip install --no-cache-dir --upgrade -r ./requirements.txt -r requirements.core.txt
COPY ./src/core/ ./core/
COPY ./src/telegram_bot/ .
RUN pybabel compile -d locale

CMD ["python", "app.py"]
