#!/usr/bin/env python
import os
import json
import time
import paho.mqtt.client as mqtt
from datetime import datetime
from pytz import timezone

fmt = "%Y-%m-%d %H:%M:%S %Z%z"

# Current time in UTC
now_utc = datetime.now(timezone('UTC'))
print(now_utc.strftime(fmt))

# Convert to US/Pacific time zone
now_pacific = now_utc.astimezone(timezone('US/Pacific'))
print(now_pacific.strftime(fmt))

# Convert to Europe/Berlin time zone
now_kiev = now_pacific.astimezone(timezone('Europe/Kiev'))
print(now_kiev.strftime(fmt))

topic_sub_events = 'customer_detector/exchanges/events/#'

mqtt_host = os.environ["EXCHANGE_MQTT_HOST"]
mqtt_user = os.environ["EXCHANGE_MQTT_USER"]
mqtt_password = os.environ["EXCHANGE_MQTT_PASSWORD"]
events_path = "./events/"


def on_connect(mosq, obj, flags, rc):
    mqttc.subscribe(topic_sub_events, 0)
    print("rc: " + str(rc))


def on_message(mosq, obj, msg):
    """
    get the events strings from device
    events string:
    {"event": "Customer arraived", "duration": 11125}
    or
    {"event": "heart of exchange stopped for more then .. sec", "duration": 23000}
    or
    {"event": "heart of exchange started to beat", "duration": 171257}
    """
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    json_string = ''
    try:
        json_string = msg.payload.decode('utf8')
    except UnicodeDecodeError:
        print("it was not a utf8-encoded unicode string")
    if is_json(json_string):
        d = json.loads(json_string)
        now_utc = datetime.now(timezone('UTC'))
        now_pacific = now_utc.astimezone(timezone('US/Pacific'))
        now_kiev = now_pacific.astimezone(timezone('Europe/Kiev'))
        # events_filename = events_path + str(time.strftime("%Y%m%d")) + "_" + msg.topic.split('/')[-1] + '.csv'
        events_filename = events_path + str(now_kiev.strftime("%Y%m%d")) + "_" + msg.topic.split('/')[-1] + '.csv'
        if 'event' in d.keys():
            events_file = open(events_filename, 'a')

            # events_file.write(str(time.strftime("%d.%m.%Y %H:%M:%S %Z")) +
            events_file.write(str(now_kiev.strftime("%d.%m.%Y %H:%M:%S %Z")) +
                              ', ' + str(d['event']) +
                              ', ' + str(d['duration']) + '\n')
            # print(str(time.strftime("%d.%m.%Y %H:%M:%S %Z")) +
            print(str(now_kiev.strftime("%d.%m.%Y %H:%M:%S %Z")) +
                  ', ' + str(d['event']) +
                  ', ' + str(d['duration']) + '\n')
            events_file.close()


def on_publish(mosq, obj, mid):
    print("mid: " + str(mid))


def on_subscribe(mosq, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))


def on_log(mosq, obj, level, string):
    print(string)


def is_json(myjson):
    try:
        _ = json.loads(myjson)
    except ValueError:
        return False
    return True


mqttc = mqtt.Client()
# Assign event callbacks
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_publish = on_publish
mqttc.on_subscribe = on_subscribe
# mqttc.on_log = on_log
mqttc.username_pw_set(mqtt_user, password=mqtt_password)
# Connect
mqttc.connect(mqtt_host, 1883, 60)
# Continue the network loop
mqttc.loop_forever()
# mqttc.loop_start()
# time.sleep(1)

while True:
    pass

    # TODO: You can do in the main loop monitoring of "main" monitor
