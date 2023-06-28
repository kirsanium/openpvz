FROM python:3.11.4-slim AS migrations

RUN apt-get update && apt-get install -y wait-for-it
RUN pip install --no-cache-dir --upgrade yoyo-migrations psycopg[binary] geoalchemy2
COPY ./yoyo.ini ./yoyo.ini
COPY ./migrations ./migrations
# не знаю, почему, но работает только с флагом '-c yoyo.ini', хотя должно работать без него
CMD ["wait-for-it", "db:5432", "--", "yoyo", "apply", "-c", "yoyo.ini"]
