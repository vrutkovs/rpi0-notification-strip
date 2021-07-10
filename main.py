import json
import os
import time
import logging
import paho.mqtt.client as mqtt
from rpi_ws281x import Color
from grove.grove_ws2813_rgb_led_strip import GroveWS2813RgbStrip, colorWipe

# connect to pin 12(slot PWM)
PIN   = 12
# For Grove - WS2813 RGB LED Strip Waterproof - 30 LED/m
# there is 30 RGB LEDs.
COUNT = 30

COLOR_BLANK = Color(0,0,0)
COLOR_RED = Color(255, 0, 0)
COLOR_BLUE = Color(0, 255, 0)
COLOR_GREEN = Color(0, 0, 255)

TOPIC=f'rpi0/notification_led'

global client
global strip
global status

bool2mqtt = {True: "ON", False: "OFF"}

def on_connect(client, userdata, flags, rc):
    logging.debug(f"Connected with result code {str(rc)}")

    logging.debug(f"Subscribed to {TOPIC}")
    client.subscribe(f"{TOPIC}/set")

    global status
    status = {
        'state': "OFF",
        'brightness': 100,
        'color': {
            'r': 0,
            'g': 0,
            'b': 125,
            'w': 0
        },
        'color_mode': 'rgb',
    }

    mqtt_publish(client, "set", status)


def on_log(client, userdata, level, buff):
    #otherwise we have silent exceptions
    logging.log(level, f"{userdata}-{buff}")


def on_subscribe(client, userdata, mid, granted_qos):
    logging.debug(f"Subscribed: {str(mid)} {str(granted_qos)}")


def on_message(client, userdata, msg):
    global status

    logging.debug(f"MESSAGE: '{str(msg.topic)}' '{str(msg.payload)}'")
    if msg.topic != f"${TOPIC}/set":
        pass

    obj = json.loads(msg.payload)
    print(f"Desired state: {obj}")
    reconcileColor(obj)
    reconcileBrightness(obj)
    reconcileState(obj)
    print(f"Final state: {status}")

    client.publish(f'{TOPIC}/status', json.dumps(status), retain=True)


def reconcileState(desired):
    global status

    if 'state' not in desired:
        return

    if desired['state'] != status.get('state'):
        if desired['state'] == 'ON':
            # Notify that LED is enabled
            colorWipe(strip, status_color_to_led(status), 10)
        else:
            colorWipe(strip, COLOR_BLANK, 10)

    status['state'] = desired['state']


def reconcileBrightness(desired):
    global status

    if 'brightness' not in desired:
        return

    if desired['brightness'] != status.get('brightness'):
        strip.setBrightness(int(desired['brightness']))
    status['brightness'] = desired['brightness']


def reconcileColor(desired):
    global status

    if 'color' not in desired:
        return

    status['color'] = desired['color']
    status['color_mode'] = 'rgb'


def status_color_to_led(status):
    return Color(
        status['color']['r'],
        status['color']['g'],
        status['color']['b']
    )


def mqtt_publish(client, topic, payload):
    logging.debug(f"Publishing {topic}: '{payload}'")
    client.publish(f'{TOPIC}/{topic}', json.dumps(payload))


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s  %(levelname)s:%(message)s', level=logging.DEBUG)
    strip = GroveWS2813RgbStrip(PIN, COUNT)
    client = mqtt.Client()
    client.on_log = on_log
    client.on_connect = on_connect
    client.on_subscribe = on_subscribe
    client.on_message = on_message
    client.username_pw_set(username=os.getenv("MQTT_USER"),password=os.getenv("MQTT_PASSWORD"))
    client.connect(os.getenv("MQTT_HOST"), 1883, 60)
    client.loop_forever()


# print ('Color wipe animations.')
# try:
#   while True:
#     colorWipe(strip, COLOR_RED)  # Red wipe
#     colorWipe(strip, COLOR_BLANK, 0)
#     colorWipe(strip, COLOR_BLUE)  # Blue wipe
#     colorWipe(strip, COLOR_BLANK, 0)
#     colorWipe(strip, COLOR_GREEN)  # Green wipe
#     colorWipe(strip, COLOR_BLANK, 0)
# except KeyboardInterrupt:
#     # clear all leds when exit
#     colorWipe(strip, COLOR_BLANK, 0)
