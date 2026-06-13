#!/usr/bin/env python2

## emu2mqtt
# Export Rainforest Automation EMU-2 energy monitoring data to MQTT

## Attribution
# This script is derived from the excellent [emu2influx](https://github.com/abaker/emu2influx) project by Alex Baker. Credit for the basic flow of the script and EMU API interaction goes to him.
# This script uses the [Emu-Serial-API](https://github.com/rainforestautomation/Emu-Serial-API) by Rainforest Automation.

import logging
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
from emu import *
import signal
import sys

mqtt.Client.connected_flag = False
mqtt.Client.bad_connection_flag = False

Y2K = 946684800

def get_timestamp(obj):
    return datetime.utcfromtimestamp(Y2K + int(obj.TimeStamp, 16)).isoformat()

def get_reading(reading, obj):
    value = int(reading, 16)
    if value & (1 << ((len(reading)-2) * 4 - 1)):
        value -= 1 << ((len(reading)-2) * 4) 
    return value * int(obj.Multiplier, 16) / float(int(obj.Divisor, 16))

def get_price(obj):
    return int(obj.Price, 16) / float(10 ** int(obj.TrailingDigits, 16))

def publish_message(mqttc, message):
    # Returns True only if the message was handed to the broker successfully.
    # We deliberately do NOT call wait_for_publish(): in paho-mqtt 1.4.0 that
    # call blocks forever if the socket has dropped (e.g. the broker restarts
    # with Home Assistant), which silently freezes the whole reporting loop.
    if not mqttc.connected_flag:
        logging.warning("Skipping publish to %s, MQTT not connected", message["topic"])
        return False
    logging.info(message)
    publish_msg = mqttc.publish(message["topic"], message["value"], int(args.mqtt_qos), False)
    if publish_msg.rc != mqtt.MQTT_ERR_SUCCESS:
        logging.warning("Publish to %s failed, rc=%s", message["topic"], publish_msg.rc)
        return False
    return True

def on_sigint(sig, frame):
    global exiting
    if not exiting:
        exiting = True
        logging.info("Caught a SIGINT, cleaning up and exiting")
        mqttc.loop_stop()
        mqttc.disconnect()
        emuc.stop_serial()
        time.sleep(4)
        sys.exit()

def on_mqtt_connect(client, userdata, flags, result):
    if result == 0:
        logging.info("Connected to MQTT.")
        client.connected_flag = True
        client.bad_connection_flag = False
    else:
        # A non-zero CONNACK is often transient (e.g. the broker is mid-restart
        # with Home Assistant and returns "server unavailable"). Log it but let
        # paho keep retrying rather than treating it as fatal.
        logging.warning("Error on MQTT connect: " + str(result) + " (will keep retrying)")
        client.connected_flag = False

def on_mqtt_disconnect(client, userdata, result):
    if result != 0:
        logging.error("MQTT disconnected, error " + str(result))
        client.connected_flag = False

