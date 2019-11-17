#!/usr/bin/env python
import os
import json
import time
import paho.mqtt.client as mqtt
import telebot

bot_token = os.environ["EXCHANGE_BOT_TOKEN"]
bot = telebot.TeleBot(bot_token)
topic_sub_state = 'customer_detector/exchanges/state/#'
events_path = "./events/"
mqtt_host = os.environ["EXCHANGE_MQTT_HOST"]
mqtt_user = os.environ["EXCHANGE_MQTT_USER"]
mqtt_password = os.environ["EXCHANGE_MQTT_PASSWORD"]
devices_heart_beat_times = {}
max_heart_interval = 23  # max heart beat interval in sec.


def on_connect(mosq, obj, flags, rc):
    mqttc.subscribe(topic_sub_state, 0)
    print("rc: " + str(rc))


def on_message(mosq, obj, msg):
    """
    get the state strings from the devices
    state string:
    {"status": "Ready", "customer": "left", "duration": 11123, "obstacles": 78}
    """
    global devices_heart_beat_times
    global events_path
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    json_string = ''
    try:
        json_string = msg.payload.decode('utf8')
    except UnicodeDecodeError:
        print("it was not a utf8-encoded unicode string")
    if is_json(json_string):
        d = json.loads(json_string)
        if 'status' in d.keys():
            detector = msg.topic.split('/')[-1]
            if detector not in devices_heart_beat_times.keys():
                bot.send_message(-1001440639497, f'heart of exchange ({detector}) started to beat')
                print(f'heart of exchange ({detector}) started to beat')
                events_fname = events_path + str(time.strftime("%Y%m%d")) + "_" + msg.topic.split('/')[-1] + '.csv'
                events_f = open(events_fname, 'a')
                events_f.write(str(time.strftime("%d.%m.%Y %H:%M:%S")) +
                               ', ' + f'heart of exchange ({detector}) started to beat' +
                               ', ' + str(0) + '\n')
                events_f.close()
            devices_heart_beat_times[detector] = time.time()


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
# mqttc.loop_forever()
mqttc.loop_start()
time.sleep(1)

while True:
    time.sleep(1)
    now = time.time()
    dhbt = devices_heart_beat_times.copy()
    for device in dhbt:
        beat_interval = now - dhbt[device]
        if beat_interval >= max_heart_interval:
            warning_msg = f'heart of exchange ({device}) stopped for more than {max_heart_interval} sec.'
            bot.send_message(-1001440639497, warning_msg)
            print(warning_msg)
            events_filename = events_path + str(time.strftime("%Y%m%d")) + "_" + device + '.csv'
            events_file = open(events_filename, 'a')
            events_file.write(str(time.strftime("%d.%m.%Y %H:%M:%S")) +
                              ', ' + warning_msg +
                              ', ' + str(0) + '\n')
            events_file.close()
            devices_heart_beat_times.pop(device)
