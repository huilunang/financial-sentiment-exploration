FROM python:3.9-slim

COPY . /social_media_stocks_reading
WORKDIR /social_media_stocks_reading

ENV VENV_DIR="venv_social_media_stocks_reading"
RUN ./setup.sh

ENTRYPOINT ["./entrypoint.sh"]
