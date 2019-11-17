FROM python:3.7
ENV PYTHONUNBUFFERED 1
ENV EXCHANGE_BOT_TOKEN tocken
ENV EXCHANGE_MQTT_HOST mosquitto.ex-money.in.ua
ENV EXCHANGE_MQTT_USER user
ENV EXCHANGE_MQTT_PASSWORD password
RUN mkdir /config
ADD /config/requirements.pip /config/
RUN pip install -r /config/requirements.pip
RUN mkdir /src;
WORKDIR /src

