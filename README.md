# emu2mqtt

Export real-time energy data from a [Rainforest Automation EMU-2](https://www.rainforestautomation.com/rfa-z105-2-emu-2/)
electricity monitor to an MQTT broker — ready to consume in Home Assistant,
Node-RED, or any MQTT client.

The EMU-2 pairs with your utility smart meter over Zigbee and presents itself to
the host as a USB serial device. This script reads the EMU's XML message stream,
decodes the instantaneous demand and cumulative meter readings, and republishes
them as simple MQTT topics.

## What it publishes

All topics are prefixed with the root topic (`--mqtt_topic`, default `emu2mqtt`):

| Topic | Meaning | Units |
|-------|---------|-------|
| `<root>/lwt` | Connection status — `online` / `offline` (retained, MQTT Last Will) | — |
| `<root>/demand` | Instantaneous power draw (negative = exporting to grid) | Watts |
| `<root>/reading` | Net cumulative meter reading (`delivered − received`) | kWh |
| `<root>/readingd` | Cumulative energy **delivered** to you | kWh |
| `<root>/readingr` | Cumulative energy **received** from you (e.g. solar export) | kWh |
| `<root>/price` | Current price reported by the meter (only if price data is enabled) | $/kWh |

Each value is published only when the EMU reports a newer timestamp than the
last one sent, so the broker isn't spammed with duplicates. The `lwt` topic lets
Home Assistant mark the sensors unavailable if the bridge goes offline.

## How it works

- `emu2mqtt.py` — the bridge: connects to MQTT, reads decoded values from the EMU
  object, and publishes them in a loop. Resilient to broker / Home Assistant
  restarts — it keeps reconnecting and resumes publishing automatically.
- `emu.py` — a serial driver for the EMU-2 (based on Rainforest's Emu-Serial-API).
  Runs a background thread that reads the device's XML output and exposes the
  latest `InstantaneousDemand`, `CurrentSummationDelivered`, `PriceCluster`, etc.
- `api_classes.py` — lightweight classes the XML blocks are parsed into.

## Requirements

- Python 3
- An EMU-2 connected over USB and paired with your smart meter
- An MQTT broker (e.g. Mosquitto, or the Home Assistant Mosquitto add-on)

Install dependencies:

```sh
pip install -r requirements.txt
```

## Usage

```sh
python3 emu2mqtt.py \
    --mqtt_server 192.168.50.178 \
    --mqtt_port 1883 \
    --mqtt_username pub \
    --mqtt_password mqttpub \
    --serial_port ttyACM0
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--mqtt_server` | `192.168.50.178` | MQTT broker host |
| `--mqtt_port` | `1883` | MQTT broker port |
| `--mqtt_username` | `pub` | MQTT username |
| `--mqtt_password` | `mqttpub` | MQTT password |
| `--mqtt_client_name` | `emu2mqtt` | MQTT client ID |
| `--mqtt_topic` | `emu2mqtt` | Root topic for all published values |
| `--mqtt_qos` | `0` | MQTT QoS level |
| `--serial_port` | `ttyACM0` | Serial device the EMU-2 enumerates as (Linux: under `/dev/`, e.g. `ttyACM0`; Windows: a COM port number) |

On Linux the EMU-2 usually appears as `/dev/ttyACM0`. Check `dmesg` or
`ls /dev/ttyACM*` after plugging it in. Run as a `systemd` service to keep it
alive across reboots.

### Home Assistant example

Once the bridge is publishing, add MQTT sensors:

```yaml
mqtt:
  sensor:
    - name: "Home Power Demand"
      state_topic: "emu2mqtt/demand"
      unit_of_measurement: "W"
      device_class: power
      availability_topic: "emu2mqtt/lwt"
    - name: "Home Energy Meter"
      state_topic: "emu2mqtt/reading"
      unit_of_measurement: "kWh"
      device_class: energy
      state_class: total_increasing
      availability_topic: "emu2mqtt/lwt"
```

## Attribution
- This script is derived from the excellent [emu2influx](https://github.com/abaker/emu2influx) project by Alex Baker. Credit for the basic flow of the script and EMU API interaction goes to him.
- This script uses the [Emu-Serial-API](https://github.com/rainforestautomation/Emu-Serial-API) by Rainforest Automation.