def main():
    signal.signal(signal.SIGINT, on_sigint)

    mqttc.on_connect = on_mqtt_connect
    mqttc.on_disconnect = on_mqtt_disconnect
    mqttc.will_set(args.mqtt_topic + "/lwt", "offline", int(args.mqtt_qos), True)
    mqttc.username_pw_set(args.mqtt_username, args.mqtt_password)
    # Bounded exponential backoff so reconnects keep trying after a broker/HA
    # restart instead of giving up or hammering the broker.
    mqttc.reconnect_delay_set(min_delay=1, max_delay=60)
    mqttc.connect_async(args.mqtt_server, int(args.mqtt_port), 60)

    emuc.start_serial()
    logging.info("Connected to EMU serial")
    emuc.get_instantaneous_demand('Y')
    emuc.get_current_summation_delivered()
   # emuc.get_price_blocks()

    # ISO-8601 timestamps compare correctly as strings, so seed with "" to mean
    # "nothing published yet". (Using 0 here forced a str > int comparison that
    # raised TypeError on every reading and was only masked by the duplicated
    # "== 0" special cases below.)
    last_demand = ""
    last_price = ""
    last_reading = ""

    mqttc.loop_start()
    logging.info("Connecting to MQTT broker " + args.mqtt_server + ":" + str(args.mqtt_port) + " as " + args.mqtt_client_name)

    while True:
        # Wait for the (re)connection to come back. paho's loop_start() thread
        # handles the actual reconnect/backoff; we just pause publishing until
        # connected_flag flips back to True. We never exit here so the daemon
        # survives a broker/Home Assistant restart.
        while not mqttc.connected_flag:
            logging.debug("Waiting to connect to MQTT...")
            time.sleep(3)

        #logging.debug("Sleeping for 1 seconds")
        time.sleep(1)
        #logging.debug("Checking for serial messages")

        if mqttc.connected_flag:
            mqttc.publish(args.mqtt_topic + "/lwt", "online", int(args.mqtt_qos), True)

        try:
            price_cluster = emuc.PriceCluster
            timestamp = get_timestamp(price_cluster)
            if timestamp > last_price:
                message = {
                    "topic": args.mqtt_topic + "/price",
                    "value": get_price(price_cluster),
                    "timestamp": timestamp
                }
                # Only advance the watermark if the value actually went out, so a
                # reading dropped during a disconnect is re-sent after reconnect.
                if publish_message(mqttc, message):
                    last_price = timestamp
        except AttributeError:
            pass
        except TypeError:
            pass

        try:
            instantaneous_demand = emuc.InstantaneousDemand
            timestamp = get_timestamp(instantaneous_demand)
            if timestamp > last_demand:
                message = {
                    "topic": args.mqtt_topic + "/demand",
                    "value": get_reading(instantaneous_demand.Demand, instantaneous_demand)*1000,
                    "timestamp": timestamp
                }
                if publish_message(mqttc, message):
                    last_demand = timestamp

        except AttributeError:
            pass
        except TypeError:
            pass

        try:
            current_summation_delivered = emuc.CurrentSummationDelivered
            timestamp = get_timestamp(current_summation_delivered)
            if timestamp > last_reading:
                delivered = get_reading(current_summation_delivered.SummationDelivered,
                                         current_summation_delivered)
                recieved = get_reading(current_summation_delivered.SummationReceived,
                                         current_summation_delivered)
                reading = delivered - recieved
                ok = publish_message(mqttc, {
                    "topic": args.mqtt_topic + "/reading",
                    "value": reading,
                    "timestamp": timestamp
                })
                ok = publish_message(mqttc, {
                    "topic": args.mqtt_topic + "/readingd",
                    "value": delivered,
                    "timestamp": timestamp
                }) and ok
                ok = publish_message(mqttc, {
                    "topic": args.mqtt_topic + "/readingr",
                    "value": recieved,
                    "timestamp": timestamp
                }) and ok
                # Only advance once all three sub-readings made it out.
                if ok:
                    last_reading = timestamp
        except AttributeError:
            pass
        except TypeError:
            pass
            
            
            

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action='store_true', help="enable debug logging", required=False)
    parser.add_argument("--mqtt_client_name", help="MQTT client name", required=False, default='emu2mqtt')
    parser.add_argument("--mqtt_server", help="MQTT server", required=False, default='192.168.50.178')
    parser.add_argument("--mqtt_port", help="MQTT server port", required=False, default=1883)
    parser.add_argument("--mqtt_username", help="MQTT username", required=False, default='pub')
    parser.add_argument("--mqtt_password", help="MQTT password", required=False, default='mqttpub')
    parser.add_argument("--mqtt_topic", help="MQTT root topic", required=False, default='emu2mqtt')
    parser.add_argument("--mqtt_qos", help="MQTT QoS", required=False, default=0)
    parser.add_argument("--serial_port", help="Rainforest EMU-2 serial port, e.g. 'ttyACM0'", required=False, default='ttyACM0')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    logging.basicConfig(level=('DEBUG' if args.debug else 'INFO'),
                        format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')
    emuc = emu(args.serial_port)
    mqttc = mqtt.Client(args.mqtt_client_name)
    exiting = False
    main()

